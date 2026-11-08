"""Real PostgreSQL schema, synthetic data only. No inference or live SSH writes."""
from uuid import uuid4

import pytest
from fastapi import HTTPException
from app.services.review_identity import Actor
from app.services import mcq_solver_drafts as solver
from test_learning_workflows import official


def capture(client, q, a, who=None):
    async def call():
        from app.db import cursor
        async with cursor() as cur:
            return await solver.capture(cur, who or Actor('owner', 'test', True, True), q, a)
    return client.portal.call(call)


def save(client, result, who=None):
    async def call():
        from app.db import cursor
        async with cursor() as cur:
            return await solver.save(cur, who or Actor('owner', 'test', True, True), result)
    return client.portal.call(call)


def output(snap, **changes):
    return solver.DraftResult(canonical_id=snap['canonical_id'], appearance_id=snap['appearance_id'],
        source_version=snap['source_version'], question_version_hash=snap['question_version_hash'],
        selected_option_id=changes.pop('selected_option_id', '1'),
        explanation='The second synthetic option follows from the defined arithmetic rule in this test fixture.',
        certainty='confident', review_reasons=['Original source requires human inspection'],
        model_id='synthetic-mock-model', reasoning='high', prompt_version='test-prompt-v1',
        solver_run_id=changes.pop('solver_run_id', uuid4().hex), **changes)


def test_five_separate_drafts_preserve_source_keys_and_no_publications(client, database):
    conn = database[1]
    pairs = [official(database)[:2] for _ in range(5)]
    ids = [q for q, a in pairs]
    before = conn.execute('SELECT to_jsonb(c) FROM canonical_questions c WHERE id=ANY(%s) ORDER BY id', (ids,)).fetchall()
    appearances = conn.execute('SELECT to_jsonb(a) FROM appearances a WHERE canonical_id=ANY(%s) ORDER BY id', (ids,)).fetchall()
    for i, (q, a) in enumerate(pairs):
        snap = capture(client, q, a)
        result = output(snap, selected_option_id='0' if i == 0 else '1')
        receipt = save(client, result)
        assert receipt['state'] == 'draft' and not receipt['published_by_worker']
        assert save(client, result)['contribution_id'] == receipt['contribution_id']
        cid = receipt['contribution_id']
        row = conn.execute('SELECT kind FROM bank_contributions WHERE id=%s', (cid,)).fetchone()
        assert row[0] == ('answer' if i == 0 else 'explanation')
        for table in ('bank_publications', 'contribution_decisions'):
            assert conn.execute(f'SELECT count(*) FROM {table} WHERE contribution_id=%s', (cid,)).fetchone()[0] == 0
        payload = conn.execute('SELECT payload FROM contribution_revisions WHERE contribution_id=%s', (cid,)).fetchone()[0]
        assert payload['patch'].get('answerSource', 'derived') == 'derived'
    assert before == conn.execute('SELECT to_jsonb(c) FROM canonical_questions c WHERE id=ANY(%s) ORDER BY id', (ids,)).fetchall()
    assert appearances == conn.execute('SELECT to_jsonb(a) FROM appearances a WHERE canonical_id=ANY(%s) ORDER BY id', (ids,)).fetchall()


def test_stale_source_and_document_metadata_rejected(client, database):
    conn = database[1]
    for mutation in ('text', 'documents'):
        q, a, p = official(database)
        snap = capture(client, q, a)
        if mutation == 'text':
            conn.execute("UPDATE appearances SET question='Changed source text' WHERE id=%s", (a,))
        else:
            conn.execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'Synthetic document','synthetic.pdf',%s,'paper','test')", ('solver-doc-'+uuid4().hex, p, 'a'*64))
        with pytest.raises(HTTPException) as error:
            save(client, output(snap))
        assert error.value.status_code == 409
        assert conn.execute('SELECT count(*) FROM bank_contributions WHERE canonical_id=%s', (q,)).fetchone()[0] == 0


def test_mfa_and_current_roles_required(client, database):
    q, a, _ = official(database)
    for who in (Actor('owner', 'test', True, False), Actor('owner', 'test', False, True), Actor('outsider', 'test', True, True)):
        with pytest.raises(HTTPException) as error:
            capture(client, q, a, who)
        assert error.value.status_code == 403


def test_explicit_account_exception_retains_recent_signin_and_role(client,database,monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','owner,outsider')
    q,a,_=official(database)
    snap=capture(client,q,a,Actor('owner','test',True,False))
    assert snap['canonical_id']==q
    for who in (Actor('owner','test',False,False),Actor('outsider','test',True,False),{'id':'owner'}):
        with pytest.raises(HTTPException) as error:
            capture(client,q,a,who)
        assert error.value.status_code==403


def test_wrong_appearance_null_and_invalid_option_never_saved(client, database):
    q, a, _ = official(database)
    snap = capture(client, q, a)
    for option in (None, 'A', '99'):
        with pytest.raises(HTTPException) as error:
            save(client, output(snap, selected_option_id=option))
        assert error.value.status_code == 422
    wrong = output(snap).model_copy(update={'appearance_id': 'wrong'})
    with pytest.raises(HTTPException):
        save(client, wrong)
    assert database[1].execute('SELECT count(*) FROM bank_contributions WHERE canonical_id=%s', (q,)).fetchone()[0] == 0


def test_unknown_answer_proposes_derived_only_and_replay_after_edit(client, database):
    q, a, _ = official(database)
    conn = database[1]
    conn.execute("UPDATE canonical_questions SET answer_text=NULL,answer_source='none' WHERE id=%s", (q,))
    conn.execute("UPDATE appearances SET answer_index=NULL,answer_source='none' WHERE id=%s", (a,))
    result = output(capture(client, q, a), selected_option_id='0')
    first = save(client, result)
    conn.execute("UPDATE appearances SET question='Later human source correction' WHERE id=%s", (a,))
    assert save(client, result)['contribution_id'] == first['contribution_id']
    assert conn.execute('SELECT answer_text FROM canonical_questions WHERE id=%s', (q,)).fetchone()[0] is None
    assert conn.execute('SELECT answer_index FROM appearances WHERE id=%s', (a,)).fetchone()[0] is None
