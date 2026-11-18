"""Account identity edits and moderation-aware creator bio, using existing stores."""
import re
from fastapi import HTTPException
from psycopg.types.json import Jsonb

RESERVED={'admin','administrator','moderator','owner','team','official','support','finna'}
PUBLIC_BIO="CASE WHEN NOT COALESCE(cp.bio_needs_approval,false) AND NOT COALESCE(cp.bio_hidden,false) THEN COALESCE(cp.bio,'') ELSE '' END"


async def read(cur,user):
    await cur.execute('''SELECT u.id AS user_id,u.name,u.handle,u.identity_version,
      u.handle_changed_at,u.handle_changed_at+interval '30 days' AS rename_available_at,
      COALESCE(cp.public,false) AS creator_public,COALESCE(cp.bio,'') AS bio,
      COALESCE(cp.bio_needs_approval,false) AS bio_needs_approval,COALESCE(cp.bio_hidden,false) AS bio_hidden
      FROM users u LEFT JOIN creator_profiles cp ON cp.user_id=u.id WHERE u.id=%s AND u.email IS NOT NULL''',(user,))
    return await cur.fetchone()


async def bio(cur,user,value):
    """Caller holds creator graph and user lock. Visibility changes never bypass this."""
    from ..routers.creators import event
    await cur.execute('SELECT * FROM creator_profiles WHERE user_id=%s FOR UPDATE',(user,))
    old=await cur.fetchone()
    if value==(old['bio'] if old else ''):return
    from .v5_release import require_writes
    require_writes()
    if len(value)>140:raise HTTPException(422,'Keep your bio to 140 characters')
    await cur.execute('SELECT count(*) AS n FROM posts WHERE author_id=%s AND NOT needs_approval AND NOT hidden',(user,))
    count=(await cur.fetchone())['n']
    pending=bool(value) and (bool(old and (old['bio_hidden'] or old['bio_needs_approval'])) or count<3)
    await cur.execute('''INSERT INTO creator_profiles(user_id,bio,bio_version,bio_needs_approval)
      VALUES(%s,%s,1,%s) ON CONFLICT(user_id) DO UPDATE SET bio=excluded.bio,
      bio_version=creator_profiles.bio_version+1,bio_needs_approval=excluded.bio_needs_approval,
      bio_hidden=false,updated_at=clock_timestamp() RETURNING bio_version''',(user,value,pending))
    version=(await cur.fetchone())['bio_version']
    await event(cur,user,'bio_saved',user,{'version':version,'bio':value,'needs_approval':pending})


async def save(cur,user,body):
    from .v5_release import require_writes
    require_writes()
    from ..routers.creators import graph_lock
    await graph_lock(cur)
    await cur.execute('SELECT handle,identity_version,handle_changed_at FROM users WHERE id=%s FOR UPDATE',(user,))
    old=await cur.fetchone()
    if old['identity_version']!=body.expected_version:
        raise HTTPException(409,'Your profile changed. Reload before saving.')
    handle=body.handle.strip().lower()
    changed=handle!=old['handle']
    if changed:
        if not re.fullmatch(r'[a-z][a-z0-9_-]{2,29}',handle) or handle in RESERVED or handle.startswith(('guest-','learner-')):
            raise HTTPException(422,'Choose 3–30 letters, numbers, underscores or hyphens, starting with a letter; system handles are reserved')
        await cur.execute("SELECT %s::timestamptz IS NOT NULL AND %s::timestamptz+interval '30 days'>clock_timestamp() AS cooling",(old['handle_changed_at'],old['handle_changed_at']))
        if (await cur.fetchone())['cooling']:raise HTTPException(409,'You can rename your handle once every 30 days')
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('handle:'+handle,))
        await cur.execute('SELECT 1 FROM users WHERE lower(handle)=%s AND id<>%s',(handle,user))
        if await cur.fetchone():raise HTTPException(409,'That handle is unavailable')
    await bio(cur,user,body.bio)
    await cur.execute('''UPDATE users SET name=%s,handle=%s,identity_version=identity_version+1,
      handle_changed_at=CASE WHEN %s THEN clock_timestamp() ELSE handle_changed_at END WHERE id=%s''',
      (body.name.strip() or None,handle,changed,user))
    if changed:
        await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'handle_changed',%s)",
                          (user,Jsonb({'previous':old['handle'],'handle':handle})))
    return await read(cur,user)
