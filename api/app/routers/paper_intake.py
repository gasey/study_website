"""Evidence-backed paper workflow. Publication reflects a real canonical-bank sync."""
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import Field,BaseModel,ConfigDict
from psycopg.types.json import Jsonb
from ..db import cursor
from ..source_files import source_pdf_url
from ..config import settings
from pathlib import Path
from urllib.parse import unquote
import hashlib
from .exam_inventory import Account,access,event,json_record,context_fingerprint,no_store

router=APIRouter(prefix='/api/admin/bank/intake',tags=['paper intake'],dependencies=[Depends(no_store)])
STAGES=['discovered','acquired','extracted','review','ready','published']
class Artifact(BaseModel):
 model_config=ConfigDict(extra='forbid')
 schema_version:Literal[1]=1
 source_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 text_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 pages:int=Field(ge=1,le=5000)
 characters:int=Field(ge=1,le=20000000)
 tool:Literal['pdftotext','reviewed-transcription']
 note:str=Field(min_length=10,max_length=2000)
class Step(BaseModel):
 model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
 expected_version:int=Field(ge=0)
 stage:Literal['discovered','acquired','extracted','review','ready','published']
 reason:str=Field(min_length=20,max_length=4000)
 source_sha256:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
 artifact:Artifact|None=None
 retry_error:str|None=Field(default=None,max_length=2000)

@router.get('')
async def queue(actor:Account,stage:Literal['all','discovered','acquired','extracted','review','ready','published','stale','failed']='all',
 q:str=Query('',max_length=200),exam_id:str=Query('',max_length=200),offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=50)):
 async with cursor()as cur:
  await access(cur,actor)
  where=""" FROM bank_paper_expectations x JOIN bank_exam_catalog e ON e.id=x.exam_id LEFT JOIN bank_paper_intake i ON i.expectation_id=x.id
   WHERE NOT x.archived AND (%s='' OR x.title ILIKE %s OR e.title ILIKE %s) AND (%s='' OR x.exam_id=%s)
   AND (%s IN ('all','stale') OR (%s='failed' AND i.last_error IS NOT NULL) OR (%s<>'failed' AND COALESCE(i.stage,'discovered')=%s))"""
  args=(q,'%'+q+'%','%'+q+'%',exam_id,exam_id,stage,stage,stage,stage)
  await cur.execute("SELECT COALESCE(i.stage,'discovered') AS stage,count(*)::int AS count FROM bank_paper_expectations x LEFT JOIN bank_paper_intake i ON i.expectation_id=x.id WHERE NOT x.archived GROUP BY COALESCE(i.stage,'discovered')");counts=await cur.fetchall()
  # Stale is evaluated against source context, not guessed from timestamps.
  await cur.execute('''SELECT x.id,x.exam_id,x.title,e.title AS exam,x.year,x.paper_id,x.paper_url,x.reference_url,
   COALESCE(i.stage,'discovered') AS stage,COALESCE(i.version,0) AS version,i.source_sha256,i.artifact,i.last_error,
   i.review_fingerprint,i.review_note,i.reviewed_by,i.sync_id,i.updated_at'''+where+' ORDER BY x.year DESC NULLS LAST,e.title,x.title,x.id',args)
  rows=await cur.fetchall()
  for row in rows:
   row['review_stale']=bool(row['review_fingerprint'] and (not row['paper_id'] or row['review_fingerprint']!=await context_fingerprint(cur,row['paper_id'])))
  if stage=='stale':rows=[r for r in rows if r['review_stale']]
  return {'items':rows[offset:offset+limit],'total':len(rows),'counts':counts,'stages':STAGES}

