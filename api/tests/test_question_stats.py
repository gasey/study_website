"""Aggregate per-question statistics (§VII.18 #2) — the first readers of
`v_question_stats` and `v_option_picks` since migration 0003 created them.

Pins the three properties that matter:
  * the population gate hides thin data, which is a **privacy** control as much as a
    noise one — below it, a per-option breakdown can say what one identifiable
    person chose;
  * stats appear only at a reveal moment, never with the question itself;
  * picks are reported against the question's own printed options, so option text
    that was later corrected cannot surface a choice nobody was offered.
"""
from __future__ import annotations

import json
from uuid import uuid4

from app.config import settings
from app.services.question_stats import MIN_ATTEMPTS, question_stats

ORIGIN = {'Origin': settings.public_origin}
OPTIONS = ['Alpha', 'Beta', 'Gamma', 'Delta']


def _seed_question(conn):
    paper_id = 'qs-paper-' + uuid4().hex[:8]
    qid = 'qs-q-' + uuid4().hex[:12]
    aid = 'qs-a-' + uuid4().hex[:12]
    opts = json.dumps(OPTIONS)
    with conn.transaction():
        conn.execute(
            "INSERT INTO papers(id, exam_type, exam_name, year) VALUES (%s,'Direct','Synthetic Stats Paper',2016)",
            (paper_id,),
        )
        conn.execute(
            """INSERT INTO canonical_questions(id, type, status, question, options, answer_text, answer_source)
               VALUES (%s,'mcq','live','Synthetic stats question',%s::jsonb,'Alpha','official')""",
            (qid, opts),
        )
        conn.execute(
            """INSERT INTO appearances(id, canonical_id, paper_id, type, question, options, qnum,
                 answer_index, answer_source, is_primary)
               VALUES (%s,%s,%s,'mcq','Synthetic stats question',%s::jsonb,'1',0,'official',true)""",
            (aid, qid, paper_id, opts),
        )
    return qid


def _attempts(conn, qid, picks):
    """picks: list of (chosen_text, count). Each attempt gets a distinct synthetic user."""
    with conn.transaction():
        for text, count in picks:
            for _ in range(count):
                uid = 'qs-u-' + uuid4().hex[:16]
                conn.execute(
                    "INSERT INTO users(id, email, handle) VALUES (%s, %s, %s)",
                    (uid, uid + '@example.test', uid),
                )
                conn.execute(
                    """INSERT INTO attempts(user_id, canonical_id, correct, chosen_text, context)
                       VALUES (%s,%s,%s,%s,'practice')""",
                    (uid, qid, text == 'Alpha', text),
                )


async def _stats(database, qid, options=OPTIONS):
    from app.db import cursor
    async with cursor() as cur:
        return await question_stats(cur, qid, options)


def test_below_the_population_gate_nothing_is_returned(client, database, anyio_backend=None):
    """One learner's pick must not be inferable from an aggregate."""
    import asyncio
    conn = database[1]
    qid = _seed_question(conn)
    _attempts(conn, qid, [('Beta', MIN_ATTEMPTS - 1)])
    assert asyncio.run(_stats(database, qid)) is None


def test_at_the_gate_shares_and_accuracy_are_reported(client, database):
    import asyncio
    conn = database[1]
    qid = _seed_question(conn)
    # 10 correct, 30 wrong: accuracy 25%, and the most popular option is wrong —
    # which is the case the whole feature exists to teach.
    _attempts(conn, qid, [('Alpha', 10), ('Beta', 25), ('Gamma', 5)])
    stats = asyncio.run(_stats(database, qid))
    assert stats is not None
    assert stats['attempts'] == 40
    assert stats['learners'] == 40
    assert round(stats['accuracy'], 2) == 0.25
    shares = {p['text']: p for p in stats['picks']}
    assert shares['Beta']['picks'] == 25
    assert shares['Beta']['share'] == 0.625
    assert shares['Alpha']['picks'] == 10
    # Every printed option is listed, including one nobody picked.
    assert shares['Delta']['picks'] == 0 and shares['Delta']['share'] == 0.0
    assert [p['text'] for p in stats['picks']] == OPTIONS  # printed order, not pick order


def test_picks_for_retired_option_text_are_not_listed(client, database):
    """Attempts store the chosen text, so a corrected option can hold picks for text
    no longer on the paper. Those must not appear as a choice."""
    import asyncio
    conn = database[1]
    qid = _seed_question(conn)
    _attempts(conn, qid, [('Alpha', 20), ('Betta (typo, since corrected)', 10)])
    stats = asyncio.run(_stats(database, qid))
    assert stats is not None
    assert stats['attempts'] == 30  # the retired pick still counts as an attempt
    assert [p['text'] for p in stats['picks']] == OPTIONS
    assert all('typo' not in p['text'] for p in stats['picks'])


def test_the_question_itself_never_carries_stats(client, database):
    """Pick distribution is a post-reveal disclosure, not part of the question."""
    conn = database[1]
    qid = _seed_question(conn)
    _attempts(conn, qid, [('Beta', MIN_ATTEMPTS + 5)])
    res = client.get(f'/api/questions/{qid}', headers=ORIGIN)
    assert res.status_code == 200, res.text
    assert 'stats' not in res.json()
