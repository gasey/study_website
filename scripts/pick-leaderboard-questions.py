#!/usr/bin/env python3
"""Scheduled microservice worker: pre-pick Daily Five & Weekly Cup leaderboard sets.

Runs via `finna-leaderboard-picker.timer` (00:05 & 18:00 IST daily) with zero
persistent RAM footprint, or on-demand from CLI:

  /srv/api/.venv/bin/python /srv/api/pick-leaderboard-questions.py --days-ahead 2 --json
  /srv/api/.venv/bin/python /srv/api/pick-leaderboard-questions.py --theme gk --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Support running both from `/srv/api/` (prod) and from repo `scripts/` (dev)
HERE = Path(__file__).resolve().parent
for candidate in (HERE, HERE.parent / "api"):
    if (candidate / "app").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from app.db import close_pool, cursor, open_pool
from app.services import games as g
from app.services import leaderboard_picker as picker


async def run_worker(args: argparse.Namespace) -> dict:
    await open_pool()
    try:
        async with cursor() as cur:
            now = await g.clock(cur)
            if args.dry_run:
                recent = await picker.recent_question_ids(cur)
                daily_qs = await picker._draw_with_repeat_guard(
                    cur, "daily", args.theme, recent
                )
                cup_theme = args.cup_theme or args.theme
                cup_qs = await picker._draw_with_repeat_guard(
                    cur, "cup", cup_theme, recent
                )
                return {
                    "dry_run": True,
                    "as_of": now.isoformat(),
                    "daily_theme": args.theme,
                    "cup_theme": cup_theme,
                    "recent_excluded_count": len(recent),
                    "daily_sample": [
                        {
                            "id": q["id"],
                            "pillar": q.get("pillar_label") or q.get("pillar"),
                            "question": (q.get("question") or "")[:120],
                        }
                        for q in daily_qs
                    ],
                    "cup_sample_count": len(cup_qs),
                }

            return await picker.ensure_upcoming_sets(
                cur,
                now,
                days_ahead=args.days_ahead,
                daily_theme=args.theme,
                cup_theme=args.cup_theme,
            )
    finally:
        await close_pool()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pre-generate fair non-technical Daily Five & Weekly Cup leaderboard sets."
    )
    parser.add_argument(
        "--days-ahead",
        type=int,
        default=2,
        help="How many days ahead of today (IST) to pre-pick Daily Five sets (default: 2).",
    )
    parser.add_argument(
        "--theme",
        choices=list(picker.THEMES.keys()),
        default="balanced",
        help="Subject theme for Daily Five (and default for Weekly Cup).",
    )
    parser.add_argument(
        "--cup-theme",
        choices=list(picker.THEMES.keys()),
        default=None,
        help="Optional separate subject theme for Weekly Cup.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview picked questions without writing to Postgres.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output.",
    )
    args = parser.parse_args()
    result = asyncio.run(run_worker(args))
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        created_d = sum(1 for d in result.get("dailies", []) if d.get("created"))
        created_c = sum(1 for c in result.get("cups", []) if c.get("created"))
        print(
            f"[leaderboard-picker] ok as_of={result.get('as_of')} "
            f"daily_theme={result.get('daily_theme')} cup_theme={result.get('cup_theme')} "
            f"created_dailies={created_d}/{len(result.get('dailies', []))} "
            f"created_cups={created_c}/{len(result.get('cups', []))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
