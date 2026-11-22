"""Account-owned consent and limited signed-out unsubscribe capability."""
import json
import logging
import re
from urllib.parse import parse_qs
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from ..db import cursor
from ..deps import require_account
from ..services import review_digest, mfa
from .materials import private, write_guard

router = APIRouter(prefix='/api/review-digest', dependencies=[Depends(private)])
Account = Annotated[str, Depends(require_account)]


class UnsubscribeAccessFilter(logging.Filter):
    def filter(self, record):
        # Uvicorn access arguments contain the complete target, including query.
        if isinstance(record.args, tuple):
            record.args = tuple(arg.split('?',1)[0]+'?[redacted]' if isinstance(arg,str)
                                and arg.startswith('/api/review-digest/unsubscribe?') else arg for arg in record.args)
        return True


access_log = logging.getLogger('uvicorn.access')
if not any(isinstance(f, UnsubscribeAccessFilter) for f in access_log.filters):access_log.addFilter(UnsubscribeAccessFilter())


class Consent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user_id: str = Field(min_length=1, max_length=100)
    expected_version: int = Field(ge=0)
    enabled: bool


@router.get('/preferences')
async def preferences(user: Account):
    async with cursor() as cur:return await review_digest.status(cur, user)


@router.post('/preferences')
async def save(body: Consent, request: Request, user: Account):
    await write_guard(request, user)
    if body.user_id != user:raise HTTPException(409, 'Your account changed. Reload before saving.')
    if body.enabled:await mfa.limit('review-digest-consent:'+user)
    async with cursor() as cur:return await review_digest.consent(cur, user, body.expected_version, body.enabled)


@router.get('/unsubscribe')
async def landing():
    # Scanner/prefetch GET is deliberately inert. No address or token in HTML.
    return HTMLResponse('''<!doctype html><html lang="en"><meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Finna email preferences</title><main><h1>Stop review reminders</h1>
      <p>Account security emails are unaffected.</p><form method="post">
      <input type="hidden" name="List-Unsubscribe" value="One-Click"><button>Unsubscribe</button></form></main></html>''',
      headers={'Cache-Control':'private, no-store','Referrer-Policy':'no-referrer',
               'Content-Security-Policy':"default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"})


@router.post('/unsubscribe')
async def stop(request: Request):
    body = await request.body()
    if len(body)>1024:raise HTTPException(413, 'Request too large')
    kind = request.headers.get('content-type','').split(';',1)[0]
    try:
        if kind=='application/json':
            data=json.loads(body);token=data.get('token') if isinstance(data,dict) else None
        elif kind=='application/x-www-form-urlencoded':
            data=parse_qs(body.decode(),max_num_fields=4)
            token=request.query_params.get('token') if data.get('List-Unsubscribe')==['One-Click'] else None
        else:raise ValueError()
    except (ValueError, UnicodeError):raise HTTPException(400, 'Invalid unsubscribe request')
    if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}',token):raise HTTPException(400, 'Invalid unsubscribe link')
    async with cursor() as cur:await review_digest.unsubscribe(cur, token)
    return {'unsubscribed':True,'message':'Review reminders are off. Account security emails are unaffected.'}
