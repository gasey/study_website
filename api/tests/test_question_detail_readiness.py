"""A bounded detail read must preserve authoritative readiness and source scope."""
from test_admin_workbench import workbench


def test_detail_matches_authoritative_readiness_without_revealing_answers(client,database,workbench):
    ids,_,_=workbench;conn=database[1];client.cookies.clear()
    for qid in ids.values():
        expected=conn.execute("SELECT bs.answer_status,(q.answer_source='derived' AND EXISTS(SELECT 1 FROM v_reviewed_answer_publications rp WHERE rp.canonical_id=q.id)) FROM canonical_questions q JOIN v_bank_answer_status bs ON bs.id=q.id WHERE q.id=%s",(qid,)).fetchone()
        response=client.get('/api/questions/'+qid)
        assert response.status_code==200,response.text
        body=response.json()
        assert (body['answer_status'],body['reviewed_derived'])==expected
        assert not {'answer_text','answer_index','explanation'} & body.keys()
        assert body['appearances']


def test_detail_keeps_outside_sources_closed_by_default_and_missing_ids_missing(client,database,workbench):
    ids,_,_=workbench;conn=database[1];client.cookies.clear();qid=ids['unverified']
    conn.execute("UPDATE papers SET exam_scope_id='outside-mizoram' WHERE id IN(SELECT paper_id FROM appearances WHERE canonical_id=ANY(%s))",(list(ids.values()),))
    assert client.get('/api/questions/'+qid).status_code==404
    response=client.get('/api/questions/'+qid,params={'exam_scope':'all'})
    assert response.status_code==200,response.text
    assert response.json()['answer_status']=='needs-review' and not response.json()['reviewed_derived']
    assert client.get('/api/questions/not-a-real-question').status_code==404
