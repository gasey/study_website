#!/usr/bin/env python3
"""Static-only build-tool update; preserve runtime/schema/config and old chunks."""
import copy,hashlib,importlib.util,json,os,re,shlex,shutil,subprocess,sys,tempfile
from pathlib import Path
from urllib.request import urlopen
REPORT='reports/finnaplan-v12-build-dependencies-20261118'
PUBLIC=Path('/srv/study/public')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):
 assert root.is_dir() and not any(p.is_symlink() for p in root.rglob('*'))
 return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
def run(args,**kw):
 p=subprocess.run(args,capture_output=True,text=True,timeout=900,**kw)
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
 return p.stdout

def guard(stage,scope,expected_web):
 assert sha(stage/'dependency-guard.py')==scope['dependency_guard_sha256']
 spec=importlib.util.spec_from_file_location('build_dependency_guard',stage/'dependency-guard.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 dependencies=copy.deepcopy(scope['dependencies']);dependencies['maintenance']['served_web']=expected_web
 m.guard(stage,dependencies,True)
 assert sha(Path(scope['auto_conf_path']))==scope['auto_conf_sha256'],'PostgreSQL configuration drift'
 assert sha(Path('/etc/logrotate.d/postgresql-common'))==scope['rotation_sha256'],'Rotation drift'
 return m

def write_web(source,target,atomic):
 run(['rsync','-a','--exclude','index.html',str(source)+'/',str(target)+'/'])
 atomic(source/'index.html',target/'index.html')
 run(['chown','-R','caddy:caddy',str(target)])

def restore(backup,scope):
 g=guard(backup,scope,scope['served_web'])
 assert inventory(backup/'public')==scope['prior_web']
 write_web(backup/'public',PUBLIC,g.common(backup,scope['dependencies']).atomic)
 guard(backup,scope,scope['restored_web'])
 # Newer immutable chunks remain available to already-open tabs. Only the
 # prior HTML/assets pair is selected; runtime/API/history never roll back.
 return {'prior_index_restored':True,'new_chunks_retained':True,'runtime_and_history_unchanged':True}

def remote(stage,check=False):
 assert os.geteuid()==0
 scope=json.loads((stage/'scope.json').read_text());assert sha(stage/'deploy.py')==scope['operator_sha256']
 assert inventory(stage/'web')==scope['built_web']
 g=guard(stage,scope,scope['prior_web']);assert shutil.disk_usage('/root').free>8*1024**3
 if check:print('Build-dependency preflight passed; no installed files or configuration changed.');return
 backup=Path(tempfile.mkdtemp(prefix='finna-v12-build-dependencies-backup-',dir='/root'))
 for name in ('scope.json','deploy.py','dependency-guard.py','maintenance-guard.py','verify.py'):shutil.copy2(stage/name,backup/name)
 shutil.copytree(PUBLIC,backup/'public');assert inventory(backup/'public')==scope['prior_web']
 api_pid=run(['systemctl','show','ism-api','-p','MainPID','--value']).strip()
 try:
  guard(stage,scope,scope['prior_web'])
  write_web(stage/'web',PUBLIC,g.common(stage,scope['dependencies']).atomic)
  guard(stage,scope,scope['served_web'])
  checked=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')]))
  assert all(w['state']=='healthy' for w in checked['ops']['workers'])
  sites={}
  for host in ('study.hawayu.in','family.hawayu.in'):
   with urlopen('https://'+host,timeout=30) as r:assert r.status==200;sites[host]=200
  routes=('/','/admin/ops','/admin/users','/admin/bank','/library','/feed','/exams','/bank','/revise','/desk','/create','/atlas','/chronicle','/games','/community','/login','/billing')
  for path in routes:
   with urlopen('https://study.hawayu.in'+path,timeout=30) as r:assert r.status==200 and hashlib.sha256(r.read()).hexdigest()==scope['built_web']['index.html']
  entry_assets=[n for n in scope['built_web'] if n.startswith('assets/index-') and n.endswith(('.css','.js'))]
  for name in entry_assets:
   with urlopen('https://study.hawayu.in/'+name,timeout=30) as r:assert hashlib.sha256(r.read()).hexdigest()==scope['built_web'][name]
  assert run(['systemctl','show','ism-api','-p','MainPID','--value']).strip()==api_pid
  guard(stage,scope,scope['served_web'])
  receipt={'backup':str(backup),'built_files':len(scope['built_web']),'served_files':len(scope['served_web']),'retained_prior_chunks':len(set(scope['prior_web'])-set(scope['built_web'])),'entry_assets_checked':len(entry_assets),'route_shell_checks':len(routes),'api_environment_schema_config_collectors_unchanged':True,'api_pid_unchanged':True,'health':sites,'verification':checked,'synthetic_production_activity':False,'runtime_package_versions_unchanged':True}
  (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
 except BaseException:
  actual=inventory(PUBLIC)
  assert set(scope['prior_web'])<=set(actual),'Unrelated static deletion; recovery refused'
  assert all(n in scope['served_web'] and d in (scope['prior_web'].get(n),scope['built_web'].get(n)) for n,d in actual.items()),'Unrelated static drift; recovery refused'
  guard(stage,scope,actual)
  write_web(backup/'public',PUBLIC,g.common(stage,scope['dependencies']).atomic)
  guard(stage,scope,{**actual,**scope['prior_web']})
  raise

def local(check):
 root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text())
 for name,digest in scope['sources'].items():assert sha(root/name)==digest,'Source drift: '+name
 for name,digest in scope['proofs'].items():assert sha(report/name)==digest,'Proof drift: '+name
 assert inventory(root/'web/dist')==scope['built_web']
 with tempfile.TemporaryDirectory(prefix='finna-build-dependency-package-') as directory:
  package=Path(directory);shutil.copytree(root/'web/dist',package/'web')
  for name,source in [('scope.json',report/'release-scope.json'),('deploy.py',Path(__file__)),('dependency-guard.py',root/'scripts/deploy-finnaplan-v12-dependencies.py'),('maintenance-guard.py',root/'scripts/deploy-finnaplan-v12-maintenance.py'),('verify.py',root/'scripts/verify-finnaplan-v12-maintenance.py')]:shutil.copy2(source,package/name)
  host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-v12-build-dependencies.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-v12-build-dependencies\.[A-Za-z0-9]+',stage)
  try:
   run(['rsync','-az',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod 755 '+shlex.quote(stage)])
   out=run(['ssh',host,'sudo python3 '+shlex.quote(stage+'/deploy.py')+' --remote '+shlex.quote(stage)+(' --check' if check else '')])
   (report/('preflight.txt' if check else 'release.txt')).write_text(out)
   if not check:
    data=json.loads(next(line[len('RECEIPT '):] for line in out.splitlines() if line.startswith('RECEIPT ')));(report/'release.json').write_text(json.dumps(data,indent=2)+'\n')
   print('Build dependencies '+('preflight' if check else 'release')+' passed.')
  finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
 if len(sys.argv) in (3,4) and sys.argv[1]=='--remote':remote(Path(sys.argv[2]),len(sys.argv)==4 and sys.argv[3]=='--check')
 elif len(sys.argv)==3 and sys.argv[1]=='--restore':
  backup=Path(sys.argv[2]).resolve();assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v12-build-dependencies-backup-')
  scope=json.loads((backup/'scope.json').read_text());assert sha(Path(__file__))==scope['operator_sha256'];print(json.dumps(restore(backup,scope)))
 else:assert sys.argv[1:] in ([],['--check']);local(bool(sys.argv[1:]))
