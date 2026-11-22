"""Prospective game processing restrictions; existing choices/history stay."""
from ..config import settings
from . import audience

ENDED='audience_access_ended'


class _BusyParticipant(Exception):
    pass


async def reconcile(cur,room,now):
    """Caller owns the room lock. None means retry without advancing clocks.

    Shared account leases precede every job/reward/user lock. Restrictions and
    closure already take their exclusive counterparts before those same locks.
    A failed nonblocking claim rolls back the whole admission savepoint.
    """
    if not settings.audience_gate_enabled or room['state'] not in ('waiting','running'):return room
    from . import games
    try:
        async with cur.connection.transaction():
            await cur.execute('''SELECT m.user_id FROM game_members m WHERE m.room_id=%s
              AND NOT EXISTS(SELECT 1 FROM game_events e WHERE e.room_id=m.room_id
                AND e.actor_id=m.user_id AND e.action='audience_access_ended') ORDER BY m.user_id''',(room['id'],))
            revoked=[]
            for player in await cur.fetchall():
                user=player['user_id']
                if not await audience.learning_processing_lock(cur,user):raise _BusyParticipant
                # New statement after the lease: observe a declaration/closure
                # that committed after the initial room/member selection.
                await cur.execute('''SELECT 1 FROM users u WHERE u.id=%s AND u.email IS NOT NULL
                  AND u.closed_at IS NULL AND '''+audience.eligible_sql('u.id'),(user,))
                if not await cur.fetchone():revoked.append(user)
            for user in revoked:
                await cur.execute('''UPDATE game_members SET left_at=COALESCE(left_at,%s),
                  released_at=COALESCE(released_at,%s),public_result=false,ready=false
                  WHERE room_id=%s AND user_id=%s''',(now,now,room['id'],user))
                await games.event(cur,room['id'],user,ENDED)
            if revoked:
                await cur.execute('UPDATE game_rooms SET version=version+1 WHERE id=%s',(room['id'],))
                if room['state']=='waiting' and room['owner_id'] in revoked:
                    await games.release(cur,room,'cancelled',now)
                room=await games.room(cur,room['id'])
            return room
    except _BusyParticipant:
        return None


def pending_sql():
    """Internal worker predicate; no new sweep work when the flag is off."""
    if not settings.audience_gate_enabled:return ''
    return ''' OR (state IN ('waiting','running') AND EXISTS(
      SELECT 1 FROM game_members gm JOIN users u ON u.id=gm.user_id
      WHERE gm.room_id=game_rooms.id AND gm.left_at IS NULL
      AND (u.closed_at IS NOT NULL OR u.email IS NULL OR NOT '''+audience.eligible_sql('u.id')+''')))'''
