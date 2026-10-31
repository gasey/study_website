from test_account_hardening import headers as account_headers
"""Shared questions retain exam presentation, source scope and scoring policy."""
from uuid import uuid4
from psycopg.types.json import Jsonb
from test_admin_workbench import workbench
from app.services.question_readiness import answer_status_sql


def test_bounded_readiness_matches_authoritative_view(database,workbench):
    conn=database[1]
    rows=conn.execute(f"""SELECT v.id,({answer_status_sql()}) AS bounded,bs.answer_status
        FROM canonical_questions v JOIN v_bank_answer_status bs ON bs.id=v.id""").fetchall()
    assert rows
    assert all(row[1]==row[2] for row in rows)


def test_shared_question_keeps_udc_label_and_exam_source(client,actor,database,workbench):
    ids,paper,alt=workbench;conn=database[1];actor('author')
    qid=ids['unverified'];other=conn.execute('SELECT paper_id FROM appearances WHERE id=%s',(alt,)).fetchone()[0]
    # A newer appearance in another exam must not replace the active source.
    conn.execute('UPDATE papers SET year=2099 WHERE id=%s',(other,))
    conn.execute("UPDATE question_classifications SET subject_id='general-studies',subject_label='General Studies',topic_id=NULL,topic_label=NULL WHERE question_id=%s",(qid,))
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock) SELECT 'udc',live_version,%s,false FROM collections WHERE id='udc' ON CONFLICT DO NOTHING",(paper,))
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock) SELECT 'ldc',live_version,%s,false FROM collections WHERE id='ldc' ON CONFLICT DO NOTHING",(other,))
    try:
        for exam,source in [('udc',paper),('ldc',other)]:
            tree=client.get(f'/api/collections/{exam}/study-topics').json()
            knowledge=next(s for s in tree['subjects']if s['id']=='gk-gs')
            assert knowledge['title']=='General Knowledge'
            result=client.get('/api/questions',params={'collection_id':exam,'subject_id':'gk-gs','q':'Synthetic repair unverified'}).json()
            row=next(q for q in result['items']if q['id']==qid)
            assert row['source_appearance']['paper_id']==source
            assert row['taxonomy_subject_id']=='general-studies'  # Stored path remains compatible.
            assert row['answer_status']=='needs-review'
            assert not {'answer_text','answer_index','explanation'} & row.keys()
        # A paper in a launch exam still cannot expose an outside-only question.
        conn.execute("UPDATE papers SET exam_scope_id='outside-mizoram' WHERE id=ANY(%s)",([paper,other],))
        result=client.get('/api/questions',params={'collection_id':'udc','q':'Synthetic repair unverified'}).json()
        assert qid not in {q['id']for q in result['items']}
        result=client.get('/api/questions',params={'collection_id':'udc','q':'Synthetic repair unverified','exam_scope':'all'}).json()
        assert qid in {q['id']for q in result['items']}
    finally:
        conn.execute('DELETE FROM collection_papers WHERE paper_id=ANY(%s)',([paper,other],))
        conn.execute("UPDATE papers SET exam_scope_id='mizoram-recruitment' WHERE id=ANY(%s)",([paper,other],))


def test_lightweight_exam_header_respects_visibility_and_scope(client,database):
    conn=database[1];tag=uuid4().hex
    for suffix,visibility,scope in [('private','hidden','mizoram-recruitment'),('outside','public','outside-mizoram')]:
        conn.execute("INSERT INTO collections(id,title,kind,visibility,exam_scope_id) VALUES(%s,'Synthetic header exam','exam',%s,%s)",(tag+suffix,visibility,scope))
    try:
        row=client.get('/api/collections/udc/header');assert row.status_code==200,row.text
        assert set(row.json())=={'id','title','kind','route','visibility'}
        assert row.json()['id']=='udc'
        assert client.get('/api/collections/'+tag+'private/header',params={'exam_scope':'all'}).status_code==404
        assert client.get('/api/collections/'+tag+'outside/header').status_code==404
        assert client.get('/api/collections/'+tag+'outside/header',params={'exam_scope':'all'}).status_code==200
        assert client.get('/api/collections/not-a-real-exam/header').status_code==404
    finally:conn.execute('DELETE FROM collections WHERE id=ANY(%s)',([tag+'private',tag+'outside'],))


def test_paper_cards_reuse_verified_identity_and_invalidate_replaced_source(client,actor,database,workbench):
    from test_source_identity_retagging import identity_body
    _,paper,_=workbench;conn=database[1];h=actor('owner')
    body=identity_body(client,paper)
    assert client.post('/api/admin/bank/inventory/identity',headers=h,json=body).status_code==200
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock) SELECT 'ldc',live_version,%s,false FROM collections WHERE id='ldc' ON CONFLICT DO NOTHING",(paper,))
    try:
        item=next(p for p in client.get('/api/collections/ldc').json()['paper_list']if p['id']==paper)
        assert item['paper_label']==body['paper_title']
        conn.execute("UPDATE papers SET source_file='Old_Questions/replaced-polish.pdf' WHERE id=%s",(paper,))
        item=next(p for p in client.get('/api/collections/ldc').json()['paper_list']if p['id']==paper)
        assert item['paper_label']is None
    finally:conn.execute('DELETE FROM collection_papers WHERE paper_id=%s',(paper,))


def test_clerical_practice_records_the_displayed_source(client,actor,database,workbench):
    ids,paper,alt=workbench;conn=database[1];actor('author');qid=ids['unverified']
    other=conn.execute('SELECT paper_id FROM appearances WHERE id=%s',(alt,)).fetchone()[0]
    conn.execute("INSERT INTO collection_papers(collection_id,version,paper_id,as_mock) SELECT 'assistant',live_version,%s,false FROM collections WHERE id='assistant'",(other,))
    try:
        response=client.get('/api/questions',params={'collection_id':'assistant','q':'Synthetic repair unverified'})
        shown=next(q for q in response.json()['items']if q['id']==qid)
        assert shown['source_appearance']['paper_id']==other
        response=client.post('/api/questions/'+qid+'/answer', headers=account_headers(client),json={'chosen_index':0,'context':'practice','collection_id':'assistant','paper_id':shown['source_appearance']['paper_id']})
        assert response.status_code==200,response.text
        attempt=conn.execute("SELECT paper_id,collection_id,scoring_snapshot FROM attempts WHERE canonical_id=%s AND user_id='author' ORDER BY id DESC LIMIT 1",(qid,)).fetchone()
        assert attempt[0]==other and attempt[1]=='assistant'
        assert attempt[2]['appearance_id']==alt
        assert client.post('/api/questions/'+qid+'/answer', headers=account_headers(client),json={'chosen_index':0,'context':'practice','collection_id':'assistant','paper_id':paper}).status_code==422
    finally:conn.execute("DELETE FROM collection_papers WHERE collection_id='assistant' AND paper_id=%s",(other,))
