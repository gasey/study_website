"""Isolated PostgreSQL: synthetic accounts/questions, no production access."""
import hashlib
import json
import os
from pathlib import Path
import sys
import re
from uuid import uuid4
import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'api'))
sys.path.insert(0,str(ROOT/'scripts'))

@pytest.fixture(scope='session')
def database():
    name='ism_review_test_'+uuid4().hex[:12]
    admin=psycopg.connect('dbname=postgres',autocommit=True)
    if not admin.execute("SELECT 1 FROM pg_roles WHERE rolname='mpsc'").fetchone():admin.execute('CREATE ROLE mpsc NOLOGIN')
    admin.execute('CREATE DATABASE '+name)
    conn=psycopg.connect('dbname='+name,autocommit=True)
    try:
        for path in sorted((ROOT/'api/migrations').glob('[0-9]*.sql')):
            if path.name.startswith('0005_'):
                # Legacy content migrations reference real path IDs. Seed only
                # empty synthetic paper metadata, never production questions.
                refs=set()
                for migration in (ROOT/'api/migrations').glob('*.sql'):
                    refs.update(re.findall(r"'(Old_Questions/[^']+\.pdf)'",migration.read_text()))
                for ref in refs:
                    conn.execute("INSERT INTO papers(id,exam_type,exam_name) VALUES (%s,'Direct','Synthetic migration fixture') ON CONFLICT DO NOTHING",(ref,))
            if path.name.startswith('0053_'):
                # This content migration deliberately checks its real predecessor
                # manifest. Supply its empty metadata in the disposable DB; no
                # production questions, answers or users are copied here.
                ids=json.loads((ROOT/'api/tests/fixtures/udc-v1-paper-ids.json').read_text())
                for ref in ids:
                    conn.execute("INSERT INTO papers(id,exam_type,exam_name,exam_scope_id) VALUES (%s,'Direct','Synthetic UDC predecessor','mizoram-recruitment') ON CONFLICT DO NOTHING",(ref,))
                conn.execute("DELETE FROM collection_papers WHERE collection_id='udc' AND version=1")
                conn.execute("DELETE FROM collection_sections WHERE collection_id='udc' AND version=1")
                conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES ('udc',1,'papers','Synthetic predecessor',0,%s)",(Jsonb({'paper_ids':ids}),))
                for ref in ids:
                    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock,section_path) VALUES ('udc',1,%s,false,'papers')",(ref,))
            try:conn.execute(path.read_text())
            except Exception as exc:raise RuntimeError(path.name+': '+str(exc)) from exc
        conn.execute("ALTER TABLE papers ALTER COLUMN exam_scope_id SET DEFAULT 'mizoram-recruitment'")
        conn.execute("ALTER TABLE collections ALTER COLUMN exam_scope_id SET DEFAULT 'mizoram-recruitment'")
        yield name,conn
    finally:
        conn.close();admin.execute('DROP DATABASE '+name+' WITH (FORCE)');admin.close()

@pytest.fixture(scope='session')
def client(database):
    name,conn=database
    for user in ['author','reviewer1','reviewer2','owner','outsider']:
        conn.execute("INSERT INTO users(id,handle,email,role) VALUES (%s,%s,%s,'learner')",(user,user,user+'@example.test'))
        token='test-session-'+user
        conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES (%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),user))
    for user,role in [('owner','owner'),('reviewer1','reviewer'),('reviewer2','senior')]:
        conn.execute("INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason) VALUES (%s,%s,%s,'test','Synthetic test permission')",(user,role,None if user=='owner' else 'english'))
    conn.execute("INSERT INTO papers(id,exam_type,exam_name,source_file,year) VALUES ('paper-test','Direct','Synthetic source paper','Old_Questions/test.pdf',2020)")
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES ('cq_test','mcq','Choose the correct synthetic option',%s,'B','derived')",(Jsonb(['A','B','C','D']),))
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES ('appearance-test','paper-test','mcq','Choose the correct synthetic option',%s,1,'derived','cq_test',true,'1',1)",(Jsonb(['A','B','C','D']),))
    conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES ('cq_test','english','English','test','manual','approved')")
    conn.execute("INSERT INTO review_taxonomy(id,label,level,version) VALUES ('english','English','subject','test'),('mizo','Mizo','subject','test')")
    conn.execute("INSERT INTO sync_log(bank_checksum,questions_in,finished_at) VALUES (%s,1,now())",('a'*64,))
    from app.config import settings
    settings.public_catalog_cache_seconds=0  # SQL tests mutate their isolated DB directly.
    settings.database_url='postgresql:///'+name
    settings.pool_min=1;settings.pool_max=6
    from app.main import app
    with TestClient(app,base_url='https://study.hawayu.in') as test:
        yield test

@pytest.fixture
def actor(client):
    def select(user):
        client.cookies.clear()
        client.cookies.set('ism_session','test-session-'+user)
        response=client.get('/api/review/session')
        assert response.status_code==200,response.text
        return {'Origin':'https://study.hawayu.in','X-Review-CSRF':response.json()['csrf']}
    return select

@pytest.fixture(autouse=True)
def isolate_write_rate_budget(database):
    """Each independent test owns a fresh budget; within-test limits stay real."""
    database[1].execute('DELETE FROM review_rate_buckets')
