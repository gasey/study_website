#!/usr/bin/env python3
"""Fresh dump clone, only 0120, production-only source; never starts workers."""
import hashlib,json,os,re,shlex,subprocess,sys,tempfile,time
from pathlib import Path
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finna-review-digest-production-20261119'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,**kw):
    r=subprocess.run(args,capture_output=True,text=True,**kw)
    if r.returncode:raise RuntimeError(r.stderr[-3000:])
    return r.stdout
def fingerprints(conn,definitions):
    from psycopg import sql
    result={}
    for table,columns in definitions:
        h=hashlib.sha256();n=0
        query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(table))
        with conn.cursor(name='fp_'+uuid4().hex) as cur:
            cur.execute(query)
            for row in cur:h.update(row[0].encode());n+=1
        result[table]={'count':n,'sha256':h.hexdigest()}
    return result
def remote(stage):
    import asyncio,psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
    from cryptography.fernet import Fernet
    scope=json.loads((stage/'scope.json').read_text())
    assert sha(stage/'rehearse.py')==scope['operator_sha256']
    assert all(sha(stage/'api'/n)==h for n,h in scope['api'].items())
    name='finna_digest_'+uuid4().hex[:12];admin=psycopg.connect('dbname=postgres',autocommit=True);created=False
    try:
        with tempfile.TemporaryDirectory(prefix='finna-digest-clone-') as tmp:
            dump=Path(tmp)/'workflow.dump'
            with dump.open('wb') as f:subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=f,check=True,timeout=600)
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
            subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],check=True,capture_output=True,timeout=600)
            with psycopg.connect('dbname='+name) as conn:
                definitions=conn.execute("SELECT c.relname,array_agg(a.attname ORDER BY a.attnum) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped WHERE n.nspname='public' AND c.relkind IN ('r','p') GROUP BY c.relname ORDER BY c.relname").fetchall()
                before=fingerprints(conn,definitions)
                started=time.perf_counter();conn.execute((stage/'api/migrations/0120_review_digest.sql').read_text());elapsed=round((time.perf_counter()-started)*1000,3)
                assert conn.execute('SELECT count(*) FROM review_digest_preferences').fetchone()[0]==0
            os.chdir('/');sys.path.insert(0,str(stage/'api'))
            from app.config import settings
            from app.services import review_digest,account_mail,reward_economy,mfa
            assert reward_economy.reconciled_release()
            settings.review_digest_enabled=True;settings.account_mail_enabled=True
            settings.smtp_host='synthetic.invalid';settings.smtp_from='synthetic@example.invalid'
            settings.mfa_encryption_key=Fernet.generate_key().decode()
            async def probe():
                async with await psycopg.AsyncConnection.connect('dbname='+name,row_factory=dict_row) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute('SET LOCAL ROLE mpsc')
                        await cur.execute('SELECT id FROM users WHERE email IS NOT NULL AND closed_at IS NULL ORDER BY id LIMIT 1');user=(await cur.fetchone())['id']
                        assert not (await review_digest.status(cur,user))['enabled']
                        await cur.execute('UPDATE users SET email_verified_at=now() WHERE id=%s',(user,))
                        assert (await review_digest.consent(cur,user,0,True))['version']==1
                        await cur.execute('SELECT token_cipher FROM review_digest_preferences WHERE user_id=%s',(user,));raw=mfa.decrypt(user,(await cur.fetchone())['token_cipher'])
                        await review_digest.unsubscribe(cur,raw)
                        assert not (await review_digest.status(cur,user))['enabled']
                        assert await review_digest.due(cur,user)>=0
                        budget=await account_mail.capacity(cur)
                        await conn.rollback()
                        return {'real_role':'mpsc','consent_unsubscribe_due_and_shared_capacity':True,'rolled_back':True,'day_used':budget['day_used'],'month_used':budget['month_used']}
            probe_result=asyncio.run(probe())
            with psycopg.connect('dbname='+name) as conn:
                assert before==fingerprints(conn,definitions),'Original rows changed'
                assert conn.execute('SELECT count(*) FROM review_digest_preferences').fetchone()[0]==0
                assert conn.execute("SELECT to_regclass('public.atlas_chapters')").fetchone()[0] is None
            result={'existing_tables_checked':len(before),'all_existing_rows_identical':True,'before':before,'migration':'0120_review_digest.sql','migration_ms':elapsed,'only_0120_applied':True,'desk_atlas_migrations_excluded':True,'default_subscriptions':0,'probe':probe_result,'candidate_sha256':scope['api'],'production_database_writes':False,'production_api_changed':False,'smtp_contacted':False,'workers_started':False}
    finally:
        if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
        admin.close()
    result['clone_and_dump_removed']=True
    return result
def main():
    if len(sys.argv)>1:
        result=remote(Path(sys.argv[2]));print(json.dumps(result));return
    package=Path(json.loads((REPORT/'package-path.json').read_text())['path'])
    names={str(p.relative_to(package/'api')):sha(p) for part in ('app','migrations') for p in (package/'api'/part).rglob('*') if p.suffix in ('.py','.json','.sql')}
    host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-digest-clone-stage.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-digest-clone-stage\.[A-Za-z0-9]+',stage)
    with tempfile.TemporaryDirectory(prefix='finna-digest-clone-package-') as tmp:
        local=Path(tmp);(local/'scope.json').write_text(json.dumps({'api':names,'operator_sha256':sha(Path(__file__))}))
        try:
            run(['rsync','-az','--exclude=__pycache__/','--exclude=.venv/','--exclude=tests/',str(package/'api')+'/',host+':'+stage+'/api/'])
            run(['scp','-q',str(Path(__file__)),host+':'+stage+'/rehearse.py']);run(['scp','-q',str(local/'scope.json'),host+':'+stage+'/scope.json'])
            run(['ssh',host,'chmod -R a+rX '+shlex.quote(stage)])
            raw=run(['ssh',host,'sudo -u postgres /srv/api/.venv/bin/python '+shlex.quote(stage+'/rehearse.py')+' --remote '+shlex.quote(stage)],timeout=1500)
            result=json.loads(raw);(REPORT/'clone.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({k:v for k,v in result.items() if k not in ('before','candidate_sha256')}))
        finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':main()
