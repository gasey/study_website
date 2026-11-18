#!/usr/bin/env python3
"""Bounded0110 maintenance release; preserve learner history and operational receipts."""
import hashlib,json,os,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
REPORT='reports/finnaplan-v12-maintenance-20261118'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def inventory(root):
    assert root.is_dir() and not any(p.is_symlink() for p in root.rglob('*'))
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def api_inventory(root,scope):
    names=set(scope['prior_api'])
    names.update(p.relative_to(root).as_posix() for part,pattern in [('app','*.py'),('migrations','*.sql')] for p in (root/part).rglob(pattern))
    return {n:sha(root/n) for n in sorted(names)}
MIGRATION='migrations/0110_site_maintenance.sql'
VERSION='0110_site_maintenance'
KEEP_READERS=('app/services/account_viewer.py',)
def expected(scope,released=False,restored=False,migrated=True):
    result=dict(scope['prior_api'])
    if released:result.update(scope['api'])
    if restored:result.update({n:scope['api'][n] for n in KEEP_READERS})
    if released or restored and migrated:result[MIGRATION]=scope['migration_sha256']
    return result

def guard(scope,released=False,restored=False,migrated=True,root=Path('/srv/api')):
    assert api_inventory(root,scope)==expected(scope,released,restored,migrated),'API/schema drift; release/recovery refused'

def guard_collectors(scope):
    assert all(sha(Path(n))==d for n,d in scope['protected_host_files'].items()),'Collector/unit drift; release/recovery refused'
    units=('ism-oracle-bank-review','ism-workshop-backup','ism-stats-refresh','finna-ops-host')
    for u in units:
        for suffix in ('.service','.timer'):
            p=Path('/etc/systemd/system')/(u+suffix)
            assert str(p) in scope['protected_host_files'],'Unscoped unit'
            folder=Path(str(p)+'.d')
            if folder.is_dir():assert all(str(x) in scope['protected_host_files'] for x in folder.glob('*.conf')),'Unscoped drop-in'

def run(args,**kwargs):
    r=subprocess.run(args,capture_output=True,**kwargs)
    if r.returncode:raise RuntimeError(str(args[:2])+': '+(r.stderr.decode(errors='replace') if isinstance(r.stderr,bytes) else r.stderr))
    return r
def runtime_mail_guard():
    pid=int(run(['systemctl','show','ism-api','-p','MainPID','--value'],text=True).stdout.strip());assert pid>0
    env=dict(x.split('=',1) for x in Path('/proc/'+str(pid)+'/environ').read_text().split('\0') if '=' in x)
    assert env.get('ACCOUNT_MAIL_ENABLED','').strip().lower() not in ('1','true','yes','on'),'Mail configuration changed; bounded disabled-mail release refused'
    assert not any(env.get(k) for k in ('SMTP_HOST','SMTP_FROM','SMTP_USERNAME','SMTP_PASSWORD')),'Mail credentials configured since audit; refresh release scope'
    assert env.get('SMTP_DAILY_LIMIT','100')=='100' and env.get('SMTP_MONTHLY_LIMIT','3000')=='3000'
    assert env.get('RAZORPAY_CHECKOUT_ENABLED','').strip().lower() not in ('1','true','yes','on'),'Checkout activation changed; refresh bounded scope'
    with urlopen('https://study.hawayu.in/api/auth/recovery/status',timeout=30) as response:
        assert json.loads(response.read())=={'available':False},'Live recovery availability changed; refresh the disabled-mail scope'


