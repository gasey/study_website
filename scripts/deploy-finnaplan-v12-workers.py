#!/usr/bin/env python3
"""Bounded worker receipts and local host collectors; no schema or bank changes."""
import hashlib,json,os,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
REPORT='reports/finnaplan-v12-workers-20261118'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def inventory(root):
    assert root.is_dir() and not any(p.is_symlink() for p in root.rglob('*'))
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def api_inventory(root,scope):
    names=set(scope['prior_api'])
    names.update(p.relative_to(root).as_posix() for part,pattern in [('app','*.py'),('migrations','*.sql')] for p in (root/part).rglob(pattern))
    return {n:sha(root/n) for n in sorted(names)}
def guard(scope,released=False,root=Path('/srv/api')):
    expected={**scope['prior_api'],**(scope['api'] if released else {})}
    assert api_inventory(root,scope)==expected,'API/schema drift; release/recovery refused'
UNITS=('ism-oracle-bank-review','ism-workshop-backup','ism-stats-refresh')
def unit_inventory(scope):
    names=set(scope['prior_units'])
    for unit in UNITS:
        for suffix in ('.service','.timer'):
            p=Path('/etc/systemd/system')/(unit+suffix)
            names.add(str(p))
            folder=Path(str(p)+'.d')
            if folder.is_dir():names.update(str(p) for p in folder.glob('*.conf'))
    return {n:sha(Path(n)) for n in sorted(names)}
def guard_units(scope,released=False):
    expected={**scope['prior_units'],**({n:d for n,d in scope['extra'].items() if n.startswith('/etc/systemd/')} if released else {})}
    assert unit_inventory(scope)==expected,'Systemd drift; bounded release/recovery refused'
    expected_collector=scope['extra']['/srv/api/ops-collector.py'] if released else None
    assert sha(Path('/srv/api/ops-collector.py'))==expected_collector,'Collector drift; bounded release/recovery refused'
def extra_inventory(stage):return {'/'+n:d for n,d in inventory(stage/'extra').items()}
def restore_units(backup,scope):
    if Path('/etc/systemd/system/finna-ops-host.timer').exists():run(['systemctl','disable','--now','finna-ops-host.timer'])
    active=subprocess.run(['systemctl','is-active','finna-ops-host.service'],capture_output=True,text=True).stdout.strip()
    if active in ('active','activating','deactivating'):run(['systemctl','stop','finna-ops-host.service'])
    for n in scope['extra']:
        if Path(n).exists():Path(n).unlink()
    run(['systemctl','daemon-reload'])
def install_units(stage,scope):
    for n in scope['extra']:atomic(stage/'extra'/n.lstrip('/'),Path(n))
    run(['systemctl','daemon-reload'])
    guard_units(scope,True)
    run(['systemctl','enable','--now','finna-ops-host.timer'])
    run(['systemctl','start','finna-ops-host.service'])
    run(['systemctl','is-active','--quiet','finna-ops-host.timer'])
    run(['systemctl','is-enabled','--quiet','finna-ops-host.timer'])
def check_units(stage,scope):
    guard_units(scope)
    assert extra_inventory(stage)==scope['extra']
    # Verify actual unit definitions with only additive outcome hooks; no jobs run.
    check=stage/'unit-check';check.mkdir(exist_ok=True)
    for n in scope['prior_units']:
        p=Path(n)
        if p.is_file():
            q=check/p.relative_to('/etc/systemd/system');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    for n in scope['extra']:
        if n.startswith('/etc/systemd/'):
            q=check/Path(n).relative_to('/etc/systemd/system');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(stage/'extra'/n.lstrip('/'),q)
    env=os.environ.copy();env['SYSTEMD_UNIT_PATH']=str(check)+':/etc/systemd/system:/usr/lib/systemd/system:/lib/systemd/system'
    args=['systemd-analyze','verify','--man=no',*[str(check/(u+'.service')) for u in UNITS],str(check/'finna-ops-host.service'),str(check/'finna-ops-host.timer')]
    run(args,env=env,text=True)
    # Root-only staging cache, actual backup/disk reads. No production DB writes.
    code="import importlib.util,json;from pathlib import Path;s=importlib.util.spec_from_file_location('c',"+repr(str(stage/'extra/srv/api/ops-collector.py'))+");c=importlib.util.module_from_spec(s);s.loader.exec_module(c);rows,failed=c.host_records(c.now(),cache=Path("+repr(str(stage/'backup-cache.json'))+"));assert not failed;print(json.dumps(rows))"
    data=json.loads(run(['/srv/api/.venv/bin/python','-B','-c',code],text=True).stdout)
    assert next(r for r in data if r['worker']=='probe:backup')['note']['state']=='healthy'
    return data
