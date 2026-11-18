"""Disposable local board/recap UI fixture. Ctrl-C removes its database."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from datetime import timedelta
from uuid import uuid4
from test_weekly_boards import profile,game

databases=conftest.fresh_database();database=next(databases)
clients=conftest.client.__wrapped__(database);client=next(clients)
conn=database[1]
from app.config import settings
settings.public_origin='http://127.0.0.1:5189'
from app.routers.auth import _hash_password
conn.execute("UPDATE users SET password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES('author',%s,'adjustment',173,'Synthetic private viewer')",(uuid4().hex,))
for i in range(40):
    who=profile(conn,290-i*5)
    conn.execute('UPDATE users SET handle=%s WHERE id=%s',(f'Preview learner {i+1:02}',who))
    if i<4:game(conn,who,1000-i*10,'speed')
# Preview Monday's source-derived card on any day without changing source code.
from app.services import weekly_recap
original=weekly_recap.compose
monday=conn.execute("SELECT (date_trunc('week',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')+interval '10 hours'").fetchone()[0]
last=monday-timedelta(days=7)
conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note,created_at) VALUES('author',%s,'adjustment',42,'Synthetic last-week receipt',%s)",(uuid4().hex,last))
conn.execute("INSERT INTO study_focus_sessions(id,user_id,duration_seconds,state,elapsed_seconds,ended_at) VALUES(%s,'author',600,'completed',600,%s)",(uuid4().hex,last))
for i in range(3):conn.execute("INSERT INTO user_learning_days(user_id,day) VALUES('author',%s)",(last.date()+timedelta(days=i),))
async def preview_recap(cur,user,*,as_of=None):return await original(cur,user,as_of=monday)
weekly_recap.compose=preview_recap
print('Synthetic local preview: author@example.test / SyntheticPassword123!; board + Monday recap. No production data.',flush=True)
from app.main import app
try:next(clients)
except StopIteration:pass
try:uvicorn.run(app,host='127.0.0.1',port=8019,log_level='warning')
finally:
    try:next(clients)
    except StopIteration:pass
    try:next(databases)
    except StopIteration:pass
