from uuid import uuid4
from psycopg.types.json import Jsonb
from test_admin_workbench import workbench
BASE='/api/admin/bank/inventory'
def create(client,actor,title='Synthetic inventory exam'):
 h=actor('owner');r=client.post(BASE+'/exams',headers=h,json={'title':title,'reason':'Synthetic inventory rehearsal only'});assert r.status_code==200,r.text
 return r.json()['id'],h
def body(eid,paper=None):return {'exam_id':eid,'title':'Synthetic expected English paper','year':2020,'booklet':'A','expected_questions':3,'paper_id':paper,'reference_url':'https://mpsc.mizoram.gov.in/page/synthetic','paper_url':'','note':'Synthetic source context check for isolated tests','context_reviewed':bool(paper)}
def test_inventory_permissions_and_csrf(client,actor):
 actor('outsider');assert client.get(BASE+'/exams').status_code==403
 actor('reviewer1');assert client.get(BASE+'/exams').status_code==403
 h=actor('owner');assert client.post(BASE+'/exams',json={'title':'Synthetic','reason':'Synthetic test only'}).status_code==403
 assert client.get(BASE+'/exams').status_code==200

def test_inventory_crud_conflict_archival_and_export(client,actor,workbench,database):
 ids,paper,alt=workbench;eid,h=create(client,actor);payload=body(eid,paper)
 r=client.post(BASE+'/expectations',headers=h,json=payload);assert r.status_code==200,r.text;x=r.json()
 assert x['context_fingerprint']and x['version']==1
 d=client.get(BASE+'/paper',params={'paper_id':paper}).json();assert d['expectations'][0]['context_reviewed_current']is True
 database[1].execute("UPDATE appearances SET direction='Changed after context check' WHERE paper_id=%s",(paper,))
 assert client.get(BASE+'/paper',params={'paper_id':paper}).json()['expectations'][0]['context_reviewed_current']is False
 assert client.post(BASE+'/expectations/'+x['id'],headers=h,json=payload).status_code==409
 payload.update(expected_version=1,note='Synthetic reviewed registry revision')
 r=client.post(BASE+'/expectations/'+x['id'],headers=h,json=payload);assert r.status_code==200 and r.json()['version']==2
 assert client.post(BASE+'/expectations/'+x['id'],headers=h,json=payload).status_code==409
 r=client.get(BASE+'/export');assert r.status_code==200 and 'private' in r.headers['cache-control']
 assert next(e for e in r.json()['bank_paper_expectations']if e['id']==x['id'])['version']==2
 assert client.post(BASE+'/exams/'+eid+'/papers',headers=h,json={'paper_id':paper,'remove':True,'reason':'Synthetic unlink with dependency'}).status_code==409
 payload.update(expected_version=2,archived=True)
 assert client.post(BASE+'/expectations/'+x['id'],headers=h,json=payload).status_code==200
 assert client.post(BASE+'/exams/'+eid+'/papers',headers=h,json={'paper_id':paper,'remove':True,'reason':'Synthetic unlink after archival'}).status_code==200
 assert client.get(BASE+'/expectations',params={'exam_id':eid}).json()['total']==0
 assert client.get(BASE+'/expectations',params={'exam_id':eid,'register_state':'archived'}).json()['total']==1
 payload.update(expected_version=3,archived=False,paper_id=None,context_reviewed=False)
 assert client.post(BASE+'/expectations/'+x['id'],headers=h,json=payload).status_code==200
 assert client.get(BASE+'/expectations',params={'exam_id':eid}).json()['total']==1
 assert client.get(BASE+'/events').json()

