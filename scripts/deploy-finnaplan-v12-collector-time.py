#!/usr/bin/env python3
"""One read-only timer classification repair over the verified worker release."""
import hashlib,importlib.util,json,os,shlex,shutil,subprocess,sys,tempfile
from pathlib import Path
RNAME='reports/finnaplan-v12-collector-time-20261118'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def run(args,**kwargs):
 p=subprocess.run(args,text=True,capture_output=True,**kwargs)
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
 return p.stdout

def base(stage,scope):
 assert sha(stage/'base.py')==scope['base_sha256']
 spec=importlib.util.spec_from_file_location('base',stage/'base.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def guards(m,scope,released):
 m.guard(scope,released)
 assert m.inventory(Path('/srv/study/public'))==scope['web'],'Static drift'
 assert m.unit_inventory(scope)==scope['prior_units'],'Unit drift'
 assert sha(Path('/srv/api/ops-collector.py'))==scope['collector_sha256'],'Collector drift'

def remote(stage,check):
 assert os.geteuid()==0
 scope=json.loads((stage/'scope.json').read_text());m=base(stage,scope)
 assert sha(stage/'deploy.py')==scope['operator_sha256'] and sha(stage/'verify.py')==scope['verifier_sha256']
 assert sha(stage/'ops.py')==scope['api']['app/services/ops.py'];compile((stage/'ops.py').read_bytes(),'ops.py','exec')
 guards(m,scope,False);m.runtime_mail_guard()
 if check:print('Read-only collector classification preflight passed.');return
 backup=Path(tempfile.mkdtemp(prefix='finna-v12-collector-time-backup-',dir='/root'))
 for n in ('scope.json','base.py','deploy.py','verify.py'):shutil.copy2(stage/n,backup/n)
 shutil.copy2('/srv/api/app/services/ops.py',backup/'ops.py')
 try:
  m.run(['systemctl','stop','ism-api']);m.atomic(stage/'ops.py',Path('/srv/api/app/services/ops.py'))
  m.run(['systemctl','start','ism-api']);m.health();guards(m,scope,True);m.wait_workers()
  checked=json.loads(m.run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')],text=True).stdout)
  host=next(t for t in checked['ops']['timers'] if t['id']=='timer:finna-ops-host')
  assert host['state']=='healthy',host
  sites={}
  from urllib.request import urlopen
  from urllib.error import HTTPError
  for site in ('study.hawayu.in','family.hawayu.in'):
   with urlopen('https://'+site,timeout=30) as r:assert r.status==200;sites[site]=r.status
  try:urlopen('https://study.hawayu.in/api/admin/ops',timeout=30);raise AssertionError('Anonymous ops access')
  except HTTPError as e:assert e.code==401
  receipt={'backup':str(backup),'verification':checked,'sites':sites,'api_files_changed':['app/services/ops.py'],'static_unchanged':len(scope['web']),'units_and_collector_unchanged':True,'schema_changes':False,'economy_bound_sources_unchanged':True,'anonymous_ops_denied':True,'hash_readbacks_match':True}
  (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
 except BaseException:
  actual=m.api_inventory(Path('/srv/api'),scope);expected={**scope['prior_api'],**scope['api']}
  assert set(actual)==set(expected) and all(d in (scope['prior_api'][n],expected[n]) for n,d in actual.items()),'Unrelated API drift'
  assert sha(backup/'ops.py')==scope['prior_api']['app/services/ops.py']
  m.run(['systemctl','stop','ism-api']);m.atomic(backup/'ops.py',Path('/srv/api/app/services/ops.py'));m.run(['systemctl','start','ism-api']);m.health();raise

def local(check):
 root=Path(__file__).resolve().parents[1];report=root/RNAME;scope=json.loads((report/'scope.json').read_text())
 assert sha(Path(__file__))==scope['operator_sha256']
 for n,d in scope['sources'].items():assert sha(root/n)==d,n
 for n,d in scope['proofs'].items():assert sha(report/n)==d,n
 with tempfile.TemporaryDirectory(prefix='finna-time-package-') as directory:
  p=Path(directory)
  for n,source in [('ops.py',root/'api/app/services/ops.py'),('base.py',root/'scripts/deploy-finnaplan-v12-workers.py'),('deploy.py',Path(__file__)),('verify.py',root/'scripts/verify-finnaplan-v12-workers.py'),('scope.json',report/'scope.json')]:shutil.copy2(source,p/n)
  stage=run(['ssh','ubuntu@152.67.31.231','mktemp -d /tmp/finna-collector-time-stage.XXXXXX']).strip();assert stage.startswith('/tmp/finna-collector-time-stage.') and '\n' not in stage
  try:
   run(['rsync','-az',str(p)+'/', 'ubuntu@152.67.31.231:'+stage+'/']);run(['ssh','ubuntu@152.67.31.231','chmod 755 '+shlex.quote(stage)])
   result=run(['ssh','ubuntu@152.67.31.231','sudo python3 '+shlex.quote(stage+'/deploy.py')+(' --remote-check ' if check else ' --remote ')+shlex.quote(stage)])
   (report/('preflight.txt' if check else 'release.txt')).write_text(result)
   if not check:
    receipt=json.loads(next(l.removeprefix('RECEIPT ') for l in result.splitlines() if l.startswith('RECEIPT ')));(report/'release.json').write_text(json.dumps(receipt,indent=2)+'\n')
   print('Collector-time preflight passed.' if check else 'Collector-time read-only repair verified.')
  finally:run(['ssh','ubuntu@152.67.31.231','sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1] in ('--remote','--remote-check'):remote(Path(sys.argv[2]),sys.argv[1]=='--remote-check')
 elif len(sys.argv)==3 and sys.argv[1]=='--restore':
  backup=Path(sys.argv[2]).resolve();assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v12-collector-time-backup-')
  scope=json.loads((backup/'scope.json').read_text());m=base(backup,scope);guards(m,scope,True);assert sha(backup/'ops.py')==scope['prior_api']['app/services/ops.py']
  m.run(['systemctl','stop','ism-api']);m.atomic(backup/'ops.py',Path('/srv/api/app/services/ops.py'));m.run(['systemctl','start','ism-api']);m.health();guards(m,scope,False);print('Prior read-only classification restored.')
 else:assert sys.argv[1:] in ([],['--check']);local(sys.argv[1:]==['--check'])
