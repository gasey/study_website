#!/usr/bin/env python3
"""Bounded offline Python environment replacement; API/static/history stay fixed."""
import base64,csv,fcntl,hashlib,importlib.util,io,json,os,re,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
REPORT='reports/finnaplan-v12-dependencies-20261118'
ROOT=Path('/srv/api')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def files(root):
 out={}
 for p in sorted(root.rglob('*')):
  if '__pycache__' in p.parts or p.suffix=='.pyc':continue
  n=p.relative_to(root).as_posix()
  if p.is_symlink():out[n]={'link':str(p.readlink())}
  elif p.is_file():out[n]=sha(p)
 return out

def run(args,**kw):
 p=subprocess.run(args,capture_output=True,text=True,timeout=900,**kw)
 if p.returncode:raise RuntimeError(str(args[:2])+': '+p.stderr[-4000:])
 return p.stdout

def packages(env):
 code="import importlib.metadata,json,re;print(json.dumps({re.sub(r'[-_.]+','-',d.metadata['Name'].lower()):d.version for d in importlib.metadata.distributions()}))"
 return json.loads(run([str(env/'bin/python'),'-c',code],cwd='/'))
def normalize(data):return {re.sub(r'[-_.]+','-',k.lower()):v for k,v in data.items()}
def common(stage,scope):
 assert sha(stage/'maintenance-guard.py')==scope['guard_sha256']
 spec=importlib.util.spec_from_file_location('dependency_guard',stage/'maintenance-guard.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module

def guard(stage,scope,new=False):
 g=common(stage,scope);m=scope['maintenance']
 g.guard(m,True);g.guard_collectors(m);g.guard_extra(m,True)
 assert g.inventory(Path('/srv/study/public'))==m['served_web'],'Static drift'
 assert sha(ROOT/'requirements.txt')==scope['requirements_sha256' if new else 'prior_requirements_sha256'],'Requirements drift'
 assert files(ROOT/'.venv')==scope['environment_after' if new else 'environment_before'],'Python environment drift'
 assert packages(ROOT/'.venv')==scope['packages_after' if new else 'packages_before'],'Installed package drift'
 g.runtime_mail_guard()

def wheel_guard(stage,scope):
 assert {p.name:sha(p) for p in (stage/'wheels').iterdir()}==scope['wheels']
 assert all(n.endswith('-py3-none-any.whl') for n in scope['wheels']),'Only platform-independent runtime wheels allowed'
 assert sha(stage/'requirements.txt')==scope['requirements_sha256']

def prepare(stage,scope,parent):
 wheel_guard(stage,scope)
 env=parent/'venv';shutil.copytree(ROOT/'.venv',env,symlinks=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 pins=[k+'=='+v for k,v in scope['updates'].items()]
 run([str(env/'bin/python'),'-m','pip','install','--disable-pip-version-check','--no-index','--no-deps','--no-compile','--find-links',str(stage/'wheels'),*pins],cwd='/')
 # Console scripts must keep the installed prefix after atomic rename. Update
 # their RECORD hashes too; paths/digests then match independently staged runs.
 changed=set()
 for p in (env/'bin').iterdir():
  if p.is_symlink() or not p.is_file():continue
  data=p.read_bytes();line,sep,tail=data.partition(b'\n')
  if line.startswith(b'#!') and str(env).encode() in line:
   p.write_bytes(b'#!/srv/api/.venv/bin/python\n'+tail);changed.add(p.resolve())
 for record in env.glob('lib/python*/site-packages/*.dist-info/RECORD'):
  rows=list(csv.reader(io.StringIO(record.read_text())));touched=False
  for row in rows:
   target=(record.parent.parent/row[0]).resolve()
   if target in changed:
    data=target.read_bytes();row[1]='sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=');row[2]=str(len(data));touched=True
  if touched:
   output=io.StringIO(newline='');csv.writer(output,lineterminator='\n').writerows(rows);record.write_text(output.getvalue())
 assert packages(env)==scope['packages_after'],'Unexpected dependency resolution'
 assert 'No broken requirements found' in run([str(env/'bin/python'),'-m','pip','check'],cwd='/')
 return env

def healthy():
 for attempt in range(25):
  try:
   with urlopen('https://study.hawayu.in/api/health',timeout=5) as r:assert r.status==200
   return
  except Exception:
   if attempt==24:raise
   time.sleep(1)

def restore(backup,stage,scope):
 guard(stage,scope,True)
 assert files(backup/'venv')==scope['environment_before']
 assert sha(backup/'requirements.before.txt')==scope['prior_requirements_sha256']
 run(['systemctl','stop','ism-api'])
 os.replace(ROOT/'.venv',backup/'released-venv');os.replace(backup/'venv',ROOT/'.venv')
 common(stage,scope).atomic(backup/'requirements.before.txt',ROOT/'requirements.txt')
 run(['systemctl','start','ism-api']);healthy();guard(stage,scope)

def remote(stage,mode):
 assert os.geteuid()==0
 scope=json.loads((stage/'scope.json').read_text());assert sha(stage/'deploy.py')==scope['operator_sha256']
 if mode!='rehearse':assert scope['phase']=='ready','Final proof scope is incomplete'
 assert sha(stage/'verify.py')==scope['verifier_sha256'];wheel_guard(stage,scope)
 guard(stage,scope)
 if mode=='check':print('Dependency preflight passed; API/static/schema/environment unchanged.');return
 with (ROOT/'.finna-dependency-release.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert shutil.disk_usage(ROOT).free>8*1024**3
  with tempfile.TemporaryDirectory(prefix='.finna-dependency-stage-',dir=ROOT) as directory:
   parent=Path(directory);parent.chmod(0o755);env=prepare(stage,scope,parent)
   environment=files(env)
   if mode=='rehearse':
    (stage/'clone.py').write_text(scope['clone_source'])
    # The clone reads only; neither app workers nor economic writers start.
    result=json.loads(run(['sudo','-u','postgres',str(env/'bin/python'),str(stage/'clone.py'),str(env/'bin/python'),str(stage/'verify.py')],cwd='/'))
    guard(stage,scope)
    print('REHEARSAL '+json.dumps({'environment_after':environment,'packages_after':packages(env),'pip_check':True,'clone':result,'no_live_files_services_or_database_writes':True}));return
   assert mode=='deploy' and environment==scope['environment_after'],'Staged environment differs from rehearsal'
   guard(stage,scope)
   backup=Path(tempfile.mkdtemp(prefix='finna-v12-dependencies-backup-',dir='/root'))
   assert backup.stat().st_dev==ROOT.stat().st_dev
   for name in ('scope.json','deploy.py','maintenance-guard.py','verify.py','requirements.txt'):shutil.copy2(stage/name,backup/name)
   shutil.copy2(ROOT/'requirements.txt',backup/'requirements.before.txt')
   stopped=False;old_moved=False;new_moved=False
   try:
    run(['systemctl','stop','ism-api']);stopped=True
    # Recheck immutable runtime contents after stopping the process.
    assert files(ROOT/'.venv')==scope['environment_before']
    os.replace(ROOT/'.venv',backup/'venv');old_moved=True
    os.replace(env,ROOT/'.venv');new_moved=True
    common(stage,scope).atomic(stage/'requirements.txt',ROOT/'requirements.txt')
    run(['systemctl','start','ism-api']);stopped=False;healthy()
    common(stage,scope).wait_workers()
    checked=json.loads(run(['sudo','-u','postgres',str(ROOT/'.venv/bin/python'),str(stage/'verify.py')],cwd='/'))
    assert all(w['state']=='healthy' for w in checked['ops']['workers'])
    guard(stage,scope,True)
    sites={}
    for host in ('study.hawayu.in','family.hawayu.in'):
     with urlopen('https://'+host,timeout=30) as response:assert response.status==200;sites[host]=response.status
    with urlopen('https://study.hawayu.in/api/site-notice',timeout=30) as response:assert set(json.loads(response.read()))=={'message','expires_at','version'}
    receipt={'backup':str(backup),'package_updates':scope['updates'],'packages_after':packages(ROOT/'.venv'),'environment_files':len(environment),'offline_wheel_hashes_verified':True,'pip_check':True,'api_static_schema_collectors_unchanged':True,'requirements_hash_verified':True,'health':sites,'verification':checked,'synthetic_production_activity':False,'database_rollback':False}
    (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
   except BaseException:
    # Never roll back learner/operational data. Only this exact environment and
    # requirements pair can be restored; unscoped source drift refuses recovery.
    g=common(stage,scope);g.guard(scope['maintenance'],True);g.guard_collectors(scope['maintenance']);g.guard_extra(scope['maintenance'],True)
    assert g.inventory(Path('/srv/study/public'))==scope['maintenance']['served_web']
    if not stopped:run(['systemctl','stop','ism-api'])
    if new_moved:
     assert files(ROOT/'.venv')==scope['environment_after'];os.replace(ROOT/'.venv',backup/'failed-venv')
    if old_moved:
     assert files(backup/'venv')==scope['environment_before'];os.replace(backup/'venv',ROOT/'.venv')
    assert sha(ROOT/'requirements.txt') in (scope['requirements_sha256'],scope['prior_requirements_sha256'])
    common(stage,scope).atomic(backup/'requirements.before.txt',ROOT/'requirements.txt')
    run(['systemctl','start','ism-api']);healthy();guard(stage,scope)
    raise

def local(mode):
 root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text())
 assert sha(Path(__file__))==scope['operator_sha256']
 if mode!='rehearse':assert scope['phase']=='ready','Final proof scope is incomplete'
 for name,digest in scope['sources'].items():assert sha(root/name)==digest,'Source drift: '+name
 for name,digest in scope.get('proofs',{}).items():assert sha(report/name)==digest,'Proof drift: '+name
 with tempfile.TemporaryDirectory(prefix='finna-dependency-package-') as directory:
  package=Path(directory);shutil.copytree(report/'wheels',package/'wheels')
  for name,source in [('scope.json',report/'release-scope.json'),('deploy.py',Path(__file__)),('maintenance-guard.py',root/'scripts/deploy-finnaplan-v12-maintenance.py'),('verify.py',root/'scripts/verify-finnaplan-v12-maintenance.py'),('requirements.txt',root/'api/requirements.txt')]:shutil.copy2(source,package/name)
  host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-v12-dependencies.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-v12-dependencies\.[A-Za-z0-9]+',stage)
  try:
   run(['rsync','-az',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod 755 '+shlex.quote(stage)])
   output=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+' --remote '+mode+' '+shlex.quote(stage)])
   (report/(mode+'.txt')).write_text(output)
   if mode in ('deploy','rehearse'):
    prefix='RECEIPT ' if mode=='deploy' else 'REHEARSAL ';result=json.loads(next(line[len(prefix):] for line in output.splitlines() if line.startswith(prefix)))
    (report/('release.json' if mode=='deploy' else 'rehearsal.json')).write_text(json.dumps(result,indent=2)+'\n')
   print('Dependency '+mode+' passed; receipt in '+str(report))
  finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--remote':remote(Path(sys.argv[3]),sys.argv[2])
 elif len(sys.argv)==3 and sys.argv[1]=='--restore':
  backup=Path(sys.argv[2]).resolve();assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v12-dependencies-backup-')
  scope=json.loads((backup/'scope.json').read_text());assert sha(Path(__file__))==scope['operator_sha256']
  restore(backup,backup,scope);print('Prior exact Python environment restored; API/static/schema/history stay fixed.')
 else:
  assert sys.argv[1:] in ([],['--check'],['--rehearse']);local('deploy' if not sys.argv[1:] else 'check' if sys.argv[1]=='--check' else 'rehearse')
