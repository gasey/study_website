"""Finna Blocks: endless polyomino block-puzzle runs synced with the question bank and high-score leaderboards."""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..db import cursor
from ..deps import current_user
from ..services import audience

router = APIRouter(prefix="/api/blocks", tags=["blocks"])

IST = timezone(timedelta(hours=5, minutes=30))
ALLOWED_SUBJECT_SCOPES = {
    "all",
    "gk-gs",
    "english",
    "mathematics",
    "reasoning-and-aptitude",
    "mizo",
    "computer-science",
    "science",
}
BLOCKS_FILTER = """NOT EXISTS(
  SELECT 1 FROM creator_blocks cb
  WHERE (cb.user_id=%(viewer)s AND cb.blocked_id=u.id)
     OR (cb.user_id=u.id AND cb.blocked_id=%(viewer)s)
)"""


def _ist_today_str() -> str:
    return datetime.now(IST).date().isoformat()


def _max_plausible_score(pieces_placed: int, lines_cleared: int, questions_correct: int) -> int:
    # Generous upper bound covering up to 5-cell pieces, quad clears at 4x knowledge combo,
    # consecutive clear streaks, and question knowledge bonuses, while rejecting fabricated spikes.
    return max(0, pieces_placed * 80 + lines_cleared * 1200 + questions_correct * 650 + 500)


class StartBlockRun(BaseModel):
    mode: Literal["endless", "daily"] = "endless"
    subject_scope: str = Field(default="all", max_length=60)


class BlockRunProgress(BaseModel):
    score: int = Field(ge=0, le=10_000_000)
    lines_cleared: int = Field(ge=0, le=50_000)
    pieces_placed: int = Field(ge=0, le=100_000)
    questions_answered: int = Field(ge=0, le=50_000)
    questions_correct: int = Field(ge=0, le=50_000)
    best_streak: int = Field(ge=0, le=50_000)
    max_combo: int = Field(ge=1, le=50)
    clutch_saves_used: int = Field(default=0, ge=0, le=3)


@router.post("/runs")
async def start_block_run(
    body: StartBlockRun,
    user_id: Annotated[str, Depends(current_user)],
) -> dict:
    scope = body.subject_scope if body.subject_scope in ALLOWED_SUBJECT_SCOPES else "all"
    run_id = "blk_" + uuid4().hex[:20]
    daily_date = _ist_today_str() if body.mode == "daily" else None
    async with cursor() as cur:
        await cur.execute(
            """INSERT INTO block_puzzle_runs (id, user_id, mode, daily_date, subject_scope)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id, mode, daily_date, subject_scope, started_at""",
            (run_id, user_id, body.mode, daily_date, scope),
        )
        row = await cur.fetchone()
    return {
        "run_id": row["id"],
        "mode": row["mode"],
        "daily_date": row["daily_date"].isoformat() if row["daily_date"] else None,
        "daily_seed": f"finna-blocks-{daily_date}" if daily_date else None,
        "subject_scope": row["subject_scope"],
        "started_at": row["started_at"],
    }


