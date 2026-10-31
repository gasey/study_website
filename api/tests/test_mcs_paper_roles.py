"""MCS role filters follow appearances, with a shared canonical bank."""
from psycopg.types.json import Jsonb
from uuid import uuid4

def test_topic_map_is_scoped_by_source_paper_role(client,database):
 conn=database[1];suffix=uuid4().hex[:8]
 for role,subject in [('gs','general-studies'),('aptitude','english'),('gs','science')]:
  pid=f'mcs-role-{role}-{subject}-{suffix}';qid=f'mcs-q-{role}-{subject}-{suffix}'
  conn.execute("INSERT INTO papers(id,exam_type,exam_name,exam_scope_id) VALUES(%s,'Direct','Synthetic MCS source','mizoram-recruitment')",(pid,))
  conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) SELECT 'combined-prelims',live_version,%s,%s,false FROM collections WHERE id='combined-prelims'",(pid,role))
  conn.execute("UPDATE collection_sections SET query=jsonb_set(query,'{paper_ids}',COALESCE(query->'paper_ids','[]'::jsonb)||to_jsonb(%s::text)) WHERE collection_id='combined-prelims' AND version=2 AND path=%s",(pid,role))
  conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_source) VALUES(%s,'mcq','Synthetic MCS question',%s,'none')",(qid,Jsonb(['A','B','C','D'])))
  conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,canonical_id,is_primary,qnum,page) VALUES(%s,%s,'mcq','Synthetic MCS question',%s,%s,true,'1',1)",(qid,pid,Jsonb(['A','B','C','D']),qid))
  conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,%s,%s,'test','manual','approved')",(qid,subject,subject))
 gs=client.get('/api/collections/combined-prelims/study-topics?section_path=gs');assert gs.status_code==200
 aptitude=client.get('/api/collections/combined-prelims/study-topics?section_path=aptitude');assert aptitude.status_code==200
 assert gs.json()['questions']==2 and aptitude.json()['questions']==1
 assert gs.json()['subjects'][0]['id']=='gk-gs' and gs.json()['subjects'][0]['title']=='General Studies'
 assert aptitude.json()['subjects'][0]['id']=='english'
 assert client.get('/api/collections/combined-prelims/study-topics?section_path=missing').json()['questions']==0

 science=client.get('/api/questions?collection_id=combined-prelims&section_path=gs&subject_id=gk-gs&topic_id=gk-gs:science&pool=all')
 assert science.status_code==200 and science.json()['total']==1
 old=client.get('/api/questions?collection_id=combined-prelims&section_path=papers&pool=all')
 assert old.status_code==200 and old.json()['total']==3
