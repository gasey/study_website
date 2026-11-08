from typing import Annotated,Literal
from fastapi import APIRouter,Depends,Header,Query,HTTPException
from pydantic import BaseModel,ConfigDict,Field,model_validator
from ..db import cursor
from ..services.review_identity import Actor,identity,require_role
from ..services.review_policy import Proposal,Evidence
from ..services.admin_bank_edits import decide
from ..services.bank_organization import provider_expression,signature_sql

from .exam_inventory import no_store
router=APIRouter(prefix='/api/admin/bank',tags=['final admin corrections'],dependencies=[Depends(no_store)])

@router.get('/tag-sources')
async def tag_sources(actor:Annotated[Actor,Depends(identity)],search:str=Query('',max_length=200),
    bank:str=Query('all',max_length=100),module:str=Query('',max_length=100),offset:int=Query(0,ge=0,le=1000000)):
    pattern='%'+search.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
    async with cursor() as cur:
        await cur.execute('''SELECT p.id,p.exam_name AS title,p.year,p.paper_subject FROM papers p LEFT JOIN bank_paper_profiles bp ON bp.paper_id=p.id
          WHERE (%s='all' OR %s='''+provider_expression()+''')
            AND (%s='' OR EXISTS(SELECT 1 FROM collection_papers cp JOIN collections col ON col.id=cp.collection_id
              AND cp.version=col.live_version WHERE cp.paper_id=p.id AND cp.allow_browse AND cp.collection_id=%s))
            AND (p.exam_name ILIKE %s OR p.paper_subject ILIKE %s OR p.id ILIKE %s OR p.year::text ILIKE %s)
            AND EXISTS(SELECT 1 FROM appearances a LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
              JOIN review_grants g ON g.user_id=%s AND g.revoked_at IS NULL AND (g.subject_id IS NULL OR g.subject_id=qc.subject_id) WHERE a.paper_id=p.id)
          ORDER BY p.year DESC NULLS LAST,p.exam_name,p.id LIMIT 13 OFFSET %s''',
          (bank,bank,module,module,pattern,pattern,pattern,pattern,actor.id,offset))
        rows=await cur.fetchall()
        return {'items':rows[:12],'has_more':len(rows)>12}

class Edit(BaseModel):
    model_config=ConfigDict(extra='forbid')
    proposal:Proposal
    baseline_hash:str=Field(pattern=r'^[0-9a-f]{64}$')
    source_version:str=Field(pattern=r'^[0-9a-f]{64}$')
    report_ids:list[int]=Field(default_factory=list,max_length=50)

    @model_validator(mode='after')
    def distinct(self):
        if len(set(self.report_ids))!=len(self.report_ids) or any(i<1 for i in self.report_ids):raise ValueError('Choose distinct report IDs')
        return self

@router.post('/edits')
async def edit(body:Edit,actor:Annotated[Actor,Depends(identity)],idempotency_key:Annotated[str|None,Header()]=None):
    async with cursor() as cur:
        return await decide(cur,actor,body.proposal,idempotency_key,body.baseline_hash,body.source_version,body.report_ids)


class RoutineEdit(BaseModel):
    model_config=ConfigDict(extra='forbid')
    kind:Literal['taxonomy','transcription','source_reference','explanation']
    canonical_id:str=Field(min_length=1,max_length=100)
    appearance_id:str=Field(min_length=1,max_length=200)
    patch:dict=Field(min_length=1,max_length=20)
    note:str=Field(default='',max_length=4000)
    evidence:list[Evidence]=Field(default_factory=list,max_length=10)
    baseline_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    source_version:str=Field(pattern=r'^[a-f0-9]{64}$')
    report_ids:list[int]=Field(default_factory=list,max_length=50)

    @model_validator(mode='after')
    def reports(self):
        if len(set(self.report_ids))!=len(self.report_ids) or any(i<1 for i in self.report_ids):raise ValueError('Choose distinct report IDs')
        return self


