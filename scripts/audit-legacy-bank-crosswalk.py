#!/usr/bin/env python3
"""Conservatively map legacy Study Map questions to canonical bank IDs.

Only exact normalized question + ordered-option matches are emitted as
`exact_unique`. Ambiguous repeated questions and missing questions remain
visible in the CSV for review; this script never writes into either bank.
"""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT.parent / "mpsc-question-bankv2/bank/mpsc_bank_v2.json"
DEFAULT_LEGACY = ROOT.parent / "india-study-map/src/data/banks/mpsc-combined-prelims.json"


def normalize(value: object) -> str:
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\W+", " ", value, flags=re.UNICODE).strip()


def canonical_id(appearance_id: str) -> str:
    # Keep in lockstep with scripts/sync-bank.sh.
    return "cq_" + hashlib.md5(appearance_id.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--legacy", type=Path, default=DEFAULT_LEGACY)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/legacy-combined-prelims-crosswalk.csv")
    args = parser.parse_args()

    source_questions = json.loads(args.bank.read_text())['questions']
    legacy_questions = json.loads(args.legacy.read_text())['questions']
    index: dict[tuple[str, tuple[str, ...]], list[dict]] = defaultdict(list)
    for question in source_questions:
        key = (normalize(question.get('question')),
               tuple(normalize(option) for option in question.get('options') or []))
        index[key].append(question)

    counts: Counter[str] = Counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            'legacy_question_id', 'legacy_paper_id', 'legacy_number', 'status',
            'expected_canonical_id', 'source_appearance_id', 'candidate_count',
            'candidate_appearance_ids',
        ])
        writer.writeheader()
        for legacy in legacy_questions:
            key = (normalize(legacy.get('text', legacy.get('question'))),
                   tuple(normalize(option) for option in legacy.get('options') or []))
            matches = index.get(key, [])
            # A question reprinted in multiple source papers is not arbitrarily
            # assigned to one canonical row. Preserve all candidates for review.
            unique = {candidate['id']: candidate for candidate in matches}
            candidates = list(unique.values())
            status = 'exact_unique' if len(candidates) == 1 else (
                'ambiguous_exact' if candidates else 'unmatched')
            counts[status] += 1
            selected = candidates[0] if status == 'exact_unique' else None
            writer.writerow({
                'legacy_question_id': legacy.get('id', ''),
                'legacy_paper_id': legacy.get('paperId', ''),
                'legacy_number': legacy.get('number', legacy.get('qnum', '')),
                'status': status,
                'expected_canonical_id': canonical_id(selected['id']) if selected else '',
                'source_appearance_id': selected['id'] if selected else '',
                'candidate_count': len(candidates),
                'candidate_appearance_ids': '|'.join(c['id'] for c in candidates),
            })

    print(f"Legacy questions: {len(legacy_questions)}")
    for status in ('exact_unique', 'ambiguous_exact', 'unmatched'):
        print(f"{status}: {counts[status]}")
    print(f"Crosswalk: {args.output}")


if __name__ == '__main__':
    main()
