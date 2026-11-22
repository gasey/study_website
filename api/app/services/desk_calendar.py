"""A live, explicitly shared projection of central calendar entries. No new store."""
from . import owned_calendar,audience


async def consent(cur,did,user):
    from ..routers.study_desks import enabled,member,unrestricted
    enabled()
    row=await member(cur,did,user)
    await unrestricted(cur,user)
    return row['joined_at']


async def view(cur,did,user,start,end):
    from ..routers.study_desks import enabled,member
    enabled()
    await member(cur,did,user)
    await cur.execute('''SELECT e.*,u.handle AS author FROM calendar_entries e
      JOIN study_desk_members m ON m.desk_id=e.desk_id AND m.user_id=e.user_id
       AND m.left_at IS NULL AND m.joined_at=e.desk_joined_at
      JOIN users u ON u.id=e.user_id AND u.closed_at IS NULL
      WHERE e.desk_id=%s AND (e.date BETWEEN %s AND %s OR e.recurrence IS NOT NULL AND e.date<=%s)
       AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
        (b.user_id=%s AND b.blocked_id=e.user_id) OR (b.user_id=e.user_id AND b.blocked_id=%s))
      AND '''+audience.subject_sql('e.user_id')+''' ORDER BY e.date,e.id LIMIT 3001''',(did,start,end,end,user,user))
    rows=await cur.fetchall()
    projected=[]
    today=owned_calendar.india_today()
    for row in rows[:3000]:
        for item in owned_calendar.occurrences([row],start,end,today):
            projected.append(item|{'author':row['author'],'is_you':row['user_id']==user,
              'days_until':(item['day']-today).days})
    return {'occurrences':sorted(projected,key=lambda x:(x['day'],x['id'])),
            'limited':len(rows)>3000,'start':start,'end':end}
