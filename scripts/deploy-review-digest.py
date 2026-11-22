#!/usr/bin/env python3
"""Bounded growth release. Keep shared capacity writers on digest withdrawal."""
import fcntl,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen

VERSION='0120_review_digest'
MIGRATION='migrations/'+VERSION+'.sql'
ROOT=Path('/srv/api');PUBLIC=Path('/srv/study/public');ENV=Path('/etc/mpsc/db.env')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def inventory(root):
    assert not any(p.is_symlink() for p in root.rglob('*'))
    return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
def api_inventory(root,scope):
    names=set(scope['prior_api'])
    names.update(str(p.relative_to(root)) for part in ('app','migrations') for p in (root/part).rglob('*') if p.suffix in ('.py','.json','.sql'))
    return {n:sha(root/n) for n in sorted(names)}
def guard(scope,released=False):
    wanted=dict(scope['prior_api'])
    if released:wanted.update(scope['api'])
    assert api_inventory(ROOT,scope)==wanted,'API source drift; refused'
def run(args,**kwargs):
    r=subprocess.run(args,capture_output=True,**kwargs)
    if r.returncode:raise RuntimeError('Operator subprocess failed: '+args[0])
    return r
def sql(query):return run(['sudo','-u','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-d','mpsc'],input=query.encode()).stdout.decode().strip()
def atomic_bytes(data,path,private=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.finna-digest-',dir=path.parent)
    try:
        os.fchmod(fd,0o600 if private else 0o644)
        if private:os.fchown(fd,0,path.stat().st_gid)
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def env_value(data,enabled):
    lines=data.decode().splitlines();old=[l for l in lines if l.startswith('REVIEW_DIGEST_ENABLED=')]
    assert len(old)<=1 and (not old or old[0] in ('REVIEW_DIGEST_ENABLED=true','REVIEW_DIGEST_ENABLED=false')),'Unexpected digest configuration'
    lines=[l for l in lines if not l.startswith('REVIEW_DIGEST_ENABLED=')]
    return ('\n'.join(lines)+f'\nREVIEW_DIGEST_ENABLED={str(enabled).lower()}\n').encode()
def health():
    for attempt in range(15):
        try:
            checks=[]
            for url in ('https://study.hawayu.in/api/health','https://study.hawayu.in/','https://family.hawayu.in/','https://study.hawayu.in/api/auth/recovery/status'):
                with urlopen(url,timeout=8) as r:
                    assert r.status==200
                    row={'url':url,'status':r.status}
                    if url.endswith('/recovery/status'):row['body']=json.load(r);assert row['body']=={'available':True}
                    checks.append(row)
            return checks
        except Exception:
            if attempt==14:raise
            time.sleep(1)
def restore(backup,scope):
    # Never restore an older mail capacity reader after digest reservations exist.
    guard(scope,True)
    assert inventory(PUBLIC)==scope['served_web'],'Newer static release; refused'
    assert inventory(backup/'public')==scope['prior_web'],'Corrupt prior static; refused'
    assert ENV.read_bytes()==env_value((backup/'db.env.before').read_bytes(),True),'Mail environment drift; refused'
    for n,h in scope.get('protected',{}).items():
        if n!=str(ENV):assert sha(Path(n))==h,'Protected configuration drift; refused'
    run(['systemctl','stop','ism-api'])
    try:
        atomic_bytes(env_value((backup/'db.env.before').read_bytes(),False),ENV,True)
        run(['rsync','-a','--delete',str(backup/'public')+'/',str(PUBLIC)+'/'])
        guard(scope,True)
    finally:run(['systemctl','start','ism-api'])
    assert inventory(PUBLIC)==scope['prior_web']
    return {'digest_withdrawn':True,'compatible_api_and_capacity_retained':True,'history_and_migration_retained':True,'health':health()}
def remote(stage,check_only=False):
    assert os.geteuid()==0
    lock=open('/run/lock/finna-digest-release.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    scope=json.loads((stage/'scope.json').read_text())
    assert sha(stage/'deploy.py')==scope['operator_sha256']
    assert sha(stage/'verify.py')==scope['verifier_sha256']
    assert inventory(stage/'api')==scope['api'] and inventory(stage/'web')==scope['built_web']
    guard(scope);assert inventory(PUBLIC)==scope['prior_web'],'Static drift; refused'
    for n,h in scope['protected'].items():assert sha(Path(n))==h,'Protected configuration drift; refused'
    assert not sql("SELECT checksum FROM schema_migrations WHERE version='"+VERSION+"'")
    assert sql("SELECT checksum FROM schema_migrations WHERE version='0110_site_maintenance'")=='a032554cfb2464b8cc23c6f5af851b1a265c9b1523593e2196835b94622ddb40'
    assert not (ROOT/'migrations/0111_desk_weekly_goals.sql').exists()
    assert shutil.disk_usage('/root').free>8*1024**3
    assert ENV.stat().st_uid==0 and ENV.stat().st_mode&0o777==0o600
    assert b'ACCOUNT_MAIL_ENABLED="true"' in ENV.read_bytes()
    env_value(ENV.read_bytes(),True)
    run(['systemctl','is-active','--quiet','ism-api'])
    if check_only:return {'preflight_passed':True,'production_writes':False}
    backup=Path(tempfile.mkdtemp(prefix='finna-digest-backup-',dir='/root'))
    for n in ('scope.json','deploy.py','verify.py'):shutil.copy2(stage/n,backup/n)
    shutil.copytree(PUBLIC,backup/'public')
    shutil.copytree(stage/'api',backup/'released-api')
    (backup/'db.env.before').write_bytes(ENV.read_bytes());os.chmod(backup/'db.env.before',0o600)
    for n in scope['api']:
        if (ROOT/n).exists():target=backup/'api'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,target)
    with (backup/'database.dump').open('wb') as f:subprocess.run(['sudo','-u','postgres','pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=f,check=True,timeout=600)
    applied=False;stopped=False
    try:
        guard(scope);assert inventory(PUBLIC)==scope['prior_web']
        for n,h in scope['protected'].items():assert sha(Path(n))==h
        run(['systemctl','stop','ism-api']);stopped=True
        migration=(stage/'api'/MIGRATION).read_text().strip();assert migration.startswith('BEGIN;') and migration.endswith('COMMIT;')
        body=migration.removeprefix('BEGIN;').removesuffix('COMMIT;')
        sql("BEGIN; SET LOCAL lock_timeout='5s'; SET LOCAL statement_timeout='30s'; SELECT pg_advisory_xact_lock(hashtextextended('finna-schema-migrations',0)); "+body+" INSERT INTO schema_migrations(version,checksum) VALUES('"+VERSION+"','"+scope['api'][MIGRATION]+"'); COMMIT;")
        applied=True
        assert sql('SELECT count(*) FROM review_digest_preferences')=='0'
        for n in scope['api']:atomic_bytes((stage/'api'/n).read_bytes(),ROOT/n)
        atomic_bytes(env_value((backup/'db.env.before').read_bytes(),True),ENV,True)
        guard(scope,True);run(['systemctl','start','ism-api']);stopped=False;checks=health()
        verification=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],text=True).stdout)
        run(['rsync','-a','--exclude=index.html',str(stage/'web')+'/',str(PUBLIC)+'/'])
        atomic_bytes((stage/'web/index.html').read_bytes(),PUBLIC/'index.html')
        run(['chown','-R','caddy:caddy',str(PUBLIC)])
        assert inventory(PUBLIC)==scope['served_web'];guard(scope,True)
        for n,h in scope['protected'].items():
            if n!=str(ENV):assert sha(Path(n))==h
        receipt={'backup':str(backup),'migration':VERSION,'migration_sha256':scope['api'][MIGRATION],'api_files_changed':list(scope['api']),'built_web_files':len(scope['built_web']),'served_web_files':len(scope['served_web']),'prior_chunks_retained':True,'staged_desk_atlas_excluded':True,'default_subscribed_accounts':0,'review_digest_feature_enabled':True,'account_mail_preserved_enabled':True,'only_digest_environment_value_changed':True,'existing_credentials_preserved':True,'health':checks,'verification':verification,'synthetic_production_activity':False,'test_email_sent':False,'database_rollback':False}
        (backup/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
    except Exception:
        # Finish the compatible bundle after a committed additive migration,
        # withdraw reminders, and return the exact earlier static surface.
        if not stopped:run(['systemctl','stop','ism-api'])
        try:
            known=dict(scope['prior_api'])
            known.update({n:known.get(n) for n in scope['api'] if n not in known})
            current=api_inventory(ROOT,scope)
            assert set(current)==set(known),'Unrelated API files appeared; recovery refused'
            assert all(h in (known.get(n),scope['api'].get(n)) for n,h in current.items()),'Unrelated API drift; recovery refused'
            actual=inventory(PUBLIC)
            assert all(n in scope['served_web'] and h in (scope['prior_web'].get(n),scope['built_web'].get(n)) for n,h in actual.items()),'Unrelated static drift; recovery refused'
            prior_env=(backup/'db.env.before').read_bytes()
            assert ENV.read_bytes() in (prior_env,env_value(prior_env,True),env_value(prior_env,False)),'Concurrent credential change; recovery refused'
            if applied:
                for n in scope['api']:atomic_bytes((stage/'api'/n).read_bytes(),ROOT/n)
                atomic_bytes(env_value((backup/'db.env.before').read_bytes(),False),ENV,True)
            else:atomic_bytes((backup/'db.env.before').read_bytes(),ENV,True)
            run(['rsync','-a','--delete',str(backup/'public')+'/',str(PUBLIC)+'/'])
        finally:run(['systemctl','start','ism-api'])
        (backup/'automatic-recovery.json').write_text(json.dumps({'migration_retained':applied,'digest_withdrawn':True,'account_mail_retained':True,'static_restored':True})+'\n')
        health();raise
def local_apply(check_only=False):
    report=Path(__file__).resolve().parents[1]/'reports/finna-review-digest-production-20261119'
    scope=json.loads((report/'release-scope.json').read_text())
    package=Path(json.loads((report/'package-path.json').read_text())['path'])
    assert sha(Path(__file__))==scope['operator_sha256']
    assert inventory(package/'web/dist')==scope['built_web']
    assert all(sha(package/'api'/n)==h for n,h in scope['api'].items())
    for n,h in scope['proofs'].items():assert sha(report/n)==h,'Release proof drift'
    host='ubuntu@152.67.31.231'
    stage=run(['ssh',host,'mktemp -d /tmp/finna-digest-stage.XXXXXX'],text=True).stdout.strip()
    assert re.fullmatch(r'/tmp/finna-digest-stage\.[A-Za-z0-9]+',stage)
    with tempfile.TemporaryDirectory(prefix='finna-digest-deploy-') as directory:
        root=Path(directory)
        for n in scope['api']:
            target=root/'api'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(package/'api'/n,target)
        shutil.copytree(package/'web/dist',root/'web')
        shutil.copy2(report/'release-scope.json',root/'scope.json')
        shutil.copy2(Path(__file__),root/'deploy.py')
        shutil.copy2(Path(__file__).parent/'verify-finnaplan-v12-query-performance.py',root/'verify.py')
        try:
            run(['rsync','-az',str(root)+'/',host+':'+stage+'/'])
            run(['ssh',host,'chmod -R a+rX '+stage])
            result=run(['ssh',host,'sudo python3 '+stage+'/deploy.py --remote '+stage+(' --check' if check_only else '')],text=True)
            receipt=json.loads(result.stdout)
            (report/('preflight.json' if check_only else 'release.json')).write_text(json.dumps(receipt,indent=2)+'\n')
            print(json.dumps(receipt))
        finally:run(['ssh',host,'sudo rm -rf -- '+stage])
if __name__=='__main__':
    if len(sys.argv)==1:local_apply()
    elif sys.argv[1]=='--check':local_apply(True)
    elif sys.argv[1]=='--remote':print(json.dumps(remote(Path(sys.argv[2]),'--check' in sys.argv)))
    elif sys.argv[1]=='--restore':
        backup=Path(sys.argv[2]);assert backup.parent==Path('/root') and backup.name.startswith('finna-digest-backup-')
        scope=json.loads((backup/'scope.json').read_text());assert sha(Path(__file__))==scope['operator_sha256'];assert sql("SELECT checksum FROM schema_migrations WHERE version='"+VERSION+"'")==scope['api'][MIGRATION]
        print(json.dumps(restore(backup,scope)))
