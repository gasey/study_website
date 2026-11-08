"""Bridge a reviewed paper job into the single protected Oracle bank publisher."""
import asyncio,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from ..config import settings
from ..db import cursor
from .review_policy import digest
from .review_identity import require_role,grants
from .paper_targets import validate_target
from .paper_approval import validate_approval


def original_pdf(root, source_file, expected_sha):
 """The registered original must still exist inside this workshop's PDF root."""
 folder=(root/'pdfs').resolve()
 path=(folder/(source_file or '')).resolve()
 if not path.is_relative_to(folder) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected_sha:
  raise ValueError('Registered original PDF changed, is missing or is outside the source archive')
 return path


async def existing_source_retry(cur,target,draft,receipt_path):
 """Only the same already-written receipt can explain a now-populated target."""
 if not target or not target['question_count']:return
 try:receipt=json.loads(receipt_path.read_text())
 except (OSError,ValueError):raise ValueError('Registered paper now has questions and no matching publication receipt')
 expected=['paper_'+draft['id'].removeprefix('pwdraft_')+'_'+q['id'] for q in draft['payload']['questions']]
 if (receipt.get('paper_id'),receipt.get('payload_hash'),receipt.get('submission_id'),receipt.get('appearance_ids'))!=(target['paper_id'],digest(draft['payload']),draft['submission_id'],expected):
  raise ValueError('Populated original does not match this reviewed publication receipt')
 await cur.execute('SELECT id FROM appearances WHERE paper_id=%s',(target['paper_id'],))
 if {r['id'] for r in await cur.fetchall()}!=set(expected):raise ValueError('Registered paper contains questions outside this publication')
 # apply() additionally requires the exact immutable manifest and bank checksum.

async def register_key_document(cur,paper_id,p,publisher_id):
 """Retain the inspected edition; a provisional key must never become final."""
 if not p.key_sha256:return
 if p.key_status not in ('provisional','final'):raise ValueError('Confirm the official key edition before publication')
 did='key_'+hashlib.sha256((paper_id+'|'+p.key_sha256).encode()).hexdigest()[:24]
 source='pdfs/Old_Questions/Uploaded/'+p.key_sha256+'.pdf'
 await cur.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,key_status,registered_by) VALUES(%s,%s,%s,%s,%s,'official-key',%s,%s) ON CONFLICT DO NOTHING",(did,paper_id,p.key_title,source,p.key_sha256,p.key_status,publisher_id))
 await cur.execute('SELECT paper_id,title,source_file,sha256,kind,key_status FROM review_documents WHERE id=%s',(did,));registered=await cur.fetchone()
 expected={'paper_id':paper_id,'title':p.key_title,'source_file':source,'sha256':p.key_sha256,'kind':'official-key','key_status':p.key_status}
 if not registered or any(registered[k]!=v for k,v in expected.items()):raise ValueError('Registered official key differs from the inspected edition')

