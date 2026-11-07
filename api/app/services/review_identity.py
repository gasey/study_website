import hashlib
import hmac
from dataclasses import dataclass
from fastapi import HTTPException, Request
from ..config import settings
from ..db import cursor

@dataclass
class Actor:
    id: str
    csrf: str
    recent: bool
    mfa_verified: bool = False

async def _identity(request: Request, require_staff_mfa: bool) -> Actor:
    token=request.cookies.get('ism_session')
    if not token: raise HTTPException(401,'Sign in to contribute')
    from .account_identity import account_session
    row = await account_session(request)
    if not row: raise HTTPException(401,'Your session has expired')
    csrf=hashlib.sha256(('bank-review:'+token).encode()).hexdigest()
    if request.method not in {'GET','HEAD','OPTIONS'}:
        if request.headers.get('origin') != settings.public_origin:
            raise HTTPException(403,'A same-origin request is required')
        if not hmac.compare_digest(request.headers.get('x-review-csrf',''),csrf):
            raise HTTPException(403,'Refresh the page before saving')
        async with cursor() as cur:
            # Atomic limit persisted independently of a later rejected mutation.
            await cur.execute("""INSERT INTO review_rate_buckets(bucket,count,expires_at)
                VALUES (%s,1,date_trunc('minute',now())+interval '1 minute')
                ON CONFLICT(bucket) DO UPDATE SET count=CASE WHEN review_rate_buckets.expires_at<=now() THEN 1 ELSE review_rate_buckets.count+1 END,
                expires_at=CASE WHEN review_rate_buckets.expires_at<=now() THEN date_trunc('minute',now())+interval '1 minute' ELSE review_rate_buckets.expires_at END
                RETURNING count""",('write:'+row['user_id'],))
            count=(await cur.fetchone())['count']
        if count>60: raise HTTPException(429,'Too many changes. Try again in one minute.',headers={'Retry-After':'60'})
    from .mfa import staff_required
    if require_staff_mfa and staff_required(row['user_id']) and request.method not in {'GET','HEAD','OPTIONS'} and not request.url.path.startswith('/api/auth/mfa/'):
        async with cursor() as cur:
            await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL LIMIT 1',(row['user_id'],))
            staff=bool(await cur.fetchone())
        if staff and not row['mfa_verified']:raise HTTPException(403,'Verify your authenticator in Account security before changing reviewed bank content')
    return Actor(row['user_id'],csrf,row['recent'],bool(row['mfa_verified']))

async def identity(request: Request) -> Actor:
    return await _identity(request, require_staff_mfa=True)

async def inbox_identity(request: Request) -> Actor:
    # Reading one's own Inbox/preferences is not a privileged bank mutation.
    # Session, origin, CSRF, account binding and write limits still apply.
    return await _identity(request, require_staff_mfa=False)

async def grants(cur, actor_id, subject=None, lock=False):
    await cur.execute("SELECT role,subject_id FROM review_grants WHERE user_id=%s AND revoked_at IS NULL"+(' FOR SHARE' if lock else ''),(actor_id,))
    return [g['role'] for g in await cur.fetchall() if g['subject_id'] is None or g['subject_id']==subject]

async def require_role(cur, actor_id, subject=None, roles=('owner','senior','reviewer'), lock=True):
    found=await grants(cur,actor_id,subject,lock)
    if not set(found)&set(roles): raise HTTPException(403,'This action needs an explicitly assigned permission in this subject')
    return found
