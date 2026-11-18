"""Versioned community feed; study-note reads retain entity and assessment gates."""
from typing import Annotated,Literal
from fastapi import APIRouter,Depends,HTTPException,Query,Request,Response
from ..exam_scope import ExamScope,DEFAULT_SCOPE,question_scope
from ..db import cursor
from ..deps import current_user,require_account
from ..schemas import CommunityFeedItem,CommunityFeedResponse
from ..services.community_policy import HELPFUL_COUNT,AUTHOR_TIER,AUTHOR_PROFILE
from ..services.study_posts import REFERENCE_VISIBLE
from ..services import community_people
from .study_posts import router as study_router
router=APIRouter(prefix='/api/community',tags=['community'])
router.include_router(study_router)

@router.get('/feed',response_model=CommunityFeedResponse)
async def community_feed(user_id:Annotated[str,Depends(current_user)],response:Response,
 tab:Literal['for-you','following','mcqs','doubts','questions','materials']='for-you',
 discussion:Literal['all','doubts','unanswered']='all',
 shelf_id:str|None=Query(None,max_length=100),
 limit:int=Query(20,ge=1,le=50),offset:int=Query(0,ge=0,le=100000),exam_scope:ExamScope=DEFAULT_SCOPE,
 content_version:Annotated[int,Query(ge=1,le=2)]=1,request:Request=None):
    response.headers['Cache-Control']='private, no-store'
    # Old web/native clients keep the question-only response contract. No native
    # capability or write route is widened as a side effect of a new post kind.
    if content_version==2 and request and getattr(request.state,'mobile_session',None):
        raise HTTPException(403,'Study-note feeds are available on the website')
    if tab in {'mcqs','materials'}:
        return CommunityFeedResponse(tab=tab,available=False,message='Open the dedicated creator publications, community questions or material catalog.')
    params={'user':user_id,'discussion':'doubts' if tab=='doubts' else discussion,'following':tab=='following',
      'study':content_version==2 and tab in {'for-you','following'} and discussion=='all',
      'scope':exam_scope,'shelf':shelf_id,'limit':limit+1,'offset':offset}
    async with cursor() as cur:
        await cur.execute(f"""SELECT u.avatar,p.id,q.id AS question_id,q.question,p.kind,p.body,p.content_version,p.edited_at,t.label AS topic_label,
          p.source_context->'study_reference' AS study_reference,
          CASE WHEN p.kind='material-share' THEN jsonb_build_object('kind','material','id',m.id,'label',mr.payload->>'title',
            'url','/materials/'||m.id,'access',mr.payload->>'access','format',mr.payload->>'kind') END AS material,
          CASE WHEN p.author_id='team' THEN 'India Study Map' ELSE COALESCE(u.handle,'Learner') END AS author,
          'Learner'::text AS author_role,{AUTHOR_TIER} AS author_tier,{AUTHOR_PROFILE} AS author_profile_id,p.created_at,p.pinned,{HELPFUL_COUNT} AS helpful,
          (SELECT r.body FROM posts r WHERE r.parent_id=p.id AND r.accepted AND NOT r.hidden
           AND NOT r.needs_approval AND NOT r.before_fix
           AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%(user)s AND b.blocked_id=r.author_id) OR (b.user_id=r.author_id AND b.blocked_id=%(user)s)) LIMIT 1) AS accepted_answer,
          (SELECT r.edited_at FROM posts r WHERE r.parent_id=p.id AND r.accepted AND NOT r.hidden
           AND NOT r.needs_approval AND NOT r.before_fix
           AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%(user)s AND b.blocked_id=r.author_id) OR (b.user_id=r.author_id AND b.blocked_id=%(user)s)) LIMIT 1) AS accepted_answer_edited_at,
          COALESCE(p.source_context->>'exam_name',(SELECT pp.exam_name FROM appearances a JOIN papers pp ON pp.id=a.paper_id WHERE a.canonical_id=q.id ORDER BY a.is_primary DESC,pp.year DESC NULLS LAST,a.id LIMIT 1)) AS source_context
          FROM posts p LEFT JOIN canonical_questions q ON q.id=CASE WHEN p.kind IN ('study','material-share')
            THEN CASE WHEN p.source_context->'study_reference'->>'kind'='question' THEN p.source_context->'study_reference'->>'id' END
            ELSE p.canonical_id END AND q.status IN ('live','held')
          LEFT JOIN materials m ON m.id=p.material_id AND m.status='published'
          LEFT JOIN material_revisions mr ON mr.material_id=m.id AND mr.revision=m.published_revision
          LEFT JOIN users u ON u.id=p.author_id LEFT JOIN review_taxonomy t ON t.id=p.topic_tag
          WHERE p.parent_id IS NULL AND (p.kind IN ('doubt','explanation') OR (%(study)s AND p.kind IN ('study','material-share')))
          AND ((q.id IS NOT NULL AND {question_scope('q',exam_scope)}) OR (p.kind IN ('study','material-share') AND COALESCE(p.source_context->'study_reference'->>'kind','')<>'question'))
          AND (%(discussion)s NOT IN ('doubts','unanswered') OR p.kind='doubt')
          AND (p.kind<>'material-share' OR mr.material_id IS NOT NULL)
          AND (p.kind NOT IN ('study','material-share') OR {REFERENCE_VISIBLE})
          AND (NOT %(following)s OR EXISTS(SELECT 1 FROM creator_follows f JOIN creator_profiles cp ON cp.user_id=f.creator_id AND cp.public
            WHERE f.follower_id=%(user)s AND f.creator_id=p.author_id))
          AND (%(discussion)s<>'unanswered' OR NOT EXISTS(SELECT 1 FROM posts r WHERE r.parent_id=p.id
            AND NOT r.hidden AND NOT r.needs_approval AND NOT r.before_fix
            AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%(user)s AND b.blocked_id=r.author_id) OR (b.user_id=r.author_id AND b.blocked_id=%(user)s))))
          AND NOT p.hidden AND NOT p.needs_approval AND NOT p.before_fix
          AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%(user)s AND b.blocked_id=p.author_id) OR (b.user_id=p.author_id AND b.blocked_id=%(user)s))
          AND (q.id IS NULL OR (
            NOT EXISTS(SELECT 1 FROM mock_sessions m WHERE m.user_id=%(user)s AND m.submitted_at IS NULL AND q.id=ANY(m.question_ids))
            AND NOT EXISTS(SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id
              LEFT JOIN game_cups cup ON cup.id=gr.cup_id WHERE gm.user_id=%(user)s
              AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
              AND gr.questions @> jsonb_build_array(jsonb_build_object('id',q.id)))
            AND (EXISTS(SELECT 1 FROM attempts a WHERE a.user_id=%(user)s AND a.canonical_id=q.id)
              OR EXISTS(SELECT 1 FROM answer_reveals ar WHERE ar.user_id=%(user)s AND ar.canonical_id=q.id)
              OR ((q.status='held' OR q.source_defect IN ('duplicate-options','unresolved-source') OR q.type<>'mcq' OR q.answer_text IS NULL
                OR (SELECT count(*) FROM jsonb_array_elements_text(COALESCE(q.options,'[]'::jsonb)) opt WHERE opt=q.answer_text)<>1)
               AND EXISTS(SELECT 1 FROM discussion_disclosures d WHERE d.user_id=%(user)s AND d.canonical_id=q.id)))))
          AND (%(shelf)s::text IS NULL OR EXISTS(SELECT 1 FROM library_shelves s WHERE s.active AND s.id=%(shelf)s AND
            (p.topic_tag=ANY(s.match_ids) OR EXISTS(SELECT 1 FROM v_question_paths path WHERE path.question_id=q.id
              AND (path.subject_id=ANY(s.match_ids) OR path.topic_id=ANY(s.match_ids) OR path.subtopic_id=ANY(s.match_ids))))))
          ORDER BY CASE WHEN %(following)s THEN false ELSE p.pinned END DESC,p.created_at DESC,p.id DESC LIMIT %(limit)s OFFSET %(offset)s""",params)
        rows=await cur.fetchall()
    message='No visible posts from followed creators yet. Follow a public creator; linked question conversations unlock after you check or show their answer.' if tab=='following' else 'No unanswered doubts among the questions you have unlocked. Try All discussions, or answer more questions to join their conversations.' if discussion=='unanswered' else 'Share a study note, or open a question and join its conversation.' if content_version==2 else 'Open a question, answer it and ask a doubt. Published discussions appear here after you unlock that question.'
    return CommunityFeedResponse(tab=tab,available=True,items=[CommunityFeedItem(**row) for row in rows[:limit]],has_more=len(rows)>limit,message=message if not rows else None)


@router.get('/standing')
async def own_community_standing(request:Request,response:Response,user:Annotated[str,Depends(require_account)]):
    response.headers['Cache-Control']='private, no-store'
    if getattr(request.state,'mobile_session',None):raise HTTPException(403,'Community standing is available on the website')
    async with cursor() as cur:return await community_people.own_standing(cur,user)


@router.get('/guides')
async def weekly_guides(request:Request,response:Response,user:Annotated[str,Depends(current_user)]):
    response.headers['Cache-Control']='private, no-store'
    if getattr(request.state,'mobile_session',None):raise HTTPException(403,'Community Guides are available on the website')
    async with cursor() as cur:return await community_people.guides(cur,user)


@router.get('/submissions')
async def my_submissions(request:Request,response:Response,user:Annotated[str,Depends(require_account)],offset:int=Query(0,ge=0,le=10000),limit:int=Query(20,ge=1,le=50)):
    response.headers['Cache-Control']='private, no-store'
    if getattr(request.state,'mobile_session',None):raise HTTPException(403,'The submission tracker is available on the website')
    from ..services.submissions import tracker
    async with cursor() as cur:return await tracker(cur,user,offset,limit)
