"""Generate README.md for Batch 59."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 59: Geologist Junior General English Paper-II (100 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **100 existing questions reviewed: 64 retag proposals, 36 keep decisions, 0 tag holds. All 100 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper & 100% Paper Completion Milestone",
    "",
    "This batch achieves **100% paper completion** for the 100-MCQ General English Paper-II examination for Geologist Junior under Commerce & Industries Department:",
    "- *Competitive Examinations for Recruitment to the Post of Geologist Junior under Commerce & Industries Department, Government of Mizoram (November 2022) — General English Paper - II* (`Old_Questions/Direct_2022-2023/Geologist Junior under Commerce Deptt - Gen English-II..pdf`, `doc_a9476c81c3142d879ad48676`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).",
    "",
    "## Granular Structuring & Taxonomy Alignment",
    "",
    "All 100 items were structured into active English taxonomy paths:",
    "- `english/grammar` (30 items, confirmed and kept from baseline):",
    "  - Q41–Q50: Sentence analysis and classification (Simple, Compound, Complex sentences).",
    "  - Q51–Q60: Functional sentence types (Declarative, Imperative, Interrogative, Exclamatory).",
    "  - Q61–Q70: Clause identification for underlined clauses (Noun clause, Adjective clause, Adverb clause, Co-ordinate clause).",
    "- `english/grammar/parts-of-speech` (24 items, retagged from coarse baseline):",
    "  - Q1–Q3, Q5–Q10: Identification of parts of speech (collective nouns, proper nouns, pronouns, adjectives, adverbs, conjunctions, interjections, verbs).",
    "  - Q21–Q30: Adjective forms, degrees of comparison, and determiners (*few, plenty, a little, little, biggest, each, every*, etc.).",
    "  - Q31–Q35: Adverb classification (*rarely, seldom, frequently, often*).",
    "- `english/grammar/prepositions` (6 items, retagged from coarse baseline):",
    "  - Q4: Sentence containing a preposition (*about*).",
    "  - Q36–Q40: Preposition usage (*appeal against, ashamed of, sit beside*, etc.).",
    "- `english/grammar/tenses` (10 items, retagged from coarse baseline):",
    "  - Q11–Q20: Finite verb forms and aspect completion (*drinking, will move, was, has rained*, etc.).",
    "- `english/vocabulary/idioms-and-phrases` (11 items, retagged from coarse baseline):",
    "  - Q71–Q80: Idiomatic expressions (*apple pie order, cry for the moon, all at sea, green thumb, turn the tables*, etc.).",
    "  - Q99: Phrasal verb / idiom (*bottled up her emotions*).",
    "- `english/vocabulary/one-word-substitution` (11 items, retagged from coarse baseline):",
    "  - Q81–Q90: Concise single-word equivalents (*Connoisseur, Corselet, Cripple, Chronological, Sinecure, Pantheism, Aristocracy, Gerontocracy, Utopia, Bottleneck*).",
    "  - Q94: Lexical definition of 'sadist' (*one who gets pleasure from hurting others*).",
    "- `english/vocabulary` (6 items, confirmed and kept from baseline):",
    "  - Q91, Q95, Q96, Q97, Q98, Q100: Contextual vocabulary, orthography, and confusable words (*assemble, felicitated, beacon/guild, revolves, Culmination, gregarious*).",
    "- `english/vocabulary/synonyms` (2 items, retagged from coarse baseline):",
    "  - Q92–Q93: Lexical synonyms (*primeval -> Primitive, inception -> Start*).",
    "",
    "## Visual Source & Defect Analysis",
    "",
    "- **Underlined Target Clauses (Q61–Q70)**: Underlined via horizontal vector line strokes in the PDF stream; verified via exact PyMuPDF geometry.",
    "- **Underlined Idioms (Q71–Q80)**: Underlined with vector line geometry in the printed booklet.",
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
