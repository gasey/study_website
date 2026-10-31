from typing import Annotated,Literal
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import Field,ValidationError
from psycopg.types.json import Jsonb
from ..db import cursor
from ..source_files import figure_image_url
from ..services.review_identity import identity,Actor,require_role
from ..services import bank_review as review,module_intake as intake
from ..services.review_policy import Proposal,digest
from ..services.content_studio import Strict
from .materials import private
router=APIRouter(prefix='/api/admin/bank/module-audits',tags=['module comparison intake'],dependencies=[Depends(private)])
Staff=Annotated[Actor,Depends(identity)]
class Triage(Strict):
    expected_version:int=Field(ge=1)
    action:Literal['dismiss','reopen']
    reason:str=Field(min_length=20,max_length=2000)
class PreparedDraft(Strict):
    baseline_hash:str=Field(pattern=r'^[0-9a-f]{64}$')
    payload_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')

@router.post('/items/{itemid}/prepared/{proposalid}',status_code=201)
async def prepared_draft(itemid:str,proposalid:str,body:PreparedDraft,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT i.*,r.bank_sha256 FROM module_audit_items i JOIN module_audit_runs r ON r.id=i.run_id WHERE i.id=%s',(itemid,));item=await cur.fetchone()
        if not item:raise HTTPException(404,'Module intake record not found')
        matches=[(packet,packet['claim'],p) for packet in item['reviewed_packets'] if isinstance(packet.get('claim'),dict) for p in packet['claim'].get('proposals',[]) if p.get('id')==proposalid]
        if not matches:raise HTTPException(404,'Prepared proposal not found in this comparison')
        packet,claim,prepared=matches[0]
        if any(digest(p)!=digest(prepared) for _,_,p in matches):raise HTTPException(409,'Prepared proposal identity is ambiguous')
        payload=prepared.get('payload',{})
        if prepared.get('status')!='prepared_not_submitted' or digest(payload)!=prepared.get('payloadSha256') or body.payload_sha256!=digest(payload):raise HTTPException(422,'Prepared payload hash or status is invalid')
        try:p=Proposal.model_validate(payload)
        except ValidationError as exc:raise HTTPException(422,'Prepared proposal no longer satisfies the current review contract') from exc
        if p.appearance_id!=claim.get('appearanceId'):raise HTTPException(422,'Prepared target differs from its source assessment')
        await review.protect_answer(cur,actor.id,p.canonical_id)
        # A deterministic actor-scoped key makes retries and two browser tabs converge.
        key='prepared:'+digest([proposalid,digest(payload)])
        await cur.execute('SELECT * FROM bank_contributions WHERE author_id=%s AND idempotency_key=%s',(actor.id,key));prior=await cur.fetchone()
        if prior:
            if prior['request_hash']!=digest(p.model_dump(mode='json')):raise HTTPException(409,'Prepared draft identity was reused with different content')
            await intake.link(cur,actor.id,p,prior['id'],additional_items=(itemid,))
            return {'id':prior['id'],'state':prior['state'],'lock_version':prior['lock_version'],'replayed':True}
        if packet.get('metadata',{}).get('bankSha256AtReview')!=item['bank_sha256']:raise HTTPException(409,'The research packet belongs to an older bank snapshot. Recheck it before creating a draft.')
        await cur.execute('SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1');synced=await cur.fetchone()
        if not synced or synced['bank_checksum']!=item['bank_sha256']:raise HTTPException(409,'The bank changed since this research was prepared. Refresh the research against the current bank.')
        await cur.execute('SELECT 1 FROM module_audit_candidates WHERE item_id=%s AND appearance_id=%s AND canonical_id=%s',(itemid,p.appearance_id,p.canonical_id))
        if not await cur.fetchone():raise HTTPException(422,'Prepared target is not a candidate in this comparison')
        baseline=await review.snapshot(cur,p.canonical_id,p.appearance_id)
        record=baseline['record']
        if intake.identity(item['legacy'])!=intake.identity(record) or intake.identity(claim)!=intake.identity(record) or record['answerIndex']!=claim.get('currentBankAnswerIndex') or record['answerSource']!=claim.get('currentBankAnswerSource'):raise HTTPException(409,'Question identity or answer changed since the research assessment')
        c=await review.create(cur,actor.id,p,key,expected_baseline_hash=body.baseline_hash,additional_module_items=(itemid,))
        await cur.execute("SELECT 1 FROM contribution_events WHERE contribution_id=%s AND action='prepared_research_draft' AND detail->>'proposal_id'=%s",(c['id'],proposalid))
        replayed=bool(await cur.fetchone())
        if not replayed:await review.event(cur,c['id'],actor.id,'prepared_research_draft',{'item_id':itemid,'proposal_id':proposalid,'payload_sha256':body.payload_sha256})
        return {'id':c['id'],'state':c['state'],'lock_version':c['lock_version'],'replayed':replayed}
@router.get('/runs')
async def runs(actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT * FROM (SELECT r.*,row_number() OVER(PARTITION BY module_id ORDER BY created_at DESC,id DESC) AS position FROM module_audit_runs r) x ORDER BY created_at DESC,id DESC LIMIT 100')
        return await cur.fetchall()
@router.get('/items')
async def items(actor:Staff,run_id:str|None=Query(None,max_length=100),module:Literal['all','udc-ldc','combined-prelims']='all',match:Literal['all','exact_unique','ambiguous_exact','unmatched']='all',comparison:Literal['all','agree','conflict','module_only','bank_only','neither','ambiguous','unmatched']='all',state:Literal['all','open','linked','dismissed']='all',q:str=Query('',max_length=160),paper:str=Query('',max_length=200),offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=50)):
    base=''' FROM module_audit_items i JOIN module_audit_runs r ON r.id=i.run_id JOIN module_audit_triage t ON t.item_id=i.id WHERE
      (%s::text IS NOT NULL AND r.id=%s OR %s::text IS NULL AND r.id=(SELECT x.id FROM module_audit_runs x WHERE x.module_id=r.module_id ORDER BY x.created_at DESC,x.id DESC LIMIT 1))
      AND (%s='all' OR r.module_id=%s) AND (%s='all' OR i.match_status=%s) AND (%s='all' OR i.comparison=%s) AND (%s='all' OR t.state=%s)
      AND (%s='' OR i.legacy->>'question' ILIKE %s OR i.legacy_id ILIKE %s OR i.paper_id ILIKE %s) AND (%s='' OR i.paper_id=%s)
      AND NOT EXISTS(SELECT 1 FROM module_audit_candidates c JOIN mock_sessions m ON m.user_id=%s AND m.submitted_at IS NULL AND c.canonical_id=ANY(m.question_ids) WHERE c.item_id=i.id)'''
    args=(run_id,run_id,run_id,module,module,match,match,comparison,comparison,state,state,q,'%'+q+'%','%'+q+'%','%'+q+'%',paper,paper,actor.id)
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT count(*)::int AS total'+base,args);total=(await cur.fetchone())['total']
        await cur.execute('SELECT i.match_status,i.comparison,count(*)::int AS count'+base+' GROUP BY i.match_status,i.comparison',args);counts=await cur.fetchall()
        await cur.execute("SELECT i.id,i.legacy_id,i.paper_id,i.match_status,i.comparison,r.module_id,t.state,t.version,left(i.legacy->>'question',240) AS question,(SELECT count(*)::int FROM module_audit_candidates c WHERE c.item_id=i.id) AS candidates"+base+" ORDER BY CASE i.comparison WHEN 'conflict' THEN 0 WHEN 'module_only' THEN 1 WHEN 'ambiguous' THEN 2 WHEN 'unmatched' THEN 3 ELSE 4 END,r.module_id,i.paper_id,i.legacy_id,i.id LIMIT %s OFFSET %s",(*args,limit,offset));rows=await cur.fetchall()
    return {'items':rows,'total':total,'counts':counts}
@router.get('/items/{itemid}')
async def detail(itemid:str,actor:Staff,candidate:str|None=Query(None,max_length=200),candidate_offset:int=Query(0,ge=0,le=100000)):
    async with cursor() as cur:
        await cur.execute("SELECT 1 FROM module_audit_links l JOIN bank_contributions c ON c.id=l.contribution_id WHERE l.item_id=%s AND (c.author_id=%s OR EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))) LIMIT 1",(itemid,actor.id,actor.id))
        if not await cur.fetchone():await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT i.*,r.module_id,r.module_url,r.source_file,r.source_sha256,r.crosswalk_file,r.crosswalk_sha256,r.bank_sha256,r.manifest_sha256,r.created_at AS imported_at,t.state,t.version,t.reason FROM module_audit_items i JOIN module_audit_runs r ON r.id=i.run_id JOIN module_audit_triage t ON t.item_id=i.id WHERE i.id=%s',(itemid,));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Module intake record not found')
        await cur.execute('SELECT 1 FROM module_audit_candidates c JOIN mock_sessions m ON m.user_id=%s AND m.submitted_at IS NULL AND c.canonical_id=ANY(m.question_ids) WHERE c.item_id=%s LIMIT 1',(actor.id,itemid))
        if await cur.fetchone():raise HTTPException(409,'Finish your active mock before opening module answer comparisons')
        await cur.execute('SELECT c.*,a.paper_id,a.qnum,a.page,p.exam_name,p.year FROM module_audit_candidates c LEFT JOIN appearances a ON a.id=c.appearance_id AND a.canonical_id=c.canonical_id LEFT JOIN papers p ON p.id=a.paper_id WHERE c.item_id=%s ORDER BY c.appearance_id LIMIT 21 OFFSET %s',(itemid,candidate_offset));candidates=await cur.fetchall()
        if not candidate and row['match_status']=='exact_unique':
            await cur.execute("SELECT appearance_id FROM module_audit_candidates WHERE item_id=%s AND imported->>'identity_exact'='true' ORDER BY appearance_id LIMIT 1",(itemid,));exact=await cur.fetchone()
            if exact:candidate=exact['appearance_id']
        selected=None;bank=None;identity_matches=None;answer_comparison=None;changed=None
        if candidate:
            await cur.execute('SELECT * FROM module_audit_candidates WHERE item_id=%s AND appearance_id=%s',(itemid,candidate));selected=await cur.fetchone()
            if not selected:raise HTTPException(404,'Candidate is not part of this intake record')
            try:bank=await review.snapshot(cur,selected['canonical_id'],candidate)
            except HTTPException as exc:
                if exc.status_code!=404:raise
            if bank:
                identity_matches=intake.identity(row['legacy'])==intake.identity(bank['record'])
                answer_comparison=intake.compare(row['legacy'].get('answerIndex'),bank['record']['answerIndex']) if identity_matches else 'identity_changed'
                changed=selected['imported'].get('answer_index')!=bank['record']['answerIndex'] or selected['imported'].get('answer_source')!=bank['record']['answerSource'] or selected['imported'].get('identity_sha256')!=intake.identity_sha(bank['record'])
        await cur.execute('SELECT l.contribution_id,c.title,c.state,c.kind,l.created_at FROM module_audit_links l JOIN bank_contributions c ON c.id=l.contribution_id WHERE l.item_id=%s ORDER BY l.created_at DESC LIMIT 50',(itemid,));links=await cur.fetchall()
        await cur.execute('SELECT action,detail,actor_id,created_at FROM module_audit_events WHERE item_id=%s ORDER BY id DESC LIMIT 50',(itemid,));events=await cur.fetchall()
    return {**row,'candidates':candidates[:20],'has_more_candidates':len(candidates)>20,'selected':selected,'bank':bank,'bank_baseline_hash':digest(bank) if bank else None,'bank_figure_url':figure_image_url(bank['record']['figureImage']) if bank else None,'identity_matches':identity_matches,'live_comparison':answer_comparison,'bank_changed':changed,'links':links,'events':events}
