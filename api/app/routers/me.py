from typing import Annotated

from fastapi import APIRouter, Depends

from ..db import cursor
from ..deps import current_user
from ..schemas import Progress

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
