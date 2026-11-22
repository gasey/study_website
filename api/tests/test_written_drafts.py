"""Phase V.14 (§VII.9.1) test: written drafts accept all four descriptive kinds."""
from uuid import uuid4

from app.config import settings
from app.services.account_identity import csrf_token

ORIGIN = {'Origin': settings.public_origin}


def test_written_drafts_accept_all_descriptive_kinds(client, database):
    conn = database[1]
    email = f'drafts-{uuid4().hex}@example.test'
    reg = client.post('/api/auth/register', json={'email': email, 'password': 'StrongPassword123!'}, headers=ORIGIN)
    assert reg.status_code in (200, 201), reg.text
    csrf = csrf_token(client.cookies.get('ism_session', ''))
    headers = {**ORIGIN, 'X-Review-CSRF': csrf}

    with conn.transaction():
        paper_id = 'test-written-' + uuid4().hex
        conn.execute(
            "INSERT INTO papers(id,exam_type,exam_name,year) VALUES(%s,'Direct','Synthetic Written Paper',2025)",
            (paper_id,),
        )
        qids = {}
        for idx, kind in enumerate(('essay', 'letter', 'precis', 'comprehension'), start=1):
            qid = f'written-{kind}-{uuid4().hex}'
            qids[kind] = qid
            conn.execute(
                "INSERT INTO canonical_questions(id,type,question,answer_source) VALUES(%s,'descriptive',%s,'none')",
                (qid, f'Synthetic {kind} prompt'),
            )
            conn.execute(
                "INSERT INTO appearances(id,canonical_id,paper_id,type,question,qnum,is_primary,essay_kind) VALUES(%s,%s,%s,'descriptive',%s,%s,true,%s)",
                (f'app-{qid}', qid, paper_id, f'Synthetic {kind} prompt', str(idx), kind),
            )
        mcq_id = f'written-mcq-{uuid4().hex}'
        conn.execute(
            "INSERT INTO canonical_questions(id,type,question,answer_source) VALUES(%s,'mcq','Synthetic MCQ','none')",
            (mcq_id,),
        )
        conn.execute(
            "INSERT INTO appearances(id,canonical_id,paper_id,type,question,qnum,is_primary) VALUES(%s,%s,%s,'mcq','Synthetic MCQ','99',true)",
            (f'app-{mcq_id}', mcq_id, paper_id),
        )

    for kind, qid in qids.items():
        body = f'Private practice draft for {kind}'
        put = client.put(f'/api/me/essay-drafts/{qid}', json={'body': body}, headers=headers)
        assert put.status_code == 200, f'{kind}: {put.status_code} {put.text}'
        assert put.json()['body'] == body
        got = client.get(f'/api/me/essay-drafts/{qid}')
        assert got.status_code == 200
        assert got.json()['body'] == body

    # MCQ prompts remain rejected with 404.
    bad = client.put(f'/api/me/essay-drafts/{mcq_id}', json={'body': 'Not a written prompt'}, headers=headers)
    assert bad.status_code == 404
