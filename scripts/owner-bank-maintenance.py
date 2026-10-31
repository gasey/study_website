#!/usr/bin/env python3
"""Execute an explicitly owner-delegated source/answer repair via trusted SSH.

No HTTP session, MFA assertion, user, grant, vote or peer review is fabricated.
Input is JSON over stdin, never interpolated into shell code. Ordinary admin
browser writes continue to require their normal session and MFA protections.
"""
import argparse,json,shlex,subprocess
from pathlib import Path
REMOTE='''import asyncio,json,os,sys,subprocess,re
from pathlib import Path
from urllib.parse import urlsplit
pid=subprocess.check_output(['systemctl','show','ism-api','--property=MainPID','--value'],text=True).strip()
env=dict(x.split(b'=',1)for x in Path('/proc/'+pid+'/environ').read_bytes().split(b'\\0')if b'='in x)
os.environ['DATABASE_URL']=env[b'DATABASE_URL'].decode()
for k in (b'PGPASSWORD',b'PGSSLMODE',b'PGPASSFILE'):
 if k in env:os.environ[k.decode()]=env[k].decode()
if urlsplit(os.environ['DATABASE_URL']).path!='/mpsc':raise RuntimeError('Expected production service database')
from app.db import open_pool,close_pool,cursor
from app.services import bank_review as review
from app.services.operator_maintenance import queue_source,intake_source,queue_source_batch,OPERATOR
from app.services.review_identity import Actor
from app.services.review_policy import digest
from app.routers.admin_answers import baseline,decide,Decision
from app.routers.bank_workspace import release,Hold
async def adjudicate(owner,repair,authorization):
 account=Actor(owner,'',False,False)
 qid=repair['canonical_id'];aid=repair['appearance_id']
 async with cursor()as cur:
  q,snap,token=await baseline(cur,account,qid,aid)
  expected=repair.get('expected_source')
  if expected is not None and any(snap['record'].get(k)!=v for k,v in expected.items()):raise ValueError('Reviewed source changed; inspect the question, options, instructions and image before resuming')
  decision=Decision(appearance_id=aid,baseline_hash=token,mode=repair['mode'],answer_index=repair.get('answer_index'),explanation=repair.get('explanation',''),reason=repair['reason'],document_id=repair.get('document_id'),key_page=repair.get('key_page'),preserve_official_key=repair.get('preserve_official_key',False))
  await review.event(cur,None,OPERATOR,'operator_answer_authorization',{'owner_id':owner,'authorization':authorization,'question':qid,'appearance':aid,'request_hash':digest(repair)})
 result=await decide(qid,decision,account,'operator:'+digest(repair)[:60])
 async with cursor()as cur:
  await review.event(cur,result.get('contribution_id'),OPERATOR,'operator_answer_completed',{'owner_id':owner,'authorization':authorization,'result':result})
 return result
async def release_key_hold(owner,repair,authorization):
 account=Actor(owner,'',False,False)
 async with cursor()as cur:
  q,snap,token=await baseline(cur,account,repair['canonical_id'],repair['appearance_id'])
  expected=repair.get('expected_source')
  if not expected or any(snap['record'].get(k)!=v for k,v in expected.items()):raise ValueError('Reviewed source changed before official-key hold release')
  await cur.execute("SELECT id FROM review_documents WHERE id=%s AND paper_id=%s AND kind='official-key' AND key_status='final'",(repair['document_id'],snap['paper']['id']))
  if not await cur.fetchone():raise ValueError('A registered final official key for this exact paper is required')
  await review.event(cur,None,OPERATOR,'operator_key_hold_release_authorization',{'owner_id':owner,'authorization':authorization,'question':repair['canonical_id'],'document_id':repair['document_id'],'request_hash':digest(repair)})
 return await release(repair['canonical_id'],Hold(reason=repair['reason']),account)
async def release_review_hold(owner,repair,authorization):
 account=Actor(owner,'',False,False)
 async with cursor()as cur:
  q,snap,token=await baseline(cur,account,repair['canonical_id'],repair['appearance_id'])
  expected=repair.get('expected_source')
  if not expected or any(snap['record'].get(k)!=v for k,v in expected.items()):raise ValueError('Reviewed source changed before review-hold release')
  await review.event(cur,None,OPERATOR,'operator_review_hold_release_authorization',{'owner_id':owner,'authorization':authorization,'question':repair['canonical_id'],'request_hash':digest(repair)})
 return await release(repair['canonical_id'],Hold(reason=repair['reason']),account)
async def run():
 data=json.load(sys.stdin)
 if len(data['authorization'].strip())<20:raise ValueError('Explicit owner delegation is required')
 await open_pool()
 try:
  async with cursor()as cur:
   await cur.execute("SELECT u.id FROM users u WHERE lower(u.email)=lower(%s) AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=u.id AND g.role='owner' AND g.subject_id IS NULL AND g.revoked_at IS NULL)",(data['owner_email'],))
   users=await cur.fetchall()
   if len(users)!=1:raise ValueError('Exactly one existing owner is required')
   owner=users[0]['id'];operation=data['operation']
   quota_run=data.get('_quota_exemption_run')
   if quota_run:
    if not re.fullmatch(r'[a-zA-Z0-9_-]{8,100}',quota_run):raise ValueError('Use an explicit maintenance run identifier')
    targets=data.get('repairs',[])if operation=='answer-batch'else[data['repair']]if operation=='answer'else[x['proposal']for x in data['items']]if operation=='source-batch'else[data['proposal']]if operation=='source-intake'else[]
    if not 1<=len(targets)<=100 or any(not r.get('canonical_id')for r in targets):raise ValueError('Quota exemption requires 1–100 explicit existing canonical targets')
    exemption_authorization=data.get('_quota_exemption_authorization','')
    if len(exemption_authorization.strip())<20:raise ValueError('Record the explicit owner authorization for removing this run quota')
    review.owner_maintenance_quota_run.set({'owner_id':owner,'run_id':quota_run,'canonical_ids':frozenset(r['canonical_id']for r in targets),'authorization':exemption_authorization})
   if operation=='source-intake':result=await intake_source(cur,owner,data['proposal'],data['authorization'])
   elif operation=='source-batch':result=await queue_source_batch(cur,owner,data['items'],data['authorization'])
   elif operation=='source':result=await queue_source(cur,owner,**data['repair'],authorization=data['authorization'])
   elif operation not in('answer','answer-batch','release-key-hold','release-review-hold'):raise ValueError('Unknown operation')
  if operation=='answer':result=await adjudicate(owner,data['repair'],data['authorization'])
  elif operation=='release-key-hold':result=await release_key_hold(owner,data['repair'],data['authorization'])
  elif operation=='release-review-hold':result=await release_review_hold(owner,data['repair'],data['authorization'])
  elif operation=='answer-batch':
   repairs=data['repairs']
   if not 1<=len(repairs)<=100 or len({r['canonical_id']for r in repairs})!=len(repairs):raise ValueError('Choose 1–100 distinct reviewed canonical answers')
   if any(r['mode']not in('verified','official','needs-review')for r in repairs):raise ValueError('Answer batches contain verified solutions, review holds or explicitly mapped final keys only')
   # Inspect every requested source before committing the first decision. Each
   # decide call still obtains its own fresh locked baseline to detect races.
   async with cursor()as cur:
    for repair in repairs:
     q,snap,token=await baseline(cur,Actor(owner,'',False,False),repair['canonical_id'],repair['appearance_id'])
     expected=repair.get('expected_source')
     if expected is not None and any(snap['record'].get(k)!=v for k,v in expected.items()):raise ValueError('Batch source changed; no answer decisions created')
     opts=snap['record'].get('options',[])
     if repair['mode']=='official':
      if type(repair.get('key_page'))is not int or not 1<=repair['key_page']<=10000:raise ValueError('Official batch requires an inspected key PDF page')
      await cur.execute("SELECT id FROM review_documents WHERE id=%s AND paper_id=%s AND kind='official-key' AND key_status='final'",(repair.get('document_id'),snap['paper']['id']))
      if not await cur.fetchone():raise ValueError('Official batch requires a current final key for this exact paper')
     if repair['mode']=='needs-review':
      if q['type']!='mcq'or q['status']not in('live','held'):raise ValueError('Review holds require an available MCQ: '+repair['canonical_id'])
     elif(q['status']!='live'or q['key_disputed']or q['source_defect']in('duplicate-options','unresolved-source')or not 2<=len(opts)<=8 or any(not isinstance(o,str)or not o.strip()for o in opts)or len({o.strip()for o in opts})!=len(opts)or snap['record'].get('hasDiagram')and not snap['record'].get('figureImage')):raise ValueError('Resolve all source defects/holds before starting this answer batch: '+repair['canonical_id'])
   result={'decisions':[]}
   for repair in repairs:
    try:result['decisions'].append(await adjudicate(owner,repair,data['authorization']))
    except Exception as error:
     # Never lose the exact committed publication IDs after a later failure.
     result['partial_failure']={'canonical_id':repair['canonical_id'],'reason':getattr(error,'detail',str(error))};break
  print(json.dumps(result,default=str))
 finally:await close_pool()
asyncio.run(run())
'''

