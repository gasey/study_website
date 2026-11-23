"""The `no-explanation` authoring queue.

All five original queues are empty in production — tagging coverage is complete,
`period` was never populated, there are no open reports and no answer conflicts,
and nothing reaches the answer-stats threshold. Meanwhile 20,798 live questions
have no explanation at all. The console had nothing to offer on the one body of
work there are twenty thousand of.

This queue surfaces them, scoped to a **trustworthy answer**: writing an
explanation for an answer nobody has verified would be explaining a guess. These
tests pin that scoping, because it is the part that is a judgement rather than a
mechanism.
"""
from __future__ import annotations

import json
from uuid import uuid4

from app.config import settings
from app.services.account_identity import csrf_token

ORIGIN = {'Origin': settings.public_origin}
OPTIONS = ['Alpha', 'Beta', 'Gamma', 'Delta']


def _register_owner(client, conn):
    email = f'owner-explq-{uuid4().hex}@example.test'
    reg = client.post('/api/auth/register',
                      json={'email': email, 'password': 'StrongPassword123!'}, headers=ORIGIN)
    assert reg.status_code in (200, 201), reg.text
    uid = conn.execute('SELECT id FROM users WHERE email = %s', (email,)).fetchone()[0]
    with conn.transaction():
        conn.execute(
            """INSERT INTO review_grants(user_id, role, subject_id, granted_by, reason)
               VALUES (%s,'owner',NULL,%s,'Synthetic owner grant for queue test')""", (uid, uid))
        conn.execute('UPDATE auth_sessions SET mfa_verified_at = now() WHERE user_id = %s', (uid,))
    token = client.cookies.get('ism_session', '')
    return uid, {**ORIGIN, 'X-Review-CSRF': csrf_token(token)}


def _seed(conn, paper_id, *, explanation, answer_source='official',
          key_disputed=False, source_defect=None, status='live'):
    qid = 'eq-q-' + uuid4().hex[:12]
    aid = 'eq-a-' + uuid4().hex[:12]
    opts = json.dumps(OPTIONS)
    with conn.transaction():
        conn.execute(
            """INSERT INTO canonical_questions(id, type, status, question, options, answer_text,
                 answer_source, explanation, key_disputed, source_defect)
               VALUES (%s,'mcq',%s,'Synthetic queue question',%s::jsonb,'Alpha',%s,%s,%s,%s)""",
            (qid, status, opts, answer_source, explanation, key_disputed, source_defect))
        conn.execute(
            """INSERT INTO appearances(id, canonical_id, paper_id, type, question, options, qnum,
                 answer_index, answer_source, is_primary, explanation)
               VALUES (%s,%s,%s,'mcq','Synthetic queue question',%s::jsonb,'1',0,%s,true,%s)""",
            (aid, qid, paper_id, opts, answer_source, explanation))
    return qid


def _paper(conn):
    pid = 'eq-paper-' + uuid4().hex[:8]
    with conn.transaction():
        conn.execute("INSERT INTO papers(id, exam_type, exam_name, year) "
                     "VALUES (%s,'Direct','Synthetic Queue Paper',2017)", (pid,))
    return pid


def _queue(client, kind='no-explanation'):
    res = client.get('/api/admin/bank/authoring-queue', params={'queue': kind, 'limit': 50})
    assert res.status_code == 200, res.text
    return {it['id'] for it in res.json()['items']}


def test_unexplained_questions_with_an_official_key_are_queued(client, database):
    conn = database[1]
    _register_owner(client, conn)
    pid = _paper(conn)
    wanted = _seed(conn, pid, explanation=None)
    assert wanted in _queue(client)


def test_an_empty_string_explanation_counts_as_missing(client, database):
    """Transcription can leave '' rather than NULL; both mean 'no explanation'."""
    conn = database[1]
    _register_owner(client, conn)
    pid = _paper(conn)
    assert _seed(conn, pid, explanation='') in _queue(client)


def test_questions_that_already_have_an_explanation_are_not_queued(client, database):
    conn = database[1]
    _register_owner(client, conn)
    pid = _paper(conn)
    assert _seed(conn, pid, explanation='A worked explanation already exists.') not in _queue(client)


def test_an_unverified_answer_is_not_queued(client, database):
    """The scoping decision: you cannot explain an answer nobody has verified."""
    conn = database[1]
    _register_owner(client, conn)
    pid = _paper(conn)
    for source in ('derived', 'inferred', 'none'):
        assert _seed(conn, pid, explanation=None, answer_source=source) not in _queue(client), source


def test_a_disputed_key_is_not_queued(client, database):
    conn = database[1]
    _register_owner(client, conn)
    pid = _paper(conn)
    assert _seed(conn, pid, explanation=None, key_disputed=True) not in _queue(client)


