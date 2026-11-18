"""Disposable synthetic shared vocabulary scheduler preview, no production questions/users."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_vocabulary_decks import prepare
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients);conn=database[1]
try:
    ids=prepare(conn)
    from test_vocabulary import seed
    from psycopg.types.json import Jsonb
    more=seed(conn,8)
    for qid in more:
        conn.execute("INSERT INTO vocabulary_state(user_id,question_id,content_hash,seen,first_review_at,last_exposure_at) VALUES('author',%s,'synthetic-stale',1,now()-interval '2 days',now()-interval '2 days')",(qid,))
        conn.execute("INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result) VALUES('author','vocab',%s,%s,1,current_date,false)",(qid,qid))
    conn.execute("UPDATE users SET handle='synthetic_author',password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    print('Synthetic shared vocabulary scheduler: author@example.test / SyntheticPassword123!',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5195'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8025,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
