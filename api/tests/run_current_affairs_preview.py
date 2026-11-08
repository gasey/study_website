"""Disposable full-stack current-affairs rehearsal; synthetic data only."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest
from test_current_affairs import sources,proposal,publish,measured_proposal
from psycopg.types.json import Jsonb
if __name__=='__main__':
 databases=conftest.database.__wrapped__();database=next(databases)
 clients=conftest.client.__wrapped__(database);client=next(clients)
 select=conftest.actor.__wrapped__(client)
 rows=sources.__wrapped__(database,client)
 body,h=proposal(client,select,rows);rid=publish(client,select,body,h)
 body2,h=proposal(client,select,rows);body2['name']='Synthetic election office — pending review'
 assert client.post('/api/current-affairs/proposals',headers=h,json=body2).status_code==201
 trade_rows=sources.__wrapped__(database,client)
 for i,(qid,aid,pid) in enumerate(trade_rows):
  text=f'Synthetic trade example: which country led iron ore exports by volume in calendar year {2023+i}?'
  options=['Synthetic Country A','Synthetic Country B','Synthetic Country C','Synthetic Country D']
  database[1].execute('UPDATE canonical_questions SET question=%s,options=%s,answer_text=%s WHERE id=%s',(text,Jsonb(options),options[i],qid))
  database[1].execute("UPDATE appearances SET question=%s,options=%s,answer_index=%s,answer_source='official' WHERE id=%s",(text,Jsonb(options),i,aid))
  database[1].execute("UPDATE papers SET year=%s,exam_name='Synthetic UDC current-affairs paper' WHERE id=%s",(2024+i,pid))
 body3,h=measured_proposal(client,select,trade_rows)
 body3['name']='Synthetic iron ore exports — tonnage, worldwide'
 for i,l in enumerate(body3['links']):
  l.update(period_label=f'Calendar year {2023+i}',date_basis='The printed synthetic question explicitly names its reporting year.',context=f'This paper asks about calendar year {2023+i} iron ore exports by quantity, not current exports or production.')
 publish(client,select,body3,h)
 from app.routers.auth import _hash_password
 for user in ['owner','reviewer1','outsider']:
  database[1].execute('UPDATE users SET password_hash=%s WHERE id=%s',(_hash_password('SyntheticPassword123!'),user))
 Path('/tmp/current-affairs-preview.json').write_text(json.dumps({'questions':rows,'revision':rid,'trade_questions':trade_rows},indent=2))
 clients.close()
 from app.config import settings
 from app.main import app
 from fastapi.responses import FileResponse,JSONResponse
 root=Path(__file__).resolve().parents[2]/'web/dist'
 settings.public_origin='http://127.0.0.1:5198'
 settings.mfa_enforce_staff=False
 @app.get('/{path:path}')
 async def static(path:str):
  if path.startswith('api/'):return JSONResponse({'detail':'Not found'},status_code=404)
  f=(root/path).resolve()
  if not f.is_relative_to(root.resolve()):return JSONResponse({},status_code=404)
  return FileResponse(f if f.is_file() else root/'index.html')
 import uvicorn
 print('Synthetic only: http://127.0.0.1:5198/login?next=%2Fcurrent-affairs%2Fmanage',flush=True)
 try:uvicorn.run(app,host='127.0.0.1',port=5198,log_level='warning')
 finally:databases.close()
