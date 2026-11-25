"""Scheduled & on-demand Daily/Weekly Leaderboard Question-Picker microservice.

Pre-generates fair, official-key, non-technical question sets into `game_dailies`
(Daily Five) and `game_cups` (Weekly 25-Q Cup) ahead of time with:
- Strict non-technical allowlists (`balanced`, `gk`, `english`, `maths`, `computer`)
  so specialist medical/engineering/accounts subjects never leak into open boards.
- 30-day Daily / 8-week Cup no-repeat window across recently used question IDs.
- Safe owner preview, theme re-roll, and single-slot swap strictly locked once
  any learner has entered that day/week (`entries > 0`).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from . import game_selection as setup
from . import games as g

IST = ZoneInfo("Asia/Kolkata")
ThemeId = Literal["balanced", "gk", "english", "maths", "computer"]
SetKind = Literal["daily", "cup"]

GK_AND_COMPUTER_IDS: tuple[str, ...] = tuple(
    dict.fromkeys((*setup.PILLAR_MATCH_IDS["gk_gs"], "computer-science"))
)
ENGLISH_IDS: tuple[str, ...] = tuple(setup.PILLAR_MATCH_IDS["english"])
MATHS_IDS: tuple[str, ...] = tuple(setup.PILLAR_MATCH_IDS["everyday_math"])
COMPUTER_IDS: tuple[str, ...] = ("computer-science",)

THEMES: dict[str, dict] = {
    "balanced": {
        "id": "balanced",
        "label": "Balanced Core (GK + English + Maths)",
        "short": "Balanced Core",
        "description": "Fair non-technical mix across GK/Computer, General English, and Everyday Maths.",
        "match_ids": sorted(set(GK_AND_COMPUTER_IDS + ENGLISH_IDS + MATHS_IDS)),
        "daily_quotas": {"gk_gs": 3, "english": 1, "everyday_math": 1},
        "cup_quotas": {"gk_gs": 13, "english": 6, "everyday_math": 6},
    },
    "gk": {
        "id": "gk",
        "label": "Only GK & General Studies",
        "short": "Only GK",
        "description": "100% History, Geography, Polity, Economy, General Science & Mizoram GK.",
        "match_ids": sorted(
            {x for x in setup.PILLAR_MATCH_IDS["gk_gs"] if x != "computer-science"}
        ),
        "daily_quotas": None,
        "cup_quotas": None,
    },
    "english": {
        "id": "english",
        "label": "Only General English",
        "short": "Only English",
        "description": "100% Grammar, Vocabulary, Sentence Correction & Comprehension.",
        "match_ids": sorted(set(ENGLISH_IDS)),
        "daily_quotas": None,
        "cup_quotas": None,
    },
    "maths": {
        "id": "maths",
        "label": "Only Everyday Maths & Reasoning",
        "short": "Only Maths",
        "description": "100% Arithmetic, Percentages, Ratio, Mensuration, Geometry & Reasoning.",
        "match_ids": sorted(set(MATHS_IDS)),
        "daily_quotas": None,
        "cup_quotas": None,
    },
    "computer": {
        "id": "computer",
        "label": "Only Computer & IT",
        "short": "Only Computer",
        "description": "100% Computer Fundamentals, Networking, DBMS, Hardware & Office IT.",
        "match_ids": sorted(set(COMPUTER_IDS)),
        "daily_quotas": None,
        "cup_quotas": None,
    },
}

DEFAULT_DAILY_NO_REPEAT_DAYS = 30
DEFAULT_CUP_NO_REPEAT_DAYS = 56


def theme_catalog() -> list[dict]:
    return [
        {
            "id": t["id"],
            "label": t["label"],
            "short": t["short"],
            "description": t["description"],
        }
        for t in THEMES.values()
    ]


def validate_theme(theme: str) -> dict:
    spec = THEMES.get(theme)
    if not spec:
        raise HTTPException(
            422,
            f"Unknown theme '{theme}'. Choose one of: {', '.join(THEMES.keys())}.",
        )
    return spec


def daily_window_for_offset(
    now: datetime, day_offset: int = 0
) -> tuple[str, datetime, datetime]:
    local = now.astimezone(IST)
    target_date = local.date() + timedelta(days=day_offset)
    opens = datetime.combine(target_date, datetime.min.time(), IST)
    return target_date.isoformat(), opens, opens + timedelta(days=1)


def cup_window_for_offset(
    now: datetime, week_offset: int = 0
) -> tuple[str, datetime, datetime]:
    _, opens, closes = g.cup_window(now)
    if week_offset:
        opens = opens + timedelta(days=7 * week_offset)
        closes = closes + timedelta(days=7 * week_offset)
    return opens.date().isoformat(), opens, closes


async def recent_question_ids(
    cur,
    *,
    daily_days: int = DEFAULT_DAILY_NO_REPEAT_DAYS,
    cup_days: int = DEFAULT_CUP_NO_REPEAT_DAYS,
    exclude_daily_id: str | None = None,
    exclude_cup_id: str | None = None,
) -> list[str]:
    """Return distinct question IDs used recently in Daily Five or Weekly Cup."""
    seen: set[str] = set()

    await cur.execute(
        """SELECT id, questions FROM game_dailies
            WHERE opens_at >= now() - (%s * interval '1 day')""",
        (daily_days,),
    )
    for row in await cur.fetchall():
        if exclude_daily_id and row["id"] == exclude_daily_id:
            continue
        for q in row["questions"] or []:
            qid = q.get("id")
            if isinstance(qid, str):
                seen.add(qid)

    await cur.execute(
        """SELECT id, questions FROM game_cups
            WHERE opens_at >= now() - (%s * interval '1 day')""",
        (cup_days,),
    )
    for row in await cur.fetchall():
        if exclude_cup_id and row["id"] == exclude_cup_id:
            continue
        for q in row["questions"] or []:
            qid = q.get("id")
            if isinstance(qid, str):
                seen.add(qid)

    return sorted(seen)


async def build_picker_context(
    cur,
    kind: SetKind,
    theme: ThemeId = "balanced",
    *,
    excludes: list[str] | None = None,
    count_override: int | None = None,
) -> dict:
    spec = validate_theme(theme)
    mode = "daily" if kind == "daily" else "cup"
    ctx = await setup.resolve(cur, setup.Selection(kind="mixed"), mode)
    ctx["match_ids"] = list(spec["match_ids"])
    ctx["excludes"] = sorted(set(excludes or []))
    quotas = spec["daily_quotas"] if kind == "daily" else spec["cup_quotas"]
    if quotas and count_override is None:
        ctx["foundation_quotas"] = dict(quotas)
    else:
        ctx.pop("foundation_quotas", None)
    if count_override is not None:
        ctx["rules"]["questions"] = count_override
    if kind == "cup":
        ctx["label"] = f"Weekly Cup · {spec['short']}"
        ctx["source_label"] = f"MPSC Shared Non-Technical Core ({spec['short']})"
    else:
        ctx["label"] = f"Daily Five · {spec['short']}"
        ctx["source_label"] = f"MPSC Shared Non-Technical Core ({spec['short']})"
    return ctx


async def _draw_with_repeat_guard(
    cur,
    kind: SetKind,
    theme: ThemeId,
    recent_ids: list[str],
    *,
    extra_excludes: list[str] | None = None,
    count_override: int | None = None,
    allow_fallback: bool = False,
) -> list[dict]:
    hard_excludes = list(extra_excludes or [])
    combined_excludes = sorted(set(recent_ids) | set(hard_excludes))

    # First attempt: strict theme allowlist + full 30-day/8-week no-repeat guard
    ctx = await build_picker_context(
        cur, kind, theme, excludes=combined_excludes, count_override=count_override
    )
    try:
        return await setup.draw(cur, ctx)
    except HTTPException as exc:
        if exc.status_code != 409:
            raise

    # Second attempt: keep strict theme allowlist, relax recent-history exclusion if a narrow theme ran dry
    if recent_ids:
        ctx_relaxed = await build_picker_context(
            cur, kind, theme, excludes=hard_excludes, count_override=count_override
        )
        try:
            return await setup.draw(cur, ctx_relaxed)
        except HTTPException as exc:
            if exc.status_code != 409 or not allow_fallback:
                raise
    elif not allow_fallback:
        raise HTTPException(
            409,
            f"Not enough verified official-key questions available for theme '{theme}'.",
        )

    # Final fallback (only enabled for synthetic test databases with non-standard subject IDs)
    need = count_override or g.MODES[kind][0]
    return await g.draw(cur, need)


async def _entry_count(cur, kind: SetKind, set_id: str) -> int:
    if kind == "daily":
        await cur.execute(
            "SELECT count(*)::int AS n FROM game_daily_entries WHERE daily_id=%s",
            (set_id,),
        )
    else:
        await cur.execute(
            "SELECT count(*)::int AS n FROM game_cup_entries WHERE cup_id=%s",
            (set_id,),
        )
    row = await cur.fetchone()
    return int(row["n"] if row else 0)


async def pick_daily_set(
    cur,
    now: datetime,
    *,
    day_offset: int = 0,
    theme: ThemeId = "balanced",
    force_regenerate: bool = False,
    allow_fallback: bool = False,
) -> dict:
    did, opens, closes = daily_window_for_offset(now, day_offset)
    return await _pick_or_update_daily(
        cur,
        did,
        opens,
        closes,
        theme=theme,
        force_regenerate=force_regenerate,
        allow_fallback=allow_fallback,
    )


async def _pick_or_update_daily(
    cur,
    did: str,
    opens: datetime,
    closes: datetime,
    *,
    theme: ThemeId = "balanced",
    force_regenerate: bool = False,
    allow_fallback: bool = False,
) -> dict:
    await cur.execute(
        "SELECT pg_advisory_xact_lock(hashtext(%s))", ("game-daily:" + did,)
    )
    await cur.execute("SELECT * FROM game_dailies WHERE id=%s", (did,))
    existing = await cur.fetchone()
    if existing and not force_regenerate:
        return dict(existing) | {"created": False}

    if existing:
        entries = await _entry_count(cur, "daily", did)
        if entries > 0:
            raise HTTPException(
                409,
                f"Daily Five {did} already has {entries} player entry(s) and is locked for fairness.",
            )

    recent_ids = await recent_question_ids(cur, exclude_daily_id=did)
    questions = await _draw_with_repeat_guard(
        cur, "daily", theme, recent_ids, allow_fallback=allow_fallback
    )

    if existing:
        await cur.execute(
            "UPDATE game_dailies SET questions=%s WHERE id=%s RETURNING *",
            (Jsonb(questions), did),
        )
    else:
        await cur.execute(
            "INSERT INTO game_dailies(id,opens_at,closes_at,questions) VALUES(%s,%s,%s,%s) RETURNING *",
            (did, opens, closes, Jsonb(questions)),
        )
    row = await cur.fetchone()
    return dict(row) | {"created": not bool(existing), "regenerated": bool(existing)}


async def pick_weekly_cup(
    cur,
    now: datetime,
    *,
    week_offset: int = 0,
    theme: ThemeId = "balanced",
    force_regenerate: bool = False,
    allow_fallback: bool = False,
) -> dict:
    cid, opens, closes = cup_window_for_offset(now, week_offset)
    return await _pick_or_update_cup(
        cur,
        cid,
        opens,
        closes,
        theme=theme,
        force_regenerate=force_regenerate,
        allow_fallback=allow_fallback,
    )


async def _pick_or_update_cup(
    cur,
    cid: str,
    opens: datetime,
    closes: datetime,
    *,
    theme: ThemeId = "balanced",
    force_regenerate: bool = False,
    allow_fallback: bool = False,
) -> dict:
    await cur.execute(
        "SELECT pg_advisory_xact_lock(hashtext(%s))", ("game-cup:" + cid,)
    )
    await cur.execute("SELECT * FROM game_cups WHERE id=%s", (cid,))
    existing = await cur.fetchone()
    if existing and not force_regenerate:
        return dict(existing) | {"created": False}

    if existing:
        entries = await _entry_count(cur, "cup", cid)
        if entries > 0:
            raise HTTPException(
                409,
                f"Weekly Cup {cid} already has {entries} player entry(s) and is locked for fairness.",
            )

    recent_ids = await recent_question_ids(cur, exclude_cup_id=cid)
    questions = await _draw_with_repeat_guard(
        cur, "cup", theme, recent_ids, allow_fallback=allow_fallback
    )

    if existing:
        await cur.execute(
            "UPDATE game_cups SET questions=%s WHERE id=%s RETURNING *",
            (Jsonb(questions), cid),
        )
    else:
        await cur.execute(
            "INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,%s,%s,%s) RETURNING *",
            (cid, opens, closes, Jsonb(questions)),
        )
    row = await cur.fetchone()
    return dict(row) | {"created": not bool(existing), "regenerated": bool(existing)}


async def regenerate_set(
    cur,
    kind: SetKind,
    set_id: str,
    *,
    theme: ThemeId = "balanced",
) -> dict:
    validate_theme(theme)
    table = "game_dailies" if kind == "daily" else "game_cups"
    await cur.execute(f"SELECT id, opens_at, closes_at FROM {table} WHERE id=%s", (set_id,))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(404, f"{kind} set '{set_id}' was not found.")
    if kind == "daily":
        return await _pick_or_update_daily(
            cur,
            row["id"],
            row["opens_at"],
            row["closes_at"],
            theme=theme,
            force_regenerate=True,
        )
    return await _pick_or_update_cup(
        cur,
        row["id"],
        row["opens_at"],
        row["closes_at"],
        theme=theme,
        force_regenerate=True,
    )


async def swap_question(
    cur,
    kind: SetKind,
    set_id: str,
    position: int,
    *,
    theme: ThemeId = "balanced",
) -> dict:
    validate_theme(theme)
    lock_key = ("game-daily:" if kind == "daily" else "game-cup:") + set_id
    await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (lock_key,))
    table = "game_dailies" if kind == "daily" else "game_cups"
    await cur.execute(f"SELECT * FROM {table} WHERE id=%s", (set_id,))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(404, f"{kind} set '{set_id}' was not found.")

    entries = await _entry_count(cur, kind, set_id)
    if entries > 0:
        raise HTTPException(
            409,
            f"Cannot swap questions: {kind} '{set_id}' already has {entries} player entry(s).",
        )

    questions = list(row["questions"] or [])
    if position < 0 or position >= len(questions):
        raise HTTPException(422, f"Position {position} is out of range for this set.")

    current_ids = [q.get("id") for q in questions if isinstance(q.get("id"), str)]
    recent_ids = await recent_question_ids(
        cur,
        exclude_daily_id=set_id if kind == "daily" else None,
        exclude_cup_id=set_id if kind == "cup" else None,
    )
    replacement = await _draw_with_repeat_guard(
        cur,
        kind,
        theme,
        recent_ids,
        extra_excludes=current_ids,
        count_override=1,
    )
    if not replacement:
        raise HTTPException(409, "Could not find a fresh replacement question.")

    questions[position] = replacement[0]
    await cur.execute(
        f"UPDATE {table} SET questions=%s WHERE id=%s RETURNING *",
        (Jsonb(questions), set_id),
    )
    updated = await cur.fetchone()
    return dict(updated)


async def ensure_upcoming_sets(
    cur,
    now: datetime,
    *,
    days_ahead: int = 2,
    daily_theme: ThemeId = "balanced",
    cup_theme: ThemeId | None = None,
) -> dict:
    """Idempotently pre-generate today + upcoming Daily Five sets and Weekly Cup."""
    validate_theme(daily_theme)
    resolved_cup_theme: ThemeId = cup_theme or daily_theme
    validate_theme(resolved_cup_theme)

    dailies = []
    for offset in range(0, max(1, days_ahead) + 1):
        d = await pick_daily_set(cur, now, day_offset=offset, theme=daily_theme)
        dailies.append(
            {
                "id": d["id"],
                "opens_at": d["opens_at"].isoformat(),
                "created": bool(d.get("created")),
                "question_count": len(d.get("questions") or []),
            }
        )

    cups = []
    current_cup = await pick_weekly_cup(cur, now, week_offset=0, theme=resolved_cup_theme)
    cups.append(
        {
            "id": current_cup["id"],
            "opens_at": current_cup["opens_at"].isoformat(),
            "created": bool(current_cup.get("created")),
            "question_count": len(current_cup.get("questions") or []),
        }
    )

    # Pre-generate next week's cup too when within 48h of this Sunday's cup
    if current_cup["opens_at"] - now <= timedelta(hours=48):
        next_cup = await pick_weekly_cup(
            cur, now, week_offset=1, theme=resolved_cup_theme
        )
        cups.append(
            {
                "id": next_cup["id"],
                "opens_at": next_cup["opens_at"].isoformat(),
                "created": bool(next_cup.get("created")),
                "question_count": len(next_cup.get("questions") or []),
            }
        )

    return {
        "as_of": now.isoformat(),
        "daily_theme": daily_theme,
        "cup_theme": resolved_cup_theme,
        "dailies": dailies,
        "cups": cups,
    }


def _summarize_set(row: dict, kind: SetKind, entries: int, now: datetime) -> dict:
    questions = row.get("questions") or []
    pillar_counts: dict[str, int] = {}
    previews = []
    for idx, q in enumerate(questions):
        pillar = q.get("pillar_label") or q.get("pillar") or "General"
        pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1
        previews.append(
            {
                "position": idx,
                "id": q.get("id"),
                "question": q.get("question") or "",
                "options": q.get("options") or [],
                "answer_text": q.get("answer_text"),
                "pillar": q.get("pillar") or "gk_gs",
                "pillar_label": pillar,
                "exam_name": q.get("exam_name"),
                "year": q.get("year"),
            }
        )
    opens = row["opens_at"]
    closes = row["closes_at"]
    status = "closed" if now >= closes else "live" if now >= opens else "scheduled"
    return {
        "kind": kind,
        "id": row["id"],
        "opens_at": opens.isoformat(),
        "closes_at": closes.isoformat(),
        "status": status,
        "entries": entries,
        "locked": entries > 0,
        "question_count": len(previews),
        "pillar_counts": pillar_counts,
        "questions": previews,
    }


async def list_upcoming_sets(cur, now: datetime, *, days_ahead: int = 2) -> dict:
    daily_ids = [
        daily_window_for_offset(now, offset)[0]
        for offset in range(0, max(1, days_ahead) + 1)
    ]
    await cur.execute(
        """SELECT d.*,
                  (SELECT count(*)::int FROM game_daily_entries e WHERE e.daily_id = d.id) AS entries
             FROM game_dailies d
            WHERE d.id = ANY(%s)
            ORDER BY d.opens_at ASC""",
        (daily_ids,),
    )
    daily_rows = await cur.fetchall()
    dailies = [_summarize_set(r, "daily", int(r["entries"]), now) for r in daily_rows]

    cup_ids = [
        cup_window_for_offset(now, 0)[0],
        cup_window_for_offset(now, 1)[0],
    ]
    await cur.execute(
        """SELECT c.*,
                  (SELECT count(*)::int FROM game_cup_entries e WHERE e.cup_id = c.id) AS entries
             FROM game_cups c
            WHERE c.id = ANY(%s)
            ORDER BY c.opens_at ASC""",
        (cup_ids,),
    )
    cup_rows = await cur.fetchall()
    cups = [_summarize_set(r, "cup", int(r["entries"]), now) for r in cup_rows]

    return {
        "as_of": now.isoformat(),
        "timezone": "Asia/Kolkata",
        "no_repeat_daily_days": DEFAULT_DAILY_NO_REPEAT_DAYS,
        "no_repeat_cup_days": DEFAULT_CUP_NO_REPEAT_DAYS,
        "themes": theme_catalog(),
        "dailies": dailies,
        "cups": cups,
    }
