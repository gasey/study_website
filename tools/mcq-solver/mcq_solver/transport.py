"""Fixed public endpoints; no redirects, API-key fallback or environment proxy."""
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from .errors import SolverError

ISSUER = "https://auth.openai.com"
RESOURCE = "https://api.openai.com/v1"
AUTHORIZE = ISSUER + "/api/accounts/authorize"
TOKEN = ISSUER + "/api/accounts/oauth/token"
DISCOVERY = ISSUER + "/.well-known/openid-configuration"
JWKS = ISSUER + "/.well-known/jwks.json"
ALLOWED = {TOKEN, DISCOVERY, JWKS, RESOURCE + "/models", RESOURCE + "/responses"}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def provider_error(payload, status=None, retry_after=0) -> SolverError:
    err = payload.get("error", {}) if isinstance(payload, dict) else {}
    code = err if isinstance(err, str) else err.get("code") if isinstance(err, dict) else None
    if not code:
        code = {401: "auth_required", 403: "permission_denied", 429: "rate_limited"}.get(status, "server_error" if status and status >= 500 else "http_error")
    return SolverError(code, status=status, retry_after=retry_after)


class Transport:
    def __init__(self):
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    @contextmanager
    def open(self, url, *, body=None, form=None, token=None, timeout=90):
        if url not in ALLOWED:
            raise SolverError("invalid_request")
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body, allow_nan=False).encode()
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "text/event-stream"
        if form is not None:
            data = urlencode(form).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if token:
            headers["Authorization"] = "Bearer " + token
        try:
            with self.opener.open(Request(url, data=data, headers=headers), timeout=timeout) as response:
                yield response
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read(65536))
            except (ValueError, OSError):
                payload = {}
            retry = exc.headers.get("Retry-After", "0")
            try:
                delay = float(retry)
            except ValueError:
                try:
                    delay = max(0, parsedate_to_datetime(retry).timestamp() - time.time())
                except (ValueError, TypeError):
                    delay = 0
            raise provider_error(payload, exc.code, delay) from None
        except (URLError, TimeoutError, ConnectionError, OSError):
            raise SolverError("network_error") from None

    def json(self, url, **kwargs):
        with self.open(url, **kwargs) as response:
            try:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise SolverError("invalid_response")
                return json.loads(raw)
            except (ValueError, UnicodeError):
                raise SolverError("invalid_response") from None
