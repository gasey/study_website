"""Disposable calendar UI fixture; all synthetic data. Ctrl-C drops its database."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from datetime import timedelta
from uuid import uuid4
from app.services.owned_calendar import india_today

databases=conftest.fresh_database();database=next(databases)
clients=conftest.client.__wrapped__(database);client=next(clients)
conn=database[1]
from app.config import settings
settings.public_origin='http://127.0.0.1:5189'
from app.routers.auth import _hash_password
conn.execute("UPDATE users SET password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
day=india_today()
for title,kind,cadence,cid,delta,note in [
 ('Finish Polity chapter 3','personal',None,None,0,'Read the chapter, then revisit saved questions.'),
 ('Weekly progress check','progress-test',7,'udc',0,'A normal 20-minute mock. Take it when ready.'),
 ('My exam target','exam-target',None,'udc',7,'My planning date; check official notices for confirmed dates.')]:
 conn.execute('INSERT INTO calendar_entries(id,user_id,date,title,note,kind,recurrence,collection_id) VALUES(%s,\'author\',%s,%s,%s,%s,%s,%s)',(uuid4(),day+timedelta(days=delta),title,note,kind,cadence,cid))
print('Synthetic calendar preview: author@example.test / SyntheticPassword123!; no production data.',flush=True)
from app.main import app
try:next(clients)
except StopIteration:pass
try:uvicorn.run(app,host='127.0.0.1',port=8019,log_level='warning')
finally:
 try:next(databases)
 except StopIteration:pass