def test_a_blocking_source_defect_is_not_queued(client, database):
    conn = database[1]
    _register_owner(client, conn)
    pid = _paper(conn)
    for defect in ('duplicate-options', 'unresolved-source'):
        assert _seed(conn, pid, explanation=None, source_defect=defect) not in _queue(client), defect


def test_a_held_question_is_not_queued(client, database):
    conn = database[1]
    _register_owner(client, conn)
    pid = _paper(conn)
    assert _seed(conn, pid, explanation=None, status='held') not in _queue(client)


def test_the_queue_carries_what_a_batch_needs(client, database):
    """explanations/apply requires baseline_hash and source_version per target."""
    conn = database[1]
    _register_owner(client, conn)
    pid = _paper(conn)
    qid = _seed(conn, pid, explanation=None)
    res = client.get('/api/admin/bank/authoring-queue', params={'queue': 'no-explanation', 'limit': 50})
    row = next(it for it in res.json()['items'] if it['id'] == qid)
    assert len(row['baseline_hash']) == 64
    assert len(row['source_version']) == 64
    assert row['answer_source'] == 'official'
    assert not row['explanation']


def _seed_taxonomy(conn):
    """apply_explanations binds an unclassified question to 'general-knowledge', and
    validate_evidence checks that subject against the registry."""
    with conn.transaction():
        conn.execute("INSERT INTO review_taxonomy(id,label,level,version) "
                     "VALUES ('general-knowledge','General Knowledge','subject','test') "
                     "ON CONFLICT DO NOTHING")


def test_several_explanations_publish_as_one_batch(client, database):
    """The throughput feature (§VIII.5.2 #4): N explanations in one call become one
    batch row, which is what lets the worker apply them in a single bank write
    instead of N. The console's ⌘⇧↵ queue exists to build this payload."""
    conn = database[1]
    _, headers = _register_owner(client, conn)
    _seed_taxonomy(conn)
    pid = _paper(conn)
    qids = [_seed(conn, pid, explanation=None) for _ in range(3)]

    rows = client.get('/api/admin/bank/authoring-queue',
                      params={'queue': 'no-explanation', 'limit': 50}).json()['items']
    by_id = {r['id']: r for r in rows}
    targets = [{
        'question_id': q,
        'appearance_id': by_id[q]['appearance_id'],
        'baseline_hash': by_id[q]['baseline_hash'],
        'source_version': by_id[q]['source_version'],
        'explanation': f'A worked explanation for question {i}, long enough to pass the minimum.',
    } for i, q in enumerate(qids)]

    res = client.post('/api/admin/bank/explanations/apply',
                      headers={**headers, 'Idempotency-Key': 'batch-' + uuid4().hex[:8]},
                      json={'targets': targets, 'reason': ''})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body['count'] == 3
    assert body['replayed'] is False

    # ONE batch row carrying all three contributions — this is what the worker groups on.
    row = conn.execute(
        'SELECT contribution_ids FROM bank_retag_batches WHERE id = %s', (body['batch_id'],)
    ).fetchone()
    assert row is not None, 'no batch row was written'
    assert len(row[0]) == 3
    assert set(row[0]) == set(body['contribution_ids'])

    kinds = conn.execute(
        'SELECT DISTINCT kind FROM bank_contributions WHERE id = ANY(%s)', (list(row[0]),)
    ).fetchall()
    assert [k[0] for k in kinds] == ['explanation']


def test_a_replayed_batch_does_not_create_a_second_batch_row(client, database):
    """UNIQUE(author_id, idempotency_key) would reject the retry; the replay guard
    returns the original batch instead."""
    conn = database[1]
    _, headers = _register_owner(client, conn)
    _seed_taxonomy(conn)
    pid = _paper(conn)
    qid = _seed(conn, pid, explanation=None)
    row = next(r for r in client.get('/api/admin/bank/authoring-queue',
                                     params={'queue': 'no-explanation', 'limit': 50}).json()['items']
               if r['id'] == qid)
    payload = {'targets': [{
        'question_id': qid, 'appearance_id': row['appearance_id'],
        'baseline_hash': row['baseline_hash'], 'source_version': row['source_version'],
        'explanation': 'A worked explanation long enough to clear the twenty character minimum.',
    }], 'reason': ''}
    key = 'replay-' + uuid4().hex[:8]

    first = client.post('/api/admin/bank/explanations/apply',
                        headers={**headers, 'Idempotency-Key': key}, json=payload)
    assert first.status_code == 200, first.text
    second = client.post('/api/admin/bank/explanations/apply',
                         headers={**headers, 'Idempotency-Key': key}, json=payload)
    assert second.status_code == 200, second.text
    assert second.json()['replayed'] is True
    assert second.json()['batch_id'] == first.json()['batch_id']
    # Scoped to this key: the fixture database is shared across tests in this module.
    same_key = conn.execute(
        'SELECT count(*) FROM bank_retag_batches WHERE idempotency_key = %s', (key,)
    ).fetchone()[0]
    assert same_key == 1, 'the retry wrote a second batch row for the same key'
