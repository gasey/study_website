from typing import Annotated

from fastapi import APIRouter, Depends

from ..db import cursor
from ..deps import current_user
from ..schemas import Mistake, Progress

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("/progress", response_model=Progress)
async def my_progress(user_id: Annotated[str, Depends(current_user)]) -> Progress:
    async with cursor() as cur:
        await cur.execute(
            """SELECT COUNT(*)::int AS answered,
                      COUNT(*) FILTER (WHERE correct)::int AS correct,
                      COUNT(DISTINCT canonical_id)::int AS unique_questions
                 FROM attempts WHERE user_id = %s""",
            (user_id,),
        )
        row = await cur.fetchone()
    return Progress(**(row or {"answered": 0, "correct": 0, "unique_questions": 0}))


@router.get("/mistakes", response_model=list[Mistake])
async def my_mistakes(
    user_id: Annotated[str, Depends(current_user)],
    limit: int = 50,
) -> list[Mistake]:
    """Questions this device has got wrong and not since got right.

    A question answered wrong in March and right in April is not a mistake
    any more — showing it would waste the learner's time and understate
    their progress. So the filter is on the LATEST attempt per question,
    not on the existence of any wrong one.
    """
    async with cursor() as cur:
        await cur.execute(
            """WITH latest AS (
                 SELECT DISTINCT ON (canonical_id)
                        canonical_id, correct, chosen_text, at
                   FROM attempts
                  WHERE user_id = %s AND canonical_id IS NOT NULL
                  ORDER BY canonical_id, at DESC
               )
               SELECT q.id, q.question, q.options, q.answer_text, q.explanation,
                      l.chosen_text, l.at AS last_attempt,
                      (SELECT COUNT(*) FROM attempts a2
                        WHERE a2.user_id = %s AND a2.canonical_id = q.id
                          AND NOT a2.correct)::int AS times_wrong
                 FROM latest l
                 JOIN canonical_questions q ON q.id = l.canonical_id
                WHERE NOT l.correct
                ORDER BY l.at DESC
                LIMIT %s""",
            (user_id, user_id, limit),
        )
        return [Mistake(**r) for r in await cur.fetchall()]
