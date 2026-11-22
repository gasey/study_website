#!/usr/bin/env python3
"""Two-file reader/evidence release; exact paired recovery, no data rollback."""
import fcntl,hashlib,importlib.util,json,os,re,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
ROOT=Path('/srv/api')
REPORT='reports/finna-subject-count-order-production-20261119'
CHANGES=('app/routers/collections.py','app/data/learning-economy-v2.json')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args,**kwargs):
    result=subprocess.run(args,capture_output=True,text=True,**kwargs)
    if result.returncode:raise RuntimeError('Bulk collection reader operation failed: '+args[0])
    return result.stdout
def common(stage,scope):
    assert sha(stage/'common.py')==scope['common_sha256']
    spec=importlib.util.spec_from_file_location('counts_common',stage/'common.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def schema_digest(helper):
    return hashlib.sha256(helper.sql("SELECT jsonb_agg(jsonb_build_array(version,checksum) ORDER BY version)::text FROM schema_migrations").encode()).hexdigest()
def guard(stage,scope,released=False):
    helper=common(stage,scope)
    wanted={**scope['prior_api'],**(scope['api'] if released else {})}
    assert helper.api_inventory(ROOT,scope)==wanted,'API source drift; refused'
    assert helper.inventory(helper.PUBLIC)==scope['served_web'],'Static release drift; refused'
    for name,digest in scope['protected'].items():assert sha(Path(name))==digest,'Protected configuration drift; refused'
    assert schema_digest(helper)==scope['schema_digest'],'Schema migration history drift; refused'
    stat=helper.ENV.stat();assert stat.st_uid==0 and stat.st_mode&0o777==0o600,'Private environment permissions drift'
    return helper
def restore(stage,scope):
    helper=guard(stage,scope,True)
    for name in CHANGES:assert sha(stage/'prior-api'/name)==scope['prior_api'][name],'Corrupt recovery preimage'
    helper.run(['systemctl','stop','ism-api'])
    try:
        for name in CHANGES:helper.atomic_bytes((stage/'prior-api'/name).read_bytes(),ROOT/name)
        guard(stage,scope)
    finally:helper.run(['systemctl','start','ism-api'])
    return {'prior_reader_and_evidence_restored':True,'schema_static_environment_history_preserved':True,'health':helper.health()}
def remote(stage,mode):
    assert os.geteuid()==0
    lock=open('/run/lock/finna-digest-release.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    scope=json.loads((stage/'scope.json').read_text());assert sha(stage/'deploy.py')==scope['operator_sha256']
    if mode=='restore':return restore(stage,scope)
    assert mode in ('check','deploy') and set(scope['api'])==set(CHANGES)
    helper=guard(stage,scope)
    assert helper.inventory(stage/'api')==scope['api']
    assert sha(stage/'verify.py')==scope['verifier_sha256']
    for name in CHANGES:
        data=(stage/'api'/name).read_bytes()
        if name.endswith('.py'):compile(data,name,'exec')
        else:json.loads(data)
    if mode=='check':return {'preflight_passed':True,'installed_files_or_services_changed':False}
    assert scope['phase']=='ready' and shutil.disk_usage('/root').free>2*1024**3
    backup=Path(tempfile.mkdtemp(prefix='finna-subject-count-order-backup-',dir='/root'))
    for name in ('scope.json','deploy.py','common.py','verify.py'):shutil.copy2(stage/name,backup/name)
    for name in CHANGES:
        for base,source in ((backup/'prior-api',ROOT),(backup/'released-api',stage/'api')):
            target=base/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,target)
    stopped=False
    try:
        guard(stage,scope);helper.run(['systemctl','stop','ism-api']);stopped=True
        for name in CHANGES:helper.atomic_bytes((stage/'api'/name).read_bytes(),ROOT/name)
        guard(stage,scope,True);helper.run(['systemctl','start','ism-api']);stopped=False
        health=helper.health()
        checked=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')]))
        assert all(w['state']=='healthy' for w in checked['ops']['workers'])
        samples=[]
        for collection in ('subject-wise-practice','group-b-non-gazetted'):
            started=time.perf_counter()
            with urlopen('https://study.hawayu.in/api/collections/'+collection,timeout=30) as response:
                assert response.status==200;body=json.load(response)
            assert body['id']==collection and isinstance(body['section_list'],list)
            samples.append({'collection':collection,'elapsed_ms':round((time.perf_counter()-started)*1000,3),'http_status':200,'payload_sha256':hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
        guard(stage,scope,True)
        receipt={'backup':str(backup),'api_files_changed':list(CHANGES),'source_readbacks_match':True,'schema_static_environment_preserved':True,'health':health,'verification':checked,'public_collection_http':samples,'database_history_rollback':False,'synthetic_production_activity':False,'email_sent':False}
        (backup/'release.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
    except BaseException:
        try:
            expected={**scope['prior_api'],**scope['api']};actual=helper.api_inventory(ROOT,scope)
            assert set(actual)==set(expected) and all(h in (expected[n],scope['prior_api'][n]) for n,h in actual.items()),'Unrelated source drift; recovery refused'
            guard(stage,{**scope,'api':{name:actual[name] for name in CHANGES}},True)
            if not stopped:helper.run(['systemctl','stop','ism-api']);stopped=True
            for name in CHANGES:helper.atomic_bytes((backup/'prior-api'/name).read_bytes(),ROOT/name)
            guard(stage,scope)
        finally:
            if stopped:helper.run(['systemctl','start','ism-api'])
            helper.health()
        raise
def main():
    if len(sys.argv)==3 and sys.argv[1]=='--restore':
        print(json.dumps(remote(Path(sys.argv[2]),'restore')));return
    if len(sys.argv)==4 and sys.argv[1]=='--remote':
        print(json.dumps(remote(Path(sys.argv[3]),sys.argv[2])));return
    assert sys.argv[1:] in (['--check'],[])
    root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text());package=Path(json.loads((report/'package-path.json').read_text())['path'])
    assert sha(Path(__file__))==scope['operator_sha256']
    for name,digest in scope['proof_sha256'].items():assert sha(root/name)==digest,'Release proof changed'
    for name,digest in scope['api'].items():assert sha(package/'api'/name)==digest,'Candidate source changed'
    mode='check' if sys.argv[1:] else 'deploy';host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-counts-release.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-counts-release\.[A-Za-z0-9]+',stage)
    try:
        with tempfile.TemporaryDirectory(prefix='finna-counts-transfer-') as directory:
            local=Path(directory)
            for name in CHANGES:
                target=local/'api'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(package/'api'/name,target)
            for source,target in ((Path(__file__),'deploy.py'),(root/'scripts/deploy-review-digest.py','common.py'),(root/'scripts/verify-finnaplan-v12-query-performance.py','verify.py'),(report/'release-scope.json','scope.json')):shutil.copy2(source,local/target)
            run(['rsync','-az',str(local)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod -R a+rX '+shlex.quote(stage)])
            receipt=json.loads(run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+' --remote '+mode+' '+shlex.quote(stage)]))
            (report/('check.json' if mode=='check' else 'release.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='verification'}))
    finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':main()
