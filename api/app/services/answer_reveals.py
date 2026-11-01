"""Serialize checking and viewing across tabs and all appearances of a question."""
from fastapi import HTTPException

async def lock_answer(cur, user_id, question_id):
    await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))",
                      ("answer-study:" + user_id + ":" + question_id,))

async def record_reveal(cur, user_id, question_id):
    await lock_answer(cur, user_id, question_id)
    await cur.execute("""INSERT INTO answer_reveals(user_id,canonical_id) VALUES(%s,%s)
      ON CONFLICT(user_id,canonical_id) DO UPDATE SET revealed_at=clock_timestamp()""",
      (user_id, question_id))

async def require_fresh_attempt(cur, user_id, question_id):
    await lock_answer(cur, user_id, question_id)
    await cur.execute("""SELECT 1 FROM answer_reveals WHERE user_id=%s AND canonical_id=%s
      AND revealed_at > clock_timestamp() - interval '30 minutes'""", (user_id, question_id))
    if await cur.fetchone():
        raise HTTPException(409, "Viewed answer: this question is in review mode. Retry after 30 minutes from your last reveal; no attempt or reward has been recorded.")