async def _apply_run_progress(
    cur,
    run_id: str,
    user_id: str,
    body: BlockRunProgress,
    *,
    finish: bool,
) -> dict:
    await cur.execute(
        "SELECT * FROM block_puzzle_runs WHERE id=%s AND user_id=%s FOR UPDATE",
        (run_id, user_id),
    )
    run = await cur.fetchone()
    if not run:
        raise HTTPException(404, "Block puzzle run not found")
    if run["status"] == "finished" and not finish:
        return {
            "run_id": run["id"],
            "status": run["status"],
            "score": run["score"],
            "lines_cleared": run["lines_cleared"],
            "xp_awarded": run["xp_awarded"],
            "is_new_best": False,
        }

    q_answered = max(run["questions_answered"], body.questions_answered)
    q_correct = min(q_answered, max(run["questions_correct"], body.questions_correct))
    pieces = max(run["pieces_placed"], body.pieces_placed)
    lines = max(run["lines_cleared"], body.lines_cleared)
    streak = max(run["best_streak"], body.best_streak)
    max_combo = max(run["max_combo"], body.max_combo)
    clutch = max(run["clutch_saves_used"], min(3, body.clutch_saves_used))
    cap = _max_plausible_score(pieces, lines, q_correct)
    safe_score = min(max(run["score"], body.score), cap)

    # Check if this beats user's previous personal best in this mode
    await cur.execute(
        """SELECT COALESCE(max(score), 0)::int AS prev_best
           FROM block_puzzle_runs
           WHERE user_id=%s AND mode=%s AND id<>%s""",
        (user_id, run["mode"], run_id),
    )
    prev_best = (await cur.fetchone())["prev_best"]
    is_new_best = safe_score > prev_best and safe_score > 0

    xp_awarded = run["xp_awarded"]
    if finish and run["status"] != "finished" and (q_correct > 0 or lines > 0):
        # Award fair daily-capped XP for registered accounts (only when bank questions were answered)
        await cur.execute("SELECT email FROM users WHERE id=%s", (user_id,))
        u = await cur.fetchone()
        if u and u["email"] and q_correct > 0:
            raw_xp = min(35, q_correct * 3 + min(15, lines))
            await cur.execute(
                """SELECT COALESCE(sum(xp), 0)::int AS today_xp
                   FROM reward_ledger
                   WHERE user_id=%s
                     AND (created_at AT TIME ZONE 'Asia/Kolkata')::date
                       = (clock_timestamp() AT TIME ZONE 'Asia/Kolkata')::date""",
                (user_id,),
            )
            today_xp = (await cur.fetchone())["today_xp"]
            grant_xp = max(0, min(raw_xp, 300 - today_xp))
            if grant_xp > 0:
                await cur.execute(
                    """INSERT INTO reward_ledger (user_id, event_key, kind, xp, points, note, rule_version)
                       VALUES (%s, %s, 'game', %s, %s, %s, 'learning-v2')
                       ON CONFLICT (event_key) DO NOTHING""",
                    (
                        user_id,
                        f"blocks-run:{run_id}",
                        grant_xp,
                        min(5, q_correct),
                        f"Finna Blocks ({run['mode']}): {safe_score:,} pts · {lines} lines · {q_correct} MCQs",
                    ),
                )
                xp_awarded = grant_xp

    next_status = "finished" if finish else run["status"]
    await cur.execute(
        """UPDATE block_puzzle_runs
           SET score=%s,
               lines_cleared=%s,
               pieces_placed=%s,
               questions_answered=%s,
               questions_correct=%s,
               best_streak=%s,
               max_combo=%s,
               clutch_saves_used=%s,
               status=%s,
               xp_awarded=%s,
               finished_at=CASE WHEN %s THEN COALESCE(finished_at, now()) ELSE finished_at END,
               updated_at=now()
           WHERE id=%s
           RETURNING id, mode, status, score, lines_cleared, pieces_placed,
                     questions_answered, questions_correct, best_streak, max_combo, xp_awarded""",
        (
            safe_score,
            lines,
            pieces,
            q_answered,
            q_correct,
            streak,
            max_combo,
            clutch,
            next_status,
            xp_awarded,
            finish,
            run_id,
        ),
    )
    updated = dict(await cur.fetchone())
    updated["run_id"] = updated.pop("id")
    updated["is_new_best"] = is_new_best
    return updated


@router.post("/runs/{run_id}/checkpoint")
async def checkpoint_block_run(
    run_id: str,
    body: BlockRunProgress,
    user_id: Annotated[str, Depends(current_user)],
) -> dict:
    async with cursor() as cur:
        return await _apply_run_progress(cur, run_id, user_id, body, finish=False)


@router.post("/runs/{run_id}/finish")
async def finish_block_run(
    run_id: str,
    body: BlockRunProgress,
    user_id: Annotated[str, Depends(current_user)],
) -> dict:
    async with cursor() as cur:
        return await _apply_run_progress(cur, run_id, user_id, body, finish=True)


@router.get("/me")
async def my_block_stats(user_id: Annotated[str, Depends(current_user)]) -> dict:
    today_ist = _ist_today_str()
    async with cursor() as cur:
        await cur.execute(
            """SELECT
                 COALESCE(max(score) FILTER (WHERE mode='endless'), 0)::int AS best_endless,
                 COALESCE(max(score) FILTER (WHERE mode='daily' AND daily_date=%s::date), 0)::int AS best_daily_today,
                 COALESCE(max(lines_cleared), 0)::int AS best_lines,
                 count(*)::int AS total_runs,
                 COALESCE(sum(lines_cleared), 0)::int AS total_lines,
                 COALESCE(sum(questions_correct), 0)::int AS total_questions_correct
               FROM block_puzzle_runs
               WHERE user_id=%s AND score>0""",
            (today_ist, user_id),
        )
        summary = dict(await cur.fetchone())
        await cur.execute(
            """SELECT id, mode, daily_date, subject_scope, score, lines_cleared,
                      questions_answered, questions_correct, best_streak, status, updated_at
               FROM block_puzzle_runs
               WHERE user_id=%s AND score>0
               ORDER BY updated_at DESC
               LIMIT 8""",
            (user_id,),
        )
        recent = [dict(r) for r in await cur.fetchall()]
    return {**summary, "today_ist": today_ist, "recent_runs": recent}


