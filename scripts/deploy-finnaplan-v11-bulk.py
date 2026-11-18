#!/usr/bin/env python3
"""Bounded0109 release; recovery keeps shared writers and quarantines bulk assignment."""
import hashlib,json,os,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
REPORT='reports/finnaplan-v11-bulk-20261118'
MIGRATION='migrations/0109_bulk_account_rates.sql'
VERSION='0109_bulk_account_rates'
FLAG='app/data/bulk-rate-writes.json'
PAUSED=(json.dumps({'version':1,'writes_enabled':False},indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def inventory(root):
    assert root.is_dir() and not any(p.is_symlink() for p in root.rglob('*'))
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def api_inventory(root,scope):
    names=set(scope['prior_api'])
    names.update(p.relative_to(root).as_posix() for part,pattern in [('app','*.py'),('migrations','*.sql')] for p in (root/part).rglob(pattern))
    return {n:sha(root/n) for n in sorted(names)}
def expected(scope,released=False,paused=False):
    result=dict(scope['prior_api'])
    if released or paused:result.update(scope['api']);result[MIGRATION]=scope['migration_sha256']
    if paused:result[FLAG]=hashlib.sha256(PAUSED).hexdigest()
    return result
def guard(scope,released=False,paused=False,root=Path('/srv/api')):
    assert api_inventory(root,scope)==expected(scope,released,paused),'API/schema drift; release/recovery refused'
def run(args,**kwargs):
    r=subprocess.run(args,capture_output=True,**kwargs)
    if r.returncode:raise RuntimeError(str(args[:2])+': '+(r.stderr.decode(errors='replace') if isinstance(r.stderr,bytes) else r.stderr))
    return r
def sql(query):return run(['sudo','-u','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-d','mpsc'],input=query.encode()).stdout.decode().strip()
def runtime_mail_guard():
    pid=int(run(['systemctl','show','ism-api','-p','MainPID','--value'],text=True).stdout.strip());assert pid>0
    env=dict(x.split('=',1) for x in Path('/proc/'+str(pid)+'/environ').read_text().split('\0') if '=' in x)
    assert env.get('ACCOUNT_MAIL_ENABLED','').strip().lower() not in ('1','true','yes','on'),'Mail configuration changed; bounded disabled-mail release refused'
    assert not any(env.get(k) for k in ('SMTP_HOST','SMTP_FROM','SMTP_USERNAME','SMTP_PASSWORD')),'Mail credentials configured since audit; refresh release scope'
    assert env.get('SMTP_DAILY_LIMIT','100')=='100' and env.get('SMTP_MONTHLY_LIMIT','3000')=='3000'
    with urlopen('https://study.hawayu.in/api/auth/recovery/status',timeout=30) as response:
        assert json.loads(response.read())=={'available':False},'Live recovery availability changed; refresh the disabled-mail scope'

def health():
    for attempt in range(15):
        try:
            with urlopen('https://study.hawayu.in/api/health',timeout=5) as r:assert r.status==200
            return
        except Exception:
            if attempt==14:raise
            time.sleep(1)
def atomic(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.finna-vocabulary-',dir=target.parent);os.close(fd);tmp=Path(name)
    try:shutil.copy2(source,tmp);os.replace(tmp,target)
    finally:
        if tmp.exists():tmp.unlink()
def pause(backup,root):
    source=backup/'paused-writes.json';source.write_bytes(PAUSED);os.chmod(source,0o644);atomic(source,root/FLAG)
def restore_artifacts(backup,scope,root=Path('/srv/api'),public=Path('/srv/study/public')):
    # Current bulk, onboarding, mail and shared-review writers remain compatible with live history.
    # Current API, scoring, privacy, caps and source-bound evidence stay together.
    guard(scope,True,root=root)
    assert inventory(public)==scope['served_web'],'Newer static release; recovery refused'
    assert inventory(backup/'public')==scope['prior_web']
    run(['systemctl','stop','ism-api'])
    try:
        pause(backup,root)
        run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
        guard(scope,paused=True,root=root)
    finally:run(['systemctl','start','ism-api'])
    health();assert inventory(public)==scope['prior_web']
def restore(backup):
    assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v11-bulk-backup-')
    scope=json.loads((backup/'scope.json').read_text())
    assert sql("SELECT checksum FROM schema_migrations WHERE version='"+VERSION+"'")==scope['migration_sha256']
    restore_artifacts(backup,scope)
    print('Prior static restored; bulk assignment writes paused. Compatible bulk/onboarding/mail/CMS/shared API/queue writers,0105–0109 and all answer/review history retained. Do not restore older mail or review writers.')
def remote(stage,check_only=False):
    assert os.geteuid()==0
    scope=json.loads((stage/'scope.json').read_text());root=Path('/srv/api');public=Path('/srv/study/public')
    assert sha(stage/'deploy.py')==scope['operator_sha256'] and sha(stage/'verify.py')==scope['verifier_sha256']
    assert inventory(stage/'api')==scope['api'] and sha(stage/'migration.sql')==scope['migration_sha256']
    for n in scope['api']:
        if n.endswith('.py'):compile((stage/'api'/n).read_bytes(),n,'exec')
        else:json.loads((stage/'api'/n).read_text())
    assert inventory(stage/'web')==scope['built_web']
    guard(scope);assert inventory(public)==scope['prior_web'],'Static drift since audit'
    assert not sql("SELECT checksum FROM schema_migrations WHERE version='"+VERSION+"'"),'Already/partially applied; use the saved backup for recovery'
    run(['systemctl','is-active','--quiet','ism-api']);runtime_mail_guard();assert shutil.disk_usage('/root').free>8*1024**3
    if check_only:print('Bulk pricing preflight passed; no live files, SQL or services changed.');return
    backup=Path(tempfile.mkdtemp(prefix='finna-v11-bulk-backup-',dir='/root'))
    for n in ('scope.json','deploy.py','verify.py','migration.sql'):shutil.copy2(stage/n,backup/n)
    shutil.copytree(public,backup/'public');shutil.copytree(stage/'api',backup/'released-api');shutil.copytree(stage/'web',backup/'released-public')
    for n in scope['api']:
        if (root/n).is_file():target=backup/'api'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,target)
    with (backup/'database.dump').open('wb') as output:subprocess.run(['sudo','-u','postgres','pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
    stopped=False
    try:
        guard(scope);assert inventory(public)==scope['prior_web']
        run(['systemctl','stop','ism-api']);stopped=True
        atomic(stage/'migration.sql',root/MIGRATION)
        migration=(stage/'migration.sql').read_text().strip();assert migration.startswith('BEGIN;') and migration.endswith('COMMIT;')
        body=migration.removeprefix('BEGIN;').removesuffix('COMMIT;')
        before=int(sql("SELECT count(*) FROM reward_ledger"))
        sql("BEGIN; SET LOCAL jit=off; SET LOCAL lock_timeout='5s'; SET LOCAL statement_timeout='30s'; SELECT pg_advisory_xact_lock(hashtextextended('finna-schema-migrations',0)); "+body+" INSERT INTO schema_migrations(version,checksum) VALUES('"+VERSION+"','"+scope['migration_sha256']+"'); COMMIT;")
        assert int(sql("SELECT count(*) FROM reward_ledger"))==before
        added=int(sql('SELECT count(*) FROM billing_rate_redemptions'))
        for n in scope['api']:atomic(stage/'api'/n,root/n)
        guard(scope,True);run(['systemctl','start','ism-api']);stopped=False;health()
        run(['rsync','-a','--exclude','index.html',str(stage/'web')+'/',str(public)+'/'])
        atomic(stage/'web/index.html',public/'index.html');run(['chown','-R','caddy:caddy',str(public)])
        assert inventory(public)==scope['served_web'];guard(scope,True)
        checked=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],text=True).stdout)
        runtime_mail_guard()
        with urlopen('https://study.hawayu.in/api/auth/recovery/status',timeout=30) as response:assert json.loads(response.read())=={'available':False}
        sites={}
        for host in ('study.hawayu.in','family.hawayu.in'):
            with urlopen('https://'+host,timeout=30) as r:assert r.status==200;sites[host]=r.status
        routes=('/billing','/billing?group_code=missing','/admin/bank?tab=rewards','/revise','/feed','/desk','/onboarding','/profile')
        for route in routes:
            with urlopen('https://study.hawayu.in'+route,timeout=30) as r:assert r.status==200 and hashlib.sha256(r.read()).hexdigest()==scope['built_web']['index.html']
        receipt={'backup':str(backup),'api_files_changed':list(scope['api']),'migration':VERSION,'migration_sha256':scope['migration_sha256'],'bulk_code_redemptions_after_apply':added,'built_files':len(scope['built_web']),'served_files':len(scope['served_web']),'retained_prior_chunks':len(set(scope['prior_web'])-set(scope['built_web'])),'hash_readbacks_match':True,'unchanged_dependencies':len(scope['prior_api'])-len(scope['api'])-1,'learner_history_or_economy_writes':False,'synthetic_production_activity':False,'mail_configuration_unchanged_and_disabled':True,'recovery_availability':False,'workshop_changes':False,'unit_files_changed':False,'api_restarted':True,'route_shell_checks':len(routes),'health':sites,'verification':checked}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
    except BaseException:
        actual=api_inventory(root,scope);candidate=expected(scope,True)
        assert set(actual)==set(candidate) and all(d in (scope['prior_api'][n],candidate[n]) for n,d in actual.items()),'Unrelated API drift; recovery refused'
        current=inventory(public);assert all(n in scope['served_web'] and d in (scope['prior_web'].get(n),scope['built_web'].get(n)) for n,d in current.items()),'Unrelated static drift; recovery refused'
        recorded=sql("SELECT checksum FROM schema_migrations WHERE version='"+VERSION+"'")
        assert not recorded or recorded==scope['migration_sha256'],'Different0109 applied; recovery refused'
        if not stopped:run(['systemctl','stop','ism-api'])
        if recorded:
            # Complete the compatible bundle, then withdraw bulk assignment writes.
            # Older shared writers would discard check-in/source and native guards.
            for n in scope['api']:atomic(stage/'api'/n,root/n)
            pause(backup,root)
        else:
            for n in scope['api']:
                if scope['prior_api'][n] is None:
                    if (root/n).exists():(root/n).unlink()
                else:atomic(backup/'api'/n,root/n)
            if (root/MIGRATION).exists():(root/MIGRATION).unlink()
        run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
        run(['systemctl','start','ism-api']);health();guard(scope,paused=bool(recorded))
        (backup/'automatic-recovery.json').write_text(json.dumps({'migration_retained':bool(recorded),'bulk_assignment_quarantined':bool(recorded),'prior_static_restored':True,'learner_history_retained':True},indent=2)+'\n')
        raise

def local(check_only):
    root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text())
    assert sha(Path(__file__))==scope['operator_sha256']
    for n,d in scope['sources'].items():assert sha(root/n)==d,'Source drift: '+n
    for n,d in scope['proofs'].items():assert sha(report/n)==d,'Proof drift: '+n
    assert inventory(root/'web/dist')==scope['built_web']
    host=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
    with tempfile.TemporaryDirectory(prefix='finna-onboarding-package-') as directory:
        package=Path(directory);shutil.copytree(root/'web/dist',package/'web')
        for n in scope['api']:target=package/'api'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'api'/n,target)
        for n,source in [('deploy.py',Path(__file__)),('verify.py',root/'scripts/verify-finnaplan-v11-bulk.py'),('migration.sql',root/'api'/MIGRATION),('scope.json',report/'release-scope.json')]:shutil.copy2(source,package/n)
        stage=run(['ssh',host,'mktemp -d /tmp/finna-v11-bulk-stage.XXXXXX'],text=True).stdout.strip();assert stage.startswith('/tmp/finna-v11-bulk-stage.') and '\n' not in stage
        try:
            run(['rsync','-az','-e','ssh',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod 755 '+shlex.quote(stage)])
            result=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+(' --remote-check ' if check_only else ' --remote ')+shlex.quote(stage)],text=True)
            (report/('preflight.txt' if check_only else 'release.txt')).write_text(result.stdout)
            if check_only:print(result.stdout.strip());return
            receipt=json.loads(next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT ')))
            (report/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Bulk pricing release verified: '+str(report/'release.json'))
        finally:run(['ssh',host,'rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--remote','--remote-check'):remote(Path(sys.argv[2]),sys.argv[1]=='--remote-check')
    elif len(sys.argv)==3 and sys.argv[1]=='--restore':restore(Path(sys.argv[2]).resolve())
    else:assert sys.argv[1:] in ([],['--check']);local(sys.argv[1:]==['--check'])
