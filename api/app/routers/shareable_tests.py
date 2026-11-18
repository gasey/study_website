"""User test builder discovery, answer-free landing pages and share previews."""
from typing import Annotated,Literal
from fastapi import APIRouter,Depends,HTTPException,Query
from fastapi.responses import HTMLResponse
from ..services.public_share import share_page
from ..db import cursor
from ..deps import require_account
from ..services import shareable_tests as service
from .current_affairs import no_assessment
from .exam_inventory import no_store

router=APIRouter(prefix='/api/tests',tags=['shareable tests'],dependencies=[Depends(no_store)])
User=Annotated[str,Depends(require_account)]


@router.get('')
async def directory(q:str=Query('',max_length=120),offset:int=Query(0,ge=0,le=100000)):
    async with cursor() as cur:
        await cur.execute('''SELECT p.entry_id,p.revision,p.payload,p.published_at,count(*) OVER()::int AS total
          FROM learning_catalog c JOIN learning_test_publications p ON p.entry_id=c.id AND p.revision=c.live_test_version
          WHERE c.live_payload IS NOT NULL AND (%s='' OR p.payload->>'title' ILIKE %s)
          ORDER BY p.published_at DESC,p.entry_id LIMIT 20 OFFSET %s''',(q,'%'+q+'%',offset))
        rows=await cur.fetchall()
        return {'items':[service.metadata(r) for r in rows],'total':rows[0]['total'] if rows else 0}


@router.get('/find')
async def find_questions(user:User,q:str=Query('',max_length=120),subject:str=Query('',max_length=160),
    answer_mode:Literal['official','derived-practice']='official',offset:int=Query(0,ge=0,le=100000)):
    view='v_mock_practice' if answer_mode=='derived-practice' else 'v_scorable'
    async with cursor() as cur:
        await no_assessment(cur,user)
        await cur.execute('''SELECT v.id,v.question,v.options,v.answer_source,
          count(*) OVER()::int AS total FROM '''+view+''' v
          WHERE (%s='' OR v.question ILIKE %s) AND (%s='' OR EXISTS(SELECT 1 FROM v_question_paths p
            WHERE p.question_id=v.id AND p.subject_id=%s AND p.review_status='approved'))
          ORDER BY v.id LIMIT 20 OFFSET %s''',(q,'%'+q+'%',subject,subject,offset))
        rows=await cur.fetchall()
        return {'items':rows,'total':rows[0]['total'] if rows else 0}


@router.get('/{eid}/stats')
async def statistics(eid:str,user:User):
    async with cursor() as cur:
        await no_assessment(cur,user)
        await cur.execute('SELECT author_id FROM learning_catalog WHERE id=%s',(eid,));owner=await cur.fetchone()
        if not owner or owner['author_id']!=user:raise HTTPException(404,'Your test was not found')
        await cur.execute('''SELECT learning_test_version AS revision,count(*)::int AS starts,
          count(*) FILTER(WHERE submitted_at IS NOT NULL)::int AS completions,
          count(*) FILTER(WHERE late AND submitted_at IS NOT NULL)::int AS late_completions
          FROM mock_sessions WHERE learning_test_id=%s GROUP BY learning_test_version ORDER BY learning_test_version DESC''',(eid,))
        return {'editions':await cur.fetchall(),'basis':'Attempts, not unique people. Individual learner identities, answers and scores are private.'}


@router.get('/selection')
async def selection(user:User,ids:Annotated[list[str],Query(max_length=100)]):
    if any(not 1<=len(q)<=120 for q in ids):raise HTTPException(422,'Invalid question ID')
    async with cursor() as cur:
        await no_assessment(cur,user)
        await cur.execute('SELECT id,question,options,answer_source FROM v_all_questions WHERE id=ANY(%s)',(ids,))
        return {'items':await cur.fetchall()}


@router.get('/{eid}/share',response_class=HTMLResponse)
async def share(eid:str):
    async with cursor() as cur:row=await service.published(cur,eid)
    p=service.metadata(row)
    return share_page(title=p['title'], description=p['description'],
        badge=f"{p['question_count']} questions · {p['config']['duration_minutes']} minutes",
        target_path=p['path'], share_path=p['share_path'], action='Open this mock test')


@router.get('/{eid}')
async def landing(eid:str):
    async with cursor() as cur:return service.metadata(await service.published(cur,eid))
