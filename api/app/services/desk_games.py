"""Membership/visibility adapter for ordinary frozen party games. No awards here."""
from fastapi import HTTPException
from ..config import settings
from . import games as g, game_selection as setup,audience


def web_write(request, room):
    if room.get('desk_id') and getattr(request.state, 'mobile_session', None):
        raise HTTPException(403, 'Desk practice controls are available on the website')


async def access(cur, room, user, joined_at=None):
    """Recheck current membership, its epoch, blocks and the exact frozen shares.

    Reads do not lock Desk rows after taking the game lock: Desk mutations never
    need a game lock, and lifecycle workers use this same adapter before scoring.
    """
    did = room.get('desk_id')
    if not did:
        return
    if not settings.study_desks_private_enabled:
        raise HTTPException(409, 'Private Desk practice is not open')
    await cur.execute('''SELECT m.joined_at FROM study_desk_members m
      JOIN study_desks d ON d.id=m.desk_id JOIN users u ON u.id=m.user_id
      WHERE m.desk_id=%s AND m.user_id=%s AND m.left_at IS NULL
      AND d.closed_at IS NULL AND u.closed_at IS NULL AND u.email IS NOT NULL AND '''+audience.subject_sql('d.owner_id')+' AND '+audience.subject_sql('m.user_id'), (did,user))
    member = await cur.fetchone()
    if not member or (joined_at is not None and member['joined_at'] > joined_at):
        raise HTTPException(404, 'Desk practice is unavailable or membership has ended')
    # Include departed players: results must not disclose a blocked identity.
    await cur.execute('''SELECT 1 FROM game_members p JOIN creator_blocks b
      ON (b.user_id=%s AND b.blocked_id=p.user_id) OR (b.blocked_id=%s AND b.user_id=p.user_id)
      WHERE p.room_id=%s''', (user,user,room['id']))
    if await cur.fetchone():
        raise HTTPException(403, 'Desk practice is unavailable due to a blocked participant')
    sources = room.get('selection_context', {}).get('desk_sources', [])
    if not sources:
        raise HTTPException(409, 'Desk practice has no shared source set')
    await cur.execute('''SELECT x.id,x.question_id FROM study_desk_items x
      JOIN study_desk_members m ON m.desk_id=x.desk_id AND m.user_id=x.author_id
       AND m.left_at IS NULL AND m.joined_at<=x.created_at
      JOIN users u ON u.id=x.author_id AND u.closed_at IS NULL
      WHERE x.desk_id=%s AND x.id=ANY(%s) AND x.deleted_at IS NULL
       AND x.kind IN ('question','bookmark') AND '''+audience.subject_sql('x.author_id')+''' AND NOT EXISTS(SELECT 1 FROM creator_blocks b
        WHERE (b.user_id=%s AND b.blocked_id=x.author_id) OR (b.blocked_id=%s AND b.user_id=x.author_id))''',
      (did,[s['item_id'] for s in sources],user,user))
    visible = {r['id']:r['question_id'] for r in await cur.fetchall()}
    if any(visible.get(s['item_id']) != s['question_id'] for s in sources):
        raise HTTPException(404, 'A question shared for this session is no longer available')


async def reconcile(cur, room, now):
    """Release revoked participants before the unchanged engine finalizes awards."""
    if not room.get('desk_id') or room['state'] not in ('waiting','running'):
        return room
    if not settings.study_desks_private_enabled:
        await g.release(cur,room,'cancelled',now)
        return await g.room(cur,room['id'])
    await cur.execute('SELECT user_id,joined_at FROM game_members WHERE room_id=%s AND left_at IS NULL ORDER BY user_id', (room['id'],))
    revoked = []
    for p in await cur.fetchall():
        try:
            await access(cur,room,p['user_id'],p['joined_at'])
        except HTTPException:
            revoked.append(p['user_id'])
    for user in revoked:
        await cur.execute('UPDATE game_members SET left_at=%s,released_at=%s WHERE room_id=%s AND user_id=%s', (now,now,room['id'],user))
        await g.event(cur,room['id'],user,'desk_access_ended')
    if revoked:
        await cur.execute('UPDATE game_rooms SET version=version+1 WHERE id=%s',(room['id'],))
        if room['state']=='waiting' and room['owner_id'] in revoked:
            await g.release(cur,room,'cancelled',now)
        room = await g.room(cur,room['id'])
    return room


async def preview(cur, did, user):
    # Only deliberate room question/bookmark shares; personal saves and consent-
    # based mistakes/updates are not silently copied into a multiplayer snapshot.
    await cur.execute('''SELECT DISTINCT ON(x.question_id) x.id,x.question_id
      FROM study_desk_items x JOIN study_desk_members m ON m.desk_id=x.desk_id
       AND m.user_id=x.author_id AND m.left_at IS NULL AND m.joined_at<=x.created_at
      JOIN users u ON u.id=x.author_id AND u.closed_at IS NULL
      WHERE x.desk_id=%s AND x.deleted_at IS NULL AND x.kind IN ('question','bookmark')
       AND x.question_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM creator_blocks b
        WHERE (b.user_id=%s AND b.blocked_id=x.author_id) OR (b.blocked_id=%s AND b.user_id=x.author_id))
       AND NOT EXISTS(SELECT 1 FROM mock_sessions s WHERE s.user_id=%s AND s.submitted_at IS NULL AND x.question_id=ANY(s.question_ids))
       AND NOT EXISTS(SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id
        LEFT JOIN game_cups c ON c.id=gr.cup_id WHERE gm.user_id=%s
        AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR c.closes_at>now())
        AND gr.questions @> jsonb_build_array(jsonb_build_object('id',x.question_id)))
      AND '''+audience.subject_sql('x.author_id')+''' ORDER BY x.question_id,x.id''',(did,user,user,user,user))
    shares = await cur.fetchall()
    ctx = await setup.resolve(cur,setup.Selection(kind='mixed'),'party')
    ctx |= {'desk_question_ids':[r['question_id'] for r in shares], 'desk_id':did,
            'label':'Desk shared questions'}
    rows = await setup.candidates(cur,ctx)
    ctx['pool_revision'] = g.digest([(r['id'],r['appearance_id'],r['eligibility_revision']) for r in rows])
    eligible = {r['id'] for r in rows}
    ctx['desk_sources'] = [{'item_id':r['id'],'question_id':r['question_id']} for r in shares if r['question_id'] in eligible]
    need = g.MODES['party'][0]; count = len(rows)
    return {'context':ctx,'context_hash':g.digest(ctx),'available':count,'required':need,
      'can_start':count>=need, 'capacity':g.MODES['party'][2], 'round_seconds':g.MODES['party'][1],
      'message':f'{count} shared questions with official keys are ready; a session needs {need}.'}


def public_preview(result):
    return {k:v for k,v in result.items() if k!='context'}
