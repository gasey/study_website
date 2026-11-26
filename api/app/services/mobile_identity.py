"""Mobile credentials are learner-only, with an explicit method/path allowlist."""
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from ..db import cursor
from .account_identity import digest

PREFIX = 'ism_mobile_'
READ = (
    # Only public statistical reads; admin review is deliberately absent.
    r'/api/stats/(?:overview|sources|surveys(?:/[^/]+)?|metrics/[^/]+(?:/(?:releases|rankings))?)',
    r'/api/mobile/(?:taxonomy|contributions(?:/[^/]+)?|learning|billing|security)',
    r'/api/me/avatar',
    r'/api/tests(?:/(?:find|selection|[^/]+(?:/stats)?))?',
    r'/api/topic-trail',
    r'/api/mobile/(?:session|bookmarks(?:/[^/]+)?)',
    r'/api/questions(?:/[^/]+(?:/(?:practice-state|answer-comparison))?)?',
    r'/api/collections(?:/[^/]+(?:/(?:header|study-topics|paper-questions|paper-readiness))?)?',
    r'/api/me/(?:profile|progress|exam-progress|exam-bookmarks|mistakes|score-summary|home-preferences)',
    # Native filter UI can inspect its account's allowance before issuing a query.
    # The read is private; no new mobile mutation route is granted.
    r'/api/me/browse-allowance',
    # Learning projections remain private; practice writes negotiate separately.
    r'/api/me/(?:mastery|review-queue|focus-subjects|today|calendar-layers)',
    r'/api/contributions/summary',
    # Read-only Chronicle projection; its endpoint retains no_assessment.
    r'/api/learning-catalog/bank-dates',
    # Learner content and account-owned Inbox. No editorial/admin routes.
    r'/api/materials(?:/[^/]+)?',
    r'/api/studio/materials(?:/[^/]+)?',
    r'/api/creators(?:/[^/]+)?',
    r'/api/inbox/(?:notifications|preferences|threads|unread)',
    r'/api/inbox/threads/[^/]+/messages',
    r'/api/rewards/(?:me|history|leaderboard)', r'/api/scoring-facts',
    # Community reads. routers/discussions.py mounts /api/community/admin/* on
    # this same prefix; every pattern here anchors a literal segment after
    # /api/community/ so the moderation queue, post actions and question locks
    # are never matched.
    r'/api/community/feed',
    r'/api/community/(?:contributors|contributions)',
    r'/api/community/questions/[^/]+/discussion',
    r'/api/community/posts/[^/]+/(?:replies|evidence)',
    r'/api/study-sessions(?:/[^/]+)?',
    r'/api/mocks(?:/[^/]+)?',
    r'/api/games(?:/(?:exam-sections|join-preview|leaderboard|rooms/[^/]+))?',
    r'/api/blocks/(?:leaderboard|me)',
    # Private desks retain their existing membership and disclosure guards.
    # /api/desk/admin/* is never matched here.
    r'/api/desk/(?:personal|overview|questions|rooms)',
    r'/api/desk/rooms/[^/]+(?:/(?:items|messages))?',
)
WRITE = {
    # PATCH /me/profile only sets the display name (routers/me.py) and has no
    # cookie or origin coupling. POST /auth/password is deliberately absent: it
    # enforces _same_origin and revokes every auth_session, which would both
    # reject a native request and sign the mobile session out of itself.
    'PATCH': (r'/api/me/profile',r'/api/me/focus-subjects'),
    'POST': (r'/api/mobile/logout', r'/api/mobile/questions/[^/]+/(?:report|answer)',
             r'/api/review-sessions',
             r'/api/mobile/contributions(?:/[^/]+/(?:revisions|submit|withdraw))?',
             r'/api/mobile/learning(?:/[^/]+/decision)?',
             r'/api/mobile/security/revoke',
             r'/api/me/avatar',
             r'/api/topic-trail/(?:start|[^/]+/begin)',
             r'/api/materials/[^/]+/(?:reaction|report)',
             r'/api/studio/materials(?:/[^/]+/(?:save|submit))?',
             r'/api/creators/settings',
             r'/api/creators/[^/]+/(?:follow|block|report)',
             r'/api/inbox/(?:notifications/read-all|notifications/[0-9]+/read|preferences|threads/[^/]+/read)',
             r'/api/desk/rooms',
             r'/api/desk/rooms/[^/]+/(?:settings|invite|sharing|items|messages|leave|report)',
             r'/api/desk/invites/[^/]+',
             r'/api/desk/focus(?:/[^/]+)?',
             r'/api/rewards/daily-quests/[^/]+/claim',
             r'/api/rewards/redeem',
             r'/api/questions/[^/]+/answer',
             r'/api/study-sessions(?:/[^/]+/(?:answer|position|viewed|finish))?',
             r'/api/mocks(?:/[^/]+/submit)?',
             r'/api/games/(?:preview|rooms|join|rooms/[^/]+/(?:ready|start|answer|leave))',
             r'/api/blocks/runs(?:/[^/]+/(?:checkpoint|finish))?',
             # Community writes. Posting is rate-limited to 30/day and the first
             # three posts from a new author queue for moderation (discussions.py),
             # so the learner-only boundary still holds. /api/community/admin/* is
             # never matched. Reward visibility/cohort settings and streak-shield
             # purchases remain outside this learner surface.
             r'/api/community/questions/[^/]+/discussion(?:/open)?',
             r'/api/community/posts/[^/]+/(?:helpful|accept|report|withdraw)'),
    'PUT': (r'/api/mobile/bookmarks/[^/]+',r'/api/me/exam-bookmarks/[^/]+',r'/api/me/home-preferences',r'/api/mocks/[^/]+/answers'),
    'DELETE': (r'/api/mobile/bookmarks/[^/]+',r'/api/me/exam-bookmarks/[^/]+'),
}

