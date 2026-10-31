"""Cookie mutation boundary, including routes with optional account identity."""
import hmac
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from ..config import settings
from .account_identity import csrf_token

# Pre-auth forms use strict origin checks instead of authenticated CSRF.
PREAUTH={'/api/auth/login','/api/auth/register','/api/auth/recovery/request','/api/auth/recovery/complete','/api/auth/email/confirm'}
# This endpoint is a read-only preview despite POST semantics.
READ_POST={'/api/games/preview'}

class AccountBoundary(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        if request.url.path.startswith('/api/') and request.method not in {'GET','HEAD','OPTIONS'}:
            token=request.cookies.get('ism_session')
            if token and request.url.path not in PREAUTH|READ_POST:
                if request.headers.get('origin','').rstrip('/')!=settings.public_origin.rstrip('/'):
                    return JSONResponse({'detail':'A same-origin request is required'},status_code=403)
                if not hmac.compare_digest(request.headers.get('x-review-csrf',''),csrf_token(token)):
                    return JSONResponse({'detail':'Refresh the page before saving'},status_code=403)
        response=await call_next(request)
        # Identity-dependent APIs must never be reused by a shared cache.
        if request.url.path.startswith('/api/'):
            response.headers.setdefault('Cache-Control','private, no-store')
        return response
