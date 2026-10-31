"""Audited staff inventory. Never changes canonical answers or learner exam selection."""
import hashlib,json
from pathlib import Path
from typing import Annotated,Literal
from urllib.parse import urlsplit,unquote
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Query,Response
from pydantic import BaseModel,ConfigDict,Field,field_validator
from psycopg.types.json import Jsonb
from ..config import settings
from ..db import cursor
from ..source_files import source_pdf_url
from ..services.review_identity import Actor,identity,require_role
def no_store(response:Response):response.headers['Cache-Control']='private, no-store'
router=APIRouter(prefix='/api/admin/bank/inventory',tags=['exam inventory'],dependencies=[Depends(no_store)])
Account=Annotated[Actor,Depends(identity)]
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class ExamInput(Strict):
 title:str=Field(min_length=2,max_length=400)
 reason:str=Field(min_length=10,max_length=4000)
class ExpectedInput(Strict):
 exam_id:str=Field(min_length=1,max_length=200)
 title:str=Field(min_length=2,max_length=600)
 year:int|None=Field(default=None,ge=1900,le=2100)
 booklet:str=Field(default='',max_length=80)
 expected_questions:int|None=Field(default=None,ge=1,le=2000)
 paper_id:str|None=Field(default=None,max_length=600)
 reference_url:str=Field(default='',max_length=2000)
 paper_url:str=Field(default='',max_length=2000)
 note:str=Field(min_length=10,max_length=4000)
 context_reviewed:bool=False
 archived:bool=False
 expected_version:int|None=Field(default=None,ge=1)
 @field_validator('reference_url','paper_url')
 @classmethod
 def safe_url(cls,v):
  if v:
   try:u=urlsplit(v);port=u.port
   except ValueError:raise ValueError('Invalid URL')
   if u.scheme!='https' or not u.hostname or u.username or u.password or port not in (None,443):raise ValueError('Use an HTTPS reference without credentials')
  return v
class LinkInput(Strict):
 paper_id:str=Field(min_length=1,max_length=600)
 remove:bool=False
 reason:str=Field(min_length=10,max_length=4000)
async def access(cur,actor,write=False):await require_role(cur,actor.id,roles=('owner','publisher')if write else ('owner','publisher','senior','reviewer'))
async def event(cur,actor,action,target,before,after,reason):
 await cur.execute('INSERT INTO bank_inventory_events(actor_id,action,target_id,before_data,after_data,reason) VALUES(%s,%s,%s,%s,%s,%s)',(actor.id,action,target,Jsonb(before)if before is not None else None,Jsonb(after)if after is not None else None,reason))
def json_record(row):return json.loads(json.dumps(row,default=str))if row else None
def local_pdf_state(url):
 if not url:return 'not-linked'
 if not url.startswith('/papers/source/'):return 'external-unchecked'
 root=Path(settings.paper_archive_root).resolve();path=(root/unquote(url[len('/papers/source/'):])).resolve()
 return 'available' if path.is_relative_to(root)and path.is_file() else 'missing-file'
STATS='''SELECT a.paper_id,count(*)::int AS questions,count(DISTINCT a.canonical_id)::int AS unique_questions,
 count(*) FILTER(WHERE s.answer_status='official')::int AS official,
 count(*) FILTER(WHERE s.answer_status='verified')::int AS verified,
 count(*) FILTER(WHERE s.answer_status='needs-review')::int AS needs_review,
 count(*) FILTER(WHERE s.answer_status='unsolved')::int AS unsolved,
 count(*) FILTER(WHERE s.answer_status='written')::int AS written,
 count(*) FILTER(WHERE NULLIF(btrim(COALESCE(a.direction,q.direction)), '') IS NOT NULL)::int AS directions_present,
 count(*) FILTER(WHERE NULLIF(btrim(COALESCE(a.passage,q.passage)), '') IS NOT NULL)::int AS passages_present,
 count(*) FILTER(WHERE a.has_diagram AND NULLIF(btrim(a.figure_image),'') IS NULL)::int AS missing_figures,
 count(*) FILTER(WHERE NULLIF(btrim(a.question),'') IS NULL)::int AS empty_stems
 FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id AND q.status<>'merged'
 JOIN v_bank_answer_status s ON s.id=q.id GROUP BY a.paper_id'''
