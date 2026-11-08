"""Private source-first paper preparation, independent review and durable jobs."""
import hashlib,json,os,tempfile
from pathlib import Path
from typing import Annotated,Literal
from uuid import uuid4
from urllib.parse import unquote
from fastapi import APIRouter,Depends,HTTPException,Request,Query
from fastapi.responses import FileResponse
from pydantic import BaseModel,ConfigDict,Field,model_validator
from psycopg.types.json import Jsonb
from starlette.concurrency import run_in_threadpool
from ..config import settings
from ..db import cursor
from ..services.review_identity import Actor,identity,grants,require_role
from ..services.review_policy import digest
from ..services import bank_review
from ..services.paper_targets import registered_sources,validate_target
from ..services.paper_approval import owner_ai_evidence,owner_evidence,owner_preview_hash,validate_approval
from .current_affairs import no_assessment
from .materials import private

router=APIRouter(prefix='/api/paper-workbench',tags=['paper preparation'],dependencies=[Depends(private)])
Account=Annotated[Actor,Depends(identity)]
MAX_UPLOAD=20*1024*1024
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class Question(Strict):
 id:str=Field(pattern=r'^[a-zA-Z0-9_-]{8,80}$')
 number:str=Field(min_length=1,max_length=40)
 page:int=Field(ge=1,le=300)
 type:Literal['mcq','descriptive']='mcq'
 question:str=Field(default='',max_length=40000)
 options:list[str]=Field(default_factory=list,max_length=6)
 direction:str=Field(default='',max_length=20000)
 passage:str=Field(default='',max_length=50000)
 explanation:str=Field(default='',max_length=20000)
 answer_index:int|None=Field(default=None,ge=0,le=5)
 answer_source:Literal['none','derived','key']='none'
 key_page:int|None=Field(default=None,ge=1,le=300)
 subject_id:str=Field(default='',max_length=120)
 topic_id:str|None=Field(default=None,max_length=160)
 subtopic_id:str|None=Field(default=None,max_length=180)
 figure_job:str|None=Field(default=None,pattern=r'^pwjob_[0-9a-f]{32}$')
 @model_validator(mode='after')
 def valid(self):
  if any(len(x)>10000 for x in self.options):raise ValueError('An option exceeds 10000 characters')
  if self.type=='descriptive' and (self.options or self.answer_index is not None or self.answer_source!='none'):raise ValueError('Written questions have no MCQ options or scoring key')
  if (self.answer_index is None)!=(self.answer_source=='none'):raise ValueError('An answer needs explicit provenance; no answer means none')
  if self.answer_index is not None and self.answer_index>=len(self.options):raise ValueError('Answer is outside the printed options')
  if self.answer_source=='key' and self.key_page is None:raise ValueError('Map the answer to its official key PDF page')
  return self
class Payload(Strict):
 title:str=Field(min_length=3,max_length=300)
 exam_name:str=Field(min_length=3,max_length=300)
 year:int|None=Field(default=None,ge=1900,le=2100)
 paper_subject:str=Field(default='',max_length=200)
 booklet:str=Field(default='',max_length=80)
 source_reference:str=Field(default='',max_length=2000)
 identity_page:int|None=Field(default=None,ge=1,le=300)
 identity_note:str=Field(default='',max_length=3000)
 expected_questions:int|None=Field(default=None,ge=1,le=500)
 target_paper_id:str|None=Field(default=None,min_length=1,max_length=500)
 target_source_version:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
 key_sha256:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
 key_status:Literal['provisional','final']|None=None
 key_title:str=Field(default='',max_length=300)
 key_series:str=Field(default='',max_length=80)
 questions:list[Question]=Field(default_factory=list,max_length=500)
 @model_validator(mode='after')
 def unique(self):
  if (self.target_paper_id is None)!=(self.target_source_version is None):raise ValueError('An existing source needs both its paper ID and current source version')
  if len({q.id for q in self.questions})!=len(self.questions) or len({q.number for q in self.questions})!=len(self.questions):raise ValueError('Question IDs and printed numbers must be unique')
  if any(q.answer_source=='key' for q in self.questions) and not self.key_sha256:raise ValueError('Attach the official key upload before recording keyed answers')
  if any(q.answer_source=='key' for q in self.questions) and not self.key_status:raise ValueError('Confirm whether the attached official key is provisional or final')
  return self
