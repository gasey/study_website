"""Derived owner work queue: no duplicated workflow state or automatic decisions."""
from typing import Annotated,Literal
from urllib.parse import urlencode
from fastapi import APIRouter,Depends,Query
from ..db import cursor
from ..services.review_identity import identity,Actor,require_role
from .materials import private
router=APIRouter(prefix='/api/admin/bank',tags=['publishing dashboard'],dependencies=[Depends(private)])
Staff=Annotated[Actor,Depends(identity)]
WORK="""WITH work AS (
 SELECT 'correction'::text AS kind,c.id::text,c.title,c.state,
 CASE WHEN c.state='publication_failed' THEN 'failed' WHEN c.state IN ('accepted','publishing') THEN 'ready' WHEN c.state='changes_requested' THEN 'awaiting_author' WHEN c.state='in_review' THEN 'in_progress' ELSE 'new' END AS stage,
 COALESCE(u.handle,'Contributor') AS author,c.created_at,c.updated_at,c.subject_id,c.canonical_id AS related_id,
 CASE WHEN c.state='publication_failed' THEN 0 ELSE 2 END AS priority,
 CASE WHEN c.state='publication_failed' THEN 'Publication failed: inspect the publication receipt' ELSE 'Review correction evidence and quorum' END AS priority_reason
 FROM bank_contributions c JOIN users u ON u.id=c.author_id WHERE c.state IN ('submitted','in_review','changes_requested','accepted','publishing','publication_failed')
 UNION ALL
 SELECT 'material',m.id,m.title,m.workflow_state,CASE WHEN m.workflow_state='changes_requested' THEN 'awaiting_author' ELSE 'new' END,
 COALESCE(u.handle,'India Study Map'),first_rev.created_at,m.updated_at,r.payload->>'subject_id',NULL::text,2,'Review the exact submitted material revision'
 FROM materials m JOIN material_revisions r ON r.material_id=m.id AND r.revision=m.revision JOIN material_revisions first_rev ON first_rev.material_id=m.id AND first_rev.revision=1 LEFT JOIN users u ON u.id=m.author_id WHERE m.workflow_state IN ('submitted','changes_requested')
 UNION ALL
 SELECT 'question-report',r.id::text,left(q.question,180),r.status,CASE WHEN r.status='confirmed' THEN 'in_progress' ELSE 'new' END,
 'Question report',r.created_at,r.created_at,qc.subject_id,r.canonical_id,
 CASE WHEN r.kind IN ('wrong_key','outdated') THEN 1 ELSE 2 END,
 CASE WHEN r.kind IN ('wrong_key','outdated') THEN 'Potential scoring/currentness issue; evidence still needs review' ELSE 'Investigate reported source/presentation issue' END
 FROM content_reports r JOIN canonical_questions q ON q.id=r.canonical_id LEFT JOIN question_classifications qc ON qc.question_id=q.id WHERE r.status IN ('open','confirmed')
 UNION ALL
 SELECT 'material-report',r.id::text,m.title,r.state,'new','Material report',r.created_at,r.created_at,NULL::text,r.material_id,
 CASE WHEN r.reason='copyright' THEN 1 ELSE 2 END,'Investigate the material report before resolving'
 FROM material_reports r JOIN materials m ON m.id=r.material_id WHERE r.state='open'
 UNION ALL
 SELECT 'creator-report',r.id::text,u.handle,r.state,'new','Creator report',r.created_at,r.updated_at,NULL::text,r.creator_id,
 CASE WHEN r.reason IN ('harassment','impersonation') THEN 1 ELSE 2 END,'Investigate the creator report before resolving'
 FROM creator_reports r JOIN users u ON u.id=r.creator_id WHERE r.state='open'
) """
@router.get('/work')
async def work(actor:Staff,kind:Literal['all','correction','material','question-report','material-report','creator-report']='all',stage:Literal['all','new','in_progress','awaiting_author','ready','failed']='all',priority:Literal['all','urgent','high','normal']='all',q:str=Query('',max_length=160),subject_id:str=Query('',max_length=100),order:Literal['priority','oldest','newest']='priority',offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=50)):
    where=" WHERE (%s='all' OR kind=%s) AND (%s='all' OR stage=%s) AND (%s='all' OR priority=%s) AND (%s='' OR title ILIKE %s OR id ILIKE %s OR author ILIKE %s) AND (%s='' OR subject_id=%s)"
    rank={'all':-1,'urgent':0,'high':1,'normal':2}[priority]
    args=(kind,kind,stage,stage,priority,rank,q,'%'+q+'%','%'+q+'%','%'+q+'%',subject_id,subject_id)
    sorting={'priority':'priority,created_at,kind,id','oldest':'created_at,kind,id','newest':'created_at DESC,kind,id'}[order]
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute(WORK+'SELECT kind,count(*)::int AS count FROM work GROUP BY kind ORDER BY kind');counts=await cur.fetchall()
        await cur.execute(WORK+'SELECT count(*)::int AS total,count(*) FILTER(WHERE priority=0)::int AS urgent,count(*) FILTER(WHERE stage=\'awaiting_author\')::int AS awaiting_author FROM work'+where,args);summary=await cur.fetchone()
        await cur.execute(WORK+'SELECT * FROM work'+where+' ORDER BY '+sorting+' LIMIT %s OFFSET %s',(*args,limit,offset));rows=await cur.fetchall()
    for row in rows:
        k,i=row['kind'],row['id']
        if k=='correction':row['url']='/contributions/'+i
        elif k=='material':row['url']='/admin/bank?'+urlencode({'tab':'content','material':i})
        elif k=='material-report':row['url']='/admin/bank?'+urlencode({'tab':'content','material':row['related_id'],'material_report':i})
        elif k=='creator-report':row['url']='/admin/bank?'+urlencode({'tab':'content','creator_report':i})+'#creator-reports'
        else:row['url']='/admin/bank?'+urlencode({'tab':'reports','report':i})
    return {**summary,'counts':counts,'items':rows}

