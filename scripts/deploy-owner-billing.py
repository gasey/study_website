#!/usr/bin/env python3
"""Bounded Oracle billing release, with a full dump rehearsal and rollback copy.
Run as root with the uploaded source directory. Checkout stays disabled.
"""
import hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

PREIMAGES={
 'billing.py':'7b86d1e6cbc9804d303912b11cb5974807bdb77cd6a0d106c81a99928e61b858',
 'auth.py':'aeca3820b25d2c530feb257d978d234401daae687d82d0004c30199c02702534',
 'me.py':'c7c44e33051dba6f2c4bc2dd5a8c6e0bb844a892e79725a41966151f313ca569',
 'rewards.py':'ddb5cd13cd2d0af672c60e97187134753707a5aae93c398ecb142d89a261e149'}
VERSION='0089_owner_billing_access'
def run(args,**kwargs):return subprocess.run(args,check=True,capture_output=True,**kwargs)
def sql(db,text):return run(['sudo','-u','postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-d',db],input=text.encode()).stdout.decode().strip()
def main():
 assert os.geteuid()==0
 stage=Path(sys.argv[1]);root=Path('/srv/api/app/routers')
 for name,digest in PREIMAGES.items():
  assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Source changed: '+name
  compile((stage/name).read_bytes(),name,'exec')
 assert not sql('mpsc',"SELECT version FROM schema_migrations WHERE version='"+VERSION+"'")
 backup=Path(tempfile.mkdtemp(prefix='finna-owner-billing-',dir='/root'))
 for name in PREIMAGES:shutil.copy2(root/name,backup/name)
 shutil.copytree('/srv/study/public',backup/'public')
 old_function=sql('mpsc',"SELECT pg_get_functiondef('account_has_pro(text)'::regprocedure)")
 (backup/'account_has_pro.sql').write_text(old_function+';\n')
 with (backup/'database.dump').open('wb') as dump:
  subprocess.run(['sudo','-u','postgres','pg_dump','-Fc','mpsc'],stdout=dump,check=True)
 (backup/'database.dump').chmod(0o600)
 print('Paired API/web/database backup saved:',backup,flush=True)
 migration=(stage/(VERSION+'.sql')).read_text()
 clone='finna_billing_rehearsal_'+str(os.getpid())
 run(['sudo','-u','postgres','createdb',clone])
 try:
  with (backup/'database.dump').open('rb') as dump:
   run(['sudo','-u','postgres','pg_restore','--no-owner','--no-privileges','-d',clone],stdin=dump)
  proof="SELECT md5(string_agg(id||':'||account_has_pro(id)::text,',' ORDER BY id)) FROM users; SELECT count(*) FROM canonical_questions; SELECT count(*) FROM appearances;"
  before=sql(clone,proof)
  sql(clone,migration)
  assert sql(clone,proof)==before,'Rehearsal changed existing entitlements/content counts'
  assert sql(clone,'SELECT count(*) FROM billing_access_grants')=='0'
  print('Full database clone rehearsal passed; existing access and bank counts preserved.',flush=True)
 finally:run(['sudo','-u','postgres','dropdb','--force',clone])
 checksum=hashlib.sha256(migration.encode()).hexdigest()[:16]
 ledger="INSERT INTO schema_migrations(version,checksum) VALUES ('"+VERSION+"','"+checksum+"');\nCOMMIT;"
 assert migration.rstrip().endswith('COMMIT;')
 sql('mpsc',migration.rstrip()[:-len('COMMIT;')]+ledger)
 shutil.copy2(stage/(VERSION+'.sql'),Path('/srv/api/migrations')/(VERSION+'.sql'))
 try:
  for name in PREIMAGES:shutil.copy2(stage/name,root/name)
  run(['systemctl','restart','ism-api'])
  for attempt in range(20):
   try:
    with urlopen('https://study.hawayu.in/api/health',timeout=5) as r:healthy=json.load(r).get('status')=='ok'
    if healthy:break
   except Exception:pass
   time.sleep(1)
  else:raise RuntimeError('API did not recover')
  with urlopen('https://study.hawayu.in/api/billing/config',timeout=10) as r:config=json.load(r)
  assert config['enabled'] is False and config['plans']==[{'code':'pro','period':'monthly','amount_paise':10000}]
  with urlopen('https://family.hawayu.in',timeout=15) as r:assert r.status==200
 except Exception:
  for name in PREIMAGES:shutil.copy2(backup/name,root/name)
  sql('mpsc',old_function+';')
  run(['systemctl','restart','ism-api'])
  raise RuntimeError('Health failed; prior routers/function restored; additive tables retained') from None
 print(json.dumps({'installed':True,'migration':VERSION,'checkout_enabled':False,'backup':str(backup)}),flush=True)
if __name__=='__main__':main()
