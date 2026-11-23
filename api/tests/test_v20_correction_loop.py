"""Isolated PostgreSQL tests for Part VIII Phase V.20 — the admin correction loop.

Covers, against a synthetic bank only:
- `/admin/bank/authoring-queue` serving the **appearance-level** record a
  correction is diffed against, plus `answer_index` / `answer_source` / `page`,
  so the keyboard console can edit text and re-map options (§VIII.5.1).
- `routine-edits` accepting `transcription` and `source_reference` — the kinds the
  shipped console never sent — and hard-requiring an `Idempotency-Key`, which the
  shipped console also never sent, so its taxonomy save returned 422.
- `/admin/bank/questions/{qid}/inspect` returning `baseline_token` (§VIII.5.2 #3).
- A learning-context save succeeding with no typed reason (§VIII.5.2 #7).
- The guard that must NOT relax: an option edit that does not re-map the recorded
  answer is still rejected (`review_policy.validate_target`).
"""
from __future__ import annotations

import json
from uuid import uuid4

from app.config import settings
from app.services.account_identity import csrf_token

ORIGIN = {'Origin': settings.public_origin}


def _register_owner(client, conn):
    email = f'owner-v20-{uuid4().hex}@example.test'
    reg = client.post(
        '/api/auth/register',
        json={'email': email, 'password': 'StrongPassword123!'},
        headers=ORIGIN,
    )
    assert reg.status_code in (200, 201), reg.text
    uid = conn.execute('SELECT id FROM users WHERE email = %s', (email,)).fetchone()[0]
    with conn.transaction():
        conn.execute(
            """INSERT INTO review_grants(user_id, role, subject_id, granted_by, reason)
               VALUES (%s, 'owner', NULL, %s, 'Synthetic owner grant for V.20 test')""",
            (uid, uid),
        )
    token = client.cookies.get('ism_session', '')
    with conn.transaction():
        conn.execute('UPDATE auth_sessions SET mfa_verified_at = now() WHERE user_id = %s', (uid,))
    return uid, {**ORIGIN, 'X-Review-CSRF': csrf_token(token)}


def _seed_taxonomy(conn):
    """Production's registry holds `general-knowledge`; the synthetic database starts
    empty. A non-taxonomy correction binds its proposal to the question's subject, and
    validate_evidence checks that subject against this registry."""
    with conn.transaction():
        conn.execute(
            "INSERT INTO review_taxonomy(id,label,level,version) "
            "VALUES ('general-knowledge','General Knowledge','subject','test') ON CONFLICT DO NOTHING"
        )


def _seed(conn, *, answer_index=0, page=4, qnum='7'):
    """Canonical and appearance text deliberately differ: the console must edit the
    appearance record, because that is what decide() diffs the patch against."""
    paper_id = 'v20-paper-' + uuid4().hex[:8]
    qid = 'v20-q-' + uuid4().hex[:12]
    aid = 'v20-a-' + uuid4().hex[:12]
    opts = json.dumps(['Alpha', 'Beta', 'Gamma', 'Delta'])
    with conn.transaction():
        conn.execute(
            "INSERT INTO papers(id, exam_type, exam_name, year) VALUES (%s, 'Direct', 'Synthetic V20 Paper', 2015)",
            (paper_id,),
        )
        conn.execute(
            """INSERT INTO canonical_questions(id, type, status, question, options, answer_text,
                 answer_source, explanation)
               VALUES (%s, 'mcq', 'live', %s, %s::jsonb, 'Alpha', 'official', 'Short explanation text.')""",
            (qid, 'CANONICAL projection of the question', opts),
        )
        conn.execute(
            """INSERT INTO appearances(id, canonical_id, paper_id, type, question, options, qnum, page,
                 answer_index, answer_source, is_primary, explanation)
               VALUES (%s, %s, %s, 'mcq', %s, %s::jsonb, %s, %s, %s, 'official', true,
                 'Short explanation text.')""",
            (aid, qid, paper_id, 'PRINTED apperance text with a typo', opts, qnum, page, answer_index),
        )
    return paper_id, qid, aid


def _row(client, qid):
    res = client.get('/api/admin/bank/authoring-queue', params={'queue': 'untagged', 'limit': 50})
    assert res.status_code == 200, res.text
    return next(it for it in res.json()['items'] if it['id'] == qid)