class Create(Strict):
 source_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 title:str=Field(min_length=3,max_length=300)
 exam_name:str=Field(min_length=3,max_length=300)
 year:int|None=Field(default=None,ge=1900,le=2100)
class Save(Strict):
 expected_version:int=Field(ge=1)
 payload:Payload
class Change(Strict):
 expected_version:int=Field(ge=1)
 reason:str=Field(min_length=20,max_length=3000)
class Reviewer(Change):
 email:str=Field(min_length=5,max_length=254)
 active:bool=True
class Restore(Change):version:int=Field(ge=1)
class Review(Change):decision:Literal['approve','changes'];source_checked:bool;options_checked:bool;answers_checked:bool;explanations_checked:bool
class OwnerPublish(Strict):
 expected_version:int=Field(ge=1)
 preview_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
 inspected:bool
 note:str=Field(default='',max_length=3000)
class Process(Strict):
 kind:Literal['extract','render','ocr','crop']
 page:int=Field(default=1,ge=1,le=300)
 rotation:Literal[0,90,180,270]=0
 psm:Literal[3,4,6]=3
 x:float=Field(default=0,ge=0,le=1);y:float=Field(default=0,ge=0,le=1)
 width:float=Field(default=1,gt=0,le=1);height:float=Field(default=1,gt=0,le=1)
 @model_validator(mode='after')
 def region(self):
  if self.x+self.width>1.000001 or self.y+self.height>1.000001:raise ValueError('Crop must stay inside the original page')
  if self.rotation and self.kind not in ('render','ocr'):raise ValueError('Crop coordinates use the unrotated source page')
  return self

def storage():return Path(settings.paper_workbench_root)
def source_path(sha):return storage()/'sources'/(sha+'.pdf')
async def global_access(cur,user,write=False):
 await require_role(cur,user,roles=('owner','publisher') if write else ('owner','publisher','reviewer','senior'))
async def draft(cur,did,actor,write=False,lock=False):
 await no_assessment(cur,actor.id)
 await cur.execute('SELECT * FROM paper_workbench_drafts WHERE id=%s'+(' FOR UPDATE' if lock else ''),(did,));row=await cur.fetchone()
 if not row:raise HTTPException(404,'Paper draft not found')
 if not set(await grants(cur,actor.id))&{'owner','publisher','reviewer','senior'}:
  await cur.execute('SELECT 1 FROM paper_workbench_reviewers WHERE draft_id=%s AND user_id=%s AND active',(did,actor.id))
  if not await cur.fetchone():raise HTTPException(404,'Paper draft not found')
 if write:await global_access(cur,actor.id,True)
 return row
async def history(cur,row,actor,action):
 await cur.execute('INSERT INTO paper_workbench_history(draft_id,version,actor_id,action,payload) VALUES(%s,%s,%s,%s,%s)',(row['id'],row['version'],actor.id,action,Jsonb(row['payload'])))
 await bank_review.event(cur,None,actor.id,'paper_workbench_'+action,{'draft':row['id'],'version':row['version']})
async def job(cur,did,kind,args):
 jid='pwjob_'+uuid4().hex
 await cur.execute('INSERT INTO paper_workbench_jobs(id,draft_id,kind,args) VALUES(%s,%s,%s,%s)',(jid,did,kind,Jsonb(args)))
 return jid
