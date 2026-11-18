#!/usr/bin/env python3
"""Bounded V.10 following/deflection release. One API reader; no SQL or bank writes."""
import hashlib,json,os,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
REPORT='reports/finnaplan-v10-following-20261117'
READER='app/routers/community.py'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
def inventory(root):
    assert root.is_dir() and not any(p.is_symlink() for p in root.rglob('*'))
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def api_inventory(root,scope):
    names=set(scope['prior_api'])
    names.update(p.relative_to(root).as_posix() for part,pattern in [('app','*.py'),('migrations','*.sql')] for p in (root/part).rglob(pattern))
    return {name:sha(root/name) for name in sorted(names)}
def run(args,**kwargs):
    result=subprocess.run(args,capture_output=True,**kwargs)
    if result.returncode:raise RuntimeError(str(args[:2])+': '+(result.stderr.decode(errors='replace') if isinstance(result.stderr,bytes) else result.stderr))
    return result
def health():
    for attempt in range(15):
        try:
            with urlopen('https://study.hawayu.in/api/health',timeout=5) as response:assert response.status==200
            return
        except Exception:
            if attempt==14:raise
            time.sleep(1)
def atomically_copy(source,target):
    fd,name=tempfile.mkstemp(prefix='.finna-v10-',dir=target.parent);os.close(fd)
    tmp=Path(name)
    try:shutil.copy2(source,tmp);os.replace(tmp,target)
    finally:
        if tmp.exists():tmp.unlink()
def guard(scope,released=False,root=Path('/srv/api')):
    expected=dict(scope['prior_api'])
    if released:expected[READER]=scope['reader_sha256']
    assert api_inventory(root,scope)==expected,'API or migration drift; release/recovery refused'
def restore_pair(backup,scope,root=Path('/srv/api'),public=Path('/srv/study/public')):
    guard(scope,True,root)
    assert inventory(public)==scope['served_web'],'Newer static release; recovery refused'
    assert inventory(backup/'public')==scope['prior_web'] and sha(backup/'community.py')==scope['prior_api'][READER]
    run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
    atomically_copy(backup/'community.py',root/READER)
    run(['systemctl','restart','ism-api']);health();guard(scope,root=root)
    assert inventory(public)==scope['prior_web']
def restore(backup):
    assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v10-following-backup-')
    scope=json.loads((backup/'scope.json').read_text())
    restore_pair(backup,scope)
    print('Prior API reader and static restored. No SQL, learner history or workshop changes.')
