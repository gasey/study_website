import random
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..db import cursor
from ..deps import current_user
from ..schemas import (
    MockQuestion,
    MockResult,
    MockSession,
    MockStart,
    MockSubmission,
    MockReviewRow,
)

router = APIRouter(prefix="/api/mocks", tags=["mocks"])

#: Grace for a submit that was in flight when the clock ran out. Beyond this
#: the attempt still records, but is flagged `late` rather than silently
#: accepted — see migration 0006.
GRACE_SECONDS = 20


async def _candidate_ids(cur, collection_id: str, section_path: str | None) -> list[str]:
    """Scorable question ids for a collection, optionally one section.

    Reads v_scorable, so a mock can only ever contain questions with an
    official key. CLAUDE.md rule 1.
    """
    if section_path:
        await cur.execute(
            """SELECT query -> 'paper_ids' AS pids FROM collection_sections s
                JOIN collections c ON c.id = s.collection_id AND c.live_version = s.version
               WHERE s.collection_id = %s AND s.path = %s""",
            (collection_id, section_path),
        )
    else:
        await cur.execute(
            """SELECT jsonb_agg(p) AS pids FROM (
                 SELECT jsonb_array_elements(s.query -> 'paper_ids') AS p
                   FROM collection_sections s
                   JOIN collections c ON c.id = s.collection_id AND c.live_version = s.version
                  WHERE s.collection_id = %s) x""",
            (collection_id,),
        )
    row = await cur.fetchone()
    if not row or not row["pids"]:
        raise HTTPException(404, "no papers for that collection or section")

    await cur.execute(
        """SELECT DISTINCT v.id FROM v_scorable v
             JOIN appearances a ON a.canonical_id = v.id
            WHERE a.paper_id = ANY(%s)""",
        ([str(p) for p in row["pids"]],),
    )
    return [r["id"] for r in await cur.fetchall()]


@router.post("", response_model=MockSession)
async def start_mock(
    body: MockStart, user_id: Annotated[str, Depends(current_user)]
) -> MockSession:
    async with cursor() as cur:
        await cur.execute(
            "SELECT id FROM mock_sessions WHERE user_id = %s AND submitted_at IS NULL",
            (user_id,),
        )
        if await cur.fetchone():
            raise HTTPException(409, "a mock is already open; resume or submit it first")

        ids = await _candidate_ids(cur, body.collection_id, body.section_path)
        if len(ids) < body.count:
            raise HTTPException(
                422, f"only {len(ids)} keyed questions available; asked for {body.count}"
            )

        # Draw in Python and fetch by primary key. Never ORDER BY random():
        # measured 19.8 ms vs 0.67 ms, and it degrades as the bank grows.
        chosen = random.sample(ids, body.count)
        mock_id = uuid.uuid4().hex

        await cur.execute(
            """INSERT INTO mock_sessions
                 (id, user_id, collection_id, section_path, question_ids,
                  duration_seconds, marks_correct, marks_wrong)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING started_at""",
            (mock_id, user_id, body.collection_id, body.section_path, chosen,
             body.duration_minutes * 60, body.marks_correct, body.marks_wrong),
        )
        started = (await cur.fetchone())["started_at"]
        questions = await _load_questions(cur, chosen)

    return MockSession(
        id=mock_id, collection_id=body.collection_id, section_path=body.section_path,
        duration_seconds=body.duration_minutes * 60, started_at=started,
        seconds_remaining=body.duration_minutes * 60, questions=questions,
    )


async def _load_questions(cur, ids: list[str]) -> list[MockQuestion]:
    """Fetch by primary key and restore the frozen order. Answers are not
    selected at all — the client never receives them until submit."""
    await cur.execute(
        "SELECT id, question, options FROM canonical_questions WHERE id = ANY(%s)", (ids,)
    )
    by_id = {r["id"]: r for r in await cur.fetchall()}
    return [
        MockQuestion(id=i, position=n, question=by_id[i]["question"], options=by_id[i]["options"])
        for n, i in enumerate(ids)
        if i in by_id
    ]


