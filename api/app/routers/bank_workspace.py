from ..config import settings
"""Account-bound contribution, reviewer and bank administration API."""
from typing import Annotated, Literal
import copy
import json
from functools import lru_cache
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from psycopg.types.json import Jsonb

from ..db import cursor
from ..deps import current_user
from ..services.review_identity import Actor, identity, grants, require_role
from ..services.review_policy import Proposal, digest, validate_target, quorum
from ..services import bank_review as service
from ..services.editorial_access import assigned, source_version, require_version

router=APIRouter(tags=['bank workspace'])
Account=Annotated[Actor,Depends(identity)]

@lru_cache(maxsize=1)
def luna_priority_solutions():
    path=Path(__file__).resolve().parents[1]/'data/luna_priority_solutions.json'
    return json.loads(path.read_text())

class Strict(BaseModel): model_config=ConfigDict(extra='forbid')
class Transition(Strict):
    expected_version: int = Field(ge=1)
    reason: str = Field(default='',max_length=4000)
class Revise(Transition): proposal: Proposal
class Decision(Transition):
    publish: bool = False
    decision: Literal['approve','reject','request_changes']
    reason: str = Field(min_length=20,max_length=4000)
class Grant(Strict):
    email: str = Field(min_length=3,max_length=254)
    role: Literal['owner','publisher','senior','reviewer']
    subject_id: str | None = Field(default=None,max_length=100)
    reason: str = Field(min_length=10,max_length=4000)

class TagReport(Strict):
    appearance_id:str=Field(min_length=1,max_length=200)
    note:str=Field(min_length=20,max_length=4000)

class QuestionReport(Strict):
    kind:Literal['wrong_key','typo_ocr','outdated','ambiguous']
    note:str=Field(min_length=20,max_length=4000)
    paper_id:str|None=Field(default=None,min_length=1,max_length=500)

@router.post('/api/review/questions/{qid}/report')
async def report_question(qid:str,body:QuestionReport,actor:Account):
    """Private learner feedback; never changes an answer or its scoring status."""
    note=body.note.strip()
    if len(note)<20:raise HTTPException(422,'Describe the issue in at least 20 characters')
    async with cursor() as cur:
        await cur.execute('''SELECT 1 FROM canonical_questions c
          WHERE c.id=%s AND c.status IN ('live','held')
          AND (%s::text IS NULL OR EXISTS (SELECT 1 FROM appearances a
            WHERE a.canonical_id=c.id AND a.paper_id=%s))''',(qid,body.paper_id,body.paper_id))
        if not await cur.fetchone():raise HTTPException(404,'Published question source not found')
        await cur.execute('''INSERT INTO content_reports(canonical_id,kind,reporter_id,note,evidence_paper)
          VALUES(%s,%s,%s,%s,%s) ON CONFLICT(canonical_id,kind,reporter_id) DO NOTHING RETURNING id,status''',
          (qid,body.kind,actor.id,note,body.paper_id))
        report=await cur.fetchone()
        if not report:
            await cur.execute('SELECT id,status FROM content_reports WHERE canonical_id=%s AND kind=%s AND reporter_id=%s',(qid,body.kind,actor.id))
            report=await cur.fetchone()
        return report

@router.post('/api/review/questions/{qid}/tag-report')
async def report_tags(qid:str,body:TagReport,actor:Account):
    async with cursor() as cur:
        await cur.execute('''SELECT 1 FROM canonical_questions c JOIN appearances a ON a.canonical_id=c.id
          WHERE c.id=%s AND a.id=%s AND c.status IN ('live','held')''',(qid,body.appearance_id))
        if not await cur.fetchone():raise HTTPException(404,'Published question not found')
        if len(body.note.strip())<20:raise HTTPException(422,'Describe the tag issue in at least 20 characters')
        await cur.execute('''INSERT INTO content_reports(canonical_id,kind,reporter_id,note)
          VALUES(%s,'subject',%s,%s) ON CONFLICT(canonical_id,kind,reporter_id) DO NOTHING RETURNING id,status''',
          (qid,actor.id,body.note.strip()))
        report=await cur.fetchone()
        if not report:
            await cur.execute("SELECT id,status FROM content_reports WHERE canonical_id=%s AND kind='subject' AND reporter_id=%s",(qid,actor.id))
            report=await cur.fetchone()
        return report
class Hold(Strict):
    reason: str=Field(min_length=10,max_length=4000)
class AppealDecision(Strict):
    decision: Literal['granted','denied']
    reason: str=Field(min_length=20,max_length=4000)