def test_counts_filters_numbering_and_source_safety(client,actor,workbench,database,tmp_path,monkeypatch):
 ids,paper,alt=workbench;eid,h=create(client,actor)
 assert client.post(BASE+'/exams/'+eid+'/papers',headers=h,json={'paper_id':paper,'reason':'Synthetic explicit inventory association'}).status_code==200
 for status,wanted in [('official','keyed'),('unsolved','missing'),('written','descriptive'),('needs-review','unverified')]:
  r=client.get('/api/admin/bank/questions',params={'paper_id':paper,'answer_status':status,'exam_id':eid,'year':2020});assert r.status_code==200,r.text
  assert ids[wanted]in{q['id']for q in r.json()['items']}
 assert client.get('/api/admin/bank/questions',params={'paper_id':paper,'answer_status':'verified'}).json()['total']==0
 assert client.get('/api/admin/bank/questions',params={'paper_id':paper,'year':2021}).json()['total']==0
 assert client.get('/api/admin/bank/questions',params={'answer_status':'made-up'}).status_code==422
 summary=client.get(BASE+'/summary',params={'exam_id':eid}).json();assert sum(x['count']for x in summary['statuses'])==8
 d=client.get(BASE+'/paper',params={'paper_id':paper}).json();assert d['numbering']['duplicates'][0]['copies']==8
 assert d['written']==1 and d['official']==1 and d['unsolved']==1
 assert client.get(BASE+'/papers',params={'exam_id':eid,'offset':1000}).json()=={'items':[],'total':1}
 bad=body(eid);bad['reference_url']='https://user:password@example.com/test'
 assert client.post(BASE+'/expectations',headers=h,json=bad).status_code==422
 bad=body(eid,'not-a-paper');assert client.post(BASE+'/expectations',headers=h,json=bad).status_code==404
 from app.routers.exam_inventory import local_pdf_state
 from app.config import settings
 monkeypatch.setattr(settings,'paper_archive_root',str(tmp_path));(tmp_path/'Old_Questions').mkdir();(tmp_path/'Old_Questions/test.pdf').write_bytes(b'synthetic')
 assert local_pdf_state('/papers/source/Old_Questions/test.pdf')=='available'
 assert local_pdf_state('/papers/source/../../etc/passwd')=='missing-file'
 assert local_pdf_state('https://example.test/test.pdf')=='external-unchecked'

def test_key_document_active_mock_protection(client,actor,workbench,database,tmp_path,monkeypatch):
 ids,paper,alt=workbench;conn=database[1];h=actor('owner');tag=uuid4().hex
 from app.config import settings
 monkeypatch.setattr(settings,'registered_document_root',str(tmp_path))
 sha='b'*64;(tmp_path/(sha+'.pdf')).write_bytes(b'%PDF-synthetic')
 conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,key_status,registered_by) VALUES(%s,%s,'Synthetic final key','keys/synthetic.pdf',%s,'official-key','final','test')",(tag,paper,sha))
 r=client.get(BASE+'/document/'+tag);assert r.status_code==200 and r.headers['content-type']=='application/pdf'
 assert r.headers['cache-control']=='private, no-store'
 ranged=client.get(BASE+'/document/'+tag,headers={'Range':'bytes=0-4'});assert ranged.status_code==206 and ranged.content==b'%PDF-'
 conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner','ldc',%s,60)",(tag,[ids['keyed']]))
 assert client.get(BASE+'/document/'+tag).status_code==409
 assert client.get(BASE+'/paper',params={'paper_id':paper}).status_code==409
 conn.execute('DELETE FROM mock_sessions WHERE id=%s',(tag,))

def test_exam_year_filter_uses_same_appearance(client,actor,workbench,database):
 ids,paper,alternate=workbench;eid,h=create(client,actor)
 assert client.post(BASE+'/exams/'+eid+'/papers',headers=h,json={'paper_id':paper,'reason':'Synthetic same-appearance test association'}).status_code==200
 database[1].execute('UPDATE papers SET year=2021 WHERE id=(SELECT paper_id FROM appearances WHERE id=%s)',(alternate,))
 r=client.get('/api/admin/bank/questions',params={'exam_id':eid,'year':2021});assert r.status_code==200 and r.json()['total']==0
 r=client.get('/api/admin/bank/questions',params={'exam_id':eid,'year':2020,'q':ids['unverified']});assert r.status_code==200 and r.json()['items'][0]['paper_id']==paper
 r=client.get('/api/admin/bank/questions',params={'year':2021,'q':ids['unverified']});assert r.status_code==200 and r.json()['items'][0]['appearance_id']==alternate

def test_expected_years_without_imported_papers_are_filterable(client,actor):
 eid,h=create(client,actor);payload=body(eid);payload['year']=2026
 assert client.post(BASE+'/expectations',headers=h,json=payload).status_code==200
 summary=client.get(BASE+'/summary',params={'exam_id':eid}).json();assert {'year':2026,'papers':0}in summary['years']
 assert client.get(BASE+'/expectations',params={'exam_id':eid,'year':2026,'unmatched':True}).json()['total']==1
