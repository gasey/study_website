"""Public standing is consented; exact post counts retain viewer disclosure gates."""
from .community_policy import VALID_VOTE,TIERS,policy
from .study_posts import REFERENCE_VISIBLE

VISIBLE_STATS="""
 WITH candidates AS (
   SELECT child.id,child.author_id,child.accepted,child.kind,child.canonical_id,
     COALESCE(parent.source_context,child.source_context) AS source_context
   FROM posts child LEFT JOIN posts parent ON parent.id=child.parent_id
   WHERE child.author_id=ANY(%(authors)s) AND NOT child.hidden AND NOT child.needs_approval AND NOT child.before_fix
   AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
     (b.user_id=%(user)s AND b.blocked_id=child.author_id) OR (b.user_id=child.author_id AND b.blocked_id=%(user)s))
   AND (child.parent_id IS NULL OR (parent.id IS NOT NULL AND NOT parent.hidden AND NOT parent.needs_approval
     AND NOT parent.before_fix AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
       (b.user_id=%(user)s AND b.blocked_id=parent.author_id) OR (b.user_id=parent.author_id AND b.blocked_id=%(user)s))))
 ), visible AS (
   SELECT p.* FROM candidates p LEFT JOIN canonical_questions q ON q.id=COALESCE(p.canonical_id,
     CASE WHEN p.source_context->'study_reference'->>'kind'='question' THEN p.source_context->'study_reference'->>'id' END)
   WHERE (p.canonical_id IS NULL AND COALESCE(p.source_context->'study_reference'->>'kind','')<>'question' OR q.id IS NOT NULL)
   AND (q.id IS NULL OR (q.status IN ('live','held')
     AND NOT EXISTS(SELECT 1 FROM mock_sessions ms WHERE ms.user_id=%(user)s AND ms.submitted_at IS NULL AND q.id=ANY(ms.question_ids))
     AND NOT EXISTS(SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id LEFT JOIN game_cups cup ON cup.id=gr.cup_id
       WHERE gm.user_id=%(user)s AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
       AND gr.questions @> jsonb_build_array(jsonb_build_object('id',q.id)))
     AND (EXISTS(SELECT 1 FROM attempts a WHERE a.user_id=%(user)s AND a.canonical_id=q.id)
       OR EXISTS(SELECT 1 FROM answer_reveals ar WHERE ar.user_id=%(user)s AND ar.canonical_id=q.id)
       OR ((q.status='held' OR q.source_defect IN ('duplicate-options','unresolved-source') OR q.type<>'mcq' OR q.answer_text IS NULL
         OR (SELECT count(*) FROM jsonb_array_elements_text(COALESCE(q.options,'[]'::jsonb)) opt WHERE opt=q.answer_text)<>1)
         AND EXISTS(SELECT 1 FROM discussion_disclosures d WHERE d.user_id=%(user)s AND d.canonical_id=q.id)))))
   AND """+REFERENCE_VISIBLE+"""
   AND (COALESCE(p.source_context->'study_reference'->>'kind','')<>'material' OR EXISTS(
     SELECT 1 FROM materials m JOIN material_revisions r ON r.material_id=m.id AND r.revision=m.published_revision
     WHERE m.id=p.source_context->'study_reference'->>'id' AND m.status='published'))
 )
 SELECT p.author_id,count(*) FILTER(WHERE p.accepted AND p.kind='reply')::int AS accepted_answers,
   COALESCE(sum(v.helpful),0)::int AS helpful_count,
   COALESCE(sum(v.weekly_helpful),0)::int AS weekly_helpful,
   COALESCE(sum(v.weekly_weighted),0)::float AS weekly_weighted
 FROM visible p LEFT JOIN LATERAL (
   SELECT count(*)::int AS helpful,
     count(*) FILTER(WHERE v.created_at>=date_trunc('week',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')::int AS weekly_helpful,
     COALESCE(sum(CASE WHEN (SELECT count(*) FROM (SELECT 1 FROM attempts a WHERE a.user_id=v.user_id
       AND a.correct IS NOT NULL AND a.canonical_id IS NOT NULL LIMIT 50) scored)=50 THEN 1.0 ELSE 0.25 END)
       FILTER(WHERE v.created_at>=date_trunc('week',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata'),0) AS weekly_weighted
   FROM post_votes v WHERE v.post_id=p.id AND v.created_at<=now() AND """+VALID_VOTE+"""
 ) v ON true GROUP BY p.author_id
"""

async def visible_stats(cur,authors,viewer):
    if not authors:return {}
    await cur.execute(VISIBLE_STATS,{'authors':authors,'user':viewer,'scope':'all'})
    return {row['author_id']:row for row in await cur.fetchall()}

def counts(stats):
    return {key:stats.get(key,0) for key in ('helpful_count','accepted_answers','weekly_helpful')}

async def profile_standing(cur,author,viewer):
    await cur.execute('SELECT community_display_tier_rank(%s) AS rank',(author,));tier=TIERS[(await cur.fetchone())['rank']]
    stats=(await visible_stats(cur,[author],viewer)).get(author,{})
    return {'display_tier':tier,**counts(stats),'counts_scope':'Published posts visible to you'}

async def own_standing(cur,user):
    state=await policy(cur,user)
    await cur.execute('''SELECT COALESCE(cp.public,false) AS creator_public,COALESCE(rp.board_public,false) AS board_public
      FROM users u LEFT JOIN creator_profiles cp ON cp.user_id=u.id LEFT JOIN reward_profiles rp ON rp.user_id=u.id WHERE u.id=%s''',(user,))
    consent=await cur.fetchone()
    return {**await profile_standing(cur,user,user),**consent,**{key:state.get(key) for key in
      ('weighted_helpful','tier','privileges_restricted','mentor_eligible','can_create','post_limit','reply_limit')}}

async def guides(cur,viewer):
    # Existing public-profile consent and weekly-board opt-in both apply. A
    # display-only retained Guide label does not override current eligibility.
    await cur.execute('''SELECT u.id,u.handle,u.avatar FROM users u JOIN creator_profiles cp ON cp.user_id=u.id AND cp.public
      JOIN reward_profiles rp ON rp.user_id=u.id AND rp.board_public
      WHERE u.email IS NOT NULL AND community_weighted_helpful(u.id)>=150
      AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=u.id) OR (b.user_id=u.id AND b.blocked_id=%s))
      ORDER BY u.id''',(viewer,viewer));candidates=await cur.fetchall()
    eligible=[]
    for author in candidates:
        state=await policy(cur,author['id'])
        if not state['privileges_restricted']:eligible.append(author)
    stats=await visible_stats(cur,[author['id'] for author in eligible],viewer)
    items=[{**author,**counts(stats[author['id']]),'display_tier':'Guide','_weight':stats[author['id']]['weekly_weighted']}
      for author in eligible if stats.get(author['id'],{}).get('weekly_helpful',0)>0]
    items.sort(key=lambda item:(-item['_weight'],-item['weekly_helpful'],item['id']))
    for item in items:item.pop('_weight')
    await cur.execute("SELECT date_trunc('week',now() AT TIME ZONE 'Asia/Kolkata')::date AS week_start,(date_trunc('week',now() AT TIME ZONE 'Asia/Kolkata')+interval '6 days')::date AS week_end,now() AS as_of")
    return {**await cur.fetchone(),'items':items[:6],'counts_scope':'Published posts visible to you'}
