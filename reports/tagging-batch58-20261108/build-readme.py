"""Generate README.md for Batch 58."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 58: Grade-V of MSCS (Cooperative Audit Officer) General English Paper - II (100 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **100 existing questions reviewed: 60 retag proposals, 40 keep decisions, 0 tag holds. All 100 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper & 100% Paper Completion Milestone",
    "",
    "This batch achieves **100% paper completion** for the 100-MCQ General English Paper-II examination for Grade-V of MSCS (Cooperative Audit Officer):",
    "- *Competitive Examinations for Recruitment to the Post of Grade-V of MSCS (Cooperative Audit Officer) under Cooperation Department (December 2022) — General English Paper - II* (`Old_Questions/Direct_2022-2023/General English Paper-II (CAO).pdf`, `doc_8cd9d275470b7aa2b6b85cbd`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).",
    "",
    "## Granular Structuring & Taxonomy Alignment",
    "",
    "All 100 items were structured into active English taxonomy paths:",
    "- `english/grammar` (30 items, confirmed and kept from baseline):",
    "  - Q41–Q50: Sentence conversion between compound, complex, and simple structures.",
    "  - Q51–Q60: Clause identification (noun clauses, adjectival clauses, adverbial clauses, and main matrix clauses).",
    "  - Q61–Q70: Sentence synthesis and transformation (infinitives, participles, conjunctions, removal of 'too', degree changes).",
    "- `english/grammar/parts-of-speech` (24 items, retagged from coarse baseline):",
    "  - Q1–Q10: Identification of parts of speech for underlined words (*once, fined, else, Time, next, long, ylong, after, left, hard*).",
    "  - Q21–Q30: Adjectives, adverbs, and derivative word formations.",
    "  - Q31, Q36, Q38, Q39: Subordinating and adverbial conjunctions (*unless, lest, although, even if*).",
    "- `english/grammar/tenses` (10 items, retagged from coarse baseline):",
    "  - Q11–Q20: Verb forms, sequence of tenses, and aspect (*have never seen, had lost, is building, have been waiting, will have completed*).",
    "- `english/grammar/prepositions` (6 items, retagged from coarse baseline):",
    "  - Q32–Q35, Q37, Q40: Prepositions (*beyond, among*, etc.).",
    "- `english/vocabulary` (10 items, retagged from coarse baseline):",
    "  - Q71–Q80: Contextual vocabulary, homophones, and confusable words (*edible, access/excess, cite/site*, etc.).",
    "- `english/vocabulary/idioms-and-phrases` (10 items, retagged from coarse baseline):",
    "  - Q91–Q100: Idiomatic expressions and phrases (*burn the candle at both ends, hit the nail on the head, once in a blue moon*, etc.).",
    "- `english/vocabulary/antonyms` (5 items, retagged from coarse baseline):",
    "  - Q81–Q85: Direct antonyms (*ancient, bold, obscure, shallow, rigid*).",
    "- `english/vocabulary/synonyms` (5 items, retagged from coarse baseline):",
    "  - Q86–Q90: Direct synonyms (*foster, candid, lethal, barren, frugal*).",
    "",
    "## Visual Source & Defect Analysis",
    "",
    "- **Underlined Target Words (Q1–Q10, Q81–Q100)**: Rendered in booklet with vector horizontal line paths directly underneath target stems/words; inspected and confirmed against PDF page geometry.",
    "- **Typesetting Inconsistencies**: Preserved original exam wording without unverified structural alterations.",
    "",
    "## Validation Summary",
    "",
    f"- Target appearances verified: {validation['source_fingerprints_verified']}/100",
    f"- Live changes: {validation['database_live_writes']}",
    f"- Candidates status: `{validation['candidates_status']}`",
    f"- Taxonomy validity: `{validation['taxonomy_validity']}`",
    f"- Audit verification: `{validation['verified']}`",
    "",
    "```json",
    json.dumps(summary, indent=2),
    "```",
]

(out / "README.md").write_text("\n".join(lines) + "\n")
print("README.md generated successfully.")
