"""One plain-text announcement; no maintenance switch or write-freeze state."""
from fastapi import HTTPException
from psycopg.types.json import Jsonb


async def public(cur):
    await cur.execute('''SELECT CASE WHEN expires_at IS NULL OR expires_at>now() THEN message ELSE '' END AS message,
      expires_at,version FROM site_notice WHERE singleton''')
    row=await cur.fetchone()
    if not row:raise RuntimeError('Site notice setting missing')
    return row


async def setting(cur):
    await cur.execute('SELECT message,expires_at,version,updated_at FROM site_notice WHERE singleton')
    row=await cur.fetchone()
    if not row:raise RuntimeError('Site notice setting missing')
    return row


async def save(cur,actor,body):
    await cur.execute('SELECT message,expires_at,version FROM site_notice WHERE singleton FOR UPDATE')
    old=await cur.fetchone()
    if not old:raise HTTPException(503,'Site notice setting is unavailable')
    if old['version']!=body.expected_version:raise HTTPException(409,'Site notice changed. Reload before saving')
    await cur.execute('SELECT now() AS now');now=(await cur.fetchone())['now']
    message=body.message.strip();expires=body.expires_at if message else None
    if expires and expires<=now:raise HTTPException(422,'Choose a future expiry time')
    await cur.execute('''UPDATE site_notice SET message=%s,expires_at=%s,version=version+1,
      updated_by=%s,updated_at=now() WHERE singleton RETURNING message,expires_at,version,updated_at''',(message,expires,actor))
    saved=await cur.fetchone()
    def encode(row):return {k:v.isoformat() if hasattr(v,'isoformat') else v for k,v in row.items()}
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'owner_site_notice_set',%s)",
      (actor,Jsonb({'before':encode(old),'after':encode(saved)})))
    return saved
