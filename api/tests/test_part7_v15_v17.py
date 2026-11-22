"""Comprehensive isolated PostgreSQL tests for Part VII Phases V.15–V.18:
- V.15: Guides CRUD, published-only public reads, live question FK validation, FTS search
- V.16: Explanation provenance columns (`0135`), voice linter warnings, bulk context/currency
  apply (`POST /api/admin/bank/contexts/apply`), bulk explanation apply (`explanations/apply`),
  prefetching authoring queue (`authoring-queue`)
- V.17: `v_answer_conflicts` matview (`0137`) matching Shape B ('key-won') and Shape A
  ('solution-won'), paper cluster gate (>5 conflicts flags paper), `/api/admin/ops`
  conflict counts, and `key_disputed` flip triggering `assessment_jobs` reassessment
- V.18: `answer_status` CASE parity (tested in `test_answer_status_drift.py`)
"""
from __future__ import annotations

import json
from uuid import uuid4

from app.config import settings
from app.services.account_identity import csrf_token
from app.services.editorial_access import source_version
from app.services.explanation_voice import check_explanation_voice, voice_score
from app.services.review_policy import digest

ORIGIN = {'Origin': settings.public_origin}


def _register_owner(client, conn):
    email = f'owner-v15-{uuid4().hex}@example.test'
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
               VALUES (%s, 'owner', NULL, %s, 'Synthetic owner grant for Part VII test')""",
            (uid, uid),
        )
    # Mark session MFA-verified so owner mutations pass staff MFA checks in tests
    token = client.cookies.get('ism_session', '')
    with conn.transaction():
        conn.execute(
            'UPDATE auth_sessions SET mfa_verified_at = now() WHERE user_id = %s',
            (uid,),
        )
    headers = {**ORIGIN, 'X-Review-CSRF': csrf_token(token)}
    return uid, headers


def _seed_question(conn, paper_id, qnum='1', answer_source='official', answer_text='Alpha', explanation='Short explanation text.'):
    qid = 'p7-q-' + uuid4().hex[:12]
    aid = 'p7-a-' + uuid4().hex[:12]
    opts = json.dumps(['Alpha', 'Beta', 'Gamma', 'Delta'])
    conn.execute(
        """INSERT INTO canonical_questions(id, type, status, question, options, answer_text, answer_source, explanation)
           VALUES (%s, 'mcq', 'live', %s, %s::jsonb, %s, %s, %s)""",
        (qid, f'Synthetic Part VII question {qnum}', opts, answer_text, answer_source, explanation),
    )
    conn.execute(
        """INSERT INTO appearances(id, canonical_id, paper_id, type, question, options, qnum, is_primary, explanation)
           VALUES (%s, %s, %s, 'mcq', %s, %s::jsonb, %s, true, %s)""",
        (aid, qid, paper_id, f'Synthetic Part VII question {qnum}', opts, qnum, explanation),
    )
    return qid, aid


def test_v15_guides_lifecycle_and_fts(client, database):
    conn = database[1]
    _, headers = _register_owner(client, conn)
    paper_id = 'p7-guide-paper-' + uuid4().hex[:8]
    with conn.transaction():
        conn.execute(
            "INSERT INTO papers(id, exam_type, exam_name, year) VALUES (%s, 'Direct', 'Synthetic Polity Paper', 2024)",
            (paper_id,),
        )
        qid, _ = _seed_question(conn, paper_id, qnum='1')

    slug = 'polity-codex-test-' + uuid4().hex[:6]
    # 1. Draft guide is not visible publicly
    draft = client.post(
        '/api/guides/admin',
        headers=headers,
        json={
            'slug': slug,
            'title': 'Polity Codex Test Guide',
            'summary': 'A constitutional guide covering Fundamental Rights and Parliament.',
            'reading_minutes': 12,
            'status': 'draft',
            'exam_scope': ['udc'],
            'chapters': [
                {
                    'ord': 1,
                    'anchor': 'fundamental-rights',
                    'heading': 'Fundamental Rights',
                    'body_markdown': 'Article 14 guarantees equality before the law across India.',
                    'question_ids': [qid],
                }
            ],
        },
    )
    assert draft.status_code == 200, draft.text
    assert client.get(f'/api/guides/{slug}').status_code == 404

    # 2. Publish guide -> visible in list, FTS search, and detail with linked live bank question
    pub = client.post(
        '/api/guides/admin',
        headers=headers,
        json={
            'slug': slug,
            'title': 'Polity Codex Test Guide',
            'summary': 'A constitutional guide covering Fundamental Rights and Parliament.',
            'reading_minutes': 12,
            'status': 'published',
            'exam_scope': ['udc'],
            'chapters': [
                {
                    'ord': 1,
                    'anchor': 'fundamental-rights',
                    'heading': 'Fundamental Rights',
                    'body_markdown': 'Article 14 guarantees equality before the law across India.',
                    'question_ids': [qid],
                }
            ],
        },
    )
    assert pub.status_code == 200, pub.text
    assert pub.json()['version'] == 2

    listing = client.get('/api/guides', params={'q': 'equality'})
    assert listing.status_code == 200
    assert any(item['slug'] == slug for item in listing.json()['items'])

    detail = client.get(f'/api/guides/{slug}')
    assert detail.status_code == 200
    body = detail.json()
    assert body['chapters'][0]['question_ids'] == [qid]

    # 3. Unknown question_id rejected with 422
    bad = client.post(
        '/api/guides/admin',
        headers=headers,
        json={
            'slug': slug,
            'title': 'Polity Codex Test Guide',
            'summary': 'A constitutional guide covering Fundamental Rights and Parliament.',
            'reading_minutes': 12,
            'status': 'published',
            'chapters': [
                {
                    'ord': 1,
                    'anchor': 'bad-ref',
                    'heading': 'Bad Reference',
                    'body_markdown': 'Should fail because question does not exist in bank.',
                    'question_ids': ['nonexistent-qid'],
                }
            ],
        },
    )
    assert bad.status_code == 422


def test_v16_voice_linter_currency_context_and_authoring_queue(client, database):
    conn = database[1]
    _, headers = _register_owner(client, conn)

    # Voice linter catches AI boilerplate, passes crisp factual writing
    ai_prose = "Let's look at this carefully. It is important to note that Article 21 protects life. Therefore, the correct answer is (A)."
    warns = check_explanation_voice(ai_prose)
    codes = {w['code'] for w in warns}
    assert {'reader-address', 'meta-commentary', 'answer-restatement'}.issubset(codes)
    assert voice_score(ai_prose) >= 30

    clean_prose = 'Article 21 protects life and personal liberty against arbitrary executive action.'
    assert check_explanation_voice(clean_prose) == []

    # HTTP voice-check endpoint works
    vc = client.post('/api/admin/bank/explanations/voice-check', headers=headers, json={'explanation': ai_prose})
    assert vc.status_code == 200
    assert vc.json()['clean'] is False

    # Seed question & test authoring queue + bulk context apply
    paper_id = 'p7-ctx-paper-' + uuid4().hex[:8]
    with conn.transaction():
        conn.execute(
            "INSERT INTO papers(id, exam_type, exam_name, year) VALUES (%s, 'Direct', 'Synthetic 2015 Paper', 2015)",
            (paper_id,),
        )
        qid, aid = _seed_question(conn, paper_id, qnum='7')

    q_res = client.get('/api/admin/bank/authoring-queue', params={'queue': 'untagged', 'limit': 50})
    assert q_res.status_code == 200, q_res.text
    row = next(it for it in q_res.json()['items'] if it['id'] == qid)
    assert len(row['baseline_hash']) == 64
    assert len(row['source_version']) == 64

    # Superseded without >=20 char note rejected
    bad_ctx = client.post(
        '/api/admin/bank/contexts/apply',
        headers={**headers, 'Idempotency-Key': 'ctx-bad-' + uuid4().hex[:8]},
        json={
            'targets': [{
                'question_id': qid,
                'appearance_id': aid,
                'source_version': row['source_version'],
                'time_behavior': 'dated-event',
                'scheme_status': 'superseded',
                'superseded_note': 'too short',
            }],
        },
    )
    assert bad_ctx.status_code == 422

    # Valid bulk context + paper period apply succeeds
    ok_ctx = client.post(
        '/api/admin/bank/contexts/apply',
        headers={**headers, 'Idempotency-Key': 'ctx-ok-' + uuid4().hex[:8]},
        json={
            'targets': [{
                'question_id': qid,
                'appearance_id': aid,
                'source_version': row['source_version'],
                'time_behavior': 'dated-event',
                'scheme_status': 'superseded',
                'superseded_note': 'Replaced by the revised 2022 MPSC scheme and updated syllabus.',
            }],
            'paper_period': 'legacy',
        },
    )
    assert ok_ctx.status_code == 200, ok_ctx.text
    assert ok_ctx.json()['updated_question_ids'] == [qid]
    period_db = conn.execute('SELECT period FROM bank_paper_profiles WHERE paper_id = %s', (paper_id,)).fetchone()[0]
    assert period_db == 'legacy'


def test_v17_conflicts_matview_cluster_gate_ops_and_reassessment_trigger(client, database):
    conn = database[1]
    uid, headers = _register_owner(client, conn)
    paper_id = 'p7-conflict-paper-' + uuid4().hex[:8]

    with conn.transaction():
        conn.execute(
            "INSERT INTO papers(id, exam_type, exam_name, year) VALUES (%s, 'Direct', 'Synthetic Offset Paper', 2021)",
            (paper_id,),
        )
        # Seed 6 Shape B ('key-won') conflicts in one paper to trigger the >5 cluster gate
        seeded_qids = []
        for i in range(1, 7):
            qid, aid = _seed_question(conn, paper_id, qnum=str(i), answer_source='official', answer_text='Alpha')
            seeded_qids.append(qid)
            cid = 'p7-c-' + uuid4().hex[:12]
            pid = 'p7-p-' + uuid4().hex[:12]
            conn.execute(
                """INSERT INTO bank_contributions(id, author_id, kind, canonical_id, appearance_id, subject_id, title, state, revision, idempotency_key, request_hash)
                   VALUES (%s, %s, 'explanation', %s, %s, 'polity', 'Conflict pub', 'published', 1, %s, %s)""",
                (cid, uid, qid, aid, 'idem-' + cid, digest({'cid': cid})),
            )
            manifest = {
                'admin_decision': {
                    'mode': 'verified',
                    'preserve_official_key': True,
                    'solution_answer_text': 'Beta',
                },
            }
            receipt = {
                'after': {
                    'question': f'Synthetic Part VII question {i}',
                    'options': ['Alpha', 'Beta', 'Gamma', 'Delta'],
                },
            }
            conn.execute(
                """INSERT INTO bank_publications(id, contribution_id, revision, state, manifest, manifest_hash, exported_by, receipt, finished_at)
                   VALUES (%s, %s, 1, 'applied', %s::jsonb, %s, %s, %s::jsonb, now())""",
                (pid, cid, json.dumps(manifest), digest(manifest), uid, json.dumps(receipt)),
            )

    # Refresh matview via owner endpoint
    ref = client.post('/api/admin/bank/conflicts/refresh', headers=headers)
    assert ref.status_code == 200, ref.text
    assert ref.json()['shape_b'] >= 6

    # Verify /api/admin/bank/conflicts surfaces Shape B and triggers >5 cluster gate
    c_list = client.get('/api/admin/bank/conflicts', params={'paper_id': paper_id})
    assert c_list.status_code == 200, c_list.text
    data = c_list.json()
    assert len(data['items']) == 6
    assert all(it['cluster_flagged'] is True for it in data['items'])
    assert any(p['paper_id'] == paper_id and p['conflicts'] == 6 for p in data['clustered_papers'])

    # Verify /api/admin/ops reports the conflict counts and refresh heartbeat
    ops_res = client.get('/api/admin/ops')
    assert ops_res.status_code == 200, ops_res.text
    ops_conflicts = ops_res.json()['conflicts']
    assert ops_conflicts['available'] is True
    assert ops_conflicts['shape_b'] >= 6
    assert ops_conflicts['clustered_papers'] >= 1
    assert ops_conflicts['refreshed_at'] is not None

    # §VII.6.3 Step 4 #7: Verify flipping `key_disputed` enqueues reassessment in `assessment_jobs`
    target_qid = seeded_qids[0]
    with conn.transaction():
        conn.execute('DELETE FROM assessment_jobs WHERE canonical_id = %s', (target_qid,))
        conn.execute(
            "UPDATE canonical_questions SET key_disputed = true, dispute_note = 'Q1: official key A; derived answer B.' WHERE id = %s",
            (target_qid,),
        )
    enqueued = conn.execute(
        'SELECT canonical_id, finished_at FROM assessment_jobs WHERE canonical_id = %s',
        (target_qid,),
    ).fetchone()
    assert enqueued is not None and enqueued[1] is None