@router.post('/routine-edits')
async def routine_edit(body:RoutineEdit,actor:Annotated[Actor,Depends(identity)],idempotency_key:Annotated[str|None,Header()]=None):
    from ..services import bank_review
    from ..services.owner_workflow import routine_proposal
    if not idempotency_key or len(idempotency_key)>80:raise HTTPException(422,'A stable request key is required')
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await bank_review.protect_answer(cur,actor.id,body.canonical_id)
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('admin-edit:'+actor.id+':'+idempotency_key,))
        await cur.execute('''SELECT d.canonical_id,r.baseline FROM admin_bank_decisions d JOIN contribution_revisions r
          ON r.contribution_id=d.contribution_id AND r.revision=d.revision WHERE d.actor_id=%s AND d.request_key=%s''',(actor.id,idempotency_key))
        prior=await cur.fetchone()
        if prior and (prior['canonical_id']!=body.canonical_id or prior['baseline']['record']['id']!=body.appearance_id):raise HTTPException(409,'This request key belongs to another source question')
        snap=prior['baseline'] if prior else await bank_review.snapshot(cur,body.canonical_id,body.appearance_id)
        p=routine_proposal({**snap,'canonical_id':body.canonical_id},body.kind,body.patch,body.note,
          [e.model_dump(mode='json') for e in body.evidence])
        result=await decide(cur,actor,p,idempotency_key,body.baseline_hash,body.source_version,body.report_ids)
        if not result.get('replayed'):
            await bank_review.event(cur,result['contribution_id'],actor.id,'owner_routine_summary',{
              'summary_kind':'automatic_change_summary','owner_note':bool(body.note.strip()),'kind':body.kind})
        return {**result,'summary_kind':'automatic_change_summary'}


