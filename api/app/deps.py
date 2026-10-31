import re
import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, Response
import hashlib

from .db import cursor

# X-Device-Id remains a compatibility preference header only. Private guest
# history is owned by a random server-issued HttpOnly guest credential.
_DEVICE_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

DeviceId = Annotated[str | None, Header(alias="X-Device-Id")]


async def current_user(request: Request, response: Response, x_device_id: DeviceId = None) -> str:
    from .services.account_identity import account_session, guest_identity
    session = await account_session(request)
    if session:
        return session['user_id']
    if request.cookies.get('ism_session') and request.method not in {'GET','HEAD','OPTIONS'}:
        raise HTTPException(401, 'Your session has expired. Sign in again before saving.')
    return await guest_identity(request, response)


async def require_account(user_id: Annotated[str, Depends(current_user)]) -> str:
    async with cursor() as cur:
        await cur.execute("SELECT email FROM users WHERE id=%s", (user_id,))
        row = await cur.fetchone()
    if not row or not row.get("email"):
        raise HTTPException(401, "Sign in to continue")
    return user_id


async def admin_actor(authorization: Annotated[str | None, Header()] = None) -> str:
    """Require the separately provisioned owner token for moderation routes."""
    from .config import settings

    expected = settings.admin_token
    if not expected:
        raise HTTPException(503, "moderation admin is not configured")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(401, "valid admin bearer token required", headers={"WWW-Authenticate": "Bearer"})
    return "admin:site-owner"
