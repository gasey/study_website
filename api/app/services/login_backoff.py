"""Persistent, independent account/IP sign-in backoff; no raw identifiers."""
import hashlib
import math
from fastapi import HTTPException
from ..db import cursor


def bucket(kind,value):
    return kind+':'+hashlib.sha256(value.encode()).hexdigest()


async def check(email,ip):
    keys=[bucket('account',email),bucket('ip',ip)]
    # Independent commit: neither invalid credentials nor a blocked response can
    # roll back the IP burst budget. Proxy headers are not trusted as an address.
    async with cursor() as cur:
        await cur.execute('''INSERT INTO review_rate_buckets(bucket,count,expires_at) VALUES(%s,1,now()+interval '1 minute')
          ON CONFLICT(bucket) DO UPDATE SET count=CASE WHEN review_rate_buckets.expires_at<=now() THEN 1 ELSE review_rate_buckets.count+1 END,
          expires_at=CASE WHEN review_rate_buckets.expires_at<=now() THEN now()+interval '1 minute' ELSE review_rate_buckets.expires_at END
          RETURNING count,GREATEST(1,extract(epoch FROM expires_at-now())) AS seconds''',('login-ip:'+keys[1],))
        budget=await cur.fetchone()
        await cur.execute('SELECT GREATEST(0,extract(epoch FROM max(blocked_until)-now())) AS seconds FROM auth_login_backoff WHERE bucket=ANY(%s)',(keys,))
        seconds=(await cur.fetchone())['seconds'] or 0
    if budget['count']>60:seconds=max(seconds,budget['seconds'])
    if seconds>0:
        raise HTTPException(429,'Too many sign-in attempts. Try again shortly or use password recovery.',headers={'Retry-After':str(math.ceil(seconds))})


async def failed(email,ip):
    async with cursor() as cur:
        for key,threshold in sorted([(bucket('account',email),5),(bucket('ip',ip),20)]):
            await cur.execute('''INSERT INTO auth_login_backoff(bucket,failures) VALUES(%s,1)
              ON CONFLICT(bucket) DO UPDATE SET failures=CASE WHEN auth_login_backoff.last_failed_at<now()-interval '15 minutes'
              THEN 1 ELSE auth_login_backoff.failures+1 END,last_failed_at=now() RETURNING failures''',(key,))
            failures=(await cur.fetchone())['failures']
            delay=min(900,2**min(10,failures-threshold)) if failures>=threshold else 0
            await cur.execute('UPDATE auth_login_backoff SET blocked_until=now()+%s*interval \'1 second\' WHERE bucket=%s',(delay,key))


async def clear_account(cur,email):
    # A valid login or a completed purpose-bound reset unlocks this account.
    # An IP's protection cannot be cleared by signing in to an unrelated account.
    await cur.execute('DELETE FROM auth_login_backoff WHERE bucket=%s',(bucket('account',email),))
