"""Disposable browser rehearsal; no production accounts or records."""
from pathlib import Path
import conftest
from test_learning_workflows import official
from test_learning_catalog import content
if __name__=='__main__':
 databases=conftest.database.__wrapped__();database=next(databases)
 clients=conftest.client.__wrapped__(database);client=next(clients)
 actor=conftest.actor.__wrapped__(client)
 q,a,p=official(database)
 data=content(q);data['title']='Synthetic Important Day';data['description']='A synthetic observance to rehearse the learning flow. This is not a real-world factual entry.'
 r=client.post('/api/learning-catalog',headers=actor('author'),json={'content':data,'reason':'Synthetic browser verification only.'});assert r.status_code==200,r.text
 eid=r.json()['id']
 for who,version,action in [('author',1,'submit'),('reviewer1',2,'publish')]:
  r=client.post('/api/learning-catalog/'+eid+'/decision',headers=actor(who),json={'expected_version':version,'action':action,'reason':'Synthetic browser verification only; not production evidence.'});assert r.status_code==200,r.text
 data.update(kind='practice',title='Synthetic English practice',month=None,day=None,sources=[],suggested_minutes=5)
 r=client.post('/api/learning-catalog',headers=actor('author'),json={'content':data,'reason':'Synthetic browser verification only.'});assert r.status_code==200,r.text
 eid=r.json()['id']
 for who,version,action in [('author',1,'submit'),('reviewer1',2,'publish')]:
  r=client.post('/api/learning-catalog/'+eid+'/decision',headers=actor(who),json={'expected_version':version,'action':action,'reason':'Synthetic browser verification only; not production evidence.'});assert r.status_code==200,r.text
 from app.routers.auth import _hash_password
 for user in ['author','reviewer1','owner','outsider']:database[1].execute('UPDATE users SET password_hash=%s WHERE id=%s',(_hash_password('SyntheticPassword123!'),user))
 clients.close()
 from app.config import settings
 from app.main import app
 from fastapi.responses import FileResponse,JSONResponse
 root=Path(__file__).resolve().parents[2]/'web/dist'
 settings.public_origin='http://127.0.0.1:5202'
 settings.mfa_enforce_staff=False
 @app.get('/{path:path}')
 async def static(path:str):
  if path.startswith('api/'):return JSONResponse({'detail':'Not found'},status_code=404)
  f=(root/path).resolve()
  if not f.is_relative_to(root.resolve()):return JSONResponse({},status_code=404)
  return FileResponse(f if f.is_file() else root/'index.html')
 import uvicorn
 print('Synthetic preview: http://127.0.0.1:5202/important-days',flush=True)
 try:uvicorn.run(app,host='127.0.0.1',port=5202,log_level='warning')
 finally:databases.close()