@router.get("/current", response_model=MockSession | None)
async def current_mock(user_id: Annotated[str, Depends(current_user)]) -> MockSession | None:
    async with cursor() as cur:
        await cur.execute(
            """SELECT id, collection_id, section_path, question_ids, duration_seconds,
                      started_at,
                      GREATEST(0, duration_seconds
                               - EXTRACT(EPOCH FROM (now() - started_at)))::int AS remaining
                 FROM mock_sessions
                WHERE user_id = %s AND submitted_at IS NULL""",
            (user_id,),
        )
        row = await cur.fetchone()
        if row is None:
            return None
        questions = await _load_questions(cur, row["question_ids"])
    return MockSession(
        id=row["id"], collection_id=row["collection_id"], section_path=row["section_path"],
        duration_seconds=row["duration_seconds"], started_at=row["started_at"],
        seconds_remaining=row["remaining"], questions=questions,
    )


@router.post("/{mock_id}/submit", response_model=MockResult)
async def submit_mock(
    mock_id: str, body: MockSubmission, user_id: Annotated[str, Depends(current_user)]
) -> MockResult:
    async with cursor() as cur:
        await cur.execute(
            """SELECT question_ids, duration_seconds, marks_correct, marks_wrong,
                      submitted_at,
                      EXTRACT(EPOCH FROM (now() - started_at))::int AS elapsed
                 FROM mock_sessions WHERE id = %s AND user_id = %s""",
            (mock_id, user_id),
        )
        s = await cur.fetchone()
        if s is None:
            raise HTTPException(404, "no such mock for this device")
        if s["submitted_at"] is not None:
            raise HTTPException(409, "already submitted")

        # The clock is read here, from the row written at start. Nothing the
        # client sends influences it.
        elapsed = s["elapsed"]
        late = elapsed > s["duration_seconds"] + GRACE_SECONDS

        ids: list[str] = s["question_ids"]
        await cur.execute(
            "SELECT id, question, options, answer_text, explanation FROM canonical_questions WHERE id = ANY(%s)",
            (ids,),
        )
        qs = {r["id"]: r for r in await cur.fetchall()}
        given = {a.question_id: a.chosen_index for a in body.answers}

        rows, n_ok, n_bad, n_skip = [], 0, 0, 0
        for pos, qid in enumerate(ids):
            q = qs.get(qid)
            if q is None:
                continue
            opts: list[str] = q["options"]
            idx = given.get(qid)
            chosen_text = opts[idx] if idx is not None and 0 <= idx < len(opts) else None
            if chosen_text is None:
                n_skip += 1
                correct = False
            else:
                correct = chosen_text == q["answer_text"]
                n_ok += correct
                n_bad += not correct
                # chosen_text, not the index, so a later key fix can re-score.
                await cur.execute(
                    """INSERT INTO attempts
                         (user_id, canonical_id, correct, chosen_text, context, mock_id, position)
                       VALUES (%s,%s,%s,%s,'mock',%s,%s)""",
                    (user_id, qid, correct, chosen_text, mock_id, pos),
                )
            rows.append(MockReviewRow(
                position=pos, question_id=qid, question=q["question"],
                chosen_text=chosen_text, answer_text=q["answer_text"], correct=correct,
                explanation=q["explanation"],
            ))

        score = float(n_ok) * float(s["marks_correct"]) - float(n_bad) * float(s["marks_wrong"])
        await cur.execute(
            """UPDATE mock_sessions
                  SET submitted_at = now(), elapsed_seconds = %s, late = %s,
                      n_correct = %s, n_wrong = %s, n_skipped = %s, score = %s
                WHERE id = %s""",
            (elapsed, late, n_ok, n_bad, n_skip, score, mock_id),
        )

    return MockResult(
        id=mock_id, n_correct=n_ok, n_wrong=n_bad, n_skipped=n_skip, score=score,
        total=len(ids), elapsed_seconds=elapsed, late=late, review=rows,
    )