@router.get('/tag-issues')
async def tag_issues(actor:Annotated[Actor,Depends(identity)],
    issue:Literal['attention','reported','no-subject','no-topic','invalid','all']='attention',
    q:str=Query('',max_length=200),subject:str=Query('',max_length=100),topic:str=Query('',max_length=160),
    subtopic:str=Query('',max_length=200),path:Literal['primary','related','any']='primary',
    period:Literal['all','legacy','current','unknown']='all',region:str=Query('',max_length=160),
    time_behavior:Literal['all','unknown','static','dated-event','changes-over-time']='all',
    bank:str=Query('all',max_length=100),module:str=Query('',max_length=100),paper:str=Query('',max_length=600),
    year:int|None=Query(None,ge=1900,le=2100),sort:Literal['priority','paper','reported']='priority',
    offset:int=Query(0,ge=0,le=1000000),limit:int=Query(20,ge=1,le=100)):
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone():raise HTTPException(403,'Review permission required')
        invalid="""(qc.subject_id IS NOT NULL AND (s.id IS NULL OR NOT s.active OR s.level<>'subject' OR s.parent_id IS NOT NULL
          OR (qc.topic_id IS NOT NULL AND (t.id IS NULL OR NOT t.active OR t.level<>'topic' OR t.parent_id IS DISTINCT FROM s.id))
          OR (qc.subtopic_id IS NOT NULL AND (st.id IS NULL OR NOT st.active OR st.level<>'subtopic' OR st.parent_id IS DISTINCT FROM t.id OR t.id IS NULL))))
          OR EXISTS(SELECT 1 FROM question_topic_links l
            LEFT JOIN review_taxonomy ls ON ls.id=l.subject_id LEFT JOIN review_taxonomy lt ON lt.id=l.topic_id
            LEFT JOIN review_taxonomy lst ON lst.id=l.subtopic_id
            WHERE l.question_id=c.id AND l.review_status='approved' AND
            (ls.id IS NULL OR NOT ls.active OR ls.level<>'subject' OR ls.parent_id IS NOT NULL
            OR (l.topic_id IS NOT NULL AND (lt.id IS NULL OR NOT lt.active OR lt.level<>'topic' OR lt.parent_id IS DISTINCT FROM ls.id))
            OR (l.subtopic_id IS NOT NULL AND (lst.id IS NULL OR NOT lst.active OR lst.level<>'subtopic' OR lst.parent_id IS DISTINCT FROM lt.id OR lt.id IS NULL))))"""
        common='''WITH scoped_appearances AS (
          SELECT DISTINCT ON (a.canonical_id) a.canonical_id,a.id,a.paper_id,a.qnum,a.page,a.qnum_seq
          FROM appearances a JOIN papers sp ON sp.id=a.paper_id LEFT JOIN bank_paper_profiles bp ON bp.paper_id=sp.id
          WHERE (%s='' OR a.paper_id=%s)
            AND (%s='all' OR %s='''+provider_expression('sp')+''') AND (%s='all' OR COALESCE(bp.period,'unknown')=%s) AND (%s::int IS NULL OR sp.year=%s)
            AND (%s='' OR EXISTS(SELECT 1 FROM collection_papers cp JOIN collections col ON col.id=cp.collection_id
              AND cp.version=col.live_version WHERE cp.paper_id=a.paper_id AND cp.allow_browse AND cp.collection_id=%s))
          ORDER BY a.canonical_id,a.is_primary DESC,a.id),
          tag_reports AS (SELECT canonical_id,count(*)::int AS n,min(created_at) AS oldest
            FROM content_reports WHERE kind='subject' AND status IN ('open','confirmed') GROUP BY canonical_id),
          candidates AS (SELECT c.id,c.question,qc.subject_label,qc.topic_label,qc.subject_id,qc.topic_id,
          a.id AS appearance_id,a.paper_id,a.qnum,a.page,a.qnum_seq,p.exam_name AS paper_title,p.year,
          '''+provider_expression()+''' AS bank,
          COALESCE(bp.period,'unknown') AS period,ctx.payload->>'region' AS region,ctx.payload->>'time_behavior' AS time_behavior,
          EXISTS(SELECT 1 FROM question_topic_links l WHERE l.question_id=c.id AND l.review_status='approved') AS has_related,
          qc.subject_id IS NULL AS no_subject,(qc.subject_id IS NOT NULL AND qc.topic_id IS NULL AND NOT EXISTS(SELECT 1 FROM bank_tag_resolutions br JOIN appearances ra ON ra.id=br.appearance_id JOIN papers rp ON rp.id=ra.paper_id WHERE br.question_id=c.id
            AND br.source_signature='''+signature_sql('ra','c','rp')+'''
            AND br.classification=jsonb_build_object('subject_id',qc.subject_id,'topic_id',qc.topic_id,'subtopic_id',qc.subtopic_id))) AS no_topic,
          ('''+invalid+''') AS invalid,
          coalesce(r.n,0)::int AS report_count,r.oldest AS reported_at
          FROM canonical_questions c
          LEFT JOIN question_classifications qc ON qc.question_id=c.id AND qc.review_status='approved'
          LEFT JOIN review_taxonomy s ON s.id=qc.subject_id LEFT JOIN review_taxonomy t ON t.id=qc.topic_id
          LEFT JOIN review_taxonomy st ON st.id=qc.subtopic_id
          JOIN scoped_appearances a ON a.canonical_id=c.id
          JOIN papers p ON p.id=a.paper_id
          LEFT JOIN bank_paper_profiles bp ON bp.paper_id=p.id
          LEFT JOIN bank_question_contexts ctx ON ctx.question_id=c.id AND ctx.source_signature=(SELECT '''+signature_sql('ca','c','cp')+''' FROM appearances ca JOIN papers cp ON cp.id=ca.paper_id WHERE ca.id=ctx.appearance_id)
          LEFT JOIN tag_reports r ON r.canonical_id=c.id
          WHERE c.status<>'merged' AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
            AND (g.subject_id IS NULL OR g.subject_id=qc.subject_id))
          AND (%s='' OR c.id=%s OR c.search @@ plainto_tsquery('english',%s))
          AND ((%s='' AND %s='' AND %s='' AND %s='primary') OR EXISTS(SELECT 1 FROM v_question_paths fp WHERE fp.question_id=c.id AND fp.review_status='approved'
            AND (%s='any' OR fp.is_primary=(%s='primary'))
            AND (%s='' OR fp.subject_id=%s OR (%s='gk-gs' AND fp.subject_id IN ('general-knowledge','general-studies')))
            AND (%s='' OR fp.topic_id=%s) AND (%s='' OR fp.subtopic_id=%s)))
          AND (%s='' OR ctx.payload->>'region'=%s) AND (%s='all' OR COALESCE(ctx.payload->>'time_behavior','unknown')=%s)) SELECT * FROM candidates WHERE '''
        predicate={'attention':'(invalid OR report_count>0 OR no_subject OR no_topic)','reported':'report_count>0',
          'no-subject':'no_subject','no-topic':'no_topic','invalid':'invalid','all':'TRUE'}[issue]
        args=(paper,paper,bank,bank,period,period,year,year,module,module,actor.id,q.strip(),q.strip(),q.strip(),
          subject,topic,subtopic,path,path,path,subject,subject,subject,topic,topic,subtopic,subtopic,region,region,time_behavior,time_behavior)
        # Identical predicates for count and rows; no answer-bearing values leave this endpoint.
        query=common+predicate
        order={'priority':'invalid DESC,(report_count>0) DESC,no_subject DESC,no_topic DESC,reported_at NULLS LAST,id',
          'reported':'report_count DESC,reported_at NULLS LAST,id','paper':'year DESC NULLS LAST,paper_title,paper_id,qnum_seq NULLS LAST,id'}[sort]
        # Count and page share one filtered snapshot/evaluation, including empty pages.
        await cur.execute('WITH matched AS MATERIALIZED ('+query+''') SELECT
          (SELECT count(*)::int FROM matched) AS total,
          coalesce((SELECT jsonb_agg(to_jsonb(page_rows)) FROM
            (SELECT * FROM matched ORDER BY '''+order+" LIMIT %s OFFSET %s) page_rows),'[]'::jsonb) AS items",(*args,limit,offset))
        return await cur.fetchone()


