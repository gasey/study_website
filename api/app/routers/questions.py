from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import cursor
from ..deps import current_user
from ..schemas import (
    AnswerResult,
    AnswerSubmission,
    Appearance,
    QuestionDetail,
    QuestionListItem,
    QuestionPage,
)

router = APIRouter(prefix="/api/questions", tags=["questions"])

# Two pools, and the difference matters:
#   scorable — official/key answers only, 12,454 rows. Mocks, duels, cups.
#   practice — anything with an answer, 59,047 rows, answers unverified.
# See docs/DECISIONS.md #3.
POOLS = {
    "scorable": "v_scorable",
    "practice": "v_practice",
}

# Columns every question response is built from. Note the absence of
# answer_text: see schemas.py.
_COLS = """
    id, type, question, options, subject, topic, difficulty,
    answer_source,
    (answer_source IN ('official','key')) AS verified,
    source_defect, times_asked, first_year, last_year
"""


@router.get("", response_model=QuestionPage)
async def list_questions(
    pool: Literal["scorable", "practice"] = "practice",
    q: str | None = Query(None, min_length=2, max_length=120),
    year_from: int | None = Query(None, ge=1900, le=2100),
    year_to: int | None = Query(None, ge=1900, le=2100),
    source: Annotated[list[str] | None, Query()] = None,
    repeats_only: bool = False,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> QuestionPage:
    view = POOLS[pool]
    where: list[str] = []
    params: dict[str, object] = {}

    if source:
        # Whitelisted against the enum rather than interpolated: this value
        # reaches a query, and the CHECK constraint is not a sanitiser.
        allowed = {"official", "key", "derived", "inferred", "none"}
        chosen = [s for s in source if s in allowed]
        if not chosen:
            raise HTTPException(422, "no recognised answer_source values")
        where.append("answer_source = ANY(%(source)s)")
        params["source"] = chosen
    if repeats_only:
        where.append("times_asked >= 2")

    if q:
        # Uses the GIN index on the generated tsvector; ~0.1-0.5 ms at 77k rows.
        where.append("search @@ plainto_tsquery('english', %(q)s)")
        params["q"] = q
    if year_from is not None:
        where.append("last_year >= %(year_from)s")
        params["year_from"] = year_from
    if year_to is not None:
        where.append("first_year <= %(year_to)s")
        params["year_to"] = year_to

    clause = f"WHERE {' AND '.join(where)}" if where else ""

    async with cursor() as cur:
        await cur.execute(f"SELECT COUNT(*) AS n FROM {view} {clause}", params)
        row = await cur.fetchone()
        total = row["n"] if row else 0

        # Deliberately NOT `ORDER BY random()` — 19.8 ms vs 0.67 ms measured,
        # and it degrades as the bank grows. times_asked DESC is indexed and
        # puts genuinely repeated questions first, which is what a learner
        # browsing the bank wants anyway.
        await cur.execute(
            f"""SELECT {_COLS} FROM {view} {clause}
                ORDER BY times_asked DESC, id
                LIMIT %(limit)s OFFSET %(offset)s""",
            {**params, "limit": limit, "offset": offset},
        )
        items = [QuestionListItem(**r) for r in await cur.fetchall()]

    return QuestionPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{question_id}", response_model=QuestionDetail)
async def get_question(question_id: str) -> QuestionDetail:
    async with cursor() as cur:
        await cur.execute(
            f"SELECT {_COLS} FROM canonical_questions WHERE id = %s AND status <> 'merged'",
            (question_id,),
        )
        row = await cur.fetchone()
        if row is None:
            raise HTTPException(404, "question not found")

        await cur.execute(
            """SELECT a.paper_id, p.year, p.exam_name AS exam, p.paper_number AS paper,
                      a.qnum, a.page, a.series
                 FROM appearances a JOIN papers p ON p.id = a.paper_id
                WHERE a.canonical_id = %s
                ORDER BY p.year DESC NULLS LAST""",
            (question_id,),
        )
        appearances = [Appearance(**r) for r in await cur.fetchall()]

    return QuestionDetail(**row, appearances=appearances)


@router.post("/{question_id}/answer", response_model=AnswerResult)
async def answer_question(
    question_id: str,
    body: AnswerSubmission,
    user_id: Annotated[str, Depends(current_user)],
) -> AnswerResult:
    """Grade an answer, record the attempt, and reveal the key.

    Grading compares option TEXT, not index: the canonical row stores the
    answer as text precisely so a reprint with shuffled options cannot
    inherit the wrong letter.
    """
    async with cursor() as cur:
        await cur.execute(
            """SELECT options, answer_text, answer_source, explanation, status
                 FROM canonical_questions WHERE id = %s""",
            (question_id,),
        )
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(404, "question not found")
    if row["status"] != "live" or row["answer_text"] is None:
        # Held, withdrawn, or simply unanswered: 17,696 rows have no key at all.
        raise HTTPException(409, "this question has no usable answer")

    options: list[str] = row["options"]
    if body.chosen_index >= len(options):
        raise HTTPException(422, "chosen_index out of range")

    answer_text = row["answer_text"]
    try:
        answer_index = options.index(answer_text)
    except ValueError:
        # answer_text not among options. The schema CHECK makes this
        # impossible to store, so reaching here means data was changed
        # out from under the constraint.
        raise HTTPException(500, "answer is not one of the options") from None

    chosen_text = options[body.chosen_index]
    correct = chosen_text == answer_text

    # Store the TEXT the learner chose, not its index. When a key is later
    # corrected, attempts can be re-scored against the new answer; an index
    # would be meaningless if the options were ever re-ordered.
    async with cursor() as cur:
        await cur.execute(
            """INSERT INTO attempts (user_id, canonical_id, correct, chosen_text, context)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, question_id, correct, chosen_text, body.context),
        )

    return AnswerResult(
        correct=correct,
        answer_index=answer_index,
        answer_text=answer_text,
        answer_source=row["answer_source"],
        verified=row["answer_source"] in ("official", "key"),
        explanation=row["explanation"] or None,
    )