def atomic(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.finna-ops-',dir=target.parent);os.close(fd);tmp=Path(name)
    try:shutil.copy2(source,tmp);os.replace(tmp,target)
    finally:
        if tmp.exists():tmp.unlink()
def health():
    for attempt in range(15):
        try:
            with urlopen('https://study.hawayu.in/api/health',timeout=5) as r:assert r.status==200
            return
        except Exception:
            if attempt==14:raise
            time.sleep(1)
def sql(query):
    return run(['sudo','-u','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-d','mpsc'],input=query.encode()).stdout.decode().strip()
def guard_extra(scope,installed=False):
    expected_files=scope['extra'] if installed else scope['prior_extra']
    assert {n:sha(Path(n)) for n in expected_files}==expected_files,'Restore tool drift; release/recovery refused'
def migration_applied(scope):
    value=sql("SELECT checksum FROM schema_migrations WHERE version='"+VERSION+"'")
    if value:assert value==scope['migration_sha256'],'Migration registry drift'
    return bool(value)
def wait_workers():
    for attempt in range(25):
        count=sql("SELECT count(*) FROM worker_heartbeats WHERE worker IN('score-reassessment','desk-retention','account-retention','calendar-reminders','game-lifecycle','account-mail','mastery-reconciler') AND last_beat>clock_timestamp()-interval '2 minutes'")
        if count=='7':return
        if attempt==24:raise AssertionError('Current worker cycle receipts unavailable')
        time.sleep(1)
def restore_artifacts(backup,scope,root,public,migrated=True):
    for n in scope['api']:
        if n in KEEP_READERS:atomic(backup/'released-api'/n,root/n)
        elif scope['prior_api'][n] is None:
            if (root/n).exists():(root/n).unlink()
        else:atomic(backup/'api'/n,root/n)
    if not migrated and (root/MIGRATION).exists():(root/MIGRATION).unlink()
    for n in scope['extra']:atomic(backup/'released-extra'/n.lstrip('/'),Path(n))
    run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
def restore_pair(backup,scope,root=Path('/srv/api'),public=Path('/srv/study/public')):
    guard_collectors(scope);guard_extra(scope,True);guard(scope,True,root=root)
    assert migration_applied(scope),'Applied0110 is required for this recovery'
    assert inventory(public)==scope['served_web'],'Newer static release; recovery refused'
    assert inventory(backup/'public')==scope['prior_web']
    for n in scope['api']:
        if scope['prior_api'][n] is not None:assert sha(backup/'api'/n)==scope['prior_api'][n]
    for n in KEEP_READERS:assert sha(backup/'released-api'/n)==scope['api'][n]
    assert {'/'+n:d for n,d in inventory(backup/'released-extra').items()}==scope['extra']
    run(['systemctl','stop','ism-api'])
    restore_artifacts(backup,scope,root,public)
    run(['systemctl','start','ism-api']);health();guard(scope,restored=True,root=root)
    guard_collectors(scope);guard_extra(scope,True);assert inventory(public)==scope['prior_web']
def remote(stage,check_only=False):
    assert os.geteuid()==0
    scope=json.loads((stage/'scope.json').read_text());root=Path('/srv/api');public=Path('/srv/study/public')
    assert sha(stage/'deploy.py')==scope['operator_sha256'] and sha(stage/'verify.py')==scope['verifier_sha256']
    assert sha(stage/'migration.sql')==scope['migration_sha256']
    assert inventory(stage/'api')==scope['api'] and inventory(stage/'web')==scope['built_web']
    assert {'/'+n:d for n,d in inventory(stage/'extra').items()}==scope['extra']
    for n in scope['api']:
        if n.endswith('.py'):compile((stage/'api'/n).read_bytes(),n,'exec')
        else:json.loads((stage/'api'/n).read_text())
    guard_collectors(scope);guard_extra(scope);guard(scope)
    assert inventory(public)==scope['prior_web'],'Static drift since audit'
    assert not migration_applied(scope),'Already/partially applied; use the saved recovery backup'
    run(['systemctl','is-active','--quiet','ism-api']);runtime_mail_guard()
    assert shutil.disk_usage('/root').free>8*1024**3
    if check_only:print('Maintenance preflight passed; no live files, SQL or services changed.');return
    backup=Path(tempfile.mkdtemp(prefix='finna-v12-maintenance-backup-',dir='/root'))
    for n in ('scope.json','deploy.py','verify.py','migration.sql'):shutil.copy2(stage/n,backup/n)
    shutil.copytree(public,backup/'public');shutil.copytree(stage/'api',backup/'released-api');shutil.copytree(stage/'extra',backup/'released-extra')
    for n in scope['api']:
        if scope['prior_api'][n] is not None:
            p=backup/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,p)
    with (backup/'database.dump').open('wb') as output:
        subprocess.run(['sudo','-u','postgres','pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
    stopped=False
    try:
        guard(scope);guard_collectors(scope);guard_extra(scope);assert inventory(public)==scope['prior_web']
        run(['systemctl','stop','ism-api']);stopped=True
        atomic(stage/'migration.sql',root/MIGRATION)
        text=(stage/'migration.sql').read_text().strip();assert text.startswith('BEGIN;') and text.endswith('COMMIT;')
        body=text.removeprefix('BEGIN;').removesuffix('COMMIT;')
        before=int(sql('SELECT count(*) FROM reward_ledger'));start=time.monotonic()
        sql("BEGIN;SET LOCAL jit=off;SET LOCAL lock_timeout='5s';SET LOCAL statement_timeout='30s';SELECT pg_advisory_xact_lock(hashtextextended('finna-schema-migrations',0));"+body+" INSERT INTO schema_migrations(version,checksum) VALUES('"+VERSION+"','"+scope['migration_sha256']+"');COMMIT;")
        apply_ms=round((time.monotonic()-start)*1000,3)
        assert migration_applied(scope) and int(sql('SELECT count(*) FROM reward_ledger'))==before
        seed=json.loads(sql("SELECT json_build_object('message',message,'version',version,'updated_by',updated_by) FROM site_notice WHERE singleton"))
        assert seed=={'message':'','version':1,'updated_by':None}
        for n in scope['api']:atomic(stage/'api'/n,root/n)
        for n in scope['extra']:atomic(stage/'extra'/n.lstrip('/'),Path(n))
        guard(scope,True);guard_collectors(scope);guard_extra(scope,True)
        run(['systemctl','start','ism-api']);stopped=False;health();wait_workers()
        run(['rsync','-a','--exclude','index.html',str(stage/'web')+'/',str(public)+'/']);atomic(stage/'web/index.html',public/'index.html')
        run(['chown','-R','caddy:caddy',str(public)]);assert inventory(public)==scope['served_web'];guard(scope,True)
        checked=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],text=True).stdout)
        assert next(w for w in checked['ops']['workers'] if w['id']=='account-retention')['state']=='healthy'
        assert checked['ops']['restore_rehearsal']['state']=='healthy'
        runtime_mail_guard();guard_collectors(scope);guard_extra(scope,True)
        sites={}
        for host in ('study.hawayu.in','family.hawayu.in'):
            with urlopen('https://'+host,timeout=30) as response:assert response.status==200;sites[host]=response.status
        from urllib.error import HTTPError
        for path in ('/api/admin/users?q=owner','/api/admin/ops/notice'):
            try:urlopen('https://study.hawayu.in'+path,timeout=30);raise AssertionError('Anonymous admin access')
            except HTTPError as exc:assert exc.code==401
        with urlopen('https://study.hawayu.in/api/site-notice',timeout=30) as response:
            visible=json.loads(response.read());assert response.status==200 and set(visible)=={'message','expires_at','version'}
        routes=('/admin/users','/admin/ops','/admin/bank','/feed','/revise','/desk','/create','/bank','/billing')
        for path in routes:
            with urlopen('https://study.hawayu.in'+path,timeout=30) as response:assert response.status==200 and hashlib.sha256(response.read()).hexdigest()==scope['built_web']['index.html']
        with urlopen('https://study.hawayu.in/ops-runbook.html',timeout=30) as response:assert hashlib.sha256(response.read()).hexdigest()==scope['built_web']['ops-runbook.html']
        receipt={'backup':str(backup),'api_files_changed':list(scope['api']),'migration':VERSION,'migration_sha256':scope['migration_sha256'],'migration_apply_ms':apply_ms,'initial_notice_seed_verified':True,'built_files':len(scope['built_web']),'served_files':len(scope['served_web']),'retained_prior_chunks':len(set(scope['prior_web'])-set(scope['built_web'])),'unchanged_dependencies':len(scope['prior_api'])-len(scope['api'])-1,'installed_collectors_unchanged':True,'installed_restore_tool_verified':True,'anonymous_admin_denied':True,'route_shell_checks':len(routes),'hash_readbacks_match':True,'health':sites,'verification':checked,'synthetic_production_activity':False,'bank_or_workshop_changes':False,'provider_configuration_changes':False}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
    except BaseException:
        guard_collectors(scope)
        actual=api_inventory(root,scope);candidate=expected(scope,True)
        assert set(actual)==set(candidate) and all(d in (scope['prior_api'].get(n),candidate[n]) for n,d in actual.items()),'Unrelated API drift; automatic recovery refused'
        current=inventory(public);assert all(n in scope['served_web'] and d in (scope['prior_web'].get(n),scope['built_web'].get(n)) for n,d in current.items()),'Unrelated static drift; recovery refused'
        for n,d in scope['extra'].items():assert sha(Path(n)) in (scope['prior_extra'][n],d),'Restore tool drift'
        applied=migration_applied(scope)
        if not stopped:run(['systemctl','stop','ism-api'])
        restore_artifacts(backup,scope,root,public,migrated=applied)
        run(['systemctl','start','ism-api']);health();guard(scope,restored=True,migrated=applied)
        raise

