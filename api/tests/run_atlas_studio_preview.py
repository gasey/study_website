"""Disposable local Atlas curation/browser fixture; never a real reviewed binding."""
from pathlib import Path
from uuid import uuid4
import json,signal,sys
signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from app.config import settings
from app.routers.auth import _hash_password
from psycopg.types.json import Jsonb
from app.services.atlas_bindings import CHAPTERS
marker=Path('/tmp/finna-atlas-studio-preview.json')
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
 conn=database[1]
 conn.execute("UPDATE users SET email='synthetic_studio@example.test',password_hash=%s,plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '7 days' WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
 marker.write_text(json.dumps({'database':database[0],'seeded_chapters':26}))
 print('Synthetic Studio preview ready; existing 26 chapters attributed as current-site content.',flush=True)
finally:
 try:next(clients)
 except StopIteration:pass
settings.public_origin='http://localhost:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
 try:next(prepared)
 except StopIteration:pass
 marker.unlink(missing_ok=True)
