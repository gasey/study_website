import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('inventory_import',ROOT/'scripts/import-mpsc-paper-inventory.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_listing_identity_dedup_empty_row_and_exact_download_index():
 url='https://mpsc.mizoram.gov.in/uploads/key.pdf';page='https://mpsc.mizoram.gov.in/page/old-question-ng'
 snapshots=[{'url':page,'title':'Synthetic listing','rows':[{'cells':['No','Exam','Paper'],'links':[]},{'cells':['1','Synthetic exam 2026','Paper'],'links':[{'title':'1.','url':url},{'title':'Synthetic English Paper I, Booklet A','url':url}]},{'cells':['2','Synthetic exam without link',''],'links':[]}]}]
 bank={'papers':[{'id':'p1','sourceFile':'Old_Questions/English.pdf','year':2026}]};index=[{'pdf_url':url.replace('https','http'),'category':'Old_Questions','filename':'English.pdf'}]
 result=m.prepare(snapshots,bank,index);assert len(result['expectations'])==2
 linked=next(x for x in result['expectations']if x['paper_id']);assert linked['paper_id']=='p1' and linked['booklet']=='A' and linked['title'].startswith('Synthetic English')
 assert not any('answer' in k.lower()for k in linked)
 assert m.prepare(snapshots,bank,index)==result
 bank['papers'].append({'id':'p2','sourceFile':'Old_Questions/English2.pdf','year':2026});index.append({'pdf_url':url,'category':'Old_Questions','filename':'English2.pdf'})
 assert all(x['paper_id']is None for x in m.prepare(snapshots,bank,index)['expectations'])

def test_operator_import_is_atomic_replay_safe_and_preserves_edits(database):
 from uuid import uuid4
 conn=database[1];tag=uuid4().hex
 manifest={'sha256':tag+tag,'exams':[{'id':tag,'title':"Synthetic exam ' source"}],'expectations':[{'id':'x'+tag,'exam_id':tag,'title':'Synthetic expected question paper','year':2026,'booklet':'A','paper_id':None,'reference_url':'https://mpsc.mizoram.gov.in/page/test','paper_url':'','note':'Synthetic metadata import only'}]}
 conn.execute(m.build_sql(manifest))
 conn.execute('UPDATE bank_paper_expectations SET note=%s WHERE id=%s',('Manual reviewed note must survive the replay','x'+tag))
 conn.execute(m.build_sql(manifest))
 assert conn.execute('SELECT note FROM bank_paper_expectations WHERE id=%s',('x'+tag,)).fetchone()[0]=='Manual reviewed note must survive the replay'
 assert conn.execute('SELECT count(*) FROM bank_inventory_events WHERE target_id=%s',(tag+tag,)).fetchone()[0]==1