async def validate_payload(cur,p,complete=False):
 for q in p.questions:
  if complete and (len(q.question.strip())<3 or not q.subject_id or q.type=='mcq' and (not 2<=len(q.options)<=6 or any(not x.strip() for x in q.options) or len(set(x.strip() for x in q.options))!=len(q.options))):raise HTTPException(422,'Finish every question and its classification; MCQs need two to six distinct printed options')
  parent=None
  for tid,level in [(q.subject_id,'subject'),(q.topic_id,'topic'),(q.subtopic_id,'subtopic')]:
   if tid:
    await cur.execute('SELECT parent_id,level FROM review_taxonomy WHERE id=%s AND active',(tid,));n=await cur.fetchone()
    if not n or n['level']!=level or n['parent_id']!=parent:raise HTTPException(422,'Select a valid approved subject/topic/subtopic hierarchy')
    parent=tid
  if q.subtopic_id and not q.topic_id:raise HTTPException(422,'Choose a topic for the subtopic')
  if q.figure_job:
   await cur.execute("SELECT draft_id FROM paper_workbench_jobs WHERE id=%s AND kind='crop' AND state='done'",(q.figure_job,));crop=await cur.fetchone()
   if not crop:raise HTTPException(422,'A figure crop must finish before saving')
 if p.key_sha256:
  await cur.execute('SELECT 1 FROM paper_workbench_assets WHERE sha256=%s',(p.key_sha256,))
  if not await cur.fetchone():raise HTTPException(422,'Upload the original official key PDF first')

@router.post('/uploads',status_code=201)
async def upload(request:Request,actor:Account):
 async with cursor() as cur:await no_assessment(cur,actor.id);await global_access(cur,actor.id,True)
 if request.headers.get('content-type','').split(';')[0]!='application/pdf':raise HTTPException(415,'Upload a PDF file')
 folder=storage()/'sources';folder.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=folder,prefix='.upload-');size=0;sha=hashlib.sha256();header=b''
 try:
  with os.fdopen(fd,'wb') as f:
   async for chunk in request.stream():
    size+=len(chunk)
    if size>MAX_UPLOAD:raise HTTPException(413,'PDF must be at most 20 MB')
    if len(header)<8:header=(header+chunk)[:8]
    sha.update(chunk);f.write(chunk)
   f.flush();os.fsync(f.fileno())
  if not header.startswith(b'%PDF-') or size<16:raise HTTPException(422,'This is not a PDF document')
  key=sha.hexdigest();target=source_path(key)
  if not target.exists():os.replace(name,target)
  filename=unquote(request.headers.get('x-filename','Source paper.pdf'))[:200]
  async with cursor() as cur:
   await cur.execute('INSERT INTO paper_workbench_assets(sha256,bytes,filename,created_by) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING',(key,size,filename,actor.id))
   await cur.execute("SELECT paper_id,title FROM review_documents WHERE sha256=%s AND kind='paper' LIMIT 10",(key,));duplicates=await cur.fetchall()
   await bank_review.event(cur,None,actor.id,'paper_pdf_uploaded',{'sha256':key,'bytes':size})
  return {'sha256':key,'bytes':size,'filename':filename,'existing_papers':duplicates}
 finally:
  if os.path.exists(name):os.unlink(name)

@router.get('/drafts')
async def listing(actor:Account):
 async with cursor() as cur:
  await no_assessment(cur,actor.id)
  staff=bool(set(await grants(cur,actor.id))&{'owner','publisher','reviewer','senior'})
  await cur.execute('''SELECT d.id,d.version,d.state,d.payload->>'title' AS title,d.payload->>'exam_name' AS exam_name,d.updated_at,d.last_error
   FROM paper_workbench_drafts d WHERE %s OR EXISTS(SELECT 1 FROM paper_workbench_reviewers r WHERE r.draft_id=d.id AND r.user_id=%s AND r.active)
   ORDER BY d.updated_at DESC LIMIT 100''',(staff,actor.id))
  items=await cur.fetchall()
  await cur.execute("SELECT worker_id,status,seen_at>now()-interval '2 minutes' AS available FROM review_worker_health WHERE worker_id IN ('oracle-paper-documents','oracle-paper-publisher')");workers=await cur.fetchall()
  return {'items':items,'workers':workers if staff else [],'can_write':bool(set(await grants(cur,actor.id))&{'owner','publisher'})}

