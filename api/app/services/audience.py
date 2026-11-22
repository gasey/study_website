"""Age declaration boundary; never treat a declaration as guardian verification."""
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from ..config import settings
from ..db import cursor
from .account_identity import digest
from contextvars import ContextVar

mutation_actor = ContextVar('finna_audience_mutation_actor', default=None)

COOKIE = 'finna_audience'
MESSAGE = 'Finna is for people aged 18 or over. Confirm your age category at /account/privacy before saving study progress. Under-18 enrollment is not supported.'


def eligible_sql(user_expression):
    """Internal SQL expressions only; never pass request values here."""
    if not settings.audience_gate_enabled:return 'TRUE'
    return ("EXISTS(SELECT 1 FROM account_audience audience_gate WHERE audience_gate.user_id="
            +user_expression+" AND audience_gate.category='adult')")


def subject_sql(user_expression, *, team=False):
    """Public/shared subject visibility, evaluated when each query is built.

    Internal expressions only. The reserved team attribution is content, never
    a substitute adult declaration for an ordinary learner account.
    """
    if '.' not in user_expression:raise ValueError('Subject expressions must name a qualified column')
    if not settings.audience_gate_enabled:return 'TRUE'
    active=("EXISTS(SELECT 1 FROM users audience_subject WHERE audience_subject.id="
            +user_expression+" AND audience_subject.email IS NOT NULL AND audience_subject.closed_at IS NULL AND "
            +eligible_sql('audience_subject.id')+")")
    return '('+user_expression+"='team' OR "+active+')' if team else active


async def eligible(cur, user):
    # Callers delivering private data hold the users row lock first. The
    # following statement then observes a declaration committed while waiting.
    if not settings.audience_gate_enabled:return True
    await cur.execute("SELECT category FROM account_audience WHERE user_id=%s",(user,))
    row=await cur.fetchone()
    return bool(row and row['category']=='adult')


async def calendar_publication_lock(cur, *, restricting=False):
    # Calendar notifications use set-based inserts without user row locks.
    # Serialize their short publication transaction with age restrictions.
    # This lock precedes any users row lock in the declaration path.
    if not settings.audience_gate_enabled:return
    function='pg_advisory_xact_lock' if restricting else 'pg_advisory_xact_lock_shared'
    await cur.execute('SELECT '+function+"(hashtextextended('audience-calendar-publication-v1',0))")


async def learning_processing_lock(cur, user, *, restricting=False):
    # Acquire before job/reward/user row locks. A worker skips busy accounts;
    # a restriction/closure waits for already-admitted processing to commit.
    # The key is private to this account, so other accounts can still proceed.
    if not settings.audience_gate_enabled:return True
    key='audience-learning-processing-v1:'+user
    if restricting:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(key,))
        return True
    await cur.execute('SELECT pg_try_advisory_xact_lock_shared(hashtextextended(%s,0)) AS claimed',(key,))
    return (await cur.fetchone())['claimed']


async def transfer_processing_admission(cur, account, guest):
    """Both subjects, before credential/target locks or mutable ownership writes."""
    if not settings.audience_gate_enabled:return
    for user in sorted({account,guest}):
        if not await learning_processing_lock(cur,user):
            raise HTTPException(409,'Progress transfer is busy. Retry after account processing finishes.')
    await cur.execute('''SELECT u.id FROM users u JOIN account_audience a ON a.user_id=u.id
      WHERE u.id=ANY(%s) AND u.closed_at IS NULL AND a.category='adult'
      AND (u.id<>%s OR u.email IS NOT NULL)''',([account,guest],account))
    if {row['id'] for row in await cur.fetchall()} != {account,guest}:
        raise HTTPException(403,MESSAGE)


async def browser_category(request):
    token = request.cookies.get(COOKIE, '')
    if not token:return None
    async with cursor() as cur:
        await cur.execute('SELECT category FROM audience_browser_flows WHERE token_hash=%s AND expires_at>now()', (digest(token),))
        row = await cur.fetchone()
    return row['category'] if row else None


async def require_browser(request):
    if settings.audience_gate_enabled and await browser_category(request) != 'adult':
        raise HTTPException(403, MESSAGE)


async def require_learner(user):
    if not settings.audience_gate_enabled:return
    async with cursor() as cur:
        await cur.execute('SELECT category FROM account_audience WHERE user_id=%s', (user,))
        row = await cur.fetchone()
    if not row or row['category'] != 'adult':raise HTTPException(403, MESSAGE)


async def bind_adult(cur, user):
    # An existing under-18 declaration cannot be overwritten by a new browser.
    await cur.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult') ON CONFLICT DO NOTHING", (user,))
    await cur.execute('SELECT category FROM account_audience WHERE user_id=%s', (user,))
    if (await cur.fetchone())['category'] != 'adult':raise HTTPException(403, MESSAGE)


async def check_before_commit(cur):
    # Recheck inside each mutation transaction after its writes, before commit.
    # The share lock serializes with a declaration change; a concurrently
    # restricted request rolls back instead of committing a stale admission.
    user=mutation_actor.get()
    if not settings.audience_gate_enabled or not user:return
    await cur.execute('SHOW transaction_read_only')
    if (await cur.fetchone())['transaction_read_only']=='on':return
    await cur.execute('SELECT category FROM account_audience WHERE user_id=%s FOR SHARE',(user,))
    row=await cur.fetchone()
    if not row or row['category']!='adult':raise HTTPException(403,MESSAGE)


class AudienceBoundary(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # These paths are available to restricted accounts so they can recover,
        # export, close, revoke sessions or contact the operator. Native access
        # still has its independent exact route allowlist.
        safe = request.url.path.startswith(('/api/account-privacy/', '/api/auth/', '/api/review-digest/unsubscribe')) or request.url.path in {
            '/api/review/session', '/api/me/account-tools', '/api/me/data-export',
            '/api/me/account-close', '/api/me/account-signout-all', '/api/mobile/logout',
        }
        if request.url.path=='/api/auth/guest-progress/save':safe=False
        request.state.audience_safe=safe
        actor=None
        if settings.audience_gate_enabled and request.url.path.startswith('/api/') and not safe:
            from .account_identity import account_session
            mobile = getattr(request.state, 'mobile_session', None)
            session = mobile or await account_session(request)
            if session:
                try:await require_learner(session['user_id'])
                except HTTPException as exc:
                    return JSONResponse({'detail':exc.detail},status_code=exc.status_code,
                                        headers={'Cache-Control':'private, no-store'})
                if request.method not in {'GET','HEAD','OPTIONS'}:actor=session['user_id']
        token=mutation_actor.set(actor)
        try:return await call_next(request)
        finally:mutation_actor.reset(token)