@router.get('/exams')
async def exams(actor:Account,q:str=Query('',max_length=200)):
 async with cursor()as cur:
  await access(cur,actor)
  await cur.execute('''SELECT e.*,(SELECT count(*)::int FROM bank_exam_papers ep WHERE ep.exam_id=e.id) AS linked_papers,
   (SELECT count(*)::int FROM bank_paper_expectations x WHERE x.exam_id=e.id AND NOT x.archived) AS expected_papers,
   (SELECT count(*)::int FROM bank_paper_expectations x WHERE x.exam_id=e.id AND NOT x.archived AND x.paper_id IS NULL) AS unmatched
   FROM bank_exam_catalog e WHERE (%s='' OR e.title ILIKE %s) ORDER BY e.title,e.id LIMIT 1000''',(q,'%'+q+'%'));items=await cur.fetchall()
  await cur.execute('''SELECT count(*)::int AS papers,count(*) FILTER(WHERE NOT EXISTS(SELECT 1 FROM bank_exam_papers ep WHERE ep.paper_id=p.id))::int AS unassigned FROM papers p''');summary=await cur.fetchone()
  return {'items':items,'summary':summary,'register_scope':'Only recorded expectations; this is not a complete official archive census.'}
@router.post('/exams')
async def create_exam(body:ExamInput,actor:Account):
 async with cursor()as cur:
  await access(cur,actor,True);eid='exam_'+uuid4().hex
  await cur.execute('INSERT INTO bank_exam_catalog(id,title,created_by) VALUES(%s,%s,%s) RETURNING *',(eid,body.title,actor.id));row=await cur.fetchone()
  await event(cur,actor,'exam_created',eid,None,json_record(row),body.reason)
 return row