def require_batch_worker_idle(data):
 # A single-item timer can publish one member while a batch is still being
 # queued, making every remaining immutable export refer to an old bank hash.
 exports_batch=(data.get('operation')=='source-batch' or
     data.get('operation')=='answer-batch' and len(data.get('repairs',[]))>1
     and any(r.get('mode')!='needs-review'for r in data['repairs']))
 if not exports_batch:return
 for unit in ('ism-bank-review.timer','ism-bank-review.service'):
  try:state=subprocess.run(['systemctl','--user','is-active',unit],capture_output=True,text=True).stdout.strip()
  except FileNotFoundError:return  # Hosts without systemd have no such timer.
  if state in ('active','activating','reloading'):
   raise ValueError('Pause ism-bank-review.timer and wait for ism-bank-review.service to finish before queuing batch exports; resume the timer after publication.')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--quota-exemption-run',help='Explicit owner-authorized SSH-only run; normal HTTP/user quotas stay unchanged');p.add_argument('--quota-exemption-reason',help='Owner authorization for this specific maintenance exemption');args=p.parse_args()
 data=json.loads(args.request.read_text())
 require_batch_worker_idle(data)
 data.pop('_quota_exemption_run',None)
 data.pop('_quota_exemption_authorization',None)
 if args.quota_exemption_run:
  if not args.quota_exemption_reason or len(args.quota_exemption_reason.strip())<20:p.error('An explicit --quota-exemption-reason is required for this run')
  data['_quota_exemption_run']=args.quota_exemption_run
  data['_quota_exemption_authorization']=args.quota_exemption_reason
 shell='set -a\n. /etc/mpsc/db.env\nset +a\ncd /srv/api\nexec .venv/bin/python -c '+shlex.quote(REMOTE)
 run=subprocess.run(['ssh','-o','BatchMode=yes','ubuntu@152.67.31.231','sudo','bash','-c',shlex.quote(shell)],input=json.dumps(data),text=True,capture_output=True,timeout=60)
 if run.returncode:raise SystemExit(run.stderr[-2500:])
 result=json.loads(run.stdout);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 if result.get('partial_failure'):raise SystemExit('Batch stopped; reconcile the exact committed IDs saved in '+str(args.output))
if __name__=='__main__':main()