@router.post('/{xid}')
async def advance(xid:str,body:Step,actor:Account):
 async with cursor()as cur:
  await access(cur,actor,True)
  await cur.execute('SELECT * FROM bank_paper_expectations WHERE id=%s AND NOT archived FOR UPDATE',(xid,));x=await cur.fetchone()
  if not x:raise HTTPException(404,'Expected paper not found')
  await cur.execute('SELECT * FROM bank_paper_intake WHERE expectation_id=%s FOR UPDATE',(xid,));old=await cur.fetchone()
  if (old['version'] if old else 0)!=body.expected_version:raise HTTPException(409,'This intake changed. Reload before saving.')
  stage=body.stage;prior=old['stage'] if old else 'discovered'
  source=body.source_sha256 or (old or {}).get('source_sha256')
  artifact=body.artifact.model_dump() if body.artifact else (old or {}).get('artifact') if source==(old or {}).get('source_sha256') else None
  if body.retry_error:
   if stage!=prior:raise HTTPException(422,'Record the failure at its current stage before retrying')
  elif STAGES.index(stage)>STAGES.index(prior)+1:raise HTTPException(409,'Complete the preceding intake stage first')
  if stage!='discovered' and not source:raise HTTPException(422,'Record the acquired PDF SHA256 first')
  if artifact and artifact['source_sha256']!=source:raise HTTPException(422,'The extraction artifact belongs to a different PDF')
  if STAGES.index(stage)>=2 and not artifact:raise HTTPException(422,'Attach the extraction artifact from the local PDF tool')
  if STAGES.index(stage)>=3 and not x['paper_id']:raise HTTPException(422,'Link the imported paper in Exams & coverage before reviewing its questions')
  fingerprint=None;reviewer=None;sync=None
  if STAGES.index(stage)>=4:
   fingerprint=await context_fingerprint(cur,x['paper_id'])
   if not x['context_reviewed'] or x['context_fingerprint']!=fingerprint:raise HTTPException(409,'Check the current paper source context in Exams & coverage before marking ready')
   await cur.execute('SELECT source_file,pdf_url FROM papers WHERE id=%s',(x['paper_id'],));paper=await cur.fetchone()
   url=source_pdf_url(paper['source_file'],paper['pdf_url'])
   root=Path(settings.paper_archive_root).resolve()
   path=(root/unquote(url[len('/papers/source/'):])).resolve() if url and url.startswith('/papers/source/') else None
   if not path or not path.is_relative_to(root) or not path.is_file():raise HTTPException(409,'Archive the registered source PDF before marking ready')
   with path.open('rb') as file:actual=hashlib.file_digest(file,'sha256').hexdigest()
   if actual!=source:raise HTTPException(409,'The archived PDF checksum differs from the extraction source')
   if stage=='published':
    if prior not in ('ready','published') or not old.get('review_fingerprint') or fingerprint!=old['review_fingerprint']:raise HTTPException(409,'Source context changed or review is missing. Return to review.')
    await cur.execute('SELECT count(*)::int AS count FROM appearances WHERE paper_id=%s AND canonical_id IS NOT NULL',(x['paper_id'],));count=(await cur.fetchone())['count']
    if not count or (x['expected_questions'] is not None and count!=x['expected_questions']):raise HTTPException(409,'Imported question count does not match the expected count')
    await cur.execute('SELECT id FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1');receipt=await cur.fetchone()
    if not receipt:raise HTTPException(409,'A completed bank sync is required')
    sync=receipt['id']
   reviewer=actor.id
  # Replacing PDF identity invalidates the old extraction and review.
  if old and source!=old['source_sha256'] and stage not in ('discovered','acquired'):raise HTTPException(409,'New PDF identity must restart at acquired')
  if stage in ('discovered','acquired'):
   artifact=body.artifact.model_dump() if body.artifact else None
  await cur.execute('''INSERT INTO bank_paper_intake(expectation_id,stage,source_sha256,artifact,review_fingerprint,review_note,reviewed_by,sync_id,last_error,updated_by)
   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(expectation_id) DO UPDATE SET
   stage=EXCLUDED.stage,source_sha256=EXCLUDED.source_sha256,artifact=EXCLUDED.artifact,review_fingerprint=EXCLUDED.review_fingerprint,
   review_note=EXCLUDED.review_note,reviewed_by=EXCLUDED.reviewed_by,sync_id=EXCLUDED.sync_id,last_error=EXCLUDED.last_error,
   updated_by=EXCLUDED.updated_by,updated_at=now(),version=bank_paper_intake.version+1 RETURNING *''',
   (xid,stage,source,Jsonb(artifact) if artifact else None,fingerprint,body.reason,reviewer,sync,body.retry_error,actor.id));row=await cur.fetchone()
  await event(cur,actor,'paper_intake_'+('failure' if body.retry_error else stage),xid,json_record(old),json_record(row),body.reason)
 return row
