#!/usr/bin/env python3
"""Bounded reviewed word-card authoring release; no SQL or economy changes."""
import hashlib,json,os,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
REPORT='reports/finnaplan-v10-vocabulary-authoring-20261118'
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
def run(args,**kwargs):
    r=subprocess.run(args,capture_output=True,**kwargs)
    if r.returncode:raise RuntimeError(str(args[:2])+': '+(r.stderr.decode(errors='replace') if isinstance(r.stderr,bytes) else r.stderr))
    return r
def atomic(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.finna-vocabulary-authoring-',dir=target.parent);os.close(fd);tmp=Path(name)
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
    guard(scope,True,root);assert inventory(public)==scope['served_web'],'Newer static release; recovery refused'
    assert inventory(backup/'public')==scope['prior_web']
    for n in scope['api']:
        if scope['prior_api'][n] is not None:assert sha(backup/'api'/n)==scope['prior_api'][n]
    run(['systemctl','stop','ism-api']);prior_artifacts(backup,scope,root,public)
    run(['systemctl','start','ism-api']);health();guard(scope,root=root);assert inventory(public)==scope['prior_web']
def remote(stage,check_only=False):
    assert os.geteuid()==0
    scope=json.loads((stage/'scope.json').read_text());root=Path('/srv/api');public=Path('/srv/study/public')
    assert sha(stage/'deploy.py')==scope['operator_sha256'] and sha(stage/'verify.py')==scope['verifier_sha256']
    assert inventory(stage/'api')==scope['api'] and inventory(stage/'web')==scope['built_web']
    for n in scope['api']:compile((stage/'api'/n).read_bytes(),n,'exec')
    guard(scope);assert inventory(public)==scope['prior_web'],'Static drift since audit'
    run(['systemctl','is-active','--quiet','ism-api']);assert shutil.disk_usage('/root').free>2*1024**3
    if check_only:print('Curated vocabulary authoring preflight passed; no live files, SQL or services changed.');return
    backup=Path(tempfile.mkdtemp(prefix='finna-v10-vocabulary-authoring-backup-',dir='/root'))
    for n in ('scope.json','deploy.py','verify.py'):shutil.copy2(stage/n,backup/n)
    shutil.copytree(public,backup/'public');shutil.copytree(stage/'api',backup/'released-api')
    for n in scope['api']:
        if scope['prior_api'][n] is not None:p=backup/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,p)
    stopped=False
    try:
        guard(scope);assert inventory(public)==scope['prior_web']
        run(['systemctl','stop','ism-api']);stopped=True
        for n in scope['api']:atomic(stage/'api'/n,root/n)
        guard(scope,True);run(['systemctl','start','ism-api']);stopped=False;health()
        run(['rsync','-a','--exclude','index.html',str(stage/'web')+'/',str(public)+'/']);atomic(stage/'web/index.html',public/'index.html')
        run(['chown','-R','caddy:caddy',str(public)]);assert inventory(public)==scope['served_web'];guard(scope,True)
        checked=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],text=True).stdout)
        sites={}
        for host in ('study.hawayu.in','family.hawayu.in'):
            with urlopen('https://'+host,timeout=30) as r:assert r.status==200;sites[host]=r.status
        routes=('/studio','/studio/new','/materials','/admin/bank?tab=content','/create','/revise?tab=vocabulary','/feed','/profile')
        for route in routes:
            with urlopen('https://study.hawayu.in'+route,timeout=30) as r:assert r.status==200 and hashlib.sha256(r.read()).hexdigest()==scope['built_web']['index.html']
        receipt={'backup':str(backup),'api_files_changed':list(scope['api']),'unchanged_dependencies':len(scope['prior_api'])-len(scope['api']),'built_files':len(scope['built_web']),'served_files':len(scope['served_web']),'retained_prior_chunks':len(set(scope['prior_web'])-set(scope['built_web'])),'hash_readbacks_match':True,'database_writes':False,'migration_changes':False,'workshop_changes':False,'unit_files_changed':False,'api_restarted':True,'route_shell_checks':len(routes),'health':sites,'verification':checked}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
    except BaseException:
        actual=api_inventory(root,scope);candidate={**scope['prior_api'],**scope['api']}
        assert set(actual)==set(candidate) and all(d in (scope['prior_api'][n],candidate[n]) for n,d in actual.items()),'Unrelated API drift; recovery refused'
        current=inventory(public);assert all(n in scope['served_web'] and d in (scope['prior_web'].get(n),scope['built_web'].get(n)) for n,d in current.items()),'Unrelated static drift; recovery refused'
        if not stopped:run(['systemctl','stop','ism-api'])
        prior_artifacts(backup,scope,root,public);run(['systemctl','start','ism-api']);health();guard(scope);raise

def local(check_only):
    root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text())
    assert sha(Path(__file__))==scope['operator_sha256']
    for n,d in scope['sources'].items():assert sha(root/n)==d,'Source drift: '+n
    for n,d in scope['proofs'].items():assert sha(report/n)==d,'Proof drift: '+n
    assert inventory(root/'web/dist')==scope['built_web']
    host=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
    with tempfile.TemporaryDirectory(prefix='finna-vocabulary-authoring-package-') as directory:
        package=Path(directory);shutil.copytree(root/'web/dist',package/'web')
        for n in scope['api']:p=package/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'api'/n,p)
        for n,source in [('deploy.py',Path(__file__)),('verify.py',root/'scripts/verify-finnaplan-v10-vocabulary-authoring.py'),('scope.json',report/'release-scope.json')]:shutil.copy2(source,package/n)
        stage=run(['ssh',host,'mktemp -d /tmp/finna-v10-vocabulary-authoring-stage.XXXXXX'],text=True).stdout.strip();assert stage.startswith('/tmp/finna-v10-vocabulary-authoring-stage.') and '\n' not in stage
        try:
            run(['rsync','-az','-e','ssh',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod 755 '+shlex.quote(stage)])
            result=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+(' --remote-check ' if check_only else ' --remote ')+shlex.quote(stage)],text=True)
            (report/('preflight.txt' if check_only else 'release.txt')).write_text(result.stdout)
            if check_only:print(result.stdout.strip());return
            receipt=json.loads(next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT ')))
            (report/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Curated vocabulary authoring release verified: '+str(report/'release.json'))
        finally:run(['ssh',host,'rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--remote','--remote-check'):remote(Path(sys.argv[2]),sys.argv[1]=='--remote-check')
    elif len(sys.argv)==3 and sys.argv[1]=='--restore':
        backup=Path(sys.argv[2]).resolve();assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v10-vocabulary-authoring-backup-');restore_pair(backup,json.loads((backup/'scope.json').read_text()));print('Prior parser/static restored; all schema and authored history retained. New word-card drafts remain stored but require the new parser to edit/publish. Shared0105 scheduler retained.')
    else:assert sys.argv[1:] in ([],['--check']);local(sys.argv[1:]==['--check'])