@router.post('/drafts',status_code=201)
async def create(body:Create,actor:Account):
 async with cursor() as cur:
  await no_assessment(cur,actor.id);await global_access(cur,actor.id,True)
  await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,771))',(body.source_sha256,))
  await cur.execute('SELECT id FROM paper_workbench_drafts WHERE source_sha256=%s ORDER BY updated_at DESC,id LIMIT 1',(body.source_sha256,));existing=await cur.fetchone()
  if existing:
   await cur.execute("SELECT id FROM paper_workbench_jobs WHERE draft_id=%s AND kind='extract' ORDER BY created_at,id LIMIT 1",(existing['id'],));extraction=await cur.fetchone()
   return {'id':existing['id'],'job_id':extraction['id'] if extraction else None,'reused':True}
  await cur.execute('SELECT 1 FROM paper_workbench_assets WHERE sha256=%s',(body.source_sha256,))
  if not await cur.fetchone():raise HTTPException(422,'Upload the source PDF first')
  did='pwdraft_'+uuid4().hex;p=Payload(title=body.title,exam_name=body.exam_name,year=body.year)
  await cur.execute('INSERT INTO paper_workbench_drafts(id,author_id,source_sha256,payload) VALUES(%s,%s,%s,%s) RETURNING *',(did,actor.id,body.source_sha256,Jsonb(p.model_dump())))
  row=await cur.fetchone();await history(cur,row,actor,'created');jid=await job(cur,did,'extract',Process(kind='extract').model_dump())
  return {'id':did,'job_id':jid}

@router.get('/drafts/{did}')
async def detail(did:str,actor:Account,page:int=Query(1,ge=1,le=300)):
 async with cursor() as cur:
  row=await draft(cur,did,actor)
  roles=set(await grants(cur,actor.id))
  row['can_write']=bool(roles&{'owner','publisher'})
  row['can_publish']='owner' in roles
  row['can_owner_publish']='owner' in roles
  row['source_url']='/api/paper-workbench/drafts/'+did+'/source'
  _,targets=await registered_sources(cur,row['source_sha256'])
  row['registered_sources']=[{k:v for k,v in target.items() if k!='snapshot'} for target in targets]
  await cur.execute('SELECT page,text FROM paper_workbench_pages WHERE extraction_id=%s AND page=%s',(row['extraction_id'],page));row['page']=await cur.fetchone()
  await cur.execute('SELECT id,kind,state,args,result,error FROM paper_workbench_jobs WHERE draft_id=%s ORDER BY created_at DESC LIMIT 30',(did,));row['jobs']=await cur.fetchall()
  await cur.execute('SELECT u.email,r.active FROM paper_workbench_reviewers r JOIN users u ON u.id=r.user_id WHERE r.draft_id=%s',(did,));row['reviewers']=await cur.fetchall()
  await cur.execute('SELECT id,reviewer_id,decision,note,created_at,review_kind,review_model FROM paper_workbench_reviews WHERE draft_id=%s ORDER BY id DESC LIMIT 20',(did,));row['reviews']=await cur.fetchall()
  await cur.execute('SELECT version,actor_id,action,created_at FROM paper_workbench_history WHERE draft_id=%s ORDER BY version DESC LIMIT 100',(did,));row['history']=await cur.fetchall()
  return row