async def publish_job(job,draft):
 from ..routers.paper_workbench import Payload,validate_payload,source_path,storage
 root=Path(settings.canonical_workshop_root);app=root.parent/'india-study-map-app';bank=root/'bank/mpsc_bank_v2.json'
 receipt_path=root/'bank/review-receipts'/('paper-'+draft['id']+'.json')
 if not (app/'scripts/paper_bank_store.py').is_file():raise ValueError('Oracle canonical publisher is not installed; the paper remains unpublished')
 sys.path.insert(0,str(app/'scripts'))
 from bank_authority import require_writable
 from review_bank_store import bank_lock
 from paper_bank_store import apply
 require_writable(bank)
 async with cursor() as cur:
  await cur.execute('SELECT * FROM paper_workbench_drafts WHERE id=%s FOR UPDATE',(draft['id'],));d=await cur.fetchone()
  if d['state'] not in ('queued','publishing','failed') or digest(d['payload'])!=job['args']['payload_hash'] or d['submission_id']!=job['args']['submission_id']:raise ValueError('The queued paper no longer matches the inspected submission')
  await require_role(cur,job['args']['published_by'],roles=('owner',))
  await require_role(cur,d['author_id'],roles=('owner','publisher'))
  await cur.execute("SELECT * FROM paper_workbench_reviews WHERE draft_id=%s AND submission_id=%s AND reviewer_id=%s AND decision='approve' AND payload_hash=%s",(d['id'],d['submission_id'],job['args']['approved_by'],digest(d['payload'])));review=await cur.fetchone()
  await validate_approval(cur,d,review)
  p=Payload(**d['payload']);await validate_payload(cur,p,complete=True)
  target=await validate_target(cur,p,d['source_sha256'],require_empty=False,publication=True)
  await existing_source_retry(cur,target,d,receipt_path)
  await cur.execute('SELECT id,label,parent_id,level,version FROM review_taxonomy WHERE active ORDER BY id');taxonomy=await cur.fetchall()
  figures={}
  for q in p.questions:
   if q.figure_job:
    await cur.execute("SELECT result FROM paper_workbench_jobs WHERE id=%s AND draft_id=%s AND kind='crop' AND state='done'",(q.figure_job,d['id']));r=await cur.fetchone()
    if not r:raise ValueError('A selected figure is missing or belongs to another paper')
    image=storage()/'outputs'/(q.figure_job+'.png');sha=r['result']['sha256']
    if not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest()!=sha:raise ValueError('Reviewed crop bytes changed')
    figures[q.figure_job]='images/page-renders/'+sha+'.png'
  await cur.execute("UPDATE paper_workbench_drafts SET state='publishing' WHERE id=%s",(d['id'],))
 manifest={'schema':1,'draft_id':d['id'],'source_sha256':d['source_sha256'],'submission_id':d['submission_id'],'payload_hash':digest(d['payload']),'payload':d['payload'],'taxonomy':taxonomy,'taxonomy_version':next(iter(taxonomy))['version'] if taxonomy else 'manual','figures':figures,'author_id':d['author_id'],'reviewer_id':review['reviewer_id'],'publisher_id':job['args']['published_by']}
 if review.get('review_kind')=='owner_ai':manifest.update(review_kind='owner_ai',review_model=review['review_model'],review_evidence=review['review_evidence'])
 if review.get('review_kind')=='owner':manifest.update(review_kind='owner',review_evidence=review['review_evidence'])
 if target:manifest['existing_source']={'paper_id':target['paper_id'],'snapshot':target['snapshot']}
 def apply_and_sync():
  # This process owns the lock through file replacement, database sync and readback.
  with bank_lock(bank):
   if target:original_pdf(root,target['snapshot']['paper']['source_file'],d['source_sha256'])
   for sha in [d['source_sha256'],*([p.key_sha256] if p.key_sha256 else [])]:
    source=source_path(sha)
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=sha:raise ValueError('Reviewed PDF bytes changed or are missing')
    # Keep an existing original at its existing identity; do not create an
    # Uploaded alias or a second public paper for the same source PDF.
    if target and sha==d['source_sha256']:continue
    dest=root/'pdfs/Old_Questions/Uploaded'/(sha+'.pdf');dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():shutil.copyfile(source,dest)
    public=Path(settings.paper_archive_root)/'Old_Questions/Uploaded'/(sha+'.pdf');public.parent.mkdir(parents=True,exist_ok=True);public.parent.chmod(0o755)
    if not public.exists():shutil.copyfile(source,public);public.chmod(0o644)
   for q in p.questions:
    if q.figure_job:
     dest=root/figures[q.figure_job];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(storage()/'outputs'/(q.figure_job+'.png'),dest)
     public=Path(settings.paper_archive_root).parent/'figures'/dest.name;public.parent.mkdir(parents=True,exist_ok=True);public.parent.chmod(0o755);shutil.copyfile(dest,public);public.chmod(0o644)
   (root/'bank/review-receipts').mkdir(parents=True,exist_ok=True)
   receipt=apply(bank,root,manifest,receipt_path)
   env={**os.environ,'ISM_DB_TRANSPORT':'local','ISM_BANK_LOCK_HELD':'1'}
   subprocess.run([str(app/'scripts/sync-bank.sh')],cwd=app,env=env,check=True,timeout=240,capture_output=True)
   return receipt
 receipt=await asyncio.to_thread(apply_and_sync)
 async with cursor() as cur:
  await cur.execute('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1');live=await cur.fetchone()
  if not live or live['bank_checksum']!=receipt['output_sha256']:raise ValueError('Bank sync receipt does not match the paper publication')
  await cur.execute('SELECT id,type,qnum,page,question,options,direction,passage,explanation,answer_index,answer_source,has_diagram,figure_image,series FROM appearances WHERE paper_id=%s ORDER BY id',(receipt['paper_id'],));rows=await cur.fetchall()
  by_id={r['id']:r for r in rows}
  for i,q in enumerate(p.questions):
   r=by_id.get(receipt['appearance_ids'][i])
   if not r or (r['question'],r['options'],r['answer_index'],r['answer_source'])!=(q.question,q.options,q.answer_index,q.answer_source):raise ValueError('Published paper readback differs from the inspected question/key')
   expected={'type':q.type,'qnum':q.number,'page':q.page,'direction':q.direction or None,'passage':q.passage or None,'explanation':q.explanation or None,'series':p.booklet or None,'has_diagram':bool(q.figure_job),'figure_image':figures.get(q.figure_job)}
   if any(r.get(k)!=v for k,v in expected.items()):raise ValueError('Published question context/figure/booklet differs from the reviewed source')
   await cur.execute('SELECT qc.subject_id,qc.topic_id,qc.subtopic_id FROM question_classifications qc JOIN appearances a ON a.canonical_id=qc.question_id WHERE a.id=%s AND qc.review_status=\'approved\'',(r['id'],));classification=await cur.fetchone()
   if not classification or any(classification[k]!=getattr(q,k) for k in ('subject_id','topic_id','subtopic_id')):raise ValueError('Published learning classification differs from review')
  await cur.execute('SELECT exam_name,year,paper_subject,source_file FROM papers WHERE id=%s',(receipt['paper_id'],));paper=await cur.fetchone()
  expected_source=target['snapshot']['paper']['source_file'] if target else receipt['paper_id']
  if not paper or (paper['exam_name'],paper['year'],paper['paper_subject'],paper['source_file'])!=(p.exam_name,p.year,p.paper_subject or None,expected_source):raise ValueError('Published exam identity differs from the source review')
  if target:
   # Compare the complete pre-existing paper identity after normal sync too.
   from .paper_targets import registered_sources
   _,registered=await registered_sources(cur,d['source_sha256'])
   current=next((r for r in registered if r['paper_id']==target['paper_id']),None)
   if not current or current['snapshot']!=target['snapshot']:raise ValueError('Registered source identity changed during publication')
  if len(rows)!=len(p.questions):raise ValueError('Published source count differs from the reviewed paper')
  await cur.execute('SELECT id FROM bank_exam_catalog WHERE title=%s ORDER BY id LIMIT 1',(p.exam_name,));exam=await cur.fetchone()
  if not exam:
   from uuid import uuid4
   eid='exam_'+uuid4().hex
   await cur.execute('INSERT INTO bank_exam_catalog(id,title,created_by) VALUES(%s,%s,%s) RETURNING id',(eid,p.exam_name,job['args']['published_by']));exam=await cur.fetchone()
  await cur.execute('INSERT INTO bank_exam_papers(exam_id,paper_id,created_by) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(exam['id'],receipt['paper_id'],job['args']['published_by']))
  if not target:
   await cur.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,%s,%s,%s,'paper',%s) ON CONFLICT DO NOTHING",('doc_'+hashlib.sha256(receipt['paper_id'].encode()).hexdigest()[:24],receipt['paper_id'],p.title,'pdfs/'+receipt['paper_id'],d['source_sha256'],job['args']['published_by']))
  await register_key_document(cur,receipt['paper_id'],p,job['args']['published_by'])
  await cur.execute("UPDATE paper_workbench_drafts SET state='published',published_paper_id=%s,last_error=NULL,version=version+1,updated_at=now() WHERE id=%s",(receipt['paper_id'],d['id']))
  from .bank_review import event
  await event(cur,None,job['args']['published_by'],'paper_published',{'draft':d['id'],'paper':receipt['paper_id'],'questions':len(rows),'receipt':receipt,'reviewer':review['reviewer_id']})
 return receipt
