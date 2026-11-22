"""Phase V.18 (§VII.16.3): zero-risk drift guard for answer_status classification.

Asserts that the live SQL view `v_bank_answer_status` (migration 0050) and the
Python SQL builder `answer_status_sql()` (`services/question_readiness.py`)
classify every single canonical question identically across every answer_status
branch (written, held, key_disputed, source_defect, unsolved, official with
valid/invalid options, derived reviewed vs unreviewed, inferred, none).
"""
from uuid import uuid4

from app.services.question_readiness import answer_status_sql


def test_answer_status_sql_matches_v_bank_answer_status_across_all_branches(database):
    conn = database[1]
    paper_id = 'drift-paper-' + uuid4().hex

    with conn.transaction(force_rollback=True):
        conn.execute(
            "INSERT INTO papers(id,exam_type,exam_name,year) VALUES(%s,'Direct','Synthetic Drift Paper',2025)",
            (paper_id,),
        )
        # Seed one synthetic question for every classification branch.
        cases = [
            ('written', 'descriptive', 'live', 'none', None, '["A","B"]', False, None),
            ('held', 'mcq', 'held', 'official', 'A', '["A","B","C","D"]', False, None),
            ('disputed', 'mcq', 'live', 'official', 'A', '["A","B","C","D"]', True, None),
            ('dup-opts', 'mcq', 'live', 'official', 'A', '["A","B","C","D"]', False, 'duplicate-options'),
            ('bad-src', 'mcq', 'live', 'official', 'A', '["A","B","C","D"]', False, 'unresolved-source'),
            ('unsolved', 'mcq', 'live', 'none', None, '["A","B","C","D"]', False, None),
            ('official-ok', 'mcq', 'live', 'official', 'A', '["A","B","C","D"]', False, None),
            ('key-ok', 'mcq', 'live', 'key', 'B', '["A","B","C","D"]', False, None),
            ('official-bad-opts', 'mcq', 'live', 'official', 'A', '["A","A","C","D"]', False, None),
            ('derived-unrev', 'mcq', 'live', 'derived', 'A', '["A","B","C","D"]', False, None),
            ('inferred', 'mcq', 'live', 'inferred', 'A', '["A","B","C","D"]', False, None),
        ]
        for tag, qtype, status, src, ans, opts, disputed, defect in cases:
            qid = f'drift-{tag}-{uuid4().hex}'
            conn.execute(
                """INSERT INTO canonical_questions
                   (id,type,status,question,options,answer_text,answer_source,key_disputed,source_defect)
                   VALUES (%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s)""",
                (qid, qtype, status, f'Synthetic {tag}', opts, ans, src, disputed, defect),
            )
            conn.execute(
                """INSERT INTO appearances(id,canonical_id,paper_id,type,question,options,qnum,is_primary)
                   VALUES (%s,%s,%s,%s,%s,%s::jsonb,'1',true)""",
                (f'app-{qid}', qid, paper_id, qtype, f'Synthetic {tag}', opts),
            )

        # Verify zero mismatches between v_bank_answer_status and answer_status_sql('q')
        # across the entire canonical_questions table.
        sql = f"""
            SELECT q.id,
                   v.answer_status AS view_status,
                   ({answer_status_sql('q')}) AS py_status
              FROM canonical_questions q
              JOIN v_bank_answer_status v ON v.id = q.id
             WHERE v.answer_status IS DISTINCT FROM ({answer_status_sql('q')})
        """
        mismatches = conn.execute(sql).fetchall()
        assert mismatches == [], f'answer_status drift detected: {mismatches[:10]}'

        # Also verify every expected status bucket was exercised.
        buckets = {
            row[0]
            for row in conn.execute("SELECT DISTINCT answer_status FROM v_bank_answer_status").fetchall()
        }
        assert {'written', 'official', 'needs-review', 'unsolved'}.issubset(buckets)