@router.get("/leaderboard")
async def block_leaderboard(
    user_id: Annotated[str, Depends(current_user)],
    period: Literal["week", "all", "daily"] = Query(default="week"),
    limit: int = Query(default=15, ge=1, le=50),
) -> dict:
    today_ist = _ist_today_str()
    async with cursor() as cur:
        await cur.execute(
            """SELECT date_trunc('week', clock_timestamp() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' AS week_start"""
        )
        week_start = (await cur.fetchone())["week_start"]

        if period == "daily":
            where_period = "r.mode='daily' AND r.daily_date=%(today)s::date"
        elif period == "week":
            where_period = "r.updated_at >= %(week_start)s"
        else:
            where_period = "true"

        params = {
            "viewer": user_id,
            "today": today_ist,
            "week_start": week_start,
            "limit": limit,
        }
        await cur.execute(
            f"""WITH best_per_user AS (
                  SELECT DISTINCT ON (r.user_id)
                         r.user_id, r.score, r.lines_cleared, r.questions_correct,
                         r.best_streak, r.mode, r.updated_at
                  FROM block_puzzle_runs r
                  JOIN users u ON u.id=r.user_id AND u.email IS NOT NULL
                  LEFT JOIN reward_profiles rp ON rp.user_id=u.id
                  WHERE r.score > 0
                    AND ({where_period})
                    AND (COALESCE(rp.board_public, false) OR u.id=%(viewer)s)
                    AND {BLOCKS_FILTER}
                    AND {audience.eligible_sql('u.id')}
                  ORDER BY r.user_id, r.score DESC, r.lines_cleared DESC, r.updated_at ASC
                ),
                public_scores AS (
                  SELECT b.*, u.handle, u.avatar,
                         COALESCE(rp.board_public, false) AS board_public,
                         COALESCE(cp.public, false) AS profile_public,
                         GREATEST(1, floor(sqrt(GREATEST(0, COALESCE((SELECT sum(rl.xp) FROM reward_ledger rl WHERE rl.user_id=b.user_id), 0)) / 40.0)))::int AS level
                  FROM best_per_user b
                  JOIN users u ON u.id=b.user_id
                  LEFT JOIN reward_profiles rp ON rp.user_id=b.user_id
                  LEFT JOIN creator_profiles cp ON cp.user_id=b.user_id
                ),
                ranked AS (
                  SELECT *, dense_rank() OVER (ORDER BY score DESC, lines_cleared DESC)::int AS rank
                  FROM public_scores
                  WHERE board_public
                ),
                viewer_row AS (
                  SELECT s.score, s.lines_cleared, s.questions_correct, s.board_public,
                         1 + (SELECT count(DISTINCT p.score)::int FROM ranked p WHERE p.score > s.score) AS rank
                  FROM public_scores s
                  WHERE s.user_id=%(viewer)s
                )
                SELECT
                  (SELECT count(*)::int FROM ranked) AS total,
                  COALESCE((
                    SELECT jsonb_agg(jsonb_build_object(
                      'rank', r.rank,
                      'handle', r.handle,
                      'score', r.score,
                      'lines_cleared', r.lines_cleared,
                      'questions_correct', r.questions_correct,
                      'best_streak', r.best_streak,
                      'level', r.level,
                      'avatar', r.avatar,
                      'profile_public', r.profile_public,
                      'user_id', CASE WHEN r.profile_public OR r.user_id=%(viewer)s THEN r.user_id ELSE NULL END
                    ) ORDER BY r.rank, r.handle)
                    FROM (SELECT * FROM ranked ORDER BY rank, handle LIMIT %(limit)s) r
                  ), '[]'::jsonb) AS items,
                  (SELECT jsonb_build_object(
                    'rank', rank,
                    'score', score,
                    'lines_cleared', lines_cleared,
                    'questions_correct', questions_correct,
                    'public', board_public
                  ) FROM viewer_row) AS placement""",
            params,
        )
        row = dict(await cur.fetchone())
    return {
        "period": period,
        "today_ist": today_ist,
        "total": row["total"],
        "items": row["items"] or [],
        "placement": row["placement"],
    }
