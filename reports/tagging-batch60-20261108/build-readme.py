"""Generate README.md for Batch 60."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 60: SEO under Sericulture General English Paper-II (100 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **100 existing questions reviewed: 60 retag proposals, 40 keep decisions, 0 tag holds. All 100 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper & 100% Paper Completion Milestone",
    "",
    "This batch achieves **100% paper completion** for the 100-MCQ General English Paper-II examination for Sericulture Extension Officer (SEO) under Sericulture Department:",
    "- *Competitive Examinations for Recruitment to the Post of Sericulture Extension Officer (SEO) under Sericulture Department, Government of Mizoram (2022) — General English Paper-II* (`Old_Questions/Direct_2022-2023/SEO under Sericulture Deptt 2022 General English-II..pdf`, `doc_488d90639b1b64f05e81c67e`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).",
    "",
    "## Granular Structuring & Taxonomy Alignment",
    "",
    "All 100 items were structured into active English taxonomy paths:",
    "- `english/grammar` (30 items, confirmed and kept from baseline):",
    "  - Q41–Q50: Sentence analysis and clause identification (noun clauses, adjective clauses, adverbial clauses).",
    "  - Q51–Q60: Sentence transformations without changing meaning (active/passive, degrees of comparison, assertive/interrogative, simple/complex).",
    "  - Q61–Q70: Sentence synthesis as directed (using participles, conjunctions, infinitives).",
    "- `english/grammar/parts-of-speech` (25 items, retagged from coarse baseline):",
    "  - Q1–Q10: Identification of parts of speech of underlined words in sentences (*fears, carefully, behind, wow, etc.*).",
    "  - Q21–Q30: Adjectives, adverbs, and degree modifiers.",
    "  - Q31, Q35, Q36, Q37, Q40: Conjunctions (*since, lest, as if, than, however*).",
    "- `english/grammar/tenses` (10 items, retagged from coarse baseline):",
    "  - Q11–Q20: Finite verb forms and aspect completion.",
    "- `english/grammar/prepositions` (5 items, retagged from coarse baseline):",
    "  - Q32–Q34, Q38–Q39: Prepositions (*look up, control over, among, accused of, leapt onto*).",
    "- `english/vocabulary` (10 items, confirmed and kept from baseline):",
    "  - Q71–Q80: Contextual vocabulary and blank completions.",
    "- `english/vocabulary/synonyms` (10 items, retagged from coarse baseline):",
    "  - Q81–Q90: Lexical synonyms of underlined words.",
    "- `english/vocabulary/antonyms` (10 items, retagged from coarse baseline):",
    "  - Q91–Q100: Lexical antonyms of underlined words.",
    "",
    "## Visual Source & Defect Analysis",
    "",
    "- **Underlined Target Words (Q1–Q10, Q81–Q100)**: Rendered in booklet with vector line strokes directly beneath target words; inspected and verified via PyMuPDF geometry.",
    "- **Preserved Question Fidelity**: Verified exact matching of question text, option texts, and choice ordering against official printed booklet.",
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
