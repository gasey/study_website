"""Explicit single-admin answer adjudication, separate from community quorum."""
from typing import Annotated,Literal
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Query,Header
from pydantic import BaseModel,ConfigDict,Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..services.review_identity import Actor,identity,require_role
from ..services.review_policy import Proposal,digest
from ..services import bank_review as service
from ..services.publication_verification import publication_mismatches,verification_status
from .exam_inventory import no_store
router=APIRouter(prefix='/api/admin/bank',tags=['direct admin answers'],dependencies=[Depends(no_store)])
Staff=Annotated[Actor,Depends(identity)]
class Decision(BaseModel):
 model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
 appearance_id:str=Field(min_length=1,max_length=200)
 baseline_hash:str=Field(pattern=r'^[0-9a-f]{64}$')
 mode:Literal['official','verified','needs-review','unsolved']
 answer_index:int|None=Field(default=None,ge=0,le=7)
 explanation:str=Field(default='',max_length=12000)
 reason:str=Field(min_length=20,max_length=4000)
 document_id:str|None=Field(default=None,max_length=100)
 key_page:int|None=Field(default=None,ge=1,le=10000)
 preserve_official_key:bool=False

@router.get('/publications/{publication_id}/verification')
async def verify_publication(publication_id:str,actor:Staff):
 """Recheck an immutable receipt against a consistent current database snapshot."""
 async with cursor()as cur:
  await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  await cur.execute('''SELECT p.*,c.canonical_id,c.subject_id FROM bank_publications p
   JOIN bank_contributions c ON c.id=p.contribution_id WHERE p.id=%s''',(publication_id,))
  pub=await cur.fetchone()
  if not pub:raise HTTPException(404,'Publication not found')
  await require_role(cur,actor.id,pub['subject_id'],('owner','publisher','senior','reviewer'),lock=False)
  qid=pub['canonical_id']
  if qid:await service.protect_answer(cur,actor.id,qid)
  result={'publication_id':publication_id,'question_id':qid,'publication_state':pub['state'],
          'checked_at':None,'differences':[]}
  await cur.execute('SELECT transaction_timestamp() AS checked_at')
  result['checked_at']=(await cur.fetchone())['checked_at']
  if pub['state']!='applied':
   return result|{'status':'reverted' if pub['state']=='reverted' else 'not_applied'}
  receipt=pub['receipt'] or {}
  if not qid or not receipt.get('appearance_id') or not isinstance(receipt.get('after'),dict):
   return result|{'status':'unavailable'}
  await cur.execute('''SELECT q.*,qc.subject_id AS current_subject,bs.answer_status FROM canonical_questions q
   JOIN v_bank_answer_status bs ON bs.id=q.id
   LEFT JOIN question_classifications qc ON qc.question_id=q.id AND qc.review_status='approved'
   WHERE q.id=%s''',(qid,))
  canonical=await cur.fetchone()
  if canonical:
   await require_role(cur,actor.id,canonical['current_subject'],('owner','publisher','senior','reviewer'),lock=False)
  try:
   snap=await service.snapshot(cur,qid,receipt['appearance_id'])
  except HTTPException as exc:
   if exc.status_code!=404:raise
   snap=None
  await cur.execute('SELECT is_primary FROM appearances WHERE id=%s AND canonical_id=%s',(receipt['appearance_id'],qid))
  source=await cur.fetchone()
  differences=publication_mismatches(receipt['after'],snap['record'] if snap else None,
   canonical,bool(source and source['is_primary']),pub['manifest']['payload']['patch'])
  await cur.execute('''SELECT EXISTS(SELECT 1 FROM bank_publications newer
   JOIN bank_contributions nc ON nc.id=newer.contribution_id
   WHERE nc.canonical_id=%s AND newer.state='applied' AND newer.finished_at>%s) AS newer''',
   (qid,pub['finished_at']))
  newer=(await cur.fetchone())['newer']
  return result|{'status':verification_status(differences,newer),'differences':differences,
                 'question_state':canonical['status'] if canonical else 'unavailable',
                 'answer_status':canonical['answer_status'] if canonical else None}

async def baseline(cur,actor,qid,aid=None,lock=False):
 await service.protect_answer(cur,actor.id,qid)
 await cur.execute('''SELECT q.id,q.type,q.question,q.options,q.status,q.key_disputed,q.source_defect,
  COALESCE(v.version,0)AS score_version,c.subject_id FROM canonical_questions q
  LEFT JOIN question_classifications c ON c.question_id=q.id AND c.review_status='approved'
  LEFT JOIN question_score_versions v ON v.canonical_id=q.id WHERE q.id=%s'''+(' FOR UPDATE OF q'if lock else ''),(qid,));q=await cur.fetchone()
 if not q:raise HTTPException(404,'Question not found')
 await require_role(cur,actor.id,q['subject_id'],('owner','publisher'))
 snap=await service.snapshot(cur,qid,aid)
 await cur.execute('SELECT is_primary FROM appearances WHERE id=%s',(snap['record']['id'],));primary=(await cur.fetchone())['is_primary']
 if not primary:raise HTTPException(409,'Choose the primary appearance before changing the shared answer')
 await cur.execute('SELECT id,sha256,kind,key_status FROM review_documents WHERE paper_id=%s ORDER BY id FOR SHARE',(snap['paper']['id'],))
 documents=await cur.fetchall()
 return q,snap,digest({'snapshot':snap,'state':q,'documents':documents})