@router.get('/api/review/session')
async def session(actor:Account):
    from ..services.mfa import staff_required
    async with cursor() as cur:
        await cur.execute('SELECT role,subject_id FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        permissions=await cur.fetchall()
    return {'user_id':actor.id,'csrf':actor.csrf,'grants':permissions,'mfa_required':bool(permissions) and staff_required(actor.id) and not actor.mfa_verified}

@router.get('/api/review/taxonomy')
async def taxonomy(actor:Account):
    async with cursor() as cur:
        await cur.execute('SELECT * FROM review_taxonomy WHERE active ORDER BY id')
        return await cur.fetchall()

@router.get('/api/review/questions/{qid}')
async def question(qid:str,actor:Account,appearance_id:str|None=None):
    async with cursor() as cur:
        await service.protect_answer(cur,actor.id,qid)
        # Authors may see source and baseline to propose a repair after answering.
        version_token=await source_version(cur,qid,appearance_id,True)
        snap=await service.snapshot(cur,qid,appearance_id)
        await cur.execute('SELECT role FROM review_grants WHERE user_id=%s AND revoked_at IS NULL AND (subject_id IS NULL OR subject_id=%s)',(actor.id,snap['record']['classification'].get('subject_id')))
        privileged=bool(await cur.fetchone()) or await assigned(cur,actor.id,snap['record']['paperId'])
        if not privileged:
            await cur.execute('SELECT 1 FROM attempts WHERE user_id=%s AND canonical_id=%s LIMIT 1',(actor.id,qid))
            if not await cur.fetchone():
                snap['record']['answerIndex']=None
                snap['record']['explanation']=None
        await cur.execute('SELECT id,title,sha256,kind,key_status FROM review_documents WHERE paper_id=%s ORDER BY kind,title FOR SHARE',(snap['paper']['id'],))
        documents=await cur.fetchall()
        snap['edit_hash']=digest(snap)
        await cur.execute("SELECT subject_label,topic_label,subtopic_label FROM question_classifications WHERE question_id=%s AND review_status='approved'",(qid,))
        labels=await cur.fetchone()
        snap['tag_label']=' / '.join(v for v in labels.values() if v) if labels else 'No approved subject'
        snap['canonical_id']=qid
        snap['can_publish']=bool(set(await grants(cur,actor.id,snap['record']['classification'].get('subject_id')))&{'owner','publisher'})
        snap['solo_owner']='owner' in await grants(cur,actor.id)
        if snap['can_publish']:
            await cur.execute("SELECT id,kind,note FROM content_reports WHERE canonical_id=%s AND status IN ('open','confirmed') ORDER BY id",(qid,))
            snap['reports']=await cur.fetchall()
        snap['documents']=documents
        snap['baseline_token']=version_token
        if privileged:
            from ..services.editorial_access import inspection_fingerprints
            snap['inspection_version']=digest((await inspection_fingerprints(cur,[snap['paper']['id']],[snap['record']['id']]))[snap['record']['id']])
        return snap

@router.get('/api/contributions/summary')
async def summary(actor:Account):
    async with cursor() as cur:
        await cur.execute('SELECT state,count(*)::int AS count FROM bank_contributions WHERE author_id=%s GROUP BY state',(actor.id,))
        states=await cur.fetchall()
        await cur.execute('SELECT COALESCE(sum(amount),0)::int AS credit FROM contribution_credit WHERE user_id=%s',(actor.id,))
        credit=(await cur.fetchone())['credit']
        await cur.execute('SELECT count(*)::int AS n FROM review_notifications WHERE user_id=%s AND read_at IS NULL AND NOT silent',(actor.id,))
        unread=(await cur.fetchone())['n']
        await cur.execute('SELECT contribution_public FROM users WHERE id=%s',(actor.id,))
        public=(await cur.fetchone())['contribution_public']
    return {'states':states,'credit':credit,'unread':unread,'public':public}

@router.get('/api/contributions')
async def mine(actor:Account,before:str|None=None,limit:int=Query(20,ge=1,le=100)):
    async with cursor() as cur:
        await cur.execute('''SELECT id,title,kind,state,revision,lock_version,subject_id,created_at,updated_at
            FROM bank_contributions WHERE author_id=%s AND (%s::text IS NULL OR (created_at,id)<
            (SELECT created_at,id FROM bank_contributions WHERE id=%s AND author_id=%s))
            ORDER BY created_at DESC,id DESC LIMIT %s''',(actor.id,before,before,actor.id,limit+1))
        rows=await cur.fetchall()
    return {'items':rows[:limit],'next_cursor':rows[limit-1]['id'] if len(rows)>limit else None}

@router.post('/api/contributions',status_code=201)
async def create(proposal:Proposal,actor:Account,idempotency_key:Annotated[str|None,Header()]=None,x_review_source_version:Annotated[str|None,Header()]=None):
    async with cursor() as cur: return await service.create(cur,actor.id,proposal,idempotency_key,source_token=x_review_source_version,require_source_version=True)

@router.get('/api/review/queue')
async def queue(actor:Account,state:str|None=None,subject_id:str|None=None,before:str|None=None,limit:int=Query(20,ge=1,le=100)):
    async with cursor() as cur:
        await cur.execute('''SELECT c.id,c.title,c.kind,c.state,c.subject_id,c.revision,c.lock_version,c.created_at,c.updated_at,c.lease_user,c.lease_until,
            u.handle AS author FROM bank_contributions c JOIN users u ON u.id=c.author_id
            WHERE c.state NOT IN ('draft','withdrawn')
            AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
                AND g.role IN ('owner','reviewer','senior','publisher') AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))
            AND (%s::text IS NULL OR c.state=%s) AND (%s::text IS NULL OR c.subject_id=%s)
            AND (%s::text IS NULL OR (c.created_at,c.id)<(SELECT created_at,id FROM bank_contributions WHERE id=%s))
            ORDER BY c.created_at DESC,c.id DESC LIMIT %s''',(actor.id,state,state,subject_id,subject_id,before,before,limit+1))
        rows=await cur.fetchall()
    return {'items':rows[:limit],'next_cursor':rows[limit-1]['id'] if len(rows)>limit else None}

@router.get('/api/contributions/{cid}')
async def detail(cid:str,actor:Account):
    async with cursor() as cur:
        await cur.execute('SELECT c.*,u.handle AS author FROM bank_contributions c JOIN users u ON u.id=c.author_id WHERE c.id=%s',(cid,))
        c=await cur.fetchone()
        if not c: raise HTTPException(404,'Contribution not found')
        roles=await grants(cur,actor.id,c['subject_id'])
        if c['author_id']!=actor.id and not roles: raise HTTPException(404,'Contribution not found')
        await service.protect_answer(cur,actor.id,c['canonical_id'])
        r=await service.revision(cur,c)
        if not roles and c['canonical_id']:
            await cur.execute('SELECT 1 FROM attempts WHERE user_id=%s AND canonical_id=%s LIMIT 1',(actor.id,c['canonical_id']))
            if not await cur.fetchone():
                r=copy.deepcopy(r)
                r['baseline']['record']['answerIndex']=None
                r['baseline']['record']['explanation']=None
                r['baseline_hash']=''
        await cur.execute('SELECT id,reviewer_id,decision,rationale,revision,created_at FROM contribution_decisions WHERE contribution_id=%s ORDER BY id',(cid,))
        decisions=await cur.fetchall()
        await cur.execute('SELECT id,actor_id,action,detail,created_at FROM contribution_events WHERE contribution_id=%s ORDER BY id',(cid,))
        events=await cur.fetchall()
        await cur.execute('SELECT * FROM contribution_appeals WHERE contribution_id=%s ORDER BY id',(cid,))
        appeals=await cur.fetchall()
        await cur.execute('SELECT id,state,error,finished_at FROM bank_publications WHERE contribution_id=%s ORDER BY created_at',(cid,))
        publications=await cur.fetchall()
    async with cursor()as cur:
        await cur.execute('SELECT mode,reason,created_at FROM admin_answer_decisions WHERE contribution_id=%s AND revision=%s',(cid,c['revision']))
        direct=await cur.fetchone()
        if not direct:
            await cur.execute("SELECT 'source repair' AS mode,detail->>'reason' AS reason,created_at FROM contribution_events WHERE contribution_id=%s AND actor_id='operator:owner-source-maintenance' AND action='operator_source_adjudication' AND detail->>'revision'=%s ORDER BY id DESC LIMIT 1",(cid,str(c['revision'])))
            direct=await cur.fetchone()
    if not direct:
        async with cursor() as cur:
            await cur.execute('SELECT kind AS mode,reason,created_at FROM admin_bank_decisions WHERE contribution_id=%s AND revision=%s',(cid,c['revision']))
            direct=await cur.fetchone()
    if direct and direct.get('mode')=='taxonomy':
        async with cursor() as cur:
            await cur.execute('SELECT id FROM bank_retag_batches WHERE %s=ANY(contribution_ids)',(cid,))
            batch=await cur.fetchone()
            if batch:direct['batch_id']=batch['id']
    return {**c,'admin_decision':direct,'viewer_id':actor.id,'required_reviews':quorum(c['kind'],r['baseline'].get('record',{}),r['payload']['patch'])[0],'current':r,'decisions':decisions,'events':events,'appeals':appeals,'publications':publications,'permissions':roles,'is_author':c['author_id']==actor.id}

@router.post('/api/contributions/{cid}/revisions')
async def revise(cid:str,body:Revise,actor:Account,x_review_source_version:Annotated[str|None,Header()]=None):
    async with cursor() as cur:
        c=await service.load(cur,cid,actor.id,body.expected_version)
        if c['state'] not in {'draft','changes_requested'}: service.conflict('This contribution is not editable in its current state')
        p=body.proposal
        if p.canonical_id:await require_version(cur,p.canonical_id,p.appearance_id,x_review_source_version)
        service.require_current_patch(p)
        if p.kind!=c['kind'] or p.canonical_id!=c['canonical_id'] or (p.appearance_id is not None and p.appearance_id!=c['appearance_id']): raise HTTPException(422,'Kind and target cannot change in a revision')
        baseline=await service.snapshot(cur,p.canonical_id,p.appearance_id) if p.canonical_id else {}
        await service.validate_evidence(cur,p,baseline)
        await cur.execute('INSERT INTO contribution_revisions(contribution_id,revision,payload,baseline,baseline_hash,actor_id) VALUES (%s,%s,%s,%s,%s,%s)',(cid,c['revision']+1,Jsonb(p.model_dump(mode='json')),Jsonb(baseline),digest(baseline),actor.id))
        await cur.execute('UPDATE bank_contributions SET revision=revision+1,title=%s,lease_user=NULL,lease_until=NULL WHERE id=%s',(p.title,cid))
        await service.module_intake.link(cur,actor.id,p,cid)
        return await service.update_state(cur,c,actor.id,'draft')

@router.post('/api/contributions/{cid}/submit')
async def submit(cid:str,body:Transition,actor:Account):
    async with cursor() as cur:
        c=await service.load(cur,cid,actor.id,body.expected_version)
        if c['state'] not in {'draft','changes_requested'}: service.conflict('Only a draft can be submitted')
        r=await service.revision(cur,c)
        await service.validate_evidence(cur,Proposal.model_validate(r['payload']),r['baseline'])
        return await service.update_state(cur,c,actor.id,'submitted')

@router.post('/api/contributions/{cid}/withdraw')
async def withdraw(cid:str,body:Transition,actor:Account):
    async with cursor() as cur:
        c=await service.load(cur,cid,actor.id,body.expected_version)
        if c['state'] not in {'draft','submitted','in_review','changes_requested'}: service.conflict('This contribution can no longer be withdrawn')
        return await service.update_state(cur,c,actor.id,'withdrawn',{'reason':body.reason})

@router.post('/api/review/{cid}/claim')
async def claim(cid:str,body:Transition,actor:Account):
    async with cursor() as cur:
        c=await service.load(cur,cid,actor.id,body.expected_version,True)
        await require_role(cur,actor.id,c['subject_id'])
        if c['author_id']==actor.id: raise HTTPException(403,'You cannot review your own contribution')
        if c['state'] not in {'submitted','in_review'}: service.conflict('This item is not awaiting review')
        await cur.execute('UPDATE bank_contributions SET lease_user=%s,lease_until=now()+interval \'15 minutes\' WHERE id=%s',(actor.id,cid))
        return await service.update_state(cur,c,actor.id,'in_review')

@router.post('/api/review/{cid}/decisions')
async def decide(cid:str,body:Decision,actor:Account):
    async with cursor() as cur:
        c=await service.load(cur,cid,actor.id,body.expected_version,True)
        await require_role(cur,actor.id,c['subject_id'])
        if c['author_id']==actor.id: raise HTTPException(403,'You cannot decide your own contribution')
        if c['state'] not in {'submitted','in_review'}: service.conflict('This item is not awaiting review')
        r=await service.revision(cur,c)
        await service.validate_evidence(cur,Proposal.model_validate(r['payload']),r['baseline'])
        target_subject=r['payload']['patch'].get('classification',{}).get('subject_id',c['subject_id'])
        if target_subject!=c['subject_id']: await require_role(cur,actor.id,target_subject)
        if set(r['payload']['patch'])&{'classification','relatedClassifications'}:
            for sid in {x['subject_id'] for x in [*r['payload']['patch'].get('relatedClassifications',[]),*r['baseline'].get('record',{}).get('relatedClassifications',[])]}: await require_role(cur,actor.id,sid)
        await cur.execute('SELECT 1 FROM contribution_decisions WHERE contribution_id=%s AND revision=%s AND reviewer_id=%s',(cid,c['revision'],actor.id))
        if await cur.fetchone(): service.conflict('You already decided this revision')
        await cur.execute('INSERT INTO contribution_decisions(contribution_id,revision,reviewer_id,decision,rationale) VALUES (%s,%s,%s,%s,%s)',(cid,c['revision'],actor.id,body.decision,body.reason))
        state={'reject':'rejected','request_changes':'changes_requested'}.get(body.decision,'in_review')
        if body.decision=='approve' and await service.eligible_reviews(cur,c,r): state='accepted'
        updated=await service.update_state(cur,c,actor.id,state,{'decision':body.decision,'reason':body.reason})
        if body.publish:
            await require_role(cur,actor.id,c['subject_id'],('owner','publisher'))
            if body.decision!='approve':raise HTTPException(422,'Only approvals can be published')
            if state=='accepted':
                from ..services.bank_publication import queue
                publication=await queue(cur,updated,actor.id)
                return {**updated,'state':'publishing','publication_id':publication['id']}
        return updated

@router.post('/api/contributions/{cid}/appeals',status_code=201)
async def appeal(cid:str,body:Transition,actor:Account):
    if len(body.reason.strip())<20: raise HTTPException(422,'Explain the appeal with new evidence')
    async with cursor() as cur:
        c=await service.load(cur,cid,actor.id,body.expected_version)
        if c['state']!='rejected': service.conflict('Only a rejected revision can be appealed')
        await cur.execute('SELECT 1 FROM contribution_appeals WHERE contribution_id=%s AND revision=%s',(cid,c['revision']))
        if await cur.fetchone(): service.conflict('This revision already has an appeal')
        await cur.execute('INSERT INTO contribution_appeals(contribution_id,revision,reason) VALUES (%s,%s,%s) RETURNING *',(cid,c['revision'],body.reason))
        result=await cur.fetchone(); await service.event(cur,cid,actor.id,'appeal',{'id':result['id']})
        return result

@router.post('/api/review/appeals/{appeal_id}/decision')
async def resolve_appeal(appeal_id:int,body:AppealDecision,actor:Account):
    async with cursor() as cur:
        await cur.execute('SELECT contribution_id FROM contribution_appeals WHERE id=%s',(appeal_id,))
        pointer=await cur.fetchone()
        if not pointer: raise HTTPException(404,'Appeal not found')
        c=await service.load(cur,pointer['contribution_id'],actor.id,review=True)
        await require_role(cur,actor.id,c['subject_id'],('owner','senior'))
        if c['author_id']==actor.id: raise HTTPException(403,'An independent adjudicator is required')
        await cur.execute('SELECT 1 FROM contribution_decisions WHERE contribution_id=%s AND reviewer_id=%s',(c['id'],actor.id))
        if await cur.fetchone(): raise HTTPException(403,'A prior decision maker cannot hear this appeal')
        await cur.execute('SELECT * FROM contribution_appeals WHERE id=%s FOR UPDATE',(appeal_id,))
        a=await cur.fetchone()
        if a['state']!='open' or a['revision']!=c['revision']: service.conflict('Appeal is already decided or stale')
        await cur.execute('UPDATE contribution_appeals SET state=%s,decided_by=%s,decision_reason=%s WHERE id=%s',(body.decision,actor.id,body.reason,appeal_id))
        if body.decision=='granted': return await service.update_state(cur,c,actor.id,'changes_requested',{'appeal':appeal_id,'reason':body.reason})
        await service.event(cur,c['id'],actor.id,'appeal_denied',{'reason':body.reason})
        return {'state':'denied'}

@router.get('/api/admin/bank/summary')
async def admin_summary(actor:Account):
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone(): raise HTTPException(403,'Admin permission required')
        # Bank health is aggregate only; restricted question reads enforce scope separately.
        await cur.execute("""SELECT count(*)::int AS questions,count(*) FILTER(WHERE type='mcq' AND answer_text IS NULL)::int AS missing_answers,
            count(*) FILTER(WHERE answer_source IN ('official','key'))::int AS keyed,
            count(*) FILTER(WHERE source_defect IS NOT NULL)::int AS defects,
            count(*) FILTER(WHERE status='held')::int AS held FROM canonical_questions""")
        health=await cur.fetchone()
        await cur.execute('''SELECT state,count(*)::int AS count FROM bank_contributions c WHERE EXISTS(
            SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL AND (g.subject_id IS NULL OR g.subject_id=c.subject_id)) GROUP BY state''',(actor.id,))
        health['queue']=await cur.fetchall()
        await cur.execute('SELECT bank_checksum,finished_at FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1')
        health['sync']=await cur.fetchone()
        await cur.execute("SELECT worker_id,seen_at,status,seen_at>now()-interval '5 minutes' AS available FROM review_worker_health WHERE worker_id IN ('oracle-bank-publisher','local-bank-publisher') ORDER BY seen_at DESC LIMIT 1")
        health['worker']=await cur.fetchone()
        await cur.execute("SELECT worker_id,seen_at,status,seen_at>now()-interval '2 minutes' AS available FROM review_worker_health WHERE worker_id='score-reassessment'")
        health['assessment_worker']=await cur.fetchone()
        await cur.execute("SELECT (SELECT count(*) FROM assessment_jobs WHERE finished_at IS NULL) + (SELECT count(*) FROM new_score_jobs WHERE finished_at IS NULL)+(SELECT count(*) FROM question_change_events WHERE finished_at IS NULL) AS pending,(SELECT count(*) FROM assessment_jobs WHERE failures>=5)+(SELECT count(*) FROM new_score_jobs WHERE failures>=5)+(SELECT count(*) FROM question_change_events WHERE failures>=5) AS failed")
        health['assessments']=await cur.fetchone()
        await cur.execute("SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL AND subject_id IS NULL AND role IN ('owner','publisher','senior','reviewer')",(actor.id,))
        health['overview']=None
        if await cur.fetchone():
            from ..services.bank_overview import overview
            health['overview']=await overview(cur)
    return health

@router.get('/api/admin/bank/grants')
async def grant_list(actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT g.*,u.email,u.handle FROM review_grants g JOIN users u ON u.id=g.user_id ORDER BY g.created_at DESC')
        return await cur.fetchall()

@router.post('/api/admin/bank/grants')
async def grant(body:Grant,actor:Account):
    if not actor.recent: raise HTTPException(403,'Sign in again before changing staff permissions')
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT id FROM users WHERE lower(email)=lower(%s)',(body.email.strip(),))
        user=await cur.fetchone()
        if not user: raise HTTPException(404,'That account must sign up first')
        if body.subject_id:
            await cur.execute("SELECT 1 FROM review_taxonomy WHERE id=%s AND level='subject' AND active",(body.subject_id,))
            if not await cur.fetchone(): raise HTTPException(422,'Unknown subject scope')
        await cur.execute('''INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id''',(user['id'],body.role,body.subject_id,actor.id,body.reason))
        result=await cur.fetchone(); await service.event(cur,None,actor.id,'grant',{'user':user['id'],'role':body.role,'subject':body.subject_id,'reason':body.reason})
        return {'id':result['id'] if result else None}

@router.post('/api/admin/bank/grants/{grant_id}/revoke')
async def revoke(grant_id:int,body:Hold,actor:Account):
    if not actor.recent: raise HTTPException(403,'Sign in again before changing staff permissions')
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT * FROM review_grants WHERE id=%s FOR UPDATE',(grant_id,))
        row=await cur.fetchone()
        if not row: raise HTTPException(404,'Grant not found')
        if row['user_id']==actor.id and row['role']=='owner': raise HTTPException(409,'Have another owner revoke your owner grant')
        await cur.execute('UPDATE review_grants SET revoked_at=now() WHERE id=%s AND revoked_at IS NULL',(grant_id,))
        await service.event(cur,None,actor.id,'revoke_grant',{'grant':grant_id,'reason':body.reason})
    return {'revoked':True}

@router.post('/api/admin/bank/questions/{qid}/hold')
async def hold(qid:str,body:Hold,actor:Account):
    async with cursor() as cur:
        snap=await service.snapshot(cur,qid)
        await require_role(cur,actor.id,snap['record']['classification']['subject_id'],('owner','publisher','senior','reviewer'))
        await cur.execute('SELECT status FROM canonical_questions WHERE id=%s FOR UPDATE',(qid,))
        state=(await cur.fetchone())['status']
        if state not in {'live','held'}: service.conflict('This question cannot be held in its current state')
        await cur.execute('INSERT INTO review_holds(canonical_id,reason,placed_by,previous_status) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING',(qid,body.reason,actor.id,state))
        await cur.execute("UPDATE canonical_questions SET status='held',held_reason=%s WHERE id=%s",(body.reason,qid))
        await service.event(cur,None,actor.id,'hold',{'question':qid,'reason':body.reason})
    return {'held':True}

@router.post('/api/admin/bank/questions/{qid}/release')
async def release(qid:str,body:Hold,actor:Account):
    async with cursor() as cur:
        snap=await service.snapshot(cur,qid)
        await require_role(cur,actor.id,snap['record']['classification']['subject_id'],('owner','publisher','senior','reviewer'))
        await cur.execute('SELECT status FROM canonical_questions WHERE id=%s FOR UPDATE',(qid,))
        state=(await cur.fetchone())['status']
        await cur.execute('UPDATE review_holds SET released_at=now(),released_by=%s WHERE canonical_id=%s AND released_at IS NULL RETURNING previous_status',(actor.id,qid))
        previous=await cur.fetchone()
        if not previous: service.conflict('No active review hold')
        if state=='held': await cur.execute("UPDATE canonical_questions SET status='live',held_reason=NULL WHERE id=%s",(qid,))
        await service.event(cur,None,actor.id,'release_hold',{'question':qid,'reason':body.reason})
    return {'held':False}

@router.get('/api/review/notifications/unread')
async def unread_notifications(actor:Account,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await cur.execute('SELECT count(*)::int AS unread FROM review_notifications WHERE user_id=%s AND read_at IS NULL AND NOT silent',(actor.id,))
        return await cur.fetchone()

@router.get('/api/review/notifications')
async def notifications(actor:Account,response:Response,before:int|None=Query(None,ge=1),limit:int=Query(20,ge=1,le=100)):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await cur.execute('SELECT * FROM review_notifications WHERE user_id=%s AND (%s::bigint IS NULL OR id<%s) ORDER BY id DESC LIMIT %s',(actor.id,before,before,limit))
        return await cur.fetchall()

@router.post('/api/review/notifications/{nid}/read')
async def read_notice(nid:int,actor:Account):
    async with cursor() as cur:
        await cur.execute('UPDATE review_notifications SET read_at=COALESCE(read_at,now()) WHERE id=%s AND user_id=%s',(nid,actor.id))
    return {'read':True}

@router.get('/api/community/contributors')
async def leaderboard(period:Literal['week','month','all']='month',subject_id:str|None=None,limit:int=Query(30,ge=1,le=100)):
    async with cursor() as cur:
        await cur.execute('''WITH net AS (
            SELECT user_id,contribution_id,sum(amount)::int AS amount FROM contribution_credit l
            WHERE (%s='all' OR l.created_at >= (date_trunc(%s,now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata'))
            AND (%s::text IS NULL OR l.subject_id=%s) GROUP BY user_id,contribution_id
        ) SELECT u.id,u.handle,u.avatar,sum(net.amount)::int AS credit,
            count(*) FILTER(WHERE net.amount>0)::int AS contributions,
            dense_rank() OVER(ORDER BY sum(net.amount) DESC,count(DISTINCT COALESCE(c.canonical_id,c.id)) FILTER(WHERE net.amount>0) DESC)::int AS rank
            FROM net JOIN users u ON u.id=net.user_id JOIN bank_contributions c ON c.id=net.contribution_id
            WHERE u.contribution_public GROUP BY u.id,u.handle HAVING sum(net.amount)>0
            ORDER BY credit DESC,contributions DESC,u.handle LIMIT %s''',(period,'week' if period=='week' else 'month',subject_id,subject_id,limit))
        return await cur.fetchall()

@router.get('/api/community/contributions')
async def published(user:Annotated[str,Depends(current_user)],before:str|None=None,limit:int=Query(20,ge=1,le=100)):
    async with cursor() as cur:
        await cur.execute('''SELECT c.id,c.title,c.kind,c.subject_id,c.canonical_id,c.updated_at,CASE WHEN u.contribution_public THEN u.handle ELSE 'Anonymous contributor' END AS author,
            (SELECT count(*)::int FROM contribution_votes v WHERE v.contribution_id=c.id) AS helpful,
            EXISTS(SELECT 1 FROM contribution_votes v WHERE v.contribution_id=c.id AND v.user_id=%s) AS voted
            FROM bank_contributions c JOIN users u ON u.id=c.author_id WHERE c.state='published'
            AND NOT EXISTS(SELECT 1 FROM mock_sessions m WHERE m.user_id=%s AND m.submitted_at IS NULL AND c.canonical_id=ANY(m.question_ids))
            AND (%s::text IS NULL OR (c.updated_at,c.id)<(SELECT updated_at,id FROM bank_contributions WHERE id=%s))
            ORDER BY c.updated_at DESC,c.id DESC LIMIT %s''',(user,user,before,before,limit+1))
        rows=await cur.fetchall()
    return {'items':rows[:limit],'next_cursor':rows[limit-1]['id'] if len(rows)>limit else None}

@router.post('/api/contributions/{cid}/vote')
async def vote(cid:str,actor:Account):
    async with cursor() as cur:
        await cur.execute("SELECT author_id,canonical_id FROM bank_contributions WHERE id=%s AND state='published'",(cid,))
        row=await cur.fetchone()
        if not row: raise HTTPException(404,'Published contribution not found')
        if row['author_id']==actor.id: raise HTTPException(403,'You cannot vote on your own work')
        await service.protect_answer(cur,actor.id,row['canonical_id'])
        await cur.execute('INSERT INTO contribution_votes(user_id,contribution_id) VALUES (%s,%s) ON CONFLICT DO NOTHING',(actor.id,cid))
    return {'voted':True}

@router.post('/api/contributions/{cid}/unvote')
async def unvote(cid:str,actor:Account):
    async with cursor() as cur: await cur.execute('DELETE FROM contribution_votes WHERE user_id=%s AND contribution_id=%s',(actor.id,cid))
    return {'voted':False}

@router.post('/api/admin/bank/contributions/{cid}/publish')
async def export_publication(cid:str,body:Transition,actor:Account):
    async with cursor() as cur:
        from ..services.bank_publication import queue
        c=await service.load(cur,cid,actor.id,body.expected_version,review=True)
        return await queue(cur,c,actor.id)

@router.get('/api/admin/bank/publications')
async def publications(actor:Account,limit:int=Query(30,ge=1,le=100)):
    async with cursor() as cur:
        await cur.execute('''SELECT p.id,p.contribution_id,p.state,p.error,p.created_at,p.finished_at,c.title
            FROM bank_publications p JOIN bank_contributions c ON c.id=p.contribution_id
            WHERE EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
             AND (g.subject_id IS NULL OR g.subject_id=c.subject_id)) ORDER BY p.created_at DESC LIMIT %s''',(actor.id,limit))
        return await cur.fetchall()

@router.get('/api/admin/bank/audit')
async def audit(actor:Account,before:int|None=None,limit:int=Query(50,ge=1,le=100)):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT * FROM contribution_events WHERE (%s::bigint IS NULL OR id<%s) ORDER BY id DESC LIMIT %s',(before,before,limit))
        return await cur.fetchall()

@router.get('/api/admin/bank/documents')
async def documents(actor:Account,paper_id:str|None=None):
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone(): raise HTTPException(403,'Review permission required')
        await cur.execute('SELECT id,paper_id,title,sha256,kind,key_status,registered_at FROM review_documents WHERE (%s::text IS NULL OR paper_id=%s) ORDER BY registered_at DESC LIMIT 100',(paper_id,paper_id))
        return await cur.fetchall()

@router.post('/api/review/{cid}/rebase')
async def request_rebase(cid:str,body:Transition,actor:Account):
    async with cursor() as cur:
        c=await service.load(cur,cid,actor.id,body.expected_version,review=True)
        if c['state'] not in {'accepted','publication_failed'}: service.conflict('This item cannot be reopened now')
        if len(body.reason.strip())<20: raise HTTPException(422,'Explain why new review is needed')
        return await service.update_state(cur,c,actor.id,'changes_requested',{'reason':body.reason})

@router.get('/api/admin/bank/publication-pulse')
async def publication_pulse(actor:Account):
    """Cheap scoped change detector; no question/answer content or user details."""
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone():raise HTTPException(403,'Admin permission required')
        await cur.execute("""SELECT COALESCE(sum(c.lock_version),0)::text||':'||
          (SELECT COALESCE(max(id),0)::text FROM sync_log WHERE finished_at IS NOT NULL) AS revision,
          count(*) FILTER(WHERE c.state IN ('accepted','publishing'))::int AS pending
          FROM bank_contributions c WHERE EXISTS(SELECT 1 FROM review_grants g
          WHERE g.user_id=%s AND g.revoked_at IS NULL AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))""",(actor.id,))
        return await cur.fetchone()

@router.get('/api/admin/bank/questions')
async def browse_admin(actor:Account,q:str=Query('',max_length=200),subject_id:str|None=None,missing:bool=False,
                       issue:Literal['all','missing','defect','held','keyed','unverified','descriptive','malformed','disputed','missing-explanation','missing-figure','missing-context']='all',
                       review_task:Literal['all','answer','source','failed','publishing']='all',paper_id:str|None=None,answer_status:Literal['official','verified','needs-review','unsolved','written']|None=None,exam_id:str|None=None,year:int|None=Query(None,ge=1900,le=2100),topic_id:str|None=None,offset:int=Query(0,ge=0,le=1000000),limit:int=Query(20,ge=1,le=100)):
    filters={
        'all':'TRUE',
        'disputed':'q.key_disputed',
        'missing-explanation':"q.type='mcq' AND NULLIF(btrim(q.explanation),'') IS NULL",
        'missing-figure':"EXISTS(SELECT 1 FROM appearances fi JOIN papers fip ON fip.id=fi.paper_id WHERE fi.canonical_id=q.id AND fi.has_diagram AND NULLIF(btrim(fi.figure_image),'') IS NULL AND (%s::text IS NULL OR fi.paper_id=%s) AND (%s::text IS NULL OR EXISTS(SELECT 1 FROM bank_exam_papers fep WHERE fep.paper_id=fi.paper_id AND fep.exam_id=%s)) AND (%s::int IS NULL OR fip.year=%s))",
        'missing-context':"q.source_defect='unresolved-source'",
        'missing':"q.type='mcq' AND q.answer_text IS NULL",
        'defect':'q.source_defect IS NOT NULL',
        'held':"q.status='held'",
        'keyed':"q.answer_source IN ('official','key')",
        'unverified':"q.type='mcq' AND q.answer_text IS NOT NULL AND q.answer_source NOT IN ('official','key')",
        'descriptive':"q.type<>'mcq'",
        'malformed':"q.type='mcq' AND (jsonb_array_length(q.options)<2 OR EXISTS(SELECT 1 FROM jsonb_array_elements_text(q.options) o(value) WHERE o.value IS NULL OR btrim(o.value)='') OR (SELECT count(DISTINCT o.value) FROM jsonb_array_elements_text(q.options) o(value))<jsonb_array_length(q.options))",
    }
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone(): raise HTTPException(403,'Admin permission required')
        where="""q.status<>'merged' AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
          AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))
          AND (%s='' OR q.search @@ plainto_tsquery('english',%s) OR q.id=%s)
          AND (%s::text IS NULL OR c.subject_id=%s OR (%s='gk-gs' AND c.subject_id IN ('general-knowledge','general-studies')))
          AND (NOT %s OR (q.type='mcq' AND q.answer_text IS NULL))
          AND ((%s::text IS NULL AND %s::text IS NULL AND %s::int IS NULL) OR EXISTS(SELECT 1 FROM appearances fa JOIN papers fp ON fp.id=fa.paper_id WHERE fa.canonical_id=q.id
           AND (%s::text IS NULL OR fa.paper_id=%s) AND (%s::text IS NULL OR EXISTS(SELECT 1 FROM bank_exam_papers ep WHERE ep.paper_id=fa.paper_id AND ep.exam_id=%s)) AND (%s::int IS NULL OR fp.year=%s)))
          AND (%s::text IS NULL OR bs.answer_status=%s)
          AND (%s::text IS NULL OR EXISTS(SELECT 1 FROM v_question_paths t WHERE t.question_id=q.id AND t.topic_id=%s))
          AND ("""+filters[issue]+')'
        params=(actor.id,q.strip(),q.strip(),q.strip(),subject_id,subject_id,subject_id,missing,paper_id,exam_id,year,paper_id,paper_id,exam_id,exam_id,year,year,answer_status,answer_status,topic_id,topic_id)
        if issue=='missing-figure':params+= (paper_id,paper_id,exam_id,exam_id,year,year)
        from ..services.admin_review_queue import page
        ordering="a.page NULLS LAST,CASE WHEN a.qnum ~ '^[0-9]{1,9}$' THEN a.qnum::int END NULLS LAST,a.qnum,q.id" if paper_id else 'q.id'
        return await page(cur,where,params,paper_id,exam_id,year,review_task,ordering,limit,offset)

@router.get('/api/admin/bank/questions/{qid}/inspect')
async def inspect_question(qid:str,actor:Account,appearance_id:str|None=None,
                           appearance_offset:int=Query(0,ge=0,le=1000000)):
    from ..source_files import figure_image_url
    async with cursor() as cur:
        await cur.execute('''SELECT q.id,q.type,q.question,q.options,q.answer_text,q.answer_source,q.answer_key_ref,
            q.status,q.source_defect,q.dispute_note,c.subject_id,c.subject_label,c.topic_label,c.subtopic_label
            FROM canonical_questions q LEFT JOIN question_classifications c ON c.question_id=q.id AND c.review_status='approved'
            WHERE q.id=%s AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
            AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))''',(qid,actor.id))
        canonical=await cur.fetchone()
        if not canonical:raise HTTPException(404,'Question not found in your review scope')
        await service.protect_answer(cur,actor.id,qid)
        snap=await service.snapshot(cur,qid,appearance_id)
        await cur.execute('''SELECT a.id,a.paper_id,a.qnum,a.page,a.is_primary,p.exam_name,p.year,
           count(*) OVER()::int AS total FROM appearances a JOIN papers p ON p.id=a.paper_id
           WHERE a.canonical_id=%s ORDER BY a.is_primary DESC,a.id LIMIT 50 OFFSET %s''',(qid,appearance_offset))
        appearances=await cur.fetchall()
        await cur.execute('SELECT count(*)::int AS total FROM appearances WHERE canonical_id=%s',(qid,))
        total=(await cur.fetchone())['total']
        await cur.execute('SELECT id,title,sha256,kind,key_status FROM review_documents WHERE paper_id=%s ORDER BY kind,title FOR SHARE',(snap['paper']['id'],))
        documents=await cur.fetchall()
        snap['edit_hash']=digest(snap)
        await cur.execute("SELECT subject_label,topic_label,subtopic_label FROM question_classifications WHERE question_id=%s AND review_status='approved'",(qid,))
        labels=await cur.fetchone()
        snap['tag_label']=' / '.join(v for v in labels.values() if v) if labels else 'No approved subject'
        snap['canonical_id']=qid
        snap['can_publish']=bool(set(await grants(cur,actor.id,snap['record']['classification'].get('subject_id')))&{'owner','publisher'})
        snap['solo_owner']='owner' in await grants(cur,actor.id)
        if snap['can_publish']:
            await cur.execute("SELECT id,kind,note FROM content_reports WHERE canonical_id=%s AND status IN ('open','confirmed') ORDER BY id",(qid,))
            snap['reports']=await cur.fetchall()
        snap['documents']=documents
        await cur.execute('''SELECT id,title,kind,state,revision,updated_at FROM bank_contributions
            WHERE canonical_id=%s AND state NOT IN ('draft','withdrawn') ORDER BY updated_at DESC,id LIMIT 20''',(qid,))
        proposals=await cur.fetchall()
        snap['figure_url']=figure_image_url(snap['record'].get('figureImage'))
    draft=luna_priority_solutions().get(qid)
    if draft and (draft['appearance_id']!=snap['record']['id'] or
                  draft['question']!=snap['record']['question'] or
                  draft['options']!=snap['record']['options']):
        draft=None
    return {'canonical':canonical,'snapshot':snap,'appearances':appearances,'appearance_total':total,
            'appearance_offset':appearance_offset,'proposals':proposals,'luna_draft':draft}

@router.get('/api/admin/bank/papers')
async def admin_papers(actor:Account,q:str='',subject_id:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=100)):
    from ..source_files import source_pdf_url
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone(): raise HTTPException(403,'Admin permission required')
        await cur.execute('''SELECT p.id,p.exam_name,p.exam_type,p.year,p.source_file,p.pdf_url,
            (SELECT count(*)::int FROM appearances a WHERE a.paper_id=p.id) AS questions,
            (SELECT count(*)::int FROM review_documents d WHERE d.paper_id=p.id) AS registered_documents,
            count(*) OVER()::int AS total FROM papers p
            WHERE (%s='' OR p.exam_name ILIKE %s OR p.source_file ILIKE %s)
            AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
                AND (g.subject_id IS NULL OR EXISTS(SELECT 1 FROM appearances a JOIN question_classifications qc ON qc.question_id=a.canonical_id WHERE a.paper_id=p.id AND qc.subject_id=g.subject_id)))
            AND (%s::text IS NULL OR EXISTS(SELECT 1 FROM appearances a JOIN question_classifications qc ON qc.question_id=a.canonical_id WHERE a.paper_id=p.id AND qc.subject_id=%s))
            ORDER BY p.year DESC NULLS LAST,p.id LIMIT %s OFFSET %s''',(q,'%'+q+'%','%'+q+'%',actor.id,subject_id,subject_id,limit,offset))
        rows=await cur.fetchall()
    return {'items':[{**r,'source_pdf_url':source_pdf_url(r['source_file'],r['pdf_url'])} for r in rows],'total':rows[0]['total'] if rows else 0}

@router.post('/api/admin/bank/publications/{pubid}/revert-proposal')
async def propose_reversal(pubid:str,body:Transition,actor:Account):
    if len(body.reason.strip())<20: raise HTTPException(422,'Explain why this publication should be reversed')
    async with cursor() as cur:
        await cur.execute('SELECT p.*,c.subject_id,c.canonical_id,c.title,c.kind FROM bank_publications p JOIN bank_contributions c ON c.id=p.contribution_id WHERE p.id=%s',(pubid,))
        original=await cur.fetchone()
        if not original: raise HTTPException(404,'Publication not found')
        await require_role(cur,actor.id,original['subject_id'],('owner','publisher'))
        if original['state']!='applied' or not original['canonical_id']: service.conflict('This publication cannot be reversed through a question revision')
        patch=original['receipt'].get('before_fields',{})
        kind=original['kind']
        if kind=='new_question' or (kind=='answer' and patch.get('answerIndex') is None):
            kind='defect';patch={'sourceDefect':'unresolved-source','disputeNote':body.reason}
        elif kind=='explanation' and not patch.get('explanation'):
            kind='transcription';patch={'explanation':None}
        if kind in {'duplicate','source_request'}: raise HTTPException(409,'Relationship/source fulfillment reversal requires an operator audit')
        if kind=='answer' and not patch.get('explanation'): patch['explanation']=body.reason
        try:
            p=Proposal.model_validate({'kind':kind,'canonical_id':original['canonical_id'],'subject_id':original['subject_id'],
            'reverts_publication':pubid,'title':('Revert: '+original['title'])[:200],
            'patch':patch,'rationale':body.reason,'evidence':original['manifest']['payload']['evidence']})
        except ValidationError as exc: raise HTTPException(422,'The previous answer needs new mapped evidence; create a correction with the original source key') from exc
        return await service.create(cur,actor.id,p,'revert:'+pubid)


class Visibility(Strict):
    public: bool

@router.post('/api/contributions/visibility')
async def visibility(body:Visibility,actor:Account):
    async with cursor() as cur:
        await cur.execute('UPDATE users SET contribution_public=%s WHERE id=%s',(body.public,actor.id))
    return {'public':body.public}


@router.get('/api/admin/bank/reports')
async def legacy_reports(actor:Account,before:int|None=None,limit:int=Query(30,ge=1,le=100),report_id:int|None=Query(None,ge=1)):
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL LIMIT 1',(actor.id,))
        if not await cur.fetchone():raise HTTPException(403,'A review permission is required')
        await cur.execute('''SELECT r.id,r.canonical_id,r.kind,r.note,r.evidence_page,r.status,r.created_at,q.question,
            qc.subject_id,qc.subject_label FROM content_reports r JOIN canonical_questions q ON q.id=r.canonical_id
            LEFT JOIN question_classifications qc ON qc.question_id=q.id
            WHERE r.status IN ('open','confirmed') AND (%s::bigint IS NULL OR r.id<%s) AND (%s::bigint IS NULL OR r.id=%s)
            AND EXISTS (SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
                AND (g.subject_id IS NULL OR g.subject_id=qc.subject_id))
            ORDER BY r.id DESC LIMIT %s''',(before,before,report_id,report_id,actor.id,limit))
        return await cur.fetchall()

class ReportResolution(Strict):
    status: Literal['fixed','rejected']
    reason: str = Field(min_length=20,max_length=2000)
    publication_id: str|None = Field(default=None,max_length=100)

@router.post('/api/admin/bank/reports/{report_id}/resolve')
async def resolve_legacy_report(report_id:int,body:ReportResolution,actor:Account):
    async with cursor() as cur:
        await cur.execute('SELECT * FROM content_reports WHERE id=%s FOR UPDATE',(report_id,))
        report=await cur.fetchone()
        if not report:raise HTTPException(404,'Report not found')
        snap=await service.snapshot(cur,report['canonical_id'])
        await require_role(cur,actor.id,snap['record']['classification'].get('subject_id'))
        if report['status'] not in {'open','confirmed'}:service.conflict('Report has already been resolved')
        if body.status=='fixed':
            await cur.execute('''SELECT 1 FROM bank_publications p JOIN bank_contributions c ON c.id=p.contribution_id
                WHERE p.id=%s AND p.state='applied' AND c.canonical_id=%s''',(body.publication_id,report['canonical_id']))
            if not await cur.fetchone():raise HTTPException(422,'Link an applied publication for this exact question before marking the report fixed')
        await cur.execute('UPDATE content_reports SET status=%s,resolved_by=%s,resolved_at=now() WHERE id=%s',(body.status,actor.id,report_id))
        await service.event(cur,None,actor.id,'legacy_report_'+body.status,{'report_id':report_id,'question':report['canonical_id'],'reason':body.reason,'publication_id':body.publication_id})
    return {'status':body.status}


@router.get('/api/review/documents')
async def paper_documents(actor:Account,paper_id:str=Query(min_length=1,max_length=300)):
    # Public source metadata only, never local filesystem paths or documents
    # from an unrelated paper. Required by source-request/original-paper editors.
    async with cursor() as cur:
        await cur.execute("SELECT id,title,sha256,kind,key_status FROM review_documents WHERE paper_id=%s ORDER BY kind,title LIMIT 100",(paper_id,))
        return await cur.fetchall()


@router.post('/api/admin/bank/assessments/retry')
async def retry_assessments(body:Hold,actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('''WITH retry AS (SELECT canonical_id FROM assessment_jobs WHERE failures>=5
          ORDER BY requested_at LIMIT 50 FOR UPDATE SKIP LOCKED)
          UPDATE assessment_jobs j SET failures=0,last_error=NULL,finished_at=NULL
          FROM retry WHERE j.canonical_id=retry.canonical_id RETURNING j.canonical_id''')
        historical=len(await cur.fetchall())
        await cur.execute('''WITH retry AS (SELECT id FROM new_score_jobs WHERE failures>=5 ORDER BY id LIMIT 50 FOR UPDATE SKIP LOCKED)
          UPDATE new_score_jobs j SET failures=0,last_error=NULL,finished_at=NULL
          FROM retry WHERE j.id=retry.id RETURNING j.id''')
        new=len(await cur.fetchall())
        await cur.execute('''WITH retry AS (SELECT id FROM question_change_events WHERE failures>=5 ORDER BY id LIMIT 50 FOR UPDATE SKIP LOCKED)
          UPDATE question_change_events j SET failures=0,last_error=NULL,finished_at=NULL FROM retry WHERE j.id=retry.id RETURNING j.id''')
        notices=len(await cur.fetchall())
        await service.event(cur,None,actor.id,'assessment_retry',{'historical':historical,'new':new,'correction_notices':notices,'reason':body.reason})
    return {'retried':historical+new+notices}


@router.get('/api/admin/bank/database-map')
async def database_map(actor:Account):
    async with cursor() as cur:
        await require_role(cur,actor.id,None,('owner',))
        from ..services.database_map import read_map
        return await read_map(cur)

from .admin_bank_edits import router as admin_edit_router
router.include_router(admin_edit_router)

@router.get('/api/admin/bank/publication-history')
async def publication_history(actor:Account,response:Response,mine:bool=True,q:str=Query('',max_length=200),
    state:Literal['','applied','exported','failed','reverted']='',kind:str=Query('',max_length=50),
    offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=100)):
    response.headers['Cache-Control']='private, no-store'
    from ..services.publication_history import listing
    async with cursor() as cur:
        return await listing(cur,actor.id,mine=mine,q=q.strip(),state=state,kind=kind,offset=offset,limit=limit)

@router.get('/api/admin/bank/publication-history/{publication_id}')
async def publication_history_detail(publication_id:str,actor:Account,response:Response):
    response.headers['Cache-Control']='private, no-store'
    from ..services.publication_history import detail
    async with cursor() as cur:
        return await detail(cur,actor.id,publication_id)
