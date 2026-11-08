"""Private source review API: exact evidence, real MFA, drafts only."""
from copy import deepcopy
from uuid import uuid4

import pytest

from app.services import mcq_solver_source_reviews as service
from test_learning_workflows import official


@pytest.fixture
def report(client, database, monkeypatch):
    q, a, p = official(database)
    doc = 'source-review-doc-' + uuid4().hex
    database[1].execute("INSERT INTO review_documents(id,paper_id,title,source_file,sha256,kind,registered_by) VALUES(%s,%s,'Synthetic source','synthetic.pdf',%s,'paper','test')", (doc, p, 'b'*64))
    item = {'id': a, 'canonical_id': q, 'title': 'Synthetic inspected source', 'decision': 'source_checked_draft',
            'expected': {'id': a, 'paperId': p, 'question': 'Synthetic learning question', 'options': ['A', 'B', 'C', 'D'], 'page': 1, 'qnum': '1'},
            'document_id': doc, 'source_sha256': 'b'*64, 'finding': 'Synthetic original source and calculation were compared by an AI operator.',
            'repair': 'Retain a separate derived-answer proposal for review.', 'selected_option_id': '0',
            'draft_explanation': 'Synthetic reasoning for the selected first option in this isolated integration fixture.',
            'initial_draft': {'do_not_expose': 'raw model output'}}
    value = {'id': 'synthetic-review-' + uuid4().hex, 'reviewed_on': '2026-11-06', 'items': [item]}
    monkeypatch.setattr(service, 'catalog', lambda: deepcopy(value))
    return value


def session(actor, database, mfa=True):
    headers = actor('owner')
    database[1].execute("UPDATE auth_sessions SET created_at=now(),mfa_verified_at=CASE WHEN %s THEN now() ELSE NULL END WHERE user_id='owner'", (mfa,))
    return headers


def request_for(client):
    r = client.get('/api/admin/mcq-solver/review')
    assert r.status_code == 200, r.text
    item = r.json()['items'][0]
    return item, {k: item[k] for k in ('source_version', 'question_version_hash')}


def test_private_owner_read_never_exposes_raw_model_output(client, actor, database, report):
    client.cookies.clear()
    assert client.get('/api/admin/mcq-solver/review').status_code == 401
    actor('outsider')
    assert client.get('/api/admin/mcq-solver/review').status_code == 403
    session(actor, database, False)
    r = client.get('/api/admin/mcq-solver/review')
    assert r.status_code == 200 and r.headers['cache-control'] == 'private, no-store'
    assert r.json()['can_save'] is False
    assert 'initial_draft' not in r.json()['items'][0] and 'do_not_expose' not in r.text


def test_mfa_csrf_and_no_arbitrary_publish_fields(client, actor, database, report):
    headers = session(actor, database, False)
    item, body = request_for(client)
    path = '/api/admin/mcq-solver/drafts/' + item['id']
    assert client.post(path, headers=headers, json=body).status_code == 403
    headers = session(actor, database)
    assert client.post(path, json=body).status_code == 403
    assert client.post(path, headers=headers, json={**body, 'publish': True}).status_code == 422
    assert client.post('/api/admin/mcq-solver/publish', headers=headers, json=body).status_code == 404


@pytest.mark.parametrize('decision', ['source_checked_draft', 'hold_format'])
def test_exact_draft_replay_no_source_answer_or_publication_changes(client, actor, database, report, decision):
    report['items'][0]['decision'] = decision
    headers = session(actor, database)
    item, body = request_for(client)
    conn = database[1]
    q, a = item['canonical_id'], item['id']
    before = conn.execute('SELECT to_jsonb(c) FROM canonical_questions c WHERE id=%s', (q,)).fetchone()
    appearance = conn.execute('SELECT to_jsonb(a) FROM appearances a WHERE id=%s', (a,)).fetchone()
    path = '/api/admin/mcq-solver/drafts/' + a
    r = client.post(path, headers=headers, json=body)
    assert r.status_code == 201, r.text
    receipt = r.json()
    assert receipt['state'] == 'draft' and not receipt['published_by_worker']
    assert client.post(path, headers=headers, json=body).json()['contribution_id'] == receipt['contribution_id']
    cid = receipt['contribution_id']
    assert conn.execute('SELECT to_jsonb(c) FROM canonical_questions c WHERE id=%s', (q,)).fetchone() == before
    assert conn.execute('SELECT to_jsonb(a) FROM appearances a WHERE id=%s', (a,)).fetchone() == appearance
    assert conn.execute('SELECT kind FROM bank_contributions WHERE id=%s', (cid,)).fetchone()[0] == ('answer' if decision == 'source_checked_draft' else 'defect')
    for table in ('bank_publications', 'contribution_decisions', 'contribution_credit'):
        assert conn.execute(f'SELECT count(*) FROM {table} WHERE contribution_id=%s', (cid,)).fetchone()[0] == 0
    event = conn.execute("SELECT detail FROM contribution_events WHERE contribution_id=%s AND action='mcq_solver_source_draft'", (cid,)).fetchone()[0]
    assert event['human_approval'] is None


def test_changed_source_or_registered_pdf_stops_draft(client, actor, database, report):
    headers = session(actor, database)
    item, body = request_for(client)
    conn = database[1]
    conn.execute("UPDATE appearances SET question='Later human correction' WHERE id=%s", (item['id'],))
    assert client.post('/api/admin/mcq-solver/drafts/' + item['id'], headers=headers, json=body).status_code == 409
    assert client.get('/api/admin/mcq-solver/review').json()['items'][0]['stale'] is True
    conn.execute('UPDATE appearances SET question=%s WHERE id=%s', (report['items'][0]['expected']['question'], item['id']))
    item, body = request_for(client)
    conn.execute('UPDATE review_documents SET sha256=%s WHERE id=%s', ('c'*64, item['document_id']))
    assert client.post('/api/admin/mcq-solver/drafts/' + item['id'], headers=headers, json=body).status_code == 409
    assert conn.execute('SELECT count(*) FROM bank_contributions WHERE canonical_id=%s', (item['canonical_id'],)).fetchone()[0] == 0
