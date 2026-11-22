"""Disposable synthetic UI fixture. Launch override is process-local; no SMTP."""
from pathlib import Path
import json,signal,sys
signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from app.config import settings
from app.routers.auth import _hash_password
from app.services import referrals,account_mail
marker=Path('/tmp/finna-referrals-preview.json')
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);next(clients)
try:
    database[1].execute("UPDATE users SET email='synthetic_referrals@example.test',email_verified_at=now(),password_hash=%s WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
    marker.write_text(json.dumps({'database':database[0],'smtp_network_disabled':True,'synthetic_launch_override':True}))
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://localhost:5199';settings.referral_rewards_enabled=True
settings.account_mail_enabled=False;settings.review_digest_enabled=False
async def launch_ready(cur):return True
referrals.launch_ready=launch_ready
account_mail.send_message=lambda *args:None
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8029,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
    marker.unlink(missing_ok=True)
