#!/usr/bin/env python3
"""Read-only explanation voice audit & ranked cleanup packet generator (§VII.8.2).

Scans explanations in the target PostgreSQL database, scores them against the
shared voice rules (`app.services.explanation_voice`), and writes a ranked JSON
packet of the worst offenders for human review. Never writes bank data.

Usage:
  api/.venv/bin/python scripts/explanation-voice-report.py --dsn "$DATABASE_URL" --limit 500 --out /tmp/voice-packet.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))

import psycopg
from psycopg.rows import dict_row
from app.services.explanation_voice import check_explanation_voice, voice_score


def main() -> int:
    parser = argparse.ArgumentParser(description='Read-only explanation voice report.')
    parser.add_argument('--dsn', default=os.environ.get('DATABASE_URL', ''), help='PostgreSQL DSN')
    parser.add_argument('--limit', type=int, default=500, help='Maximum ranked offenders to emit')
    parser.add_argument('--model-only', action='store_true', help='Only scan rows where explanation_model IS NOT NULL')
    parser.add_argument('--out', default='', help='Optional JSON output path (defaults to stdout)')
    args = parser.parse_args()

    if not args.dsn:
        print('error: --dsn or DATABASE_URL is required', file=sys.stderr)
        return 2

    with psycopg.connect(args.dsn, row_factory=dict_row) as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        where = "WHERE a.is_primary AND coalesce(btrim(a.explanation), '') <> ''"
        if args.model_only:
            where += ' AND a.explanation_model IS NOT NULL'
        rows = conn.execute(
            f"""SELECT a.id AS appearance_id,
                       a.canonical_id,
                       a.paper_id,
                       a.qnum,
                       a.explanation,
                       a.explanation_model,
                       a.explanation_prompt_version,
                       a.explanation_human_edited
                  FROM appearances a
                  {where}
                 ORDER BY a.canonical_id"""
        ).fetchall()

    ranked = []
    for row in rows:
        warnings = check_explanation_voice(row['explanation'])
        score = voice_score(row['explanation'])
        if warnings:
            ranked.append({
                'score': score,
                'canonical_id': row['canonical_id'],
                'appearance_id': row['appearance_id'],
                'paper_id': row['paper_id'],
                'qnum': row['qnum'],
                'explanation_model': row['explanation_model'],
                'explanation_prompt_version': row['explanation_prompt_version'],
                'explanation_human_edited': row['explanation_human_edited'],
                'warnings': warnings,
                'before': row['explanation'],
            })

    ranked.sort(key=lambda item: (-item['score'], item['canonical_id']))
    payload = {
        'read_only': True,
        'scanned': len(rows),
        'flagged': len(ranked),
        'limit': args.limit,
        'items': ranked[: max(1, args.limit)],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + '\n', encoding='utf-8')
    else:
        print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