def wait_workers():
    query="SELECT count(*) FROM worker_heartbeats WHERE worker IN('score-reassessment','desk-retention','calendar-reminders','game-lifecycle','account-mail','mastery-reconciler') AND last_beat>clock_timestamp()-interval '2 minutes'"
    for attempt in range(25):
        r=run(['sudo','-u','postgres','psql','-X','-At','-d','mpsc','-c',query],text=True)
        if r.stdout.strip()=='6':return
        if attempt==24:raise AssertionError('Standard cycle receipts unavailable after restart')
        time.sleep(2)
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
def prior_artifacts(backup,scope,root,public):
    for n in scope['api']:
        if scope['prior_api'][n] is None:
            if (root/n).exists():(root/n).unlink()
        else:atomic(backup/'api'/n,root/n)
    run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
def restore_pair(backup,scope,root=Path('/srv/api'),public=Path('/srv/study/public')):
    guard(scope,True,root);guard_units(scope,True);assert inventory(public)==scope['served_web'],'Newer static release; recovery refused'
    assert inventory(backup/'public')==scope['prior_web']
    for n in scope['api']:
        if scope['prior_api'][n] is not None:assert sha(backup/'api'/n)==scope['prior_api'][n]
    run(['systemctl','stop','ism-api']);restore_units(backup,scope);prior_artifacts(backup,scope,root,public)
    run(['systemctl','start','ism-api']);health();guard(scope,root=root);guard_units(scope);assert inventory(public)==scope['prior_web']
def remote(stage,check_only=False):
    assert os.geteuid()==0
    scope=json.loads((stage/'scope.json').read_text());root=Path('/srv/api');public=Path('/srv/study/public')
    assert sha(stage/'deploy.py')==scope['operator_sha256'] and sha(stage/'verify.py')==scope['verifier_sha256']
    assert inventory(stage/'api')==scope['api'] and inventory(stage/'web')==scope['built_web']
    for n in scope['api']:
        if n.endswith('.py'):compile((stage/'api'/n).read_bytes(),n,'exec')
        else:json.loads((stage/'api'/n).read_text())
    guard(scope);assert inventory(public)==scope['prior_web'],'Static drift since audit'
    host_preflight=check_units(stage,scope)
    for n in scope['prior_units']:
        p=Path(n)
        if p.exists():assert p.is_file() and not p.is_symlink(),'Unit file link drift'
    run(['systemctl','is-active','--quiet','ism-api']);runtime_mail_guard();assert shutil.disk_usage('/root').free>2*1024**3
    if check_only:print('Worker and collector preflight passed; no live files, SQL or real jobs changed; host inspection and unit syntax checks passed.');return
    backup=Path(tempfile.mkdtemp(prefix='finna-v12-workers-backup-',dir='/root'))
    for n in ('scope.json','deploy.py','verify.py'):shutil.copy2(stage/n,backup/n)
    shutil.copytree(stage/'extra',backup/'released-extra')
    shutil.copytree(public,backup/'public');shutil.copytree(stage/'api',backup/'released-api')
    for n in scope['api']:
        if scope['prior_api'][n] is not None:p=backup/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,p)
    stopped=False
    try:
        guard(scope);assert inventory(public)==scope['prior_web']
        run(['systemctl','stop','ism-api']);stopped=True
        for n in scope['api']:atomic(stage/'api'/n,root/n)
        guard(scope,True);install_units(stage,scope);run(['systemctl','start','ism-api']);stopped=False;health();wait_workers()
        run(['rsync','-a','--exclude','index.html',str(stage/'web')+'/',str(public)+'/']);atomic(stage/'web/index.html',public/'index.html')
        run(['chown','-R','caddy:caddy',str(public)]);assert inventory(public)==scope['served_web'];guard(scope,True)
        runtime_mail_guard();guard_units(scope,True)
        checked=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],text=True).stdout)
        sites={}
        for host in ('study.hawayu.in','family.hawayu.in'):
            with urlopen('https://'+host,timeout=30) as r:assert r.status==200;sites[host]=r.status
        routes=('/admin/ops','/admin/bank','/feed','/revise','/desk','/create','/bank','/billing')
        from urllib.error import HTTPError
        try:
            urlopen('https://study.hawayu.in/api/admin/ops',timeout=30)
            raise AssertionError('Anonymous operations access unexpectedly succeeded')
        except HTTPError as response:assert response.code==401
        with urlopen('https://study.hawayu.in/ops-runbook.html',timeout=30) as r:
            assert r.status==200 and hashlib.sha256(r.read()).hexdigest()==scope['built_web']['ops-runbook.html']
        for route in routes:
            with urlopen('https://study.hawayu.in'+route,timeout=30) as r:assert r.status==200 and hashlib.sha256(r.read()).hexdigest()==scope['built_web']['index.html']
        receipt={'backup':str(backup),'api_files_changed':list(scope['api']),'unchanged_dependencies':len(scope['prior_api'])-len(scope['api']),'built_files':len(scope['built_web']),'served_files':len(scope['served_web']),'retained_prior_chunks':len(set(scope['prior_web'])-set(scope['built_web'])),'hash_readbacks_match':True,'database_writes':'operational heartbeat rows only','migration_changes':False,'workshop_changes':False,'unit_files_changed':list(n for n in scope['extra'] if n.startswith('/etc/systemd/')),'api_restarted':True,'route_shell_checks':len(routes),'health':sites,'verification':checked,'anonymous_ops_denied':True,'runbook_hash_checked':True,'worker_instrumentation_changed':True,'timer_collectors_installed':True,'host_preflight':host_preflight,'extra_hashes_verified':True,'original_jobs_started':False}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
    except BaseException:
        actual=api_inventory(root,scope);candidate={**scope['prior_api'],**scope['api']}
        assert set(actual)==set(candidate) and all(d in (scope['prior_api'][n],candidate[n]) for n,d in actual.items()),'Unrelated API drift; recovery refused'
        current=inventory(public);assert all(n in scope['served_web'] and d in (scope['prior_web'].get(n),scope['built_web'].get(n)) for n,d in current.items()),'Unrelated static drift; recovery refused'
        for n,d in unit_inventory(scope).items():assert d in (scope['prior_units'].get(n),scope['extra'].get(n)),'Unrelated unit drift; recovery refused'
        assert sha(Path('/srv/api/ops-collector.py')) in (None,scope['extra']['/srv/api/ops-collector.py'])
        if not stopped:run(['systemctl','stop','ism-api'])
        restore_units(backup,scope)
        prior_artifacts(backup,scope,root,public);run(['systemctl','start','ism-api']);health();guard(scope);raise

