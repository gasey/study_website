#!/usr/bin/env python3
"""Two-file consent withdrawal correction; no schema, static or config changes."""
import fcntl,importlib.util,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finna-review-digest-withdrawal-20261119'
def run(args,**kwargs):
    r=subprocess.run(args,capture_output=True,text=True,**kwargs)
    if r.returncode:raise RuntimeError('Withdrawal release failed: '+r.stderr[-2000:])
    return r.stdout
def remote(stage):
    assert os.geteuid()==0
    lock=open('/run/lock/finna-digest-release.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    spec=importlib.util.spec_from_file_location('common',stage/'common.py');common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)
    old=json.loads((stage/'base-scope.json').read_text());scope=json.loads((stage/'scope.json').read_text())
    changes=scope['withdrawal_changes']
    assert common.sha(stage/'common.py')==old['operator_sha256']
    assert common.sha(stage/'verify.py')==old['verifier_sha256']
    assert common.sha(stage/'followup.py')==scope['followup_operator_sha256']
    assert common.inventory(stage/'api')==changes
    common.guard(old,True);assert common.inventory(common.PUBLIC)==old['served_web']
    original=Path('/root/finna-digest-backup-5qj89_ft')
    assert common.ENV.read_bytes()==common.env_value((original/'db.env.before').read_bytes(),True)
    for n,h in old['protected'].items():
        if n!=str(common.ENV):assert common.sha(Path(n))==h
    assert common.sql("SELECT checksum FROM schema_migrations WHERE version='0120_review_digest'")==old['api'][common.MIGRATION]
    backup=Path(tempfile.mkdtemp(prefix='finna-digest-backup-',dir='/root'))
    shutil.copytree(original/'public',backup/'public',copy_function=os.link)
    shutil.copy2(original/'db.env.before',backup/'db.env.before');os.chmod(backup/'db.env.before',0o600)
    shutil.copy2(stage/'common.py',backup/'deploy.py');shutil.copy2(stage/'followup.py',backup/'followup.py')
    shutil.copy2(stage/'scope.json',backup/'scope.json')
    shutil.copytree(original/'released-api',backup/'released-api')
    for n in changes:
        dest=backup/'api'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(common.ROOT/n,dest)
        common.atomic_bytes((stage/'api'/n).read_bytes(),backup/'released-api'/n)
    common.run(['systemctl','stop','ism-api'])
    try:
        common.guard(old,True)
        for n in changes:common.atomic_bytes((stage/'api'/n).read_bytes(),common.ROOT/n)
        common.guard(scope,True)
        common.run(['systemctl','start','ism-api']);health=common.health()
        verified=json.loads(common.run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],text=True).stdout)
        assert common.inventory(common.PUBLIC)==old['served_web']
        assert common.ENV.read_bytes()==common.env_value((original/'db.env.before').read_bytes(),True)
        receipt={'backup':str(backup),'previous_release_backup':str(original),'only_two_api_files_changed':list(changes),'withdrawal_bypasses_subscription_throttle':True,'migration_static_environment_unchanged':True,'health':health,'verification':verified,'synthetic_production_activity':False,'email_sent':False}
        (backup/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
    except Exception:
        current=common.api_inventory(common.ROOT,old)
        expected={**old['prior_api'],**old['api']}
        assert set(current)==set(expected) and all(h in (expected.get(n),changes.get(n)) for n,h in current.items()),'Unrelated source drift; correction rollback refused'
        common.run(['systemctl','stop','ism-api'])
        try:
            for n in changes:common.atomic_bytes((backup/'api'/n).read_bytes(),common.ROOT/n)
            common.guard(old,True)
        finally:common.run(['systemctl','start','ism-api'])
        common.health();raise
def main():
    if len(sys.argv)>1:print(json.dumps(remote(Path(sys.argv[2]))));return
    base=ROOT/'reports/finna-review-digest-production-20261119'
    package=Path(json.loads((base/'package-path.json').read_text())['path'])
    original=json.loads((base/'release-scope.json').read_text());scope=json.loads((REPORT/'scope.json').read_text())
    host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-digest-withdrawal.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-digest-withdrawal\.[A-Za-z0-9]+',stage)
    with tempfile.TemporaryDirectory(prefix='finna-digest-withdrawal-package-') as tmp:
        local=Path(tmp)
        for n in scope['withdrawal_changes']:
            target=local/'api'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(package/'api'/n,target)
        for src,dest in [(Path(__file__),'followup.py'),(ROOT/'scripts/deploy-review-digest.py','common.py'),(ROOT/'scripts/verify-finnaplan-v12-query-performance.py','verify.py'),(base/'release-scope.json','base-scope.json'),(REPORT/'scope.json','scope.json')]:shutil.copy2(src,local/dest)
        try:
            run(['rsync','-az',str(local)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod -R a+rX '+stage])
            raw=run(['ssh',host,'sudo python3 '+stage+'/followup.py --remote '+stage]);receipt=json.loads(raw)
            (REPORT/'release.json').write_text(json.dumps(receipt,indent=2)+'\n')
            print(json.dumps({k:v for k,v in receipt.items() if k!='verification'}))
        finally:run(['ssh',host,'sudo rm -rf -- '+stage])
if __name__=='__main__':main()