def test_authoring_queue_serves_the_editable_appearance_record(client, database):
    """The queue must hand back the exact bytes decide() will diff against, plus the
    answer fields an option re-map needs. Before V.20 it returned canonical text and
    no answer_index, so the console could not safely edit either."""
    conn = database[1]
    _register_owner(client, conn)
    _seed_taxonomy(conn)
    _, qid, aid = _seed(conn, answer_index=2, page=11, qnum='9')

    row = _row(client, qid)
    assert row['appearance_id'] == aid
    # Appearance text, not the canonical projection.
    assert row['question'] == 'PRINTED apperance text with a typo'
    assert row['options'] == ['Alpha', 'Beta', 'Gamma', 'Delta']
    assert row['answer_index'] == 2
    assert row['answer_source'] == 'official'
    assert row['page'] == 11
    assert row['qnum'] == '9'
    assert len(row['baseline_hash']) == 64 and len(row['source_version']) == 64


def test_routine_edit_requires_an_idempotency_key(client, database):
    """The shipped console called routine-edits with no Idempotency-Key header, so its
    primary action returned 422 and never wrote. This pins the requirement."""
    conn = database[1]
    _, headers = _register_owner(client, conn)
    _seed_taxonomy(conn)
    _, qid, aid = _seed(conn)
    row = _row(client, qid)

    res = client.post(
        '/api/admin/bank/routine-edits',
        headers=headers,  # deliberately no Idempotency-Key
        json={
            'kind': 'transcription',
            'canonical_id': qid,
            'appearance_id': aid,
            'patch': {'question': 'PRINTED appearance text with the typo fixed'},
            'baseline_hash': row['baseline_hash'],
            'source_version': row['source_version'],
        },
    )
    assert res.status_code == 422
    assert 'request key' in res.text.lower()