@router.post('/exams/{eid}/papers')
async def link_paper(eid:str,body:LinkInput,actor:Account):
 async with cursor()as cur:
  await access(cur,actor,True)
  await cur.execute('SELECT id FROM bank_exam_catalog WHERE id=%s FOR UPDATE',(eid,))
  if not await cur.fetchone():raise HTTPException(404,'Exam not found')
  await cur.execute('SELECT id FROM papers WHERE id=%s',(body.paper_id,))
  if not await cur.fetchone():raise HTTPException(404,'Paper not found')
  if body.remove:
   await cur.execute('SELECT 1 FROM bank_paper_expectations WHERE exam_id=%s AND paper_id=%s AND NOT archived',(eid,body.paper_id))
   if await cur.fetchone():raise HTTPException(409,'Unlink or archive its expected-paper entries first')
   await cur.execute('DELETE FROM bank_exam_papers WHERE exam_id=%s AND paper_id=%s',(eid,body.paper_id))
  else:await cur.execute('INSERT INTO bank_exam_papers(exam_id,paper_id,created_by) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(eid,body.paper_id,actor.id))
  await event(cur,actor,'paper_unlinked'if body.remove else 'paper_linked',eid,None,body.model_dump(),body.reason)
 return {'ok':True}
async def context_fingerprint(cur,pid):
 await cur.execute("""SELECT a.id,a.question,a.options,COALESCE(a.direction,q.direction) AS direction,COALESCE(a.passage,q.passage) AS passage,
 COALESCE(a.question_markup,q.question_markup) AS markup,COALESCE(a.options_markup,q.options_markup) AS options_markup,
 a.has_diagram,a.figure_image,a.qnum,a.page,p.source_file FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id
 JOIN papers p ON p.id=a.paper_id WHERE a.paper_id=%s ORDER BY a.id""",(pid,))
 return hashlib.sha256(json.dumps(await cur.fetchall(),sort_keys=True,default=str).encode()).hexdigest()
async def protect_paper(cur,actor,pid):
 from ..services.bank_review import protect_answer
 await cur.execute("""SELECT a.canonical_id FROM appearances a JOIN (
 SELECT unnest(question_ids) AS qid FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL
 UNION SELECT jsonb_array_elements(gr.questions)->>'id' FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id
 LEFT JOIN game_cups cup ON cup.id=gr.cup_id WHERE gm.user_id=%s AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
 ) active ON active.qid=a.canonical_id WHERE a.paper_id=%s LIMIT 1""",(actor.id,actor.id,pid))
 hit=await cur.fetchone()
 if hit:await protect_answer(cur,actor.id,hit['canonical_id'])
async def save_expectation(cur,actor,body,xid=None):
 await access(cur,actor,True)
 await cur.execute('SELECT id FROM bank_exam_catalog WHERE id=%s',(body.exam_id,))
 if not await cur.fetchone():raise HTTPException(404,'Exam not found')
 if body.paper_id:
  await cur.execute('SELECT id FROM papers WHERE id=%s',(body.paper_id,))
  if not await cur.fetchone():raise HTTPException(404,'Linked paper not found')
  await cur.execute('INSERT INTO bank_exam_papers(exam_id,paper_id,created_by) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(body.exam_id,body.paper_id,actor.id))
 before=None
 if xid:
  await cur.execute('SELECT * FROM bank_paper_expectations WHERE id=%s FOR UPDATE',(xid,));before=await cur.fetchone()
  if not before:raise HTTPException(404,'Expected paper not found')
  if body.expected_version!=before['version']:raise HTTPException(409,'This entry changed. Reload it before saving.')
 elif body.expected_version is not None:raise HTTPException(422,'A new entry has no previous version')
 if body.context_reviewed and not body.paper_id:raise HTTPException(422,'Link a registered paper before confirming source context')
 xid=xid or 'expected_'+uuid4().hex
 values=body.model_dump(exclude={'expected_version'})
 values['context_fingerprint']=await context_fingerprint(cur,body.paper_id)if body.context_reviewed else None
 if before:
  await cur.execute('UPDATE bank_paper_expectations SET '+','.join(k+'=%s'for k in values)+',version=version+1,updated_by=%s,updated_at=now() WHERE id=%s RETURNING *',(*values.values(),actor.id,xid))
 else:
  await cur.execute('INSERT INTO bank_paper_expectations(id,'+','.join(values)+',created_by,updated_by) VALUES('+','.join(['%s']*(len(values)+3))+') RETURNING *',(xid,*values.values(),actor.id,actor.id))
 row=await cur.fetchone();await event(cur,actor,'expectation_updated'if before else 'expectation_created',xid,json_record(before),json_record(row),body.note)
 return row
@router.post('/expectations')
async def create_expected(body:ExpectedInput,actor:Account):
 async with cursor()as cur:return await save_expectation(cur,actor,body)
@router.post('/expectations/{xid}')
async def update_expected(xid:str,body:ExpectedInput,actor:Account):
 async with cursor()as cur:return await save_expectation(cur,actor,body,xid)
@router.get('/expectations')
async def expected(actor:Account,exam_id:str|None=None,year:int|None=Query(None,ge=1900,le=2100),q:str=Query('',max_length=200),unmatched:bool=False,register_state:Literal['active','archived','all']='active',offset:int=Query(0,ge=0,le=1000000),limit:int=Query(20,ge=1,le=100)):
 async with cursor()as cur:
  await access(cur,actor)
  where="(%s='all' OR x.archived=(%s='archived')) AND (%s::text IS NULL OR x.exam_id=%s) AND (%s::int IS NULL OR x.year=%s) AND (%s='' OR x.title ILIKE %s OR e.title ILIKE %s) AND (NOT %s OR x.paper_id IS NULL)"
  args=(register_state,register_state,exam_id,exam_id,year,year,q,'%'+q+'%','%'+q+'%',unmatched)
  await cur.execute('SELECT count(*)::int AS total FROM bank_paper_expectations x JOIN bank_exam_catalog e ON e.id=x.exam_id WHERE '+where,args);total=(await cur.fetchone())['total']
  await cur.execute('SELECT x.*,e.title AS exam_title FROM bank_paper_expectations x JOIN bank_exam_catalog e ON e.id=x.exam_id WHERE '+where+' ORDER BY x.year DESC NULLS LAST,x.title,x.id LIMIT %s OFFSET %s',(*args,limit,offset));items=await cur.fetchall()
  for item in items:item['context_reviewed_current']=bool(item['context_reviewed'] and item['paper_id'] and item['context_fingerprint']==await context_fingerprint(cur,item['paper_id']))
 return {'items':items,'total':total}
@router.get('/papers')
async def papers(actor:Account,exam_id:str|None=None,year:int|None=Query(None,ge=1900,le=2100),q:str=Query('',max_length=200),unassigned:bool=False,offset:int=Query(0,ge=0,le=1000000),limit:int=Query(20,ge=1,le=100)):
 async with cursor()as cur:
  await access(cur,actor)
  where="(%s::text IS NULL OR EXISTS(SELECT 1 FROM bank_exam_papers ep WHERE ep.paper_id=p.id AND ep.exam_id=%s)) AND (%s::int IS NULL OR p.year=%s) AND (%s='' OR p.exam_name ILIKE %s OR p.id ILIKE %s) AND (NOT %s OR NOT EXISTS(SELECT 1 FROM bank_exam_papers ep WHERE ep.paper_id=p.id))"
  args=(exam_id,exam_id,year,year,q,'%'+q+'%','%'+q+'%',unassigned)
  await cur.execute('SELECT count(*)::int AS total FROM papers p WHERE '+where,args);total=(await cur.fetchone())['total']
  filtered=STATS.replace('GROUP BY a.paper_id','WHERE a.paper_id IN (SELECT id FROM picked) GROUP BY a.paper_id')
  await cur.execute('WITH picked AS (SELECT p.* FROM papers p WHERE '+where+' ORDER BY p.year DESC NULLS LAST,p.exam_name,p.id LIMIT %s OFFSET %s), stats AS ('+filtered+""" ) SELECT p.id,p.exam_name,p.exam_type,p.year,p.paper_number,p.source_file,p.pdf_url,s.*,
   (SELECT count(*)::int FROM review_documents d WHERE d.paper_id=p.id AND d.kind='official-key') AS key_documents
   FROM picked p LEFT JOIN stats s ON s.paper_id=p.id ORDER BY p.year DESC NULLS LAST,p.exam_name,p.id""",(*args,limit,offset));items=await cur.fetchall()
 for row in items:
  row['source_pdf_url']=source_pdf_url(row['source_file'],row['pdf_url']);row['pdf_state']=local_pdf_state(row['source_pdf_url'])
 return {'items':items,'total':total}
@router.get('/paper')
async def paper(actor:Account,paper_id:str=Query(min_length=1,max_length=600)):
 async with cursor()as cur:
  await access(cur,actor)
  await protect_paper(cur,actor,paper_id)
  filtered=STATS.replace('GROUP BY a.paper_id','WHERE a.paper_id=%s GROUP BY a.paper_id')
  await cur.execute('WITH stats AS ('+filtered+') SELECT p.*,s.* FROM papers p LEFT JOIN stats s ON s.paper_id=p.id WHERE p.id=%s',(paper_id,paper_id));row=await cur.fetchone()
  if not row:raise HTTPException(404,'Paper not found')
  await cur.execute('SELECT id,title,kind,key_status,sha256,source_file FROM review_documents WHERE paper_id=%s ORDER BY kind,title',(paper_id,));docs=await cur.fetchall()
  for d in docs:
   d['source_pdf_url']=source_pdf_url((d['source_file']or'').removeprefix('pdfs/')) or ('/api/admin/bank/inventory/document/'+d['id'] if (Path(settings.registered_document_root)/(d['sha256']+'.pdf')).is_file() else None)
  await cur.execute('SELECT * FROM bank_paper_expectations WHERE paper_id=%s AND NOT archived ORDER BY id',(paper_id,));row['expectations']=await cur.fetchall()
  fingerprint=await context_fingerprint(cur,paper_id)
  for item in row['expectations']:item['context_reviewed_current']=item['context_reviewed'] and item['context_fingerprint']==fingerprint
  await cur.execute('SELECT e.* FROM bank_exam_catalog e JOIN bank_exam_papers ep ON ep.exam_id=e.id WHERE ep.paper_id=%s ORDER BY e.title',(paper_id,));row['exams']=await cur.fetchall()
  await cur.execute("SELECT qnum,count(*)::int AS copies FROM appearances WHERE paper_id=%s AND qnum IS NOT NULL GROUP BY qnum ORDER BY qnum",(paper_id,));numbers=await cur.fetchall()
  await cur.execute('SELECT bank_checksum,finished_at FROM sync_log WHERE finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1');row['sync']=await cur.fetchone()
  await cur.execute("SELECT c.state,count(*)::int AS count FROM bank_contributions c WHERE c.appearance_id IN(SELECT id FROM appearances WHERE paper_id=%s) GROUP BY c.state",(paper_id,));row['reviews']=await cur.fetchall()
 row['source_pdf_url']=source_pdf_url(row['source_file'],row['pdf_url']);row['pdf_state']=local_pdf_state(row['source_pdf_url']);row['documents']=docs
 numeric=[int(n['qnum'])for n in numbers if n['qnum'].isascii()and n['qnum'].isdigit()and len(n['qnum'])<=4 and 0<int(n['qnum'])<=2000]
 expected_counts={x['expected_questions']for x in row['expectations']if x['expected_questions']}
 upper=max(expected_counts)if len(expected_counts)==1 else max(numeric,default=0)
 row['numbering']={'gaps':[n for n in range(1,upper+1)if n not in set(numeric)],'duplicates':[n for n in numbers if n['copies']>1],'non_numeric':[n['qnum']for n in numbers if not(n['qnum'].isascii()and n['qnum'].isdigit())],'basis':'confirmed expected count'if len(expected_counts)==1 else 'observed numeric range; not proof of missing questions','conflicting_expected_counts':len(expected_counts)>1}
 return row
@router.get('/events')
async def events(actor:Account,before:int|None=None):
 async with cursor()as cur:
  await access(cur,actor)
  await cur.execute('SELECT * FROM bank_inventory_events WHERE (%s::bigint IS NULL OR id<%s) ORDER BY id DESC LIMIT 50',(before,before));return await cur.fetchall()
@router.get('/export')
async def export(actor:Account,response:Response):
 async with cursor()as cur:
  await access(cur,actor);data={'schema':1}
  for table in ['bank_exam_catalog','bank_exam_papers','bank_paper_expectations','bank_inventory_events','bank_inventory_imports','bank_paper_intake','bank_paper_identities']:
   await cur.execute('SELECT * FROM '+table+' ORDER BY '+('expectation_id'if table=='bank_paper_intake'else 'exam_id,paper_id'if table=='bank_exam_papers'else 'sha256'if table=='bank_inventory_imports'else 'paper_id'if table=='bank_paper_identities'else 'id'));data[table]=await cur.fetchall()
 response.headers['Content-Disposition']='attachment; filename="bank-inventory.json"';response.headers['Cache-Control']='private, no-store'
 return data
@router.get('/summary')
async def coverage_summary(actor:Account,exam_id:str|None=None):
 async with cursor()as cur:
  await access(cur,actor)
  await cur.execute('''SELECT s.answer_status,count(DISTINCT s.id)::int AS count FROM v_bank_answer_status s
   JOIN canonical_questions q ON q.id=s.id AND q.status<>'merged' WHERE (%s::text IS NULL OR EXISTS(
    SELECT 1 FROM appearances a JOIN bank_exam_papers ep ON ep.paper_id=a.paper_id WHERE a.canonical_id=s.id AND ep.exam_id=%s)) GROUP BY s.answer_status''',(exam_id,exam_id));counts=await cur.fetchall()
  await cur.execute('''SELECT year,sum(papers)::int AS papers FROM (SELECT p.year,count(*)::int AS papers FROM papers p WHERE (%s::text IS NULL OR EXISTS(SELECT 1 FROM bank_exam_papers ep WHERE ep.paper_id=p.id AND ep.exam_id=%s)) GROUP BY p.year UNION ALL SELECT x.year,0 FROM bank_paper_expectations x WHERE NOT x.archived AND (%s::text IS NULL OR x.exam_id=%s) GROUP BY x.year) ys GROUP BY year ORDER BY year DESC NULLS LAST''',(exam_id,exam_id,exam_id,exam_id));years=await cur.fetchall()
  await cur.execute('''SELECT count(*)::int AS expected,count(*) FILTER(WHERE paper_id IS NULL)::int AS unmatched,
   count(*) FILTER(WHERE context_reviewed)::int AS context_reviewed FROM bank_paper_expectations WHERE NOT archived AND (%s::text IS NULL OR exam_id=%s)''',(exam_id,exam_id));register=await cur.fetchone()
 return {'statuses':counts,'years':years,'register':register,'count_basis':'Distinct canonical questions. Paper cards count printed appearances.'}
@router.get('/document/{docid}')
async def document_pdf(docid:str,actor:Account):
 from fastapi.responses import FileResponse
 async with cursor()as cur:
  await access(cur,actor);await cur.execute('SELECT sha256,title,paper_id FROM review_documents WHERE id=%s',(docid,));doc=await cur.fetchone()
 if not doc:raise HTTPException(404,'Document not found')
 async with cursor()as cur:await protect_paper(cur,actor,doc['paper_id'])
 root=Path(settings.registered_document_root).resolve();path=root/(doc['sha256']+'.pdf')
 if not path.is_file():raise HTTPException(404,'Registered document needs its operator file sync')
 return FileResponse(path,media_type='application/pdf',headers={'Cache-Control':'private, no-store','Content-Disposition':'inline'})
