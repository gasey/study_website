"""Disposable browser rehearsal. Original PDF with explicitly synthetic draft/game data."""
from pathlib import Path
import sys,hashlib,shutil,uuid,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest
from test_games_search import game_case
from psycopg.types.json import Jsonb
if __name__=='__main__':
 databases=conftest.database.__wrapped__();database=next(databases)
 clients=conftest.client.__wrapped__(database);client=next(clients);select=conftest.actor.__wrapped__(client)
 games=game_case.__wrapped__(client,database);c,subject,users,headers,ids=next(games)
 topic=subject+'/vocabulary';c.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES(%s,'Synthetic vocabulary',%s,'topic','test')",(topic,subject))
 c.execute("UPDATE question_classifications SET topic_id=%s,topic_label='Synthetic vocabulary' WHERE question_id=ANY(%s)",(topic,ids))
 c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,allow_browse) SELECT 'udc',live_version,'paper-test',true FROM collections WHERE id='udc' ON CONFLICT DO NOTHING")
 h=select('owner');r=client.post('/api/topic-trail/packs',headers=h,json={'title':'Synthetic vocabulary · UI rehearsal','collection_id':'udc','taxonomy_id':topic,'reason':'Disposable synthetic visual test; not real UDC source certification.'});assert r.status_code==200,r.text
 from app.config import settings
 from app.services.paper_jobs import process_document
 from app.routers.paper_workbench import Payload
 settings.paper_workbench_root='/tmp/ism-full-preview-documents';storage=Path(settings.paper_workbench_root);(storage/'sources').mkdir(parents=True,exist_ok=True)
 source=next(p for p in (Path(__file__).resolve().parents[3]/'mpsc-question-bankv2/pdfs/Old_Questions').rglob('*.pdf') if p.stat().st_size<500000)
 raw=source.read_bytes();r=client.post('/api/paper-workbench/uploads',headers={**h,'content-type':'application/pdf','x-filename':'Original source for synthetic UI rehearsal.pdf'},content=raw);assert r.status_code==201,r.text
 sha=r.json()['sha256'];r=client.post('/api/paper-workbench/drafts',headers=h,json={'source_sha256':sha,'title':'Synthetic workbench demonstration','exam_name':'Source identity to inspect','year':2020});assert r.status_code==201,r.text
 did=r.json()['id'];jid=r.json()['job_id'];d={'id':did,'source_sha256':sha}
 result,pages=process_document({'id':jid,'kind':'extract','args':{}},d)
 c.execute("UPDATE paper_workbench_jobs SET state='done',result=%s WHERE id=%s",(Jsonb(result),jid));c.execute('UPDATE paper_workbench_drafts SET extraction_id=%s WHERE id=%s',(jid,did))
 for p,t in pages:c.execute('INSERT INTO paper_workbench_pages VALUES(%s,%s,%s)',(jid,p,t))
 jid='pwjob_'+uuid.uuid4().hex;args={'page':1,'rotation':0};result,_=process_document({'id':jid,'kind':'render','args':args},d)
 c.execute("INSERT INTO paper_workbench_jobs(id,draft_id,kind,args,state,result) VALUES(%s,%s,'render',%s,'done',%s)",(jid,did,Jsonb(args),Jsonb(result)))
 p=Payload(title='Synthetic workbench demonstration',exam_name='Source identity to inspect',year=2020,questions=[{'id':uuid.uuid4().hex,'number':'1','page':1,'question':'Synthetic rehearsal: choose the second option. Inspect the original separately.','options':['First option','Second option','Third option','Fourth option'],'subject_id':'english','answer_index':1,'answer_source':'derived','explanation':'Synthetic UI example only; this is not a verified extraction of the displayed source.'}])
 r=client.post('/api/paper-workbench/drafts/'+did+'/save',headers=h,json={'expected_version':1,'payload':p.model_dump()});assert r.status_code==200,r.text
 from app.routers.auth import _hash_password
 for user in ['owner','outsider']:
  c.execute('UPDATE users SET password_hash=%s WHERE id=%s',(_hash_password('SyntheticPassword123!'),user))
 Path('/tmp/workbench-trail-preview.json').write_text(json.dumps({'draft':did,'pack':topic,'source':str(source)}))
 clients.close()
 from app.main import app
 from fastapi.responses import FileResponse,JSONResponse
 root=Path(__file__).resolve().parents[2]/'web/dist';settings.public_origin='http://127.0.0.1:5198';settings.mfa_enforce_staff=False
 @app.get('/{path:path}')
 async def static(path:str):
  if path.startswith('api/'):return JSONResponse({'detail':'Not found'},status_code=404)
  f=(root/path).resolve()
  if not f.is_relative_to(root.resolve()):return JSONResponse({},status_code=404)
  return FileResponse(f if f.is_file() else root/'index.html')
 import uvicorn
 print('Synthetic only: http://127.0.0.1:5198/login?next=%2Fpaper-workbench%3Fdraft%3D'+did,flush=True)
 try:uvicorn.run(app,host='127.0.0.1',port=5198,log_level='warning')
 finally:games.close();databases.close()
