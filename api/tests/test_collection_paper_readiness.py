"""Paper cards use actual eligibility and explicit states, not inferred confidence."""
from uuid import uuid4
from psycopg.types.json import Jsonb

def test_paper_cards_report_review_and_scoring_counts(client,database):
 conn=database[1];suffix=uuid4().hex[:10];paper='readiness-paper-'+suffix
 conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,exam_scope_id) VALUES (%s,'Direct','Synthetic LDC readiness paper',2026,'mizoram-recruitment')",(paper,))
 conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) VALUES ('ldc',1,%s,'papers',false)",(paper,))
 try:
  for i,source,answer,defect in [(1,'official','A',None),(2,'inferred','B',None),(3,'none',None,None),(4,'derived','B','unresolved-source')]:
   q='cq_ready_'+suffix+str(i);a='app_ready_'+suffix+str(i)
   conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source,source_defect) VALUES (%s,'mcq','Synthetic readiness question',%s,%s,%s,%s)",(q,Jsonb(['A','B','C','D']),answer,source,defect))
   conn.execute("INSERT INTO appearances(id,paper_id,type,qnum,question,options,answer_index,answer_source,canonical_id,is_primary) VALUES (%s,%s,'mcq',%s,'Synthetic readiness question',%s,%s,%s,%s,true)",(a,paper,str(i),Jsonb(['A','B','C','D']),None if answer is None else ['A','B','C','D'].index(answer),source,q))
  r=client.get('/api/collections/ldc');assert r.status_code==200,r.text
  item=next(p for p in r.json()['paper_list'] if p['id']==paper)
  assert {k:item[k] for k in ['questions','scorable','practice_count','answerable_count','verified_solutions','needs_review','unsolved','missing_explanations','blocked_count']}=={'questions':4,'scorable':1,'practice_count':1,'answerable_count':2,'verified_solutions':0,'needs_review':2,'unsolved':1,'missing_explanations':4,'blocked_count':1}
  assert not item['allow_timed_test']
 finally:
  conn.execute("DELETE FROM collection_papers WHERE paper_id=%s",(paper,))
  conn.execute("DELETE FROM appearances WHERE paper_id=%s",(paper,))
  conn.execute("DELETE FROM canonical_questions WHERE id LIKE %s",('cq_ready_'+suffix+'%',))
  conn.execute("DELETE FROM papers WHERE id=%s",(paper,))

def test_question_detail_keeps_review_hold_distinct_from_official_provenance(client,database):
 conn=database[1];suffix=uuid4().hex[:10];qid='cq_detail_status_'+suffix;aid='app_detail_status_'+suffix
 conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source,status) VALUES(%s,'mcq','Synthetic held authority answer',%s,'A','official','held')",(qid,Jsonb(['A','B','C','D'])))
 conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary)VALUES(%s,'paper-test','mcq','Synthetic held authority answer',%s,0,'official',%s,true)",(aid,Jsonb(['A','B','C','D']),qid))
 try:
  response=client.get('/api/questions/'+qid);assert response.status_code==200,response.text
  item=response.json();assert item['answer_source']=='official' and item['answer_status']=='needs-review' and item['held']is True
  assert 'answer_text'not in item and 'answer_index'not in item and 'explanation'not in item
 finally:
  conn.execute('DELETE FROM appearances WHERE id=%s',(aid,));conn.execute('DELETE FROM canonical_questions WHERE id=%s',(qid,))