@router.get('/questions/{qid}/answer-decision')
async def get_baseline(qid:str,actor:Staff,appearance_id:str|None=Query(None,max_length=200)):
 async with cursor()as cur:
  q,snap,token=await baseline(cur,actor,qid,appearance_id)
  await cur.execute("SELECT id,title,sha256,key_status FROM review_documents WHERE paper_id=%s AND kind='official-key' AND key_status IS DISTINCT FROM 'superseded' ORDER BY registered_at DESC",(snap['paper']['id'],));docs=await cur.fetchall()
  await cur.execute('''SELECT d.id,d.mode,d.reason,d.contribution_id,d.created_at,u.handle AS administrator,
   c.state AS publication_state FROM admin_answer_decisions d JOIN users u ON u.id=d.actor_id
   LEFT JOIN bank_contributions c ON c.id=d.contribution_id WHERE d.canonical_id=%s ORDER BY d.created_at DESC,d.id DESC LIMIT 10''',(qid,));history=await cur.fetchall()
 return {'viewer_id':actor.id,'baseline_hash':token,'snapshot':snap,'question_state':q['status'],'documents':docs,'history':history}

@router.post('/questions/{qid}/answer-decision')
async def decide(qid:str,body:Decision,actor:Staff,idempotency_key:Annotated[str|None,Header()]=None):
 if not idempotency_key or len(idempotency_key)>80:raise HTTPException(422,'A stable request key is required')
 request_payload=body.model_dump()
 if not body.preserve_official_key:request_payload.pop('preserve_official_key')
 request_hash=digest({'question_id':qid,**request_payload})
 async with cursor()as cur:
  await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('admin-answer:'+actor.id+':'+idempotency_key,))
  await cur.execute('SELECT * FROM admin_answer_decisions WHERE actor_id=%s AND request_key=%s',(actor.id,idempotency_key));prior=await cur.fetchone()
  if prior:
   await baseline(cur,actor,prior['canonical_id'],prior['appearance_id'])
   if prior['request_hash']!=request_hash:raise HTTPException(409,'This request key was used for another decision')
   if prior['mode']=='needs-review':return {'id':prior['id'],'contribution_id':None,'state':'held','replayed':True}
   from ..services.bank_publication import receipt
   current=await receipt(cur,prior['contribution_id'])
   return {'id':prior['id'],'contribution_id':prior['contribution_id'],'publication_id':current['id'],'state':current['state'],'replayed':True}
  await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('bank-question:'+qid,))
  q,snap,token=await baseline(cur,actor,qid,body.appearance_id,True)
  if token!=body.baseline_hash:raise HTTPException(409,'This question changed. Refresh the decision form before saving.')
  if q['type']!='mcq' or q['status']not in ('live','held'):raise HTTPException(409,'Direct answer decisions require an available MCQ')
  decision_id='adm_'+uuid4().hex
  if body.mode=='needs-review':
   await cur.execute('INSERT INTO review_holds(canonical_id,reason,placed_by,previous_status) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING',(qid,body.reason,actor.id,q['status']))
   await cur.execute("UPDATE canonical_questions SET status='held',held_reason=%s WHERE id=%s",(body.reason,qid))
   await cur.execute('''INSERT INTO admin_answer_decisions(id,canonical_id,appearance_id,actor_id,mode,baseline_hash,payload_hash,reason,request_key,request_hash)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(decision_id,qid,body.appearance_id,actor.id,body.mode,token,digest({'hold':body.reason}),body.reason,idempotency_key,request_hash))
   await service.event(cur,None,actor.id,'admin_answer_needs_review',{'decision':decision_id,'question':qid,'reason':body.reason})
   return {'id':decision_id,'contribution_id':None,'state':'held','replayed':False}
  if not q['subject_id']:raise HTTPException(409,'Add an approved subject tag before assigning the answer')
  await cur.execute("SELECT id FROM bank_contributions WHERE canonical_id=%s AND state IN ('accepted','publishing') LIMIT 1",(qid,))
  if await cur.fetchone():raise HTTPException(409,'An admin change is already waiting for publication. Open its publication progress first.')
  if q['status']=='held':raise HTTPException(409,'Release the current review hold before assigning a new answer status')
  if body.mode in ('official','verified'):
   if not q['question'].strip() or snap['record'].get('hasDiagram')and not snap['record'].get('figureImage'):raise HTTPException(409,'Restore the missing question text or required image before verifying this answer')
   if q['key_disputed']or q['source_defect']in ('duplicate-options','unresolved-source'):raise HTTPException(409,'Resolve the disputed key or source defect before verifying this answer')
   await cur.execute('SELECT valid_scoring_options(%s::jsonb)AS valid',(Jsonb(snap['record']['options']),))
   if not (await cur.fetchone())['valid']:raise HTTPException(409,'Repair the options before verifying an answer')
   if body.answer_index is None or body.answer_index>=len(snap['record']['options']):raise HTTPException(422,'Choose the correct printed option')
  elif body.answer_index is not None:raise HTTPException(422,'Unsolved must not contain an answer choice')
  if snap['record']['question']!=q['question']or snap['record']['options']!=q['options']:raise HTTPException(409,'Repair the primary source mismatch before changing the shared answer')
  source='official'if body.mode=='official'else 'derived'if body.mode=='verified'else 'none'
  separate=body.preserve_official_key
  if separate and (body.mode!='verified' or snap['record'].get('answerSource')not in('official','key') or snap['record'].get('answerIndex')is None):
   raise HTTPException(422,'A separate reviewed solution requires an existing official key and verified mode')
  evidence=[{'kind':'reasoning','note':body.reason}]
  if body.mode=='verified'and len(body.explanation.strip())<20:raise HTTPException(422,'Add a worked explanation before marking a solution verified')
  if body.mode=='official':
   if not body.document_id or not body.key_page:raise HTTPException(422,'Choose the registered official key and its PDF page')
   await cur.execute("SELECT * FROM review_documents WHERE id=%s AND paper_id=%s AND kind='official-key' AND key_status IS DISTINCT FROM 'superseded'",(body.document_id,snap['paper']['id']));doc=await cur.fetchone()
   if not doc:raise HTTPException(422,'Use a current official-key document for this exact paper')
   if not snap['record']['qnum']:raise HTTPException(422,'Record the printed question number before mapping an official key')
   evidence=[{'kind':'official-key','document_id':doc['id'],'sha256':doc['sha256'],'page':body.key_page,'printed_question':str(snap['record']['qnum']),'series':snap['paper']['series'],'answer_text':snap['record']['options'][body.answer_index],'note':body.reason}]
  # A mapped examiner key establishes an answer, not a worked explanation.
  # Keep the audit reason in rationale/evidence instead of manufacturing public
  # explanation coverage when the optional explanation was left empty.
  explanation=(body.explanation.strip() or None)if body.mode=='official'else body.explanation or body.reason
  patch={'answerIndex':body.answer_index,'answerSource':source,'answerKeyRef':body.document_id if body.mode=='official'else None,'explanation':explanation}
  if separate:
   selected=snap['record']['options'][body.answer_index]
   original=snap['record']['options'][snap['record']['answerIndex']]
   evidence=[{'kind':'reasoning','answer_text':selected,'note':body.reason}]
   patch={'explanation':f'Reviewed solution (unofficial): {selected}. {body.explanation} Official key retained: {original}. '+('The answers differ; this question is held from scoring.'if selected!=original else 'The independently reviewed solution agrees with the examiner key.')}
  p=Proposal(kind='explanation'if separate else 'answer',canonical_id=qid,appearance_id=body.appearance_id,subject_id=q['subject_id'],title='Admin answer decision: '+body.mode,
    patch=patch,rationale=body.reason,evidence=evidence)
  c=await service.create(cur,actor.id,p,'admin:'+idempotency_key,admin_attestation=True)
  r=await service.revision(cur,c)
  await cur.execute('''INSERT INTO admin_answer_decisions(id,canonical_id,appearance_id,actor_id,mode,contribution_id,revision,baseline_hash,payload_hash,reason,request_key,request_hash)
   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(decision_id,qid,body.appearance_id,actor.id,body.mode,c['id'],c['revision'],r['baseline_hash'],digest(r['payload']),body.reason,idempotency_key,request_hash))
  c=await service.update_state(cur,c,actor.id,'accepted',{'admin_decision':decision_id,'mode':body.mode})
  decision={'id':decision_id,'actor_id':actor.id,'mode':body.mode,'reason':body.reason}
  if separate:
   decision['solution_answer_text']=selected
   decision['preserve_official_key']=True
   if selected!=original:
    hold_reason='Reviewed solution differs from the preserved official key. '+body.reason
    await cur.execute('INSERT INTO review_holds(canonical_id,reason,placed_by,previous_status) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING',(qid,hold_reason,actor.id,q['status']))
    await cur.execute("UPDATE canonical_questions SET status='held',held_reason=%s WHERE id=%s",(hold_reason,qid))
    await service.event(cur,c['id'],actor.id,'admin_solution_key_conflict',{'decision':decision_id,'question':qid,'official_answer':original,'reviewed_answer':selected})
  from ..services.bank_publication import queue
  publication=await queue(cur,c,actor.id,{'admin_decision':decision})
  pub=publication['id']
 return {'id':decision_id,'contribution_id':c['id'],'publication_id':pub,'state':'queued','replayed':False}