def remote(stage,check_only=False):
    assert os.geteuid()==0
    scope=json.loads((stage/'scope.json').read_text());public=Path('/srv/study/public');root=Path('/srv/api')
    assert sha(stage/'deploy.py')==scope['operator_sha256']
    assert sha(stage/'community.py')==scope['reader_sha256']
    assert sha(stage/'verify.py')==scope['verifier_sha256']
    assert inventory(stage/'web')==scope['built_web']
    compile((stage/'community.py').read_bytes(),READER,'exec')
    guard(scope)
    assert inventory(public)==scope['prior_web'],'Static drift since audit'
    assert shutil.disk_usage('/root').free>2*1024**3
    if check_only:
        print('V.10 bounded preflight passed. No live files, services or SQL changed.');return
    backup=Path(tempfile.mkdtemp(prefix='finna-v10-following-backup-',dir='/root'))
    shutil.copytree(public,backup/'public')
    for name in ('scope.json','deploy.py','verify.py'):shutil.copy2(stage/name,backup/name)
    shutil.copy2(root/READER,backup/'community.py')
    shutil.copy2(stage/'community.py',backup/'released-community.py')
    changed=False
    try:
        guard(scope)
        atomically_copy(stage/'community.py',root/READER);changed=True
        run(['systemctl','restart','ism-api']);health()
        run(['rsync','-a','--exclude','index.html',str(stage/'web')+'/',str(public)+'/'])
        atomically_copy(stage/'web/index.html',public/'index.html')
        run(['chown','-R','caddy:caddy',str(public)])
        assert inventory(public)==scope['served_web'];guard(scope,True)
        # Separate process: actual runtime role, all transactions read-only, no auth sessions.
        verified=run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],text=True)
        reader=json.loads(verified.stdout)
        sites={}
        for host in ('study.hawayu.in','family.hawayu.in'):
            with urlopen('https://'+host,timeout=30) as response:assert response.status==200;sites[host]=response.status
        for route in ('/community?tab=following','/bank/cq_test','/revise','/chronicle','/desk'):
            with urlopen('https://study.hawayu.in'+route,timeout=30) as response:
                assert response.status==200 and hashlib.sha256(response.read()).hexdigest()==scope['built_web']['index.html']
        receipt={'backup':str(backup),'api_files_changed':[READER],'unchanged_api_dependencies':len(scope['prior_api'])-1,
            'built_files':len(scope['built_web']),'served_files':len(scope['served_web']),
            'retained_prior_chunks':len(set(scope['prior_web'])-set(scope['built_web'])),
            'hash_readbacks_match':True,'database_writes':False,'migration_changes':False,'workshop_changes':False,
            'unit_files_changed':False,'api_restarted':True,'route_shell_checks':5,'health':sites,'reader_verification':reader}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('RECEIPT '+json.dumps(receipt))
    except BaseException:
        if changed:
            guard(scope,True)
            actual=inventory(public)
            assert all(name in scope['served_web'] and digest in (scope['prior_web'].get(name),scope['built_web'].get(name)) for name,digest in actual.items()),'Unrelated static changed; recovery refused'
            run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
            atomically_copy(backup/'community.py',root/READER)
            run(['systemctl','restart','ism-api']);health();guard(scope)
        raise
def local(check_only):
    root=Path(__file__).resolve().parents[1];report=root/REPORT
    scope=json.loads((report/'release-scope.json').read_text())
    assert sha(Path(__file__))==scope['operator_sha256']
    for name,digest in scope['sources'].items():assert sha(root/name)==digest,'Source drift: '+name
    for name,digest in scope['proofs'].items():assert sha(report/name)==digest,'Proof drift: '+name
    assert inventory(root/'web/dist')==scope['built_web']
    host=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
    with tempfile.TemporaryDirectory(prefix='finna-v10-following-package-') as directory:
        package=Path(directory);shutil.copytree(root/'web/dist',package/'web')
        for name,source in [('deploy.py',Path(__file__)),('community.py',root/'api'/READER),('verify.py',root/'scripts/verify-finnaplan-v10-following.py'),('scope.json',report/'release-scope.json')]:shutil.copy2(source,package/name)
        stage=run(['ssh',host,'mktemp -d /tmp/finna-v10-following-stage.XXXXXX'],text=True).stdout.strip()
        assert stage.startswith('/tmp/finna-v10-following-stage.') and '\n' not in stage
        try:
            run(['rsync','-az','-e','ssh',str(package)+'/',host+':'+stage+'/'])
            # The isolated postgres verifier must be able to traverse the staged script.
            run(['ssh',host,'chmod 755 '+shlex.quote(stage)])
            mode='--remote-check' if check_only else '--remote'
            result=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+' '+mode+' '+shlex.quote(stage)],text=True)
            (report/('preflight.txt' if check_only else 'release.txt')).write_text(result.stdout)
            if check_only:print(result.stdout.strip());return
            receipt=json.loads(next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT ')))
            (report/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');print('V.10 following release verified: '+str(report/'release.json'))
        finally:run(['ssh',host,'rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--remote','--remote-check'):remote(Path(sys.argv[2]),sys.argv[1]=='--remote-check')
    elif len(sys.argv)==3 and sys.argv[1]=='--restore':restore(Path(sys.argv[2]).resolve())
    else:
        assert sys.argv[1:] in ([],['--check'])
        local(sys.argv[1:]==['--check'])
