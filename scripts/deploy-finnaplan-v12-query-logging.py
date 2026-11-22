#!/usr/bin/env python3
"""Bounded PostgreSQL16 duration logging; bind values suppressed, no restart."""
import hashlib,importlib.util,json,os,re,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
from uuid import uuid4
REPORT='reports/finnaplan-v12-query-logging-20261118'
SETTINGS={'log_parameter_max_length':'0','log_parameter_max_length_on_error':'0','log_min_duration_statement':'1000'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,**kw):
 p=subprocess.run(args,capture_output=True,text=True,timeout=180,**kw)
 if p.returncode:raise RuntimeError(p.stderr[-3000:])
 return p.stdout

def pg(query):return run(['sudo','-u','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-d','postgres'],input=query).strip()
def observed():
 keys=','.join("'"+k+"'" for k in SETTINGS)
 return {r['name']:r for r in json.loads(pg("SELECT json_agg(row_to_json(s)) FROM (SELECT name,setting,source,sourcefile,pending_restart FROM pg_settings WHERE name IN("+keys+") ORDER BY name) s"))}
def untargeted(data):
 return '\n'.join(line for line in data.splitlines() if not any(re.match(r'^\s*'+re.escape(k)+r'\s*=',line) for k in SETTINGS))
def guards(stage,scope):
 for name,key in [('dependency-guard.py','dependency_guard_sha256'),('maintenance-guard.py','maintenance_guard_sha256')]:assert sha(stage/name)==scope[key]
 spec=importlib.util.spec_from_file_location('logging_dependency_guard',stage/'dependency-guard.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.guard(stage,scope['dependencies'],True)
 assert sha(Path('/etc/logrotate.d/postgresql-common'))==scope['rotation_sha256']
 assert run(['systemctl','is-active','logrotate.timer']).strip()=='active'
 return m

def wait_settings(expected):
 for n in range(20):
  rows=observed()
  if {k:r['setting'] for k,r in rows.items()}==expected and not any(r['pending_restart'] for r in rows.values()):return rows
  if n==19:raise AssertionError('Reloaded settings differ')
  time.sleep(.2)

def reset_keys(scope,expected_hash):
 path=Path(scope['before']['auto_conf_path']);assert sha(path)==expected_hash,'Configuration drift; recovery refused'
 for key in reversed(SETTINGS):pg('ALTER SYSTEM RESET '+key+';')
 assert pg('SELECT pg_reload_conf()')=='t'
 rows=wait_settings({r['name']:r['setting'] for r in scope['before']['settings'] if r['name'] in SETTINGS})
 assert all(r['source']=='default' and r['sourcefile'] is None for r in rows.values())
 assert sha(path)==scope['before']['auto_conf_sha256'],'Prior auto configuration differs'

def verify_probe(scope):
 log=Path(scope['before']['logs'][0]['path']);assert log.stat().st_mode&0o777==0o640
 start=log.stat();marker='finna-slow-probe-'+uuid4().hex;canary='finna-bind-canary-'+uuid4().hex
 code="""import psycopg,json,sys
p=json.load(sys.stdin)
with psycopg.connect('dbname=mpsc',options='-c role=mpsc -c default_transaction_read_only=on -c statement_timeout=3000') as c:
 r=c.execute('SELECT %s::text,pg_sleep(1.1) /* '+p['marker']+' */',(p['canary'],)).fetchone()
 assert r[0]==p['canary']
 assert c.execute("SELECT current_setting('transaction_read_only'),current_user").fetchone()==('on','mpsc')
print('read-only application-role probe passed')
"""
 assert 'probe passed' in run(['sudo','-u','postgres','/srv/api/.venv/bin/python','-c',code],input=json.dumps({'marker':marker,'canary':canary}))
 for n in range(20):
  stat=log.stat();assert (stat.st_dev,stat.st_ino)==(start.st_dev,start.st_ino) and stat.st_size>=start.st_size,'Log rotated during probe; recheck privately'
  assert stat.st_size-start.st_size<1024**2,'Unexpected log growth during probe'
  with log.open('rb') as f:f.seek(start.st_size);window=f.read().decode(errors='replace')
  if marker in window:break
  if n==19:raise AssertionError('Slow probe absent from existing log')
  time.sleep(.1)
 assert canary not in window,'Bind parameter appeared in log'
 lines=[line for line in window.splitlines() if marker in line]
 durations=[float(v) for line in lines for v in re.findall(r'duration:\s*([0-9.]+)\s*ms',line)]
 assert durations and min(durations)>=1000
 return {'read_only_role':'mpsc','threshold_ms':1000,'observed_probe_ms':max(durations),'bind_canary_absent':True,'existing_log_mode':'0640','raw_queries_or_bind_values_exported':False}

def restore(backup,scope):
 receipt=json.loads((backup/'receipt.json').read_text());guards(backup,scope)
 assert {k:r['setting'] for k,r in observed().items()}==SETTINGS
 reset_keys(scope,receipt['auto_conf_sha256']);guards(backup,scope)
 for host in ('study.hawayu.in','family.hawayu.in'):
  with urlopen('https://'+host,timeout=20) as r:assert r.status==200
 print('Prior three logging defaults restored; unrelated configuration/history unchanged.')

def remote(stage,check=False):
 assert os.geteuid()==0
 scope=json.loads((stage/'scope.json').read_text());assert sha(stage/'deploy.py')==scope['operator_sha256']
 guards(stage,scope);path=Path(scope['before']['auto_conf_path'])
 assert sha(path)==scope['before']['auto_conf_sha256'],'Configuration drift'
 expected={r['name']:r['setting'] for r in scope['before']['settings'] if r['name'] in SETTINGS}
 rows=observed();assert {k:r['setting'] for k,r in rows.items()}==expected
 assert all(r['source']=='default' and r['sourcefile'] is None for r in rows.values()),'Only the audited default configuration is in scope'
 if check:print('Query-log preflight passed; no configuration or service changed.');return
 api_pid=run(['systemctl','show','ism-api','-p','MainPID','--value']).strip();postgres_start=pg('SELECT pg_postmaster_start_time()')
 backup=Path(tempfile.mkdtemp(prefix='finna-v12-query-logging-backup-',dir='/root'))
 for name in ('scope.json','deploy.py','dependency-guard.py','maintenance-guard.py','verify.py'):shutil.copy2(stage/name,backup/name)
 shutil.copy2(path,backup/'postgresql.auto.conf.before');original=path.read_text();expected_hash=sha(path);changed=False
 try:
  # Reload only after parameter suppression and the threshold are all persisted.
  for key,value in SETTINGS.items():
   assert sha(path)==expected_hash,'Concurrent configuration write'
   pg('ALTER SYSTEM SET '+key+"='"+value+"';");changed=True;expected_hash=sha(path)
   assert untargeted(path.read_text())==untargeted(original),'Unrelated configuration changed'
  assert pg('SELECT pg_reload_conf()')=='t';after=wait_settings(SETTINGS)
  probe=verify_probe(scope)
  checked=json.loads(run(['sudo','-u','postgres','/srv/api/.venv/bin/python',str(stage/'verify.py')]))
  assert all(w['state']=='healthy' for w in checked['ops']['workers'])
  guards(stage,scope);sites={}
  for host in ('study.hawayu.in','family.hawayu.in'):
   with urlopen('https://'+host,timeout=20) as r:assert r.status==200;sites[host]=r.status
  assert sha(path)==expected_hash and untargeted(path.read_text())==untargeted(original)
  assert run(['systemctl','show','ism-api','-p','MainPID','--value']).strip()==api_pid and pg('SELECT pg_postmaster_start_time()')==postgres_start
  receipt={'backup':str(backup),'settings':after,'auto_conf_sha256':expected_hash,'probe':probe,'verification':checked,'health':sites,'reload_only':True,'services_restarted':False,'api_static_schema_environment_collectors_unchanged':True,'existing_rotation_unchanged':True,'synthetic_product_activity':False,'historical_slow_query_review':False}
  (backup/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('RECEIPT '+json.dumps(receipt))
 except BaseException:
  if changed:reset_keys(scope,expected_hash)
  raise

def local(check):
 root=Path(__file__).resolve().parents[1];report=root/REPORT;scope=json.loads((report/'release-scope.json').read_text())
 for name,digest in scope['sources'].items():assert sha(root/name)==digest,name+' source drift'
 for name,digest in scope['proofs'].items():assert sha(report/name)==digest,name+' proof drift'
 with tempfile.TemporaryDirectory(prefix='finna-query-log-package-') as directory:
  package=Path(directory)
  for name,source in [('scope.json',report/'release-scope.json'),('deploy.py',Path(__file__)),('dependency-guard.py',root/'scripts/deploy-finnaplan-v12-dependencies.py'),('maintenance-guard.py',root/'scripts/deploy-finnaplan-v12-maintenance.py'),('verify.py',root/'scripts/verify-finnaplan-v12-maintenance.py')]:shutil.copy2(source,package/name)
  host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-v12-query-log.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-v12-query-log\.[A-Za-z0-9]+',stage)
  try:
   run(['rsync','-az',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod 755 '+shlex.quote(stage)])
   out=run(['ssh',host,'sudo /srv/api/.venv/bin/python '+shlex.quote(stage+'/deploy.py')+' --remote '+shlex.quote(stage)+(' --check' if check else '')])
   (report/('preflight.txt' if check else 'release.txt')).write_text(out)
   if not check:
    data=json.loads(next(line[len('RECEIPT '):] for line in out.splitlines() if line.startswith('RECEIPT ')));(report/'release.json').write_text(json.dumps(data,indent=2)+'\n')
   print('Query logging '+('preflight' if check else 'release')+' passed.')
  finally:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':
 if len(sys.argv) in (3,4) and sys.argv[1]=='--remote':remote(Path(sys.argv[2]),len(sys.argv)==4 and sys.argv[3]=='--check')
 elif len(sys.argv)==3 and sys.argv[1]=='--restore':
  backup=Path(sys.argv[2]).resolve();assert os.geteuid()==0 and backup.parent==Path('/root') and backup.name.startswith('finna-v12-query-logging-backup-')
  scope=json.loads((backup/'scope.json').read_text());assert sha(Path(__file__))==scope['operator_sha256'];restore(backup,scope)
 else:assert sys.argv[1:] in ([],['--check']);local(bool(sys.argv[1:]))
