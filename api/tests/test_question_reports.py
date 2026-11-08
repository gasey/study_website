"""Private student reports use the existing staff queue, without editing answers."""
from test_learning_workflows import official, learner


def test_report_enters_staff_queue_once_without_changing_answer(client,actor,database):
    q,_,paper=official(database)
    user,headers=learner(database,actor)
    path='/api/review/questions/'+q+'/report'
    body={'kind':'wrong_key','note':'Please check the reasoning for the second option.','paper_id':paper}
    result=client.post(path,headers=headers,json=body)
    assert result.status_code==200,result.text
    assert client.post(path,headers=headers,json=body).json()==result.json()
    conn=database[1]
    row=conn.execute('SELECT kind,reporter_id,evidence_paper,status FROM content_reports WHERE id=%s',(result.json()['id'],)).fetchone()
    assert row==('wrong_key',user,paper,'open')
    assert conn.execute('SELECT answer_text,answer_source,status FROM canonical_questions WHERE id=%s',(q,)).fetchone()==('B','official','live')
    assert client.get('/api/admin/bank/reports').status_code==403
    actor('owner')
    assert any(r['id']==result.json()['id'] for r in client.get('/api/admin/bank/reports').json())


def test_report_requires_session_csrf_valid_source_and_useful_note(client,actor,database):
    q,_,paper=official(database)
    _,headers=learner(database,actor)
    path='/api/review/questions/'+q+'/report'
    body={'kind':'typo_ocr','note':'The question text appears to be missing a word.','paper_id':paper}
    assert client.post(path,json=body).status_code==403
    assert client.post(path,headers={**headers,'Origin':'https://elsewhere.test'},json=body).status_code==403
    assert client.post(path,headers=headers,json={**body,'note':' '*25}).status_code==422
    assert client.post(path,headers=headers,json={**body,'kind':'publish'}).status_code==422
    assert client.post(path,headers=headers,json={**body,'paper_id':'paper-test'}).status_code==404
    assert client.post(path+'/unknown',headers=headers,json=body).status_code==404
    client.cookies.clear()
    assert client.post(path,headers=headers,json=body).status_code==401