@router.get('/editorial-inbox')
async def inbox(actor:Annotated[Actor,Depends(identity)],kind:Literal['submissions','publishing','answers','completed']='submissions',
    offset:int=Query(0,ge=0,le=1000000)):
    async with cursor() as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone():raise HTTPException(403,'Review permission required')
        if kind=='answers':
            base='''FROM content_reports r JOIN canonical_questions q ON q.id=r.canonical_id
              LEFT JOIN question_classifications qc ON qc.question_id=q.id AND qc.review_status='approved'
              WHERE r.status IN ('open','confirmed') AND r.kind<>'subject'
              AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
                AND (g.subject_id IS NULL OR g.subject_id=qc.subject_id))'''
            await cur.execute('SELECT count(*)::int AS n '+base,(actor.id,));total=(await cur.fetchone())['n']
            await cur.execute('''SELECT r.id::text,r.kind,r.note AS title,r.created_at,r.canonical_id,q.question,
              r.status AS state,(SELECT id FROM appearances a WHERE a.canonical_id=q.id ORDER BY a.is_primary DESC,a.id LIMIT 1) AS appearance_id '''+
              base+' ORDER BY r.created_at,r.id LIMIT 20 OFFSET %s',(actor.id,offset))
        else:
            states={'submissions':['submitted','in_review','changes_requested','accepted'],
                    'publishing':['publishing','publication_failed'],'completed':['published','rejected','withdrawn']}[kind]
            base='''FROM bank_contributions c WHERE c.state=ANY(%s)
              AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL
                AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))'''
            await cur.execute('SELECT count(*)::int AS n '+base,(states,actor.id));total=(await cur.fetchone())['n']
            await cur.execute('SELECT c.id,c.title,c.kind,c.state,c.created_at,c.updated_at,c.canonical_id '+base+
              (' ORDER BY c.updated_at DESC,c.id' if kind=='completed' else " ORDER BY (c.state='publication_failed') DESC,c.created_at,c.id")+' LIMIT 20 OFFSET %s',(states,actor.id,offset))
        return {'items':await cur.fetchall(),'total':total}
