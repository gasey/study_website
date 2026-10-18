#!/usr/bin/env python3
"""Harvest the old shiksha-dev corpus into the local bank JSON.

Local is the source of truth (DECISIONS #5), and shiksha-dev is an archive
to read from, never a peer to sync with (DECISIONS #7). So this is strictly
one-way: old server -> local JSON. The Oracle VM then catches up through
scripts/sync-bank.sh like any other local change.

    ./scripts/harvest_old_server.py --report        # what would change
    ./scripts/harvest_old_server.py --explanations  # only fill in explanations
    ./scripts/harvest_old_server.py --all           # explanations + new questions

Nothing is written without --write. --report is the default.

Safety rules enforced here, from DECISIONS #7:
  * imported answers are NEVER 'official' or 'key'. mpsc_study has no
    answer_source at all, so every answer it holds is of unknown provenance
    and lands as 'inferred' — which keeps it out of v_scorable.
  * imported subjects are discarded. 98% of them are the placeholder 'gk'.
  * existing local rows are never overwritten except to fill an EMPTY
    explanation. The local bank wins every other conflict.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT.parent / "mpsc-question-bankv2" / "bank" / "mpsc_bank_v2.json"
HOST = "shiksha-dev"
DB = "mpsc_study"

norm = lambda s: re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
key = lambda s: hashlib.md5(norm(s).encode()).hexdigest()

# mpsc_study's `explanation` column is mostly NOT explanations. 42,742 of the
# 43,018 it yielded were the literal placeholder "[OCR extraction from
# Old_Questions]" — the old pipeline wrote a marker there, not prose. A
# COUNT(*) on that column therefore wildly overstates what is worth having
# (the real number is ~275). Anything matching these, or too short to be an
# explanation of anything, is discarded.
_JUNK = re.compile(
    r"ocr extraction|no explanation|not available|^n/?a$|^-+$|auto[- ]generated",
    re.I,
)


def useful_explanation(s: str | None) -> str | None:
    s = (s or "").strip()
    if len(s) < 40 or _JUNK.search(s):
        return None
    return s


def fetch_old() -> list[dict]:
    """Pull the old corpus as JSON over ssh. Read-only; nothing is written
    to the remote except a temp file in /tmp."""
    # Base64 on the remote side. COPY's text format escapes backslashes and
    # tabs, which corrupts embedded JSON; -At still has to survive newlines
    # inside question text. Encoding sidesteps both.
    sql = (
        "SELECT encode(convert_to(json_agg(row_to_json(t))::text, 'UTF8'), 'base64') FROM ("
        "  SELECT q.id, q.question, q.options, q.answer_index, q.explanation,"
        "         q.type, q.year, p.exam_name, q.paper_id"
        "    FROM questions q LEFT JOIN papers p ON p.id = q.paper_id"
        "   WHERE q.question IS NOT NULL AND q.question <> ''"
        # Ordering is not cosmetic here. mpsc_study holds ~50k duplicate
        # question texts, and the dedup below keeps whichever copy it sees
        # FIRST. Without ORDER BY, Postgres returns rows arbitrarily, so the
        # representative changes between runs — two identical runs reported
        # 8,655 and 8,801 explanations to fill. Putting rows that HAVE an
        # explanation first makes the harvest both reproducible and maximal.
        "   ORDER BY (q.explanation IS NULL OR q.explanation = '') ASC, q.id ASC"
        ") t"
    )
    script = f"psql -d {DB} -At -c {json.dumps(sql)}"
    Path("/tmp/_harvest.sh").write_text(script + "\n")
    subprocess.run(
        ["scp", "-q", "-o", "BatchMode=yes", "/tmp/_harvest.sh", f"{HOST}:/tmp/_harvest.sh"],
        check=True,
    )
    out = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", HOST,
         "chmod 644 /tmp/_harvest.sh && su - postgres -c 'bash /tmp/_harvest.sh'"],
        check=True, capture_output=True, text=True,
    ).stdout
    import base64
    return json.loads(base64.b64decode("".join(out.split())))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--explanations", action="store_true", help="fill empty explanations")
    ap.add_argument("--all", action="store_true", help="explanations + unseen questions")
    ap.add_argument("--write", action="store_true", help="actually modify the bank")
    args = ap.parse_args()
    want_expl = args.explanations or args.all
    want_new = args.all

    print(f"reading {BANK.name} …")
    bank = json.loads(BANK.read_text())
    ours = bank["questions"]
    by_key: dict[str, dict] = {}
    for q in ours:
        by_key.setdefault(key(q["question"]), q)

    print(f"fetching {DB} from {HOST} …")
    old = fetch_old()
    print(f"  old rows: {len(old):,}")

    fill_expl, new_qs, seen = [], [], set()
    for o in old:
        k = key(o["question"])
        if not k or k in seen:
            continue
        seen.add(k)
        expl = useful_explanation(o.get("explanation"))
        if k in by_key:
            if expl and not (by_key[k].get("explanation") or "").strip():
                fill_expl.append((by_key[k], expl))
        else:
            new_qs.append(o)

    print("\n--- what this would do ---")
    print(f"  explanations to fill : {len(fill_expl):,}")
    print(f"  unseen questions     : {len(new_qs):,}")
    print(f"  bank size now        : {len(ours):,}")
    if want_new:
        print(f"  bank size after      : {len(ours) + len(new_qs):,}")

    if not args.write:
        print("\n(report only — pass --write to apply)")
        return 0
    if not (want_expl or want_new):
        print("\nnothing selected; pass --explanations or --all", file=sys.stderr)
        return 2

    backup = BANK.with_suffix(f".json.bak-before-harvest-{date.today():%Y%m%d}")
    shutil.copy2(BANK, backup)
    print(f"\nbacked up to {backup.name}")

    if want_expl:
        for q, expl in fill_expl:
            q["explanation"] = expl
        print(f"  filled {len(fill_expl):,} explanations")

    if want_new:
        for o in new_qs:
            ai = o.get("answer_index")
            if ai is not None and ai < 0:
                ai = None
            opts = o.get("options") or []
            if ai is not None and ai >= len(opts):
                ai = None  # would violate answer_in_range
            ours.append({
                # Namespaced so a harvested row is always identifiable later.
                "id": "old_" + hashlib.md5(o["id"].encode()).hexdigest()[:16],
                "paperId": o.get("paper_id"),
                "type": o.get("type") or ("mcq" if opts else "descriptive"),
                "question": o["question"],
                "options": opts,
                "answerIndex": ai,
                # Never 'official'/'key': the source records no provenance.
                "answerSource": "inferred" if ai is not None else None,
                "explanation": useful_explanation(o.get("explanation")),
                # subject/topic deliberately omitted — 98% are 'gk'.
                "harvestedFrom": "shiksha-dev:mpsc_study",
            })
        print(f"  added {len(new_qs):,} questions")

    BANK.write_text(json.dumps(bank, ensure_ascii=False))
    print(f"\nwrote {BANK}")
    print("next: ./scripts/sync-bank.sh --dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