def local(check_only):
    root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text())
    assert sha(Path(__file__))==scope['operator_sha256']
    for n,d in scope['sources'].items():assert sha(root/n)==d,'Source drift: '+n
    for n,d in scope['proofs'].items():assert sha(report/n)==d,'Proof drift: '+n
    assert inventory(root/'web/dist')==scope['built_web']
    host=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
    with tempfile.TemporaryDirectory(prefix='finna-workers-package-') as directory:
        package=Path(directory);shutil.copytree(root/'web/dist',package/'web')
        for n in scope['api']:p=package/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'api'/n,p)
        for n,source in scope['extra_sources'].items():p=package/'extra'/n.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/source,p)
        for n,source in [('deploy.py',Path(__file__)),('verify.py',root/'scripts/verify-finnaplan-v12-workers.py'),('scope.json',report/'release-scope.json')]:shutil.copy2(source,package/n)
        stage=run(['ssh',host,'mktemp -d /tmp/finna-v12-workers-stage.XXXXXX'],text=True).stdout.strip();assert stage.startswith('/tmp/finna-v12-workers-stage.') and '\n' not in stage
        try:
            run(['rsync','-az','-e','ssh',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod 755 '+shlex.quote(stage)])
            result=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+(' --remote-check ' if check_only else ' --remote ')+shlex.quote(stage)],text=True)
            (report/('preflight.txt' if check_only else 'release.txt')).write_text(result.stdout)
            if check_only:print(result.stdout.strip());return
            receipt=json.loads(next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT ')))
            (report/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Worker and collector release verified: '+str(report/'release.json'))
        finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--remote','--remote-check'):remote(Path(sys.argv[2]),sys.argv[1]=='--remote-check')
    elif len(sys.argv)==3 and sys.argv[1]=='--restore':
        backup=Path(sys.argv[2]).resolve();assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v12-workers-backup-');restore_pair(backup,json.loads((backup/'scope.json').read_text()));print('Prior ops readers/static restored; all schema and learner history retained.')
    else:assert sys.argv[1:] in ([],['--check']);local(sys.argv[1:]==['--check'])