@router.get('/drafts/{did}/source')
async def source(did:str,actor:Account,key:bool=False):
 async with cursor() as cur:
  row=await draft(cur,did,actor);sha=row['payload'].get('key_sha256') if key else row['source_sha256']
  if not sha:raise HTTPException(404,'Key PDF not attached')
  path=source_path(sha)
  if not path.is_file():raise HTTPException(404,'Source file missing; ask the owner to restore it')
 return FileResponse(path,media_type='application/pdf',headers={'Cache-Control':'private, no-store','Content-Disposition':'inline; filename="source.pdf"'})

@router.get('/drafts/{did}/images/{jid}')
async def image(did:str,jid:str,actor:Account):
 async with cursor() as cur:
  await draft(cur,did,actor)
  await cur.execute("SELECT result FROM paper_workbench_jobs WHERE id=%s AND draft_id=%s AND kind IN ('render','crop') AND state='done'",(jid,did));row=await cur.fetchone()
  if not row:raise HTTPException(404,'Image not ready')
  path=storage()/'outputs'/(jid+'.png')
  if not path.is_file():raise HTTPException(404,'Image file missing')
 return FileResponse(path,media_type='image/png',headers={'Cache-Control':'private, no-store'})

@router.post('/drafts/{did}/save')
async def save(did:str,body:Save,actor:Account):
 async with cursor() as cur:
  row=await draft(cur,did,actor,True,True)
  if row['version']!=body.expected_version:raise HTTPException(409,'Another editor saved this draft. Keep your text, reload and compare before saving.')
  if row['state'] not in ('draft','review','approved','failed'):raise HTTPException(409,'Queued or published drafts cannot be overwritten')
  await validate_payload(cur,body.payload)
  if body.payload.target_paper_id:await validate_target(cur,body.payload,row['source_sha256'])
  for q in body.payload.questions:
   if q.figure_job:
    await cur.execute('SELECT 1 FROM paper_workbench_jobs WHERE id=%s AND draft_id=%s',(q.figure_job,did))
    if not await cur.fetchone():raise HTTPException(422,'Figure crop belongs to another draft')
  await cur.execute("UPDATE paper_workbench_drafts SET payload=%s,version=version+1,state='draft',submission_id=NULL,last_error=NULL,updated_at=now() WHERE id=%s RETURNING *",(Jsonb(body.payload.model_dump()),did));updated=await cur.fetchone()
  await history(cur,updated,actor,'saved');return {'version':updated['version'],'state':'draft'}

@router.post('/drafts/{did}/process',status_code=202)
async def process(did:str,body:Process,actor:Account):
 async with cursor() as cur:
  await draft(cur,did,actor,True)
  await cur.execute("SELECT count(*) AS n FROM paper_workbench_jobs WHERE draft_id=%s AND state IN ('queued','running')",(did,))
  if (await cur.fetchone())['n']>=5:raise HTTPException(429,'Wait for the current page jobs to finish')
  return {'job_id':await job(cur,did,body.kind,body.model_dump())}

@router.post('/drafts/{did}/reviewer')
async def reviewer(did:str,body:Reviewer,actor:Account):
 async with cursor() as cur:
  row=await draft(cur,did,actor,True,True)
  await require_role(cur,actor.id,roles=('owner',))
  if row['version']!=body.expected_version:raise HTTPException(409,'Draft changed; refresh')
  await cur.execute('SELECT id FROM users WHERE lower(email)=%s',(body.email.strip().lower(),));u=await cur.fetchone()
  if not u or u['id']==row['author_id']:raise HTTPException(422,'Choose an existing independent reviewer account')
  await cur.execute('INSERT INTO paper_workbench_reviewers(draft_id,user_id,assigned_by,active) VALUES(%s,%s,%s,%s) ON CONFLICT(draft_id,user_id) DO UPDATE SET active=excluded.active,assigned_by=excluded.assigned_by',(did,u['id'],actor.id,body.active))
  await bank_review.event(cur,None,actor.id,'paper_reviewer_assigned',{'draft':did,'reviewer':u['id'],'reason':body.reason,'active':body.active})
  return {'assigned':body.active}

