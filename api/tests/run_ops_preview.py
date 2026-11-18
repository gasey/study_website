"""Disposable synthetic quiz preview; all data is removed when stopped."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
    actor=conftest.actor.__wrapped__(client)
    database[1].execute("UPDATE users SET email='synthetic_owner@example.test',password_hash=%s WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
    database[1].execute("UPDATE users SET email='synthetic_member@example.test',email_verified_at=now(),password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    database[1].execute("INSERT INTO worker_heartbeats(worker,last_beat,last_ok,note) VALUES('calendar-reminders',now()-interval '5 minutes',now()-interval '5 minutes','Synthetic stale worker') ON CONFLICT(worker) DO UPDATE SET last_beat=EXCLUDED.last_beat,last_ok=EXCLUDED.last_ok,note=EXCLUDED.note")
    import importlib.util
    from datetime import datetime,timedelta,timezone
    spec=importlib.util.spec_from_file_location('preview_collector',Path(__file__).resolve().parents[2]/'scripts/ops-collector.py');collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
    stamp=datetime.now(timezone.utc);backup_at=stamp-timedelta(hours=13)
    collector.write_records(database[1],[collector.record('probe:disk','healthy','Synthetic host sample',stamp,free_bytes=14*1024**3,total_bytes=96*1024**3),collector.record('probe:backup','healthy','Synthetic paired backup sample',backup_at,backup_at=backup_at.isoformat(),verification='sha256_pair_and_dump_index')])
    print('Synthetic ops preview: synthetic_owner@example.test / SyntheticPassword123!',flush=True)

finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
