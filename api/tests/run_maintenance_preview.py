"""Disposable synthetic quiz preview; all data is removed when stopped."""
from pathlib import Path
import sys,signal
signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
Path('/tmp/finna-maintenance-preview-db.txt').write_text(database[0])
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
    actor=conftest.actor.__wrapped__(client)
    database[1].execute("UPDATE users SET email='synthetic_owner@example.test',password_hash=%s WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
    database[1].execute("UPDATE users SET email='synthetic_member@example.test',email_verified_at=now(),password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    database[1].execute("INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) VALUES('author',5000,'owner')")
    database[1].execute("INSERT INTO billing_access_grants(user_id,granted_by,idempotency_key,days,starts_at,ends_at) VALUES('author','owner','synthetic-preview',7,now(),now()+interval '7 days')")
    database[1].execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES('author','synthetic:preview','adjustment',15,3,'Synthetic preview only')")
    database[1].execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author','outsider')")
    import json
    from datetime import datetime,timedelta,timezone
    stamp=datetime.now(timezone.utc)-timedelta(days=12)
    receipt={'schema':1,'source':'paired-backup-restore-v1','state':'verified','completed_at':stamp.isoformat(),'backup_at':(stamp-timedelta(hours=10)).isoformat(),'restored_tables':249,'restored_files':10,**{k:'a'*64 for k in ('archive_sha256','database_sha256','bank_sha256','report_sha256','operator_sha256','api_snapshot_sha256')},**{k:True for k in ('bank_pair_matches','database_restored','files_restored','read_only_role_checked','clone_removed','temporary_files_removed')}}
    database[1].execute("INSERT INTO worker_heartbeats(worker,last_beat,last_ok,note) VALUES('restore-rehearsal',%s,%s,%s)",(stamp,stamp,json.dumps(receipt)))
    print('Synthetic maintenance preview ready',flush=True)

finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
