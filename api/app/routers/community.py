"""Published question topics in the feed; thread answer and privacy gates apply."""
from ..exam_scope import ExamScope, DEFAULT_SCOPE, pool_view, scope_condition, question_scope
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Query, Response
from ..db import cursor
from ..deps import current_user
from ..schemas import CommunityFeedItem, CommunityFeedResponse
router=APIRouter(prefix='/api/community',tags=['community'])

@router.get('/feed',response_model=CommunityFeedResponse)
async def community_feed(user_id:Annotated[str,Depends(current_user)],response:Response,
 tab:Literal['for-you','following','mcqs','doubts','questions','materials']='for-you',
 discussion:Literal['all','doubts','unanswered']='all',
 shelf_id:str|None=Query(None,max_length=100),
 limit:int=Query(20,ge=1,le=50),offset:int=Query(0,ge=0,le=100000), exam_scope: ExamScope = DEFAULT_SCOPE):
    response.headers['Cache-Control']='private, no-store'
    if tab in {'following','mcqs','materials'}:
        return CommunityFeedResponse(tab=tab,available=False,message='Open the dedicated creator publications, community questions or material catalog.')
    async with cursor() as cur:
        await cur.execute(f"""SELECT u.avatar,p.id,p.canonical_id AS question_id,q.question,p.kind,p.body,
          CASE WHEN p.author_id='team' THEN 'India Study Map' ELSE COALESCE(u.handle,'Learner') END AS author,
          'Learner'::text AS author_role,p.created_at,p.pinned,
          (SELECT count(*)::int FROM post_votes v WHERE v.post_id=p.id) AS helpful,
          (SELECT r.body FROM posts r WHERE r.parent_id=p.id AND r.accepted AND NOT r.hidden
           AND NOT r.needs_approval AND NOT r.before_fix
           AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=r.author_id) OR (b.user_id=r.author_id AND b.blocked_id=%s)) LIMIT 1) AS accepted_answer,
          COALESCE(p.source_context->>'exam_name',(SELECT pp.exam_name FROM appearances a JOIN papers pp ON pp.id=a.paper_id WHERE a.canonical_id=p.canonical_id ORDER BY a.is_primary DESC,pp.year DESC NULLS LAST,a.id LIMIT 1)) AS source_context
          FROM posts p JOIN canonical_questions q ON q.id=p.canonical_id AND q.status IN ('live','held') LEFT JOIN users u ON u.id=p.author_id
          WHERE {question_scope('q', exam_scope)} AND p.parent_id IS NULL AND p.kind IN ('doubt','explanation') AND (%s NOT IN ('doubts','unanswered') OR p.kind='doubt')
          AND (%s<>'unanswered' OR NOT EXISTS(SELECT 1 FROM posts r WHERE r.parent_id=p.id
            AND NOT r.hidden AND NOT r.needs_approval AND NOT r.before_fix
            AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=r.author_id) OR (b.user_id=r.author_id AND b.blocked_id=%s))))
          AND NOT p.hidden AND NOT p.needs_approval AND NOT p.before_fix
          AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=p.author_id) OR (b.user_id=p.author_id AND b.blocked_id=%s))
          AND NOT EXISTS(SELECT 1 FROM mock_sessions m WHERE m.user_id=%s AND m.submitted_at IS NULL AND p.canonical_id=ANY(m.question_ids))
          AND NOT EXISTS(SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id
            LEFT JOIN game_cups cup ON cup.id=gr.cup_id WHERE gm.user_id=%s
            AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
            AND gr.questions @> jsonb_build_array(jsonb_build_object('id',p.canonical_id)))
          AND (EXISTS(SELECT 1 FROM attempts a WHERE a.user_id=%s AND a.canonical_id=p.canonical_id)
            OR ((q.type<>'mcq' OR q.answer_text IS NULL OR NOT q.options @> jsonb_build_array(q.answer_text))
             AND EXISTS(SELECT 1 FROM discussion_disclosures d WHERE d.user_id=%s AND d.canonical_id=p.canonical_id)))
          AND (%s::text IS NULL OR EXISTS(SELECT 1 FROM library_shelves s JOIN v_question_paths t ON t.question_id=p.canonical_id WHERE s.active AND s.id=%s AND (t.subject_id=ANY(s.match_ids) OR t.topic_id=ANY(s.match_ids) OR t.subtopic_id=ANY(s.match_ids))))
          ORDER BY p.pinned DESC,p.created_at DESC,p.id DESC LIMIT %s OFFSET %s""",
          (user_id,user_id,'doubts' if tab=='doubts' else discussion,discussion,user_id,user_id,user_id,user_id,user_id,user_id,user_id,user_id,shelf_id,shelf_id,limit+1,offset))
        rows=await cur.fetchall()
    return CommunityFeedResponse(tab=tab,available=True,items=[CommunityFeedItem(**r) for r in rows[:limit]],has_more=len(rows)>limit,
      message=('No unanswered doubts among the questions you have unlocked. Try All discussions, or answer more questions to join their conversations.' if discussion=='unanswered' else 'Open a question, answer it and ask a doubt. Published discussions appear here after you unlock that question.') if not rows else None)