def allowed(method, path):
    return any(re.fullmatch(p, path) for p in (READ if method in {'GET','HEAD'} else WRITE.get(method, ())))

# Desk sessions deliberately have no native capability: their new paths stay
# closed, and existing general game writes reject a Desk-bound room at runtime.
FEATURES = (
    ('referrals',(('GET','/api/referrals/me'),('POST','/api/referrals/code'))),
    ('review_digest',(('GET','/api/review-digest/preferences'),('POST','/api/review-digest/preferences'))),
    ('atlas',(('GET','/api/atlas/me/index'),('GET','/api/atlas/chronicle/date_example/links'),('GET','/api/atlas/chapters/rivers-of-india/chronicle'),('POST','/api/admin/atlas/district-proposals/example/draft'),('GET','/api/atlas/me/progress'),('POST','/api/atlas/drills/example/answer'),('GET','/api/atlas/chapters'),('GET','/api/atlas/chapters/rivers-of-india'),('POST','/api/admin/atlas/chapters/example/draft'),('GET','/api/atlas/chapters/rivers-of-india/bindings'),('GET','/api/atlas/questions/example/links'))),
    ('desk_calendar',(('GET','/api/desk/rooms/example/calendar'),)),
    # Notes/PDF and chat-link writes stay web-only pending an explicit contract.
    ('desk_notes',(('GET','/api/me/desk-notes-print'),
                   ('GET','/api/desk/rooms/example/notes/item'))),
    # Kept unadvertised until every Desk practice path is deliberately allowed.
    ('desk_practice',(('GET','/api/desk/rooms/example/practice'),
                      ('POST','/api/desk/rooms/example/practice'),
                      ('POST','/api/desk/rooms/example/practice/game/join'))),
    ('browse_allowance',(('GET','/api/me/browse-allowance'),)),
    ('mastery',(('GET','/api/me/mastery'),)),
    ('review_queue',(('GET','/api/me/review-queue'),)),
    ('focus_subjects_read',(('GET','/api/me/focus-subjects'),)),
    ('today',(('GET','/api/me/today'),)),
    ('calendar_layers',(('GET','/api/me/calendar-layers'),)),
    ('learning_habit',(('GET','/api/me/today'),('GET','/api/rewards/me'))),
    ('weekly_boards',(('GET','/api/rewards/leaderboard'),('GET','/api/games/leaderboard'))),
    ('weekly_recap',(('GET','/api/me/today'),)),
    ('review_sessions',(('POST','/api/review-sessions'),('GET','/api/study-sessions/example'))),
    ('review_answers',tuple(('POST','/api/study-sessions/example/'+action)
                           for action in ('answer','position','viewed','finish'))),
    ('focus_subjects_write',(('PATCH','/api/me/focus-subjects'),)),
)


def capabilities():
    """Only advertise features whose complete method/path surface is allowed."""
    return [name for name,paths in FEATURES if all(allowed(method,path) for method,path in paths)]


def require_capability(request, name):
    """An explicit client contract, in addition to normal identity/ownership.

    Old clients can still read a web-created review set but cannot mutate it
    through the general practice player without understanding the new contract.
    """
    if getattr(request.state,'mobile_session',None):
        if name not in capabilities() or request.headers.get('x-finna-capability')!=name:
            from fastapi import HTTPException
            raise HTTPException(403,'Update your app to use this study feature')

class MobileBoundary(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        auth = request.headers.get('authorization', '')
        scheme, _, token = auth.partition(' ')
        if scheme.lower() == 'bearer' and token.startswith(PREFIX):
            if request.cookies.get('ism_session') or not allowed(request.method, request.url.path):
                return JSONResponse({'detail':'Mobile credentials permit learner operations only'}, status_code=403)
            async with cursor() as cur:
                await cur.execute('''SELECT m.user_id,m.public_id,m.expires_at FROM mobile_sessions m
                  JOIN auth_sessions s ON s.token_hash=m.parent_session_hash AND s.user_id=m.user_id
                  JOIN users u ON u.id=m.user_id
                  WHERE m.token_hash=%s AND m.revoked_at IS NULL AND m.expires_at>now()
                  AND s.revoked_at IS NULL AND s.expires_at>now() AND u.email IS NOT NULL''', (digest(token),))
                session = await cur.fetchone()
            if not session:
                return JSONResponse({'detail':'Your mobile session has expired. Sign in again.'},status_code=401)
            request.state.mobile_session = session
            request.state.mobile_token_hash = digest(token)
        response = await call_next(request)
        if token.startswith(PREFIX):
            response.headers['Cache-Control'] = 'private, no-store'
        return response
