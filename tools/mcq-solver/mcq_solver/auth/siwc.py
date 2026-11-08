import base64
from dataclasses import dataclass
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
import time
from urllib.parse import parse_qs, urlencode, urlsplit
import uuid
import webbrowser

from ..config import Config
from ..errors import SolverError
from ..storage import atomic_json, locked, private_dir, read_private
from ..transport import AUTHORIZE, DISCOVERY, ISSUER, JWKS, RESOURCE, TOKEN, Transport

SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
DIRECT_SCOPE = "chatgpt.tokens.use.direct"
UNUSABLE = {"invalid_grant", "invalid_refresh_token", "token_expired", "refresh_token_expired", "refresh_token_invalidated", "refresh_token_reused"}


@dataclass(repr=False)
class Attempt:
    host_id: str
    redirect_uri: str
    client_id: str = "dynamic_agent_client"
    state: str = ""
    nonce: str = ""
    verifier: str = ""

    def __post_init__(self):
        self.state = secrets.token_urlsafe(32)
        self.nonce = secrets.token_urlsafe(32)
        self.verifier = secrets.token_urlsafe(64)

    def url(self, saved=None, reconsent=False):
        challenge = base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode()).digest()).decode().rstrip("=")
        params = dict(client_id=self.client_id, ext_agent_host_id=self.host_id,
                      response_type="code", redirect_uri=self.redirect_uri, scope=SCOPES,
                      resource=RESOURCE, state=self.state, nonce=self.nonce,
                      code_challenge_method="S256", code_challenge=challenge)
        if self.client_id == "dynamic_agent_client":
            params["agent_name_hint"] = "Personal MCQ Solver"
        elif saved and saved.get("id_token"):
            params["id_token_hint"] = saved["id_token"]
        if reconsent:
            params["prompt"] = "consent"
        return AUTHORIZE + "?" + urlencode(params)

    def callback(self, path: str):
        parsed = urlsplit(path)
        q = parse_qs(parsed.query, keep_blank_values=True)
        if parsed.path != "/auth/callback" or any(len(v) != 1 for v in q.values()):
            raise SolverError("invalid_callback")
        if not secrets.compare_digest(q.get("state", [""])[0], self.state):
            raise SolverError("invalid_callback")
        if "error" in q:
            raise SolverError("access_denied")
        cid = q.get("client_id", [self.client_id])[0]
        if not cid or cid == "dynamic_agent_client" or len(cid) > 256:
            raise SolverError("invalid_callback")
        if self.client_id != "dynamic_agent_client" and cid != self.client_id:
            raise SolverError("invalid_callback")
        code = q.get("code", [""])[0]
        if not code or len(code) > 8192:
            raise SolverError("invalid_callback")
        return cid, code


class IdentityVerifier:
    def __init__(self, transport):
        self.transport = transport

    def verify(self, token, client_id, nonce=None):
        # Keys and algorithms come only from the trusted issuer, never JWT URLs.
        import jwt
        try:
            discovery = self.transport.json(DISCOVERY)
            if discovery.get("issuer") != ISSUER or discovery.get("jwks_uri") != JWKS:
                raise SolverError("invalid_identity")
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256":
                raise SolverError("invalid_identity")
            keys = self.transport.json(JWKS)["keys"]
            matches = [k for k in keys if k.get("kid") == header.get("kid") and k.get("kty") == "RSA"]
            if len(matches) != 1:
                raise SolverError("invalid_identity")
            key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(matches[0]))
            claims = jwt.decode(token, key, algorithms=["RS256"], audience=client_id,
                                issuer=ISSUER, leeway=30, options={"require": ["iss", "sub", "aud", "exp", "iat"]})
            if not isinstance(claims["sub"], str) or not claims["sub"]:
                raise SolverError("invalid_identity")
            if claims.get("azp", client_id) != client_id:
                raise SolverError("invalid_identity")
            if isinstance(claims["aud"], list) and len(claims["aud"]) > 1 and claims.get("azp") != client_id:
                raise SolverError("invalid_identity")
            if nonce is not None and not secrets.compare_digest(claims.get("nonce", ""), nonce):
                raise SolverError("invalid_identity")
            return claims
        except (jwt.PyJWTError, ValueError, TypeError, KeyError):
            raise SolverError("invalid_identity") from None


