"""Disposable UDC/MCS/admin browser rehearsal. No production data or writes."""
from pathlib import Path
import json
import sys
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest
from psycopg.types.json import Jsonb
from test_study_sessions import seed


if __name__=='__main__':
    databases=conftest.database.__wrapped__();database=next(databases)
    clients=conftest.client.__wrapped__(database);next(clients);clients.close()
    from app.config import settings
    from app.main import app
    from app.routers.auth import _hash_password
    import uvicorn
    settings.public_origin='http://127.0.0.1:5189'
    settings.mfa_enforce_staff=False
    conn=database[1];paper,ids=seed(database,23)
    for i,qid in enumerate(ids):
        text=f'Synthetic UDC practice {i+1:02d}: choose the second letter.'
        conn.execute('UPDATE canonical_questions SET question=%s,explanation=%s WHERE id=%s',
          (text,'Synthetic working: B is the second letter.',qid))
        conn.execute('UPDATE appearances SET question=%s,explanation=%s,page=1 WHERE canonical_id=%s',
          (text,'Synthetic working: B is the second letter.',qid))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,%s,%s,'test','manual','approved')",
          (qid,'english' if i<20 else 'mizo','English' if i<20 else 'Mizo'))
    conn.execute("UPDATE papers SET source_file='Old_Questions/test.pdf' WHERE id=%s",(paper,))
    udc_papers=[paper];mcs_papers={'gs':[],'aptitude':[]}
    for collection,prefix in [('udc','Old_Questions/Direct_NG_2024-2027/Assistant, UDC Paper-'),
                              ('combined-prelims','Old_Questions/Direct_2025-2027/MCS Combined 2025 Preliminary Exam Paper-')]:
        for role in ['I','II']:
            for series in ['A','B','C','D']:
                pid=prefix+role+(' Series ' if collection=='udc' else ' Series-')+series+'..pdf'
                conn.execute("INSERT INTO papers(id,exam_type,exam_name,year,paper_number,source_file) VALUES(%s,'Direct','Synthetic booklet rehearsal',2025,%s,%s) ON CONFLICT(id) DO UPDATE SET year=2025,paper_number=EXCLUDED.paper_number,source_file=EXCLUDED.source_file",(pid,role,pid))
                section='papers' if collection=='udc' else 'gs' if role=='I' else 'aptitude'
                conn.execute('''INSERT INTO collection_papers(collection_id,version,paper_id,section_path)
                  SELECT id,live_version,%s,%s FROM collections WHERE id=%s ON CONFLICT DO NOTHING''',(pid,section,collection))
                if collection=='udc':udc_papers.append(pid)
                else:mcs_papers[section].append(pid)
                for n in range(2):
                    qid='release-series-'+uuid4().hex
                    text=f'Synthetic {collection} Paper {role} matching text {n+1}: choose the second letter.'
                    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source,explanation) VALUES(%s,'mcq',%s,%s,'B','official','Synthetic matching booklet working.')",(qid,text,Jsonb(['A','B','C','D'])))
                    conn.execute("INSERT INTO appearances(id,paper_id,canonical_id,type,question,options,answer_index,answer_source,explanation,is_primary,qnum,page) VALUES(%s,%s,%s,'mcq',%s,%s,1,'official','Synthetic matching booklet working.',true,%s,1)",(qid,pid,qid,text,Jsonb(['A','B','C','D']),str(n+1)))
                    conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','test','manual','approved')",(qid,))
    conn.execute("UPDATE collection_sections SET query=%s WHERE collection_id='udc'",(Jsonb({'paper_ids':udc_papers}),))
    for section,pids in mcs_papers.items():
        conn.execute("UPDATE collection_sections SET query=%s WHERE collection_id='combined-prelims' AND path=%s",(Jsonb({'paper_ids':pids}),section))
    for user in ['owner','author']:
        conn.execute('UPDATE users SET password_hash=%s WHERE id=%s',(_hash_password('SyntheticPassword123!'),user))
    metadata={'database':database[0],'paper_id':paper,'question_ids':ids,'admin_question':ids[0],
              'owner_email':'owner@example.test','udc_sources':udc_papers,'mcs_sources':mcs_papers}
    Path('/tmp/udc-release-fixture.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('Synthetic release rehearsal: http://127.0.0.1:5189/exams/udc',flush=True)
    try:uvicorn.run(app,host='127.0.0.1',port=8019,log_level='warning')
    finally:databases.close()
