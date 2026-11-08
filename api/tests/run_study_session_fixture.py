"""Disposable browser rehearsal; all questions/accounts are synthetic."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest
import uvicorn
from psycopg.types.json import Jsonb
from test_study_sessions import seed

if __name__=='__main__':
    databases=conftest.database.__wrapped__();database=next(databases)
    clients=conftest.client.__wrapped__(database);next(clients);clients.close()
    from app.config import settings
    from app.main import app
    settings.public_origin='http://127.0.0.1:5189'
    conn=database[1];paper,ids=seed(database,23)
    for i,q in enumerate(ids):
        conn.execute('UPDATE canonical_questions SET question=%s,explanation=%s WHERE id=%s',(f'Synthetic UDC practice {i+1:02d}: choose the second letter.','Synthetic working: B is the second letter.',q))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,%s,%s,'test','manual','approved')",(q,'english' if i<20 else 'mizo','English' if i<20 else 'Mizo'))
    conn.execute("UPDATE collection_sections SET query=%s WHERE collection_id='udc'",(Jsonb({'paper_ids':[paper]}),))
    print('Synthetic UDC sessions: http://127.0.0.1:5189/exams/udc?view=practice',flush=True)
    try:uvicorn.run(app,host='127.0.0.1',port=8019,log_level='warning')
    finally:databases.close()
