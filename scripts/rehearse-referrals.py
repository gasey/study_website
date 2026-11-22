#!/usr/bin/env python3
"""Fresh Oracle dump clone, pending migrations only; no production mutations."""
from pathlib import Path
from uuid import uuid4
import hashlib,json,re,shlex,shutil,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finna-referrals-staged-20261119'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args,**kwargs):
    r=subprocess.run(args,capture_output=True,text=True,**kwargs)
    if r.returncode:raise RuntimeError(r.stderr[-4000:])
    return r.stdout

def remote(stage):
    import asyncio,os,psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
    os.chdir('/')
    scope=json.loads((stage/'scope.json').read_text())
    assert sha(stage/'rehearse.py')==scope['operator_sha256']
    assert all(sha(stage/'api'/n)==h for n,h in scope['source_sha256'].items())
    assert sha(Path('/srv/api/migrations/0110_site_maintenance.sql'))=='a032554cfb2464b8cc23c6f5af851b1a265c9b1523593e2196835b94622ddb40'
    assert sha(Path('/srv/api/migrations/0120_review_digest.sql'))=='92519b14a942458e428cba72114282905ae0dfbaf575fdb9ceb7ee409a8813f5'
    assert not Path('/srv/api/migrations/0111_desk_weekly_goals.sql').exists()
    assert not Path('/srv/api/migrations/0121_referral_access.sql').exists()
    name='finna_referrals_'+uuid4().hex[:12];admin=psycopg.connect('dbname=postgres',autocommit=True);created=False
    result={'migration_ms':{},'already_applied_skipped':[]}
    def fingerprints(conn,definitions):
        output={}
        for table,columns in definitions:
            digest=hashlib.sha256();count=0
            query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(table))
            with conn.cursor(name='ref_fp_'+uuid4().hex) as cur:
                cur.execute(query)
                for row in cur:digest.update(row[0].encode());count+=1
            output[table]={'count':count,'sha256':digest.hexdigest()}
        return output
    try:
        with tempfile.TemporaryDirectory(prefix='finna-referrals-clone-') as directory:
            root=Path(directory);dump=root/'workflow.dump'
            with dump.open('wb') as output:subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
            subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],check=True,capture_output=True,timeout=600)
            candidate=root/'api';shutil.copytree(stage/'api',candidate)
            with psycopg.connect('dbname='+name) as conn:
                definitions=conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN(SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
                before=fingerprints(conn,definitions)
            with psycopg.connect('dbname='+name,autocommit=True) as conn:
                for migration in sorted((candidate/'migrations').glob('*.sql')):
                    live=Path('/srv/api/migrations')/migration.name
                    if live.exists():
                        assert sha(live)==sha(migration),'Applied migration differs: '+migration.name
                        result['already_applied_skipped'].append(migration.name);continue
                    assert 111<=int(migration.name[:4])<=121 and not migration.name.startswith('0120_')
                    started=time.perf_counter();conn.execute(migration.read_text());result['migration_ms'][migration.name]=round((time.perf_counter()-started)*1000,3)
            sys.path.insert(0,str(candidate))
            from app.services import referrals,account_tools,reward_economy
            from app.config import settings
            assert reward_economy.reconciled_release(),'Source-bound evidence is stale'
            async def probe():
                async with await psycopg.AsyncConnection.connect('dbname='+name,row_factory=dict_row) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute('SET LOCAL ROLE mpsc')
                        assert not await referrals.available(cur),'Default referral gate must be closed'
                        tag=uuid4().hex;inviter='ref_clone_'+tag;friend='ref_friend_'+tag
                        for user in (inviter,friend):await cur.execute('INSERT INTO users(id,handle,email,email_verified_at) VALUES(%s,%s,%s,now())',(user,user,user+'@example.invalid'))
                        async def synthetic_launch_ready(cur):return True
                        referrals.launch_ready=synthetic_launch_ready;settings.referral_rewards_enabled=True
                        state=await referrals.set_code(cur,inviter,0,True);code=state['code']['code']
                        assert (await referrals.attach_signup(cur,friend,code))['state']=='pending'
                        await cur.execute('SELECT * FROM referral_claims WHERE referred_id=%s FOR UPDATE',(friend,));claim=await cur.fetchone()
                        assert not await referrals.decide(cur,claim),'Zero answers must not credit'
                        assert await referrals.attempts(cur,friend,claim['created_at'])==[]
                        stamp=await referrals.clock(cur)
                        grant=await referrals.grant(cur,friend,'synthetic-rehearsal-only',stamp)
                        await cur.execute('SELECT source,granted_by,days,ends_at-starts_at AS duration FROM billing_access_grants WHERE id=%s',(grant,));g=await cur.fetchone()
                        assert g['source']=='referral' and g['granted_by'] is None and g['days']==g['duration'].days==7
                        assert (await referrals.set_code(cur,inviter,1,False))['code']['enabled'] is False
                        assert not (await referrals.public(cur,code))['available']
                        await cur.execute("SELECT has_table_privilege('mpsc','referral_claims','DELETE') AS claims,has_table_privilege('mpsc','referral_decisions','UPDATE') AS decisions")
                        assert not any((await cur.fetchone()).values())
                        await conn.rollback()
                        return {'real_role':'mpsc','default_gate_closed':True,'synthetic_launch_override_probe_only':True,'signup_only_claim':True,'zero_answers_no_credit':True,'seven_day_source_and_null_actor':True,'explicit_invitation_withdrawal':True,'least_privileges':True,'rolled_back':True}
            result['probe']=asyncio.run(probe())
            with psycopg.connect('dbname='+name) as conn:
                assert before==fingerprints(conn,definitions),'Original data changed'
                assert all(conn.execute('SELECT count(*) FROM '+t).fetchone()[0]==0 for t in ('referral_codes','referral_claims','referral_decisions'))
            result|={'existing_tables_checked':len(before),'all_original_rows_identical':True,'before':before}
    finally:
        if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
        admin.close()
    return result|{'source_sha256':scope['source_sha256'],'production_database_writes':False,'production_api_changed':False,'clone_and_dump_removed':True,'workers_started':False,'smtp_started':False}

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--remote':
        stage=Path(sys.argv[2]);receipt=remote(stage);(stage/'result.json').write_text(json.dumps(receipt)+'\n');print(json.dumps(receipt));return
    assert len(sys.argv)==1;REPORT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='finna-referrals-package-') as directory:
        package=Path(directory);sources={}
        for base in ('app','migrations'):
            for path in sorted((ROOT/'api'/base).rglob('*')):
                if not path.is_file() or path.suffix not in ('.py','.json','.sql'):continue
                name=str(path.relative_to(ROOT/'api'));target=package/'api'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);sources[name]=sha(target)
        shutil.copy2(__file__,package/'rehearse.py');(package/'scope.json').write_text(json.dumps({'source_sha256':sources,'operator_sha256':sha(package/'rehearse.py')}));(package/'result.json').touch()
        host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-referrals-stage.XXXXXX']).strip()
        assert re.fullmatch(r'/tmp/finna-referrals-stage\.[A-Za-z0-9]+',stage)
        try:
            run(['rsync','-az',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod -R a+rX '+shlex.quote(stage)+' && chmod a+w '+shlex.quote(stage+'/result.json')])
            receipt=run(['ssh',host,'sudo -u postgres /srv/api/.venv/bin/python '+shlex.quote(stage+'/rehearse.py')+' --remote '+shlex.quote(stage)],timeout=1500)
            parsed=json.loads(receipt);(REPORT/'clone.json').write_text(json.dumps(parsed,indent=2)+'\n');print(json.dumps({k:v for k,v in parsed.items() if k not in ('before','source_sha256','already_applied_skipped')}))
        finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':main()