class Credentials:
    """One explicitly selected registration; no automatic account rotation."""
    def __init__(self, root: Path, transport=None, verifier=None):
        self.root = root
        self.transport = transport or Transport()
        self.verifier = verifier or IdentityVerifier(self.transport)

    def host(self, create=True):
        p = self.root / "host.json"
        if not p.exists() and not create:
            raise SolverError("host_not_initialized")
        with locked(self.root / "auth.lock"):
            if not p.exists():
                atomic_json(p, {"ext_agent_host_id": "urn:uuid:" + str(uuid.uuid4())})
            return read_private(p)["ext_agent_host_id"]

    def read(self):
        try:
            d = read_private(self.root / "registration.json")
        except FileNotFoundError:
            raise SolverError("auth_required") from None
        if not isinstance(d, dict):
            raise SolverError("invalid_credentials")
        return d

    def write(self, data):
        atomic_json(self.root / "registration.json", data)

    def status(self):
        if not (self.root / "registration.json").exists():
            return {"authorized": False, "reason": "auth_required"}
        d = self.read()
        return {"authorized": bool(d.get("access_token")) and DIRECT_SCOPE in d.get("scopes", []) and not d.get("transferred"),
                "plan_scope": DIRECT_SCOPE in d.get("scopes", []),
                "transferred": bool(d.get("transferred")),
                "expired": d.get("expires_at", 0) <= time.time()}

    def token_record(self, payload, old, client_id, host, claims=None):
        if not isinstance(payload, dict):
            raise SolverError("invalid_credentials")
        if payload.get("token_type", "").lower() != "bearer":
            raise SolverError("invalid_credentials")
        access = payload.get("access_token")
        refresh = payload.get("refresh_token", old.get("refresh_token"))
        if not isinstance(access, str) or not access or not isinstance(refresh, str) or not refresh:
            raise SolverError("invalid_credentials")
        expires = payload.get("expires_in")
        if type(expires) not in (int, float) or not 0 < expires <= 86400 * 30:
            raise SolverError("invalid_credentials")
        scopes = payload.get("scope")
        if scopes is None:
            scopes = " ".join(old.get("scopes", []))
        if not isinstance(scopes, str):
            raise SolverError("invalid_credentials")
        identity = claims or {"sub": old.get("subject"), "iss": old.get("issuer")}
        if old.get("subject") and old["subject"] != identity["sub"]:
            raise SolverError("invalid_identity")
        return {"client_id": client_id, "subject": identity["sub"], "issuer": identity["iss"],
                "ext_agent_host_id": host, "access_token": access, "refresh_token": refresh,
                "id_token": payload.get("id_token", old.get("id_token")), "token_type": "Bearer",
                "scopes": scopes.split(), "expires_at": time.time() + expires,
                "plan_sharing_approved": True, "saved_at": time.time()}

    def complete(self, attempt, path, saved=None):
        cid, code = attempt.callback(path)
        old = saved or {}
        # Retain issued registration even if the single-use code exchange fails.
        self.write({**old, "client_id": cid, "ext_agent_host_id": attempt.host_id})
        payload = self.transport.json(TOKEN, form={"grant_type": "authorization_code", "client_id": cid,
            "code": code, "code_verifier": attempt.verifier, "redirect_uri": attempt.redirect_uri, "resource": RESOURCE})
        claims = self.verifier.verify(payload.get("id_token"), cid, attempt.nonce)
        record = self.token_record(payload, old, cid, attempt.host_id, claims)
        self.write(record)
        if DIRECT_SCOPE not in record["scopes"]:
            raise SolverError("missing_plan_scope")
        return record

    def access_token(self):
        with locked(self.root / "auth.lock"):
            d = self.read()
            if d.get("transferred"):
                raise SolverError("session_transferred")
            if not d.get("plan_sharing_approved"):
                raise SolverError("plan_approval_required")
            if DIRECT_SCOPE not in d.get("scopes", []):
                raise SolverError("missing_plan_scope")
            if not d.get("access_token"):
                raise SolverError("auth_required")
            if d.get("expires_at", 0) <= time.time() + 60:
                try:
                    payload = self.transport.json(TOKEN, form={"grant_type": "refresh_token",
                        "client_id": d["client_id"], "refresh_token": d["refresh_token"], "resource": RESOURCE})
                except SolverError as exc:
                    if exc.code in UNUSABLE:
                        self.write({k: v for k, v in d.items() if k not in {"access_token", "refresh_token", "id_token"}})
                    raise
                claims = self.verifier.verify(payload["id_token"], d["client_id"]) if payload.get("id_token") else None
                d = self.token_record(payload, d, d["client_id"], d["ext_agent_host_id"], claims)
                self.write(d)
                if DIRECT_SCOPE not in d["scopes"]:
                    raise SolverError("missing_plan_scope")
            return d["access_token"]

    def import_transfer(self, data):
        host = self.host(create=False)
        if not isinstance(data, dict) or data.get("ext_agent_host_id") == host:
            raise SolverError("invalid_credentials")
        if not data.get("subject") or data.get("issuer") != ISSUER or data.get("client_id") in (None, "dynamic_agent_client"):
            raise SolverError("invalid_credentials")
        if DIRECT_SCOPE not in data.get("scopes", []) or not data.get("plan_sharing_approved"):
            raise SolverError("missing_plan_scope")
        if not all(isinstance(data.get(k), str) and data[k] for k in ("access_token", "refresh_token", "id_token")):
            raise SolverError("invalid_credentials")
        with locked(self.root / "auth.lock"):
            if (self.root / "registration.json").exists():
                raise SolverError("invalid_credentials")
            self.write({**data, "ext_agent_host_id": host, "transferred": False})


def login(store: Credentials, config: Config, *, approved=False, reconsent=False):
    config.require_eligibility()
    if not approved:
        raise SolverError("plan_approval_required")
    host = store.host()
    private_dir(store.root)
    with locked(store.root / "auth.lock", blocking=False):
        saved = store.read() if (store.root / "registration.json").exists() else None
        result = {}

        class Callback(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # callback contains a code; never use default HTTP logging

            def do_GET(self):
                try:
                    attempt.callback(self.path)
                except SolverError as exc:
                    if exc.code == "access_denied":
                        result["error"] = exc
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Authorization could not be completed.")
                    return
                result["path"] = self.path
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Return to the terminal to check authorization.")

        with HTTPServer(("127.0.0.1", 0), Callback) as server:
            server.timeout = 1
            attempt = Attempt(host, f"http://127.0.0.1:{server.server_port}/auth/callback",
                              saved["client_id"] if saved else "dynamic_agent_client")
            # URL may contain an ID-token hint: open it, never print it.
            if not webbrowser.open(attempt.url(saved, reconsent)):
                raise SolverError("invalid_callback")
            deadline = time.monotonic() + 300
            while not result and time.monotonic() < deadline:
                server.handle_request()
            if "error" in result:
                raise result["error"]
            if "path" not in result:
                raise SolverError("invalid_callback")
            store.complete(attempt, result["path"], saved)
    return {"authorized": True, "billing_mode": "chatgpt_plan"}
