#!/usr/bin/env python3
"""Bounded detail-reader/economy-binding update; source/status/history preserved."""
import copy,hashlib,importlib.util,json,os,re,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
REPORT='reports/finnaplan-v12-query-performance-20261118'
ROOT=Path('/srv/api')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
def run(args,**kw):
 p=subprocess.run(args,capture_output=True,text=True,timeout=1200,**kw)
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
 return p.stdout

def guard(stage,scope,released=False):
 assert sha(stage/'dependency-guard.py')==scope['dependency_guard_sha256']
 spec=importlib.util.spec_from_file_location('detail_dependency_guard',stage/'dependency-guard.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
 dependencies=copy.deepcopy(scope['dependencies']);dependencies['maintenance']['served_web']=scope['served_web']
 if released:dependencies['maintenance']['api'].update(scope['api'])
 g.guard(stage,dependencies,True)
 assert sha(Path(scope['auto_conf_path']))==scope['auto_conf_sha256'],'PostgreSQL configuration drift'
 assert sha(Path('/etc/logrotate.d/postgresql-common'))==scope['rotation_sha256'],'Rotation drift'
 return g

def healthy():
 for n in range(20):
  try:
   with urlopen('https://study.hawayu.in/api/health',timeout=5) as r:assert r.status==200
   return
  except Exception:
   if n==19:raise
   time.sleep(1)

def restore(backup,scope):
 g=guard(backup,scope,True)
 for name,digest in scope['prior_api'].items():assert sha(backup/'api'/name)==digest
 run(['systemctl','stop','ism-api'])
 atomic=g.common(backup,scope['dependencies']).atomic
 for name in scope['api']:atomic(backup/'api'/name,ROOT/name)
 run(['systemctl','start','ism-api']);healthy();guard(backup,scope)
 return {'prior_reader_evidence_pair_restored':True,'schema_history_static_environment_unchanged':True}

def remote(stage,mode):
 assert os.geteuid()==0
 scope=json.loads((stage/'scope.json').read_text());assert sha(stage/'deploy.py')==scope['operator_sha256']
 assert sha(stage/'verify.py')==scope['verifier_sha256'] and inventory(stage/'api')==scope['api']
 for name in scope['api']:
  if name.endswith('.py'):compile((stage/'api'/name).read_bytes(),name,'exec')
  else:json.loads((stage/'api'/name).read_text())
 g=guard(stage,scope)
 if mode!='rehearse':assert scope['phase']=='ready','Final proof scope incomplete'
 if mode=='check':print('Question-detail preflight passed; no installed files, SQL or service changes.');return
 if mode=='rehearse':
  assert sha(stage/'clone.py')==scope['clone_sha256']
  out=run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'clone.py'),str(stage)],cwd='/')
  data=json.loads(out);guard(stage,scope)
  print('REHEARSAL '+json.dumps(data));return
 assert mode=='deploy' and shutil.disk_usage('/root').free>8*1024**3
 backup=Path(tempfile.mkdtemp(prefix='finna-v12-query-performance-backup-',dir='/root'))
 for name in ('scope.json','deploy.py','verify.py','dependency-guard.py','maintenance-guard.py'):shutil.copy2(stage/name,backup/name)
 for name in scope['api']:
  p=backup/'api'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
 shutil.copytree(stage/'api',backup/'released-api')
 stopped=False
 try:
  guard(stage,scope);run(['systemctl','stop','ism-api']);stopped=True
  atomic=g.common(stage,scope['dependencies']).atomic
  for name in scope['api']:atomic(stage/'api'/name,ROOT/name)
  run(['systemctl','start','ism-api']);stopped=False;healthy();g.common(stage,scope['dependencies']).wait_workers()
  checked=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],cwd='/'))
  assert all(w['state']=='healthy' for w in checked['ops']['workers'])
  detail=[]
  for sample in checked['question_detail_checks']:
   start=time.monotonic()
   with urlopen('https://study.hawayu.in/api/questions/'+quote(sample['id'],safe=''),timeout=30) as r:assert r.status==200;body=json.loads(r.read())
   assert body['id']==sample['id'] and body['answer_status']==sample['answer_status'] and body['reviewed_derived']==sample['reviewed_derived']
   assert not {'answer_text','answer_index','explanation'} & set(body)
   detail.append({'id':sample['id'],'elapsed_ms':round((time.monotonic()-start)*1000,3),'status_and_provenance_match':True,'answer_material_absent':True})
  sites={}
  for host in ('study.hawayu.in','family.hawayu.in'):
   with urlopen('https://'+host,timeout=30) as r:assert r.status==200;sites[host]=r.status
  guard(stage,scope,True)
  receipt={'backup':str(backup),'api_files_changed':list(scope['api']),'source_hash_readbacks_match':True,'static_environment_schema_config_collectors_unchanged':True,'question_detail_http':detail,'health':sites,'verification':checked,'synthetic_production_activity':False,'scoring_or_visibility_rules_changed':False,'database_rollback':False}
  (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
 except BaseException:
  # A paired API/evidence recovery never restores DB/user/worker history.
  actual={name:sha(ROOT/name) for name in scope['api']}
  assert all(d in (scope['api'][name],scope['prior_api'][name]) for name,d in actual.items()),'Unrelated API drift; automatic recovery refused'
  dependencies=copy.deepcopy(scope['dependencies']);dependencies['maintenance']['api'].update(actual)
  temporary={**scope,'dependencies':dependencies};guard(stage,temporary)
  if not stopped:run(['systemctl','stop','ism-api'])
  atomic=g.common(stage,scope['dependencies']).atomic
  for name in scope['api']:atomic(backup/'api'/name,ROOT/name)
  run(['systemctl','start','ism-api']);healthy();guard(stage,scope)
  raise

def local(mode):
 root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text())
 for name,digest in scope['sources'].items():assert sha(root/name)==digest,'Source drift: '+name
 for name,digest in scope['proofs'].items():assert sha(report/name)==digest,'Proof drift: '+name
 if mode!='rehearse':assert scope['phase']=='ready'
 with tempfile.TemporaryDirectory(prefix='finna-detail-package-') as directory:
  package=Path(directory)
  for name in scope['api']:
   p=package/'api'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'api'/name,p)
  for name,source in [('scope.json',report/'release-scope.json'),('deploy.py',Path(__file__)),('verify.py',root/'scripts/verify-finnaplan-v12-query-performance.py'),('dependency-guard.py',root/'scripts/deploy-finnaplan-v12-dependencies.py'),('maintenance-guard.py',root/'scripts/deploy-finnaplan-v12-maintenance.py'),('clone.py',report/'clone.py')]:shutil.copy2(source,package/name)
  host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-v12-query-performance.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-v12-query-performance\.[A-Za-z0-9]+',stage)
  try:
   run(['rsync','-az',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod -R a+rX '+shlex.quote(stage)])
   out=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+' --remote '+mode+' '+shlex.quote(stage)])
   (report/(mode+'.txt')).write_text(out)
   if mode in ('rehearse','deploy'):
    prefix='REHEARSAL ' if mode=='rehearse' else 'RECEIPT ';data=json.loads(next(line[len(prefix):] for line in out.splitlines() if line.startswith(prefix)));(report/('rehearsal.json' if mode=='rehearse' else 'release.json')).write_text(json.dumps(data,indent=2)+'\n')
   print('Question-detail '+mode+' passed.')
  finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--remote':remote(Path(sys.argv[3]),sys.argv[2])
 elif len(sys.argv)==3 and sys.argv[1]=='--restore':
  backup=Path(sys.argv[2]).resolve();assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v12-query-performance-backup-')
  scope=json.loads((backup/'scope.json').read_text());assert sha(Path(__file__))==scope['operator_sha256'];print(json.dumps(restore(backup,scope)))
 else:
  assert sys.argv[1:] in ([],['--check'],['--rehearse']);local('deploy' if not sys.argv[1:] else 'check' if sys.argv[1]=='--check' else 'rehearse')