async def validate_submission(cur,row):
 p=Payload(**row['payload'])
 if not p.questions or not p.year or not p.identity_page or len(p.identity_note)<20 or p.expected_questions!=len(p.questions):raise HTTPException(422,'Confirm exam/year, source-page evidence and the expected question count; prepare every question first')
 await validate_target(cur,p,row['source_sha256'])
 await validate_payload(cur,p,complete=True)
 if any(q.answer_source=='key' for q in p.questions) and (len(p.key_title)<5 or p.key_series!=p.booklet):raise HTTPException(422,'Confirm the official key title and exact booklet mapping')
 await cur.execute('SELECT result FROM paper_workbench_jobs WHERE id=%s AND state=\'done\'',(row['extraction_id'],));ext=await cur.fetchone()
 if not ext:raise HTTPException(409,'Complete source extraction first')
 if max([p.identity_page]+[q.page for q in p.questions])>ext['result']['pages']:raise HTTPException(422,'Source page is outside the PDF')
 if any(q.answer_source=='key' for q in p.questions):
  from ..services.paper_jobs import pdf_pages
  try:count=await run_in_threadpool(pdf_pages,source_path(p.key_sha256))
  except (ValueError,OSError) as e:raise HTTPException(422,'Official key PDF could not be inspected: '+str(e)[:300])
  if max(q.key_page for q in p.questions if q.answer_source=='key')>count:raise HTTPException(422,'Key page is outside the official key PDF')
 return p

@router.post('/drafts/{did}/submit')
async def submit(did:str,body:Change,actor:Account):
 async with cursor() as cur:
  row=await draft(cur,did,actor,True,True);p=Payload(**row['payload'])
  if row['version']!=body.expected_version or row['state']!='draft':raise HTTPException(409,'Save the current draft before submitting')
  await validate_submission(cur,row)
  await cur.execute("UPDATE paper_workbench_drafts SET state='review',submission_id=%s,version=version+1,updated_at=now() WHERE id=%s RETURNING *",(uuid4().hex,did));r=await cur.fetchone();await history(cur,r,actor,'submitted');return {'version':r['version']}

@router.post('/drafts/{did}/review')
async def review(did:str,body:Review,actor:Account):
 async with cursor() as cur:
  row=await draft(cur,did,actor,lock=True)
  if row['version']!=body.expected_version or row['state']!='review':raise HTTPException(409,'Review the current submitted version')
  await cur.execute("SELECT 1 FROM paper_workbench_history WHERE draft_id=%s AND actor_id=%s AND action IN ('created','saved') LIMIT 1",(did,actor.id))
  if await cur.fetchone():raise HTTPException(403,'Another person who has not edited this draft must inspect it')
  if body.decision=='approve' and not all([body.source_checked,body.options_checked,body.answers_checked,body.explanations_checked]):raise HTTPException(422,'Inspect all four source/answer/explanation areas before approval')
  await cur.execute('INSERT INTO paper_workbench_reviews(draft_id,submission_id,payload_hash,reviewer_id,decision,note) VALUES(%s,%s,%s,%s,%s,%s)',(did,row['submission_id'],digest(row['payload']),actor.id,body.decision,body.reason))
  await cur.execute('UPDATE paper_workbench_drafts SET state=%s,version=version+1,updated_at=now() WHERE id=%s RETURNING *',('approved' if body.decision=='approve' else 'draft',did));r=await cur.fetchone();await history(cur,r,actor,'reviewed');return {'version':r['version'],'state':r['state']}

