"""Disposable UI fixture, synthetic identities and a transport sink; no SMTP."""
from pathlib import Path
import base64,hashlib,json,signal,sys
signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from app.config import settings
from app.routers.auth import _hash_password
from app.services import account_mail,mfa

marker=Path('/tmp/finna-review-digest-preview.json')
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);next(clients)
try:
    conn=database[1]
    conn.execute("UPDATE users SET email='synthetic_digest@example.test',email_verified_at=now(),password_hash=%s WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
    settings.account_mail_enabled=True;settings.review_digest_enabled=True
    settings.smtp_host='synthetic.invalid';settings.smtp_from='synthetic@example.test'
    settings.mfa_encryption_key=base64.urlsafe_b64encode(b'0'*32).decode()
    # A separate synthetic subscriber lets browser QA exercise signed-out withdrawal.
    raw='S'*43
    conn.execute("INSERT INTO review_digest_preferences(user_id,enabled,version,token_hash,token_cipher,email_hash) VALUES('reviewer1',true,1,%s,%s,%s)",
                 (hashlib.sha256(raw.encode()).hexdigest(),mfa.encrypt('reviewer1',raw),hashlib.sha256(b'reviewer1@example.test').hexdigest()))
    marker.write_text(json.dumps({'database':database[0],'smtp_network_disabled':True}))
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://localhost:5199'
account_mail.send_message=lambda *args:None
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8029,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
    marker.unlink(missing_ok=True)