def test_console_can_fix_a_typo_and_the_printed_locator(client, database):
    """§VIII.5.1: `transcription` and `source_reference` are accepted with an
    auto-generated change summary and no typed note."""
    conn = database[1]
    _, headers = _register_owner(client, conn)
    _seed_taxonomy(conn)
    _, qid, aid = _seed(conn)
    row = _row(client, qid)

    fixed = 'PRINTED appearance text with the typo fixed'
    res = client.post(
        '/api/admin/bank/routine-edits',
        headers={**headers, 'Idempotency-Key': 'v20-txn-' + uuid4().hex[:8]},
        json={
            'kind': 'transcription',
            'canonical_id': qid,
            'appearance_id': aid,
            'patch': {'question': fixed},
            'note': '',  # no typed reason: the server writes a factual summary
            'baseline_hash': row['baseline_hash'],
            'source_version': row['source_version'],
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()['summary_kind'] == 'automatic_change_summary'
    reason = conn.execute(
        'SELECT reason FROM admin_bank_decisions WHERE canonical_id = %s', (qid,)
    ).fetchone()[0]
    assert 'question text' in reason

    # A second contribution-producing edit while the first is unpublished is refused —
    # this is why saveAndNext sends exactly one of them per save (§VIII.5.2 #2).
    clash = client.post(
        '/api/admin/bank/routine-edits',
        headers={**headers, 'Idempotency-Key': 'v20-src-' + uuid4().hex[:8]},
        json={
            'kind': 'source_reference',
            'canonical_id': qid,
            'appearance_id': aid,
            'patch': {'page': 12},
            'baseline_hash': row['baseline_hash'],
            'source_version': row['source_version'],
        },
    )
    assert clash.status_code == 409
    assert 'waiting for publication' in clash.text.lower()


def test_source_reference_edit_is_accepted_on_its_own(client, database):
    conn = database[1]
    _, headers = _register_owner(client, conn)
    _seed_taxonomy(conn)
    _, qid, aid = _seed(conn, page=4, qnum='7')
    row = _row(client, qid)

    res = client.post(
        '/api/admin/bank/routine-edits',
        headers={**headers, 'Idempotency-Key': 'v20-src-' + uuid4().hex[:8]},
        json={
            'kind': 'source_reference',
            'canonical_id': qid,
            'appearance_id': aid,
            'patch': {'page': 12},
            'baseline_hash': row['baseline_hash'],
            'source_version': row['source_version'],
        },
    )
    assert res.status_code == 200, res.text


def test_option_edit_without_a_remap_is_still_rejected(client, database):
    """The guard V.20 must not relax: review_policy.validate_target requires an
    explicit answerIndex whenever options move on a question that has an answer."""
    conn = database[1]
    _, headers = _register_owner(client, conn)
    _seed_taxonomy(conn)
    _, qid, aid = _seed(conn, answer_index=0)
    row = _row(client, qid)

    # Editing a NON-answer option still requires an explicit re-map.
    res = client.post(
        '/api/admin/bank/routine-edits',
        headers={**headers, 'Idempotency-Key': 'v20-opt-' + uuid4().hex[:8]},
        json={
            'kind': 'transcription',
            'canonical_id': qid,
            'appearance_id': aid,
            'patch': {'options': ['Alpha', 'Betaa', 'Gamma', 'Delta']},
            'baseline_hash': row['baseline_hash'],
            'source_version': row['source_version'],
        },
    )
    assert res.status_code == 422, res.text
    assert 're-map the answer index' in res.text

    # Editing the answer option itself trips the earlier, stronger guard: a moved
    # answer needs a supporting note, whatever else the patch carries.
    moved = client.post(
        '/api/admin/bank/routine-edits',
        headers={**headers, 'Idempotency-Key': 'v20-opt2-' + uuid4().hex[:8]},
        json={
            'kind': 'transcription',
            'canonical_id': qid,
            'appearance_id': aid,
            'patch': {'options': ['Alphaa', 'Beta', 'Gamma', 'Delta'], 'answerIndex': 0},
            'baseline_hash': row['baseline_hash'],
            'source_version': row['source_version'],
        },
    )
    assert moved.status_code == 422, moved.text
    assert 'correct answer needs a supporting note' in moved.text


def test_inspect_returns_the_stale_source_token(client, database):
    """§VIII.5.2 #3: the inline editor opens from this payload instead of refetching."""
    conn = database[1]
    _, headers = _register_owner(client, conn)
    _seed_taxonomy(conn)
    _, qid, aid = _seed(conn)

    res = client.get(
        f'/api/admin/bank/questions/{qid}/inspect',
        params={'appearance_id': aid},
        headers=ORIGIN,
    )
    assert res.status_code == 200, res.text
    snapshot = res.json()['snapshot']
    assert len(snapshot['baseline_token']) == 64
    assert len(snapshot['edit_hash']) == 64

    # It must be the token decide() accepts: a routine edit using it succeeds.
    ok = client.post(
        '/api/admin/bank/routine-edits',
        headers={**headers, 'Idempotency-Key': 'v20-ins-' + uuid4().hex[:8]},
        json={
            'kind': 'source_reference',
            'canonical_id': qid,
            'appearance_id': aid,
            'patch': {'page': 21},
            'baseline_hash': snapshot['edit_hash'],
            'source_version': snapshot['baseline_token'],
        },
    )
    assert ok.status_code == 200, ok.text


def test_learning_context_saves_without_a_typed_reason(client, database):
    """§VIII.5.2 #7: the write is versioned, source-signed and actor-stamped, and
    changes no bank content, so it carries no 20-character ceremony."""
    conn = database[1]
    uid, headers = _register_owner(client, conn)
    _seed_taxonomy(conn)
    _, qid, aid = _seed(conn)

    token = client.get(
        f'/api/admin/bank/questions/{qid}/inspect',
        params={'appearance_id': aid},
        headers=ORIGIN,
    ).json()['snapshot']['baseline_token']

    res = client.post(
        f'/api/admin/bank/organization/questions/{qid}/context',
        headers={**headers, 'Idempotency-Key': 'v20-ctx-' + uuid4().hex[:8]},
        json={
            'appearance_id': aid,
            'source_version': token,
            'expected_version': 0,
            'context': {'time_behavior': 'static'},
            # no 'reason'
        },
    )
    assert res.status_code == 200, res.text
    saved = conn.execute(
        'SELECT actor_id, version FROM bank_question_contexts WHERE question_id = %s', (qid,)
    ).fetchone()
    assert saved[0] == uid and saved[1] >= 1