@router.get('/quality')
async def quality(actor:Staff,subject_id:str=Query('',max_length=100),exam_id:str=Query('',max_length=200),year:int|None=Query(None,ge=1900,le=2100)):
    async with cursor()as cur:
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL',(actor.id,))
        if not await cur.fetchone():
            from fastapi import HTTPException
            raise HTTPException(403,'Review permission required')
        await cur.execute('''SELECT count(*)::int AS total,
         count(*) FILTER(WHERE q.type='mcq' AND q.answer_text IS NULL)::int AS missing,
         count(*) FILTER(WHERE q.key_disputed)::int AS disputed,
         count(*) FILTER(WHERE q.type='mcq' AND NULLIF(btrim(q.explanation),'') IS NULL)::int AS missing_explanation,
         count(*) FILTER(WHERE EXISTS(SELECT 1 FROM appearances a JOIN papers fp ON fp.id=a.paper_id WHERE a.canonical_id=q.id AND a.has_diagram AND NULLIF(btrim(a.figure_image),'') IS NULL AND (%s='' OR EXISTS(SELECT 1 FROM bank_exam_papers fep WHERE fep.paper_id=a.paper_id AND fep.exam_id=%s)) AND (%s::int IS NULL OR fp.year=%s)))::int AS missing_figure,
         count(*) FILTER(WHERE q.source_defect='unresolved-source')::int AS missing_context,
         count(*) FILTER(WHERE s.answer_status='needs-review')::int AS needs_review,
         count(*) FILTER(WHERE q.status='held')::int AS held
         FROM canonical_questions q JOIN v_bank_answer_status s ON s.id=q.id
         LEFT JOIN question_classifications c ON c.question_id=q.id AND c.review_status='approved'
         WHERE q.status<>'merged' AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=%s AND g.revoked_at IS NULL AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))
         AND (%s='' OR c.subject_id=%s)
         AND ((%s='' AND %s::int IS NULL) OR EXISTS(SELECT 1 FROM appearances a JOIN papers p ON p.id=a.paper_id
          WHERE a.canonical_id=q.id AND (%s='' OR EXISTS(SELECT 1 FROM bank_exam_papers ep WHERE ep.paper_id=a.paper_id AND ep.exam_id=%s)) AND (%s::int IS NULL OR p.year=%s)))''',
         (exam_id,exam_id,year,year,actor.id,subject_id,subject_id,exam_id,year,exam_id,exam_id,year,year));return await cur.fetchone()