@router.post('/drafts/{did}/publish',status_code=202)
async def publish(did:str,body:Change,actor:Account):
 async with cursor() as cur:
  row=await draft(cur,did,actor,True,True);await require_role(cur,actor.id,roles=('owner',))
  if row['version']!=body.expected_version or row['state']!='approved':raise HTTPException(409,'Publication needs the current approved draft')
  await cur.execute("SELECT r.* FROM paper_workbench_reviews r WHERE r.draft_id=%s AND r.submission_id=%s AND r.decision='approve' AND r.payload_hash=%s ORDER BY id DESC LIMIT 1",(did,row['submission_id'],digest(row['payload'])));review=await cur.fetchone()
  try:await validate_approval(cur,row,review)
  except ValueError as e:raise HTTPException(409,str(e))
  rid=await job(cur,did,'publish',{'payload_hash':digest(row['payload']),'submission_id':row['submission_id'],'approved_by':review['reviewer_id'],'published_by':actor.id})
  await cur.execute("UPDATE paper_workbench_drafts SET state='queued',version=version+1,updated_at=now() WHERE id=%s RETURNING *",(did,));r=await cur.fetchone();await history(cur,r,actor,'publication_queued');return {'job_id':rid,'version':r['version']}

@router.post('/drafts/{did}/owner-ai-review')
async def owner_ai_review(did:str,body:Review,actor:Account):
 """Owner accepts the installed exact-payload AI receipt; never a human sign-off."""
 async with cursor() as cur:
  row=await draft(cur,did,actor,True,True);await require_role(cur,actor.id,roles=('owner',))
  if row['version']!=body.expected_version or row['state']!='review':raise HTTPException(409,'Review the current submitted version')
  if body.decision!='approve' or not all([body.source_checked,body.options_checked,body.answers_checked,body.explanations_checked]):raise HTTPException(422,'Complete the source, options, answer evidence and explanation availability checks')
  try:evidence=owner_ai_evidence(row,actor.id)
  except ValueError as e:raise HTTPException(403,str(e))
  await validate_payload(cur,Payload(**row['payload']),complete=True)
  await cur.execute("INSERT INTO paper_workbench_reviews(draft_id,submission_id,payload_hash,reviewer_id,decision,note,review_kind,review_model,review_evidence) VALUES(%s,%s,%s,%s,'approve',%s,'owner_ai',%s,%s)",(did,row['submission_id'],digest(row['payload']),actor.id,body.reason,evidence['model'],Jsonb(evidence)))
  await cur.execute("UPDATE paper_workbench_drafts SET state='approved',version=version+1,updated_at=now() WHERE id=%s RETURNING *",(did,));updated=await cur.fetchone();await history(cur,updated,actor,'ai_reviewed')
  return {'version':updated['version'],'state':'approved','review_kind':'owner_ai'}


@router.get('/drafts/{did}/owner-preview')
async def owner_preview(did:str,actor:Account):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  row=await draft(cur,did,actor,True,True)
  if row['state'] not in ('draft','review','approved'):raise HTTPException(409,'Preview a saved draft; use its existing job to follow or retry publication')
  p=await validate_submission(cur,row)
  return {'version':row['version'],'preview_hash':owner_preview_hash(row),'title':p.title,
    'exam_name':p.exam_name,'year':p.year,'questions':len(p.questions),
    'mcq':sum(q.type=='mcq' for q in p.questions),'written':sum(q.type=='descriptive' for q in p.questions),
    'keyed':sum(q.answer_source=='key' for q in p.questions),
    'unanswered':sum(q.type=='mcq' and q.answer_index is None for q in p.questions),
    'unexplained':sum(not q.explanation.strip() for q in p.questions),'approval_kind':'owner'}


