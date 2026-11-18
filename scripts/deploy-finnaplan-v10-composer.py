#!/usr/bin/env python3
"""Frozen V.10 composer static-only release; no API, database, service or workshop changes."""
import hashlib,json,os,shlex,shutil,subprocess,sys,tempfile
from pathlib import Path
from urllib.request import urlopen
REPORT='reports/finnaplan-v10-composer-20261117'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def inventory(root):
    assert root.is_dir() and not any(p.is_symlink() for p in root.rglob('*'))
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def run(args,**kwargs):
    result=subprocess.run(args,capture_output=True,**kwargs)
    if result.returncode:
        raise RuntimeError(str(args[:2])+': '+(result.stderr.decode(errors='replace') if isinstance(result.stderr,bytes) else result.stderr))
    return result
def compatible(scope,root=Path('/srv/api')):
    names=set(scope['api_compatibility'])
    names.update(p.relative_to(root).as_posix() for part,pattern in [('app','*.py'),('migrations','*.sql')] for p in (root/part).rglob(pattern))
    assert {n:sha(root/n) for n in names}==scope['api_compatibility'],'API/schema compatibility inventory changed'

def restore_files(backup,public,scope):
    assert inventory(backup/'public')==scope['prior_web'],'Static backup changed'
    assert inventory(public)==scope['served_web'],'Newer static release; recovery refused'
    run(['rsync','-a',str(backup/'public')+'/',str(public)+'/'])
    run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
    assert inventory(public)==scope['prior_web']

def restore(backup):
    assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v10-composer-backup-')
    scope=json.loads((backup/'scope.json').read_text());public=Path('/srv/study/public')
    compatible(scope)
    restore_files(backup,public,scope)
    print('Prior static restored; API and learner history unchanged.')

def remote(stage,check_only):
    assert os.geteuid()==0
    scope=json.loads((stage/'scope.json').read_text());public=Path('/srv/study/public')
    assert sha(stage/'deploy.py')==scope['operator_sha256'],'Release helper changed'
    assert inventory(stage/'web')==scope['built_web'],'Staged static differs'
    compatible(scope)
    assert inventory(public)==scope['prior_web'],'Live static changed since audit'
    if check_only:
        print('V.10 composer static preflight passed; no live files changed.');return
    assert shutil.disk_usage('/root').free>2*1024**3
    backup=Path(tempfile.mkdtemp(prefix='finna-v10-composer-backup-',dir='/root'))
    shutil.copytree(public,backup/'public');shutil.copy2(stage/'scope.json',backup/'scope.json');shutil.copy2(stage/'deploy.py',backup/'deploy.py')
    temporary=None
    try:
        # Keep prior hashed chunks for open tabs. Publish the new index atomically
        # only after all of its assets are readable. No rsync of API/workshop.
        run(['rsync','-a','--exclude','index.html',str(stage/'web')+'/',str(public)+'/'])
        fd,name=tempfile.mkstemp(prefix='.finna-v10-composer-index-',dir=public);os.close(fd)
        temporary=Path(name);shutil.copy2(stage/'web/index.html',temporary)
        run(['chown','-R','caddy:caddy',str(public)])
        os.replace(temporary,public/'index.html')
        assert inventory(public)==scope['served_web'],'Static hash readback differs'
        compatible(scope)
        health={}
        for host in ('study.hawayu.in','family.hawayu.in'):
            with urlopen('https://'+host,timeout=30) as response:
                assert response.status==200;health[host]=response.status
        for route in ('/community?compose=study','/community?compose=material-share','/community?tab=following','/create','/revise','/revision','/mistakes','/vocabulary','/chronicle','/important-days','/games','/desk','/inbox','/notifications','/search'):
            with urlopen('https://study.hawayu.in'+route,timeout=30) as response:
                assert response.status==200 and hashlib.sha256(response.read()).hexdigest()==scope['built_web']['index.html'],route
        with urlopen('https://study.hawayu.in/api/health',timeout=30) as response:assert response.status==200
        receipt={'backup':str(backup),'built_files':len(scope['built_web']),'served_files':len(scope['served_web']),
                 'retained_prior_chunks':len(set(scope['prior_web'])-set(scope['built_web'])),
                 'static_hashes_match':True,'api_compatibility_hashes_match':True,'api_or_database_writes':False,
                 'service_changes':False,'route_shell_checks':15,'health':health,'recovery_executed':False}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('RECEIPT '+json.dumps(receipt))
    except BaseException:
        # Fail closed on unrelated operator edits; otherwise recover even a partial copy.
        if temporary and temporary.exists():temporary.unlink()
        actual=inventory(public)
        assert all(name in scope['served_web'] and digest in (scope['prior_web'].get(name),scope['built_web'].get(name)) for name,digest in actual.items()),'Unrelated static changed during release'
        run(['rsync','-a','--delete',str(backup/'public')+'/',str(public)+'/'])
        assert inventory(public)==scope['prior_web']
        raise

def local(check_only):
    root=Path(__file__).resolve().parents[1];report=root/REPORT
    scope=json.loads((report/'release-scope.json').read_text())
    assert sha(Path(__file__))==scope['operator_sha256']
    for name,digest in scope['sources'].items():assert sha(root/name)==digest,'Source changed: '+name
    for name,digest in scope['proofs'].items():assert sha(report/name)==digest,'Proof changed: '+name
    for name,digest in scope['api_compatibility'].items():assert sha(root/'api'/name)==digest,'Local API changed: '+name
    assert inventory(root/'web/dist')==scope['built_web']
    host=os.environ.get('ISM_HOST','ubuntu@152.67.31.231')
    with tempfile.TemporaryDirectory(prefix='finna-v10-composer-package-') as directory:
        package=Path(directory);shutil.copytree(root/'web/dist',package/'web');shutil.copy2(__file__,package/'deploy.py');shutil.copy2(report/'release-scope.json',package/'scope.json')
        stage=run(['ssh',host,'mktemp -d /tmp/finna-v10-composer-stage.XXXXXX'],text=True).stdout.strip()
        assert stage.startswith('/tmp/finna-v10-composer-stage.') and '\n' not in stage
        try:
            run(['rsync','-az','-e','ssh',str(package)+'/',host+':'+stage+'/'])
            mode='--remote-check' if check_only else '--remote'
            result=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+' '+mode+' '+shlex.quote(stage)],text=True)
            (report/('preflight.txt' if check_only else 'release.txt')).write_text(result.stdout)
            if check_only:print(result.stdout.strip());return
            receipt=json.loads(next(line.removeprefix('RECEIPT ') for line in result.stdout.splitlines() if line.startswith('RECEIPT ')))
            (report/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');print('V.10 composer static release verified: '+str(report/'release.json'))
        finally:run(['ssh',host,'rm -rf -- '+shlex.quote(stage)])

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1] in ('--remote','--remote-check'):remote(Path(sys.argv[2]),sys.argv[1]=='--remote-check')
    elif len(sys.argv)==3 and sys.argv[1]=='--restore':restore(Path(sys.argv[2]).resolve())
    else:
        assert sys.argv[1:] in ([],['--check'])
        local(sys.argv[1:]==['--check'])