@router.post('/items/{itemid}/triage')
async def triage(itemid:str,body:Triage,actor:Staff):
    if len(body.reason.strip())<20:raise HTTPException(422,'Explain the intake decision')
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT * FROM module_audit_triage WHERE item_id=%s FOR UPDATE',(itemid,));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Intake record not found')
        if row['version']!=body.expected_version:raise HTTPException(409,'Intake record changed; reload before deciding')
        await cur.execute('SELECT 1 FROM module_audit_candidates c JOIN mock_sessions m ON m.user_id=%s AND m.submitted_at IS NULL AND c.canonical_id=ANY(m.question_ids) WHERE c.item_id=%s LIMIT 1',(actor.id,itemid))
        if await cur.fetchone():raise HTTPException(409,'Finish your active mock before reviewing this module record')
        if body.action=='dismiss' and row['state']=='dismissed':raise HTTPException(409,'This intake record is already dismissed')
        if body.action=='reopen' and row['state']!='dismissed':raise HTTPException(409,'Only dismissed intake records can be reopened')
        state='dismissed' if body.action=='dismiss' else 'open'
        await cur.execute('UPDATE module_audit_triage SET state=%s,version=version+1,reason=%s,updated_by=%s,updated_at=now() WHERE item_id=%s',(state,body.reason.strip(),actor.id,itemid))
        await cur.execute('INSERT INTO module_audit_events(item_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)',(itemid,actor.id,body.action,Jsonb({'reason':body.reason.strip()})))
    return {'state':state,'version':body.expected_version+1}