@router.post('/drafts/{did}/owner-publish',status_code=202)
async def owner_publish(did:str,body:OwnerPublish,actor:Account):
 async with cursor() as cur:
  await require_role(cur,actor.id,roles=('owner',))
  row=await draft(cur,did,actor,True,True)
  if row['state'] in ('queued','publishing','published'):
   await cur.execute('''SELECT id,args FROM paper_workbench_jobs WHERE draft_id=%s AND kind='publish'
     AND args->>'owner_preview_hash'=%s AND args->>'published_by'=%s ORDER BY created_at DESC LIMIT 1''',(did,body.preview_hash,actor.id))
   prior=await cur.fetchone()
   if prior and prior['args'].get('owner_preview_version')==body.expected_version and prior['args']['payload_hash']==digest(row['payload']) and body.inspected:
    return {'job_id':prior['id'],'version':row['version'],'approval_kind':'owner','replayed':True}
  if row['state'] not in ('draft','review','approved') or row['version']!=body.expected_version or owner_preview_hash(row)!=body.preview_hash:
   raise HTTPException(409,'The paper changed. Save and preview its current version before publishing.')
  if not body.inspected:raise HTTPException(422,'Confirm that you checked the source, options/figures, answer evidence and explanation availability')
  await validate_submission(cur,row)
  submission=uuid4().hex;row={**row,'submission_id':submission}
  evidence=owner_evidence(row,actor.id,body.expected_version)
  note='Owner publication decision: '+row['payload']['title']+'.'+(' Owner note: '+body.note.strip() if body.note.strip() else '')
  await cur.execute('''INSERT INTO paper_workbench_reviews(draft_id,submission_id,payload_hash,reviewer_id,decision,note,review_kind,review_evidence)
    VALUES(%s,%s,%s,%s,'approve',%s,'owner',%s)''',(did,submission,digest(row['payload']),actor.id,note,Jsonb(evidence)))
  rid=await job(cur,did,'publish',{'payload_hash':digest(row['payload']),'submission_id':submission,
    'approved_by':actor.id,'published_by':actor.id,'approval_kind':'owner',
    'owner_preview_hash':body.preview_hash,'owner_preview_version':body.expected_version})
  await cur.execute("UPDATE paper_workbench_drafts SET state='queued',submission_id=%s,version=version+1,last_error=NULL,updated_at=now() WHERE id=%s RETURNING *",(submission,did))
  updated=await cur.fetchone();await history(cur,updated,actor,'owner_publication_queued')
  return {'job_id':rid,'version':updated['version'],'approval_kind':'owner','replayed':False}

@router.post('/jobs/{jid}/retry',status_code=202)
async def retry_job(jid:str,actor:Account):
 async with cursor() as cur:
  await cur.execute('SELECT * FROM paper_workbench_jobs WHERE id=%s FOR UPDATE',(jid,));j=await cur.fetchone()
  if not j:raise HTTPException(404,'Job not found')
  d=await draft(cur,j['draft_id'],actor,True,True)
  if j['state']!='failed':raise HTTPException(409,'Only failed jobs can be retried')
  if j['kind']=='publish':
   await require_role(cur,actor.id,roles=('owner',))
   if digest(d['payload'])!=j['args']['payload_hash'] or d['submission_id']!=j['args']['submission_id']:raise HTTPException(409,'Paper changed; obtain a fresh source-bound publication decision')
   await cur.execute("UPDATE paper_workbench_drafts SET state='queued',last_error=NULL WHERE id=%s",(d['id'],))
  await cur.execute("UPDATE paper_workbench_jobs SET state='queued',attempts=0,lease_until=NULL WHERE id=%s",(jid,))
  await bank_review.event(cur,None,actor.id,'paper_job_retry',{'job':jid,'previous_error':j['error']})
  return {'queued':True}

@router.post('/drafts/{did}/restore')
async def restore(did:str,body:Restore,actor:Account):
 async with cursor() as cur:
  await draft(cur,did,actor,True)
  await cur.execute('SELECT payload FROM paper_workbench_history WHERE draft_id=%s AND version=%s',(did,body.version));old=await cur.fetchone()
  if not old:raise HTTPException(404,'Saved version not found')
 return await save(did,Save(expected_version=body.expected_version,payload=Payload(**old['payload'])),actor)