def local(check_only):
    root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text())
    assert sha(Path(__file__))==scope['operator_sha256']
    for n,d in scope['sources'].items():assert sha(root/n)==d,'Source drift: '+n
    for n,d in scope['proofs'].items():assert sha(report/n)==d,'Proof drift: '+n
    assert inventory(root/'web/dist')==scope['built_web']
    host='ubuntu@152.67.31.231'
    with tempfile.TemporaryDirectory(prefix='finna-maintenance-package-') as directory:
        package=Path(directory);shutil.copytree(root/'web/dist',package/'web')
        for n in scope['api']:
            p=package/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'api'/n,p)
        for n,source in scope['extra_sources'].items():
            p=package/'extra'/n.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/source,p)
        for name,source in [('deploy.py',Path(__file__)),('verify.py',root/'scripts/verify-finnaplan-v12-maintenance.py'),('migration.sql',root/'api'/MIGRATION),('scope.json',report/'release-scope.json')]:shutil.copy2(source,package/name)
        stage=run(['ssh',host,'mktemp -d /tmp/finna-v12-maintenance-stage.XXXXXX'],text=True).stdout.strip();assert stage.startswith('/tmp/finna-v12-maintenance-stage.') and '\n' not in stage
        try:
            run(['rsync','-az',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod 755 '+shlex.quote(stage)])
            result=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+(' --remote-check ' if check_only else ' --remote ')+shlex.quote(stage)],text=True)
            (report/('preflight.txt' if check_only else 'release.txt')).write_text(result.stdout)
            if check_only:print(result.stdout.strip());return
            receipt=json.loads(next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT ')))
            (report/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Maintenance release verified: '+str(report/'release.json'))
        finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--remote','--remote-check'):remote(Path(sys.argv[2]),sys.argv[1]=='--remote-check')
    elif len(sys.argv)==3 and sys.argv[1]=='--restore':
        backup=Path(sys.argv[2]).resolve();assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v12-maintenance-backup-')
        restore_pair(backup,json.loads((backup/'scope.json').read_text()));print('Prior API/static restored with the retained activity reader;0110, all history and verified restore/collector tools remain.')
    else:assert sys.argv[1:] in ([],['--check']);local(sys.argv[1:]==['--check'])
