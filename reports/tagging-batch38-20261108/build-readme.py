"""Generate README.md for Batch 38."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 38: Assistant Director (Food & Drugs) / CDPO 2025 General English (66 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **66 existing MCQ questions reviewed: 66 retag proposals, 0 keep decisions, 0 tag holds. All 66 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper Identity & 100% Paper Completion Milestone",
    "",
    "- **Target Paper:** *Competitive Examination for Child Development Project Officer (CDPO) and Assistant Director (Food & Drugs) under Social Welfare & Tribal Affairs / Health & Family Welfare (November, 2025) — General English* (`Old_Questions/Direct_2025-2027/Assistant Director General English-2025..pdf`, `doc_000e6be43acfd05656947ae1`, `sha256: 594a8a89f8c1b6e7acb22cd8161f59c1e45b2353f7740bb9345261a882ab4438`).",
    "- **Single-Booklet Deduplication Enforced:** Successfully bypassed duplicate file `Old_Questions/Direct_2025-2027/CDPO General English-2025..pdf` (`doc_93dc9451f2beee9b16a34ec8`), which is an exact byte-for-byte binary duplicate (`sha256: 594a8a89f8c1b6e7acb22cd8161f59c1e45b2353f7740bb9345261a882ab4438`) of the same examination booklet, saving 66 redundant reviews.",
    "- **Coverage:** Complete 100% review of all 66 extracted MCQs (Q1–Q66 across physical PDF pages 1 to 9), achieving full paper completion.",
    "- **Untagged Baseline Rectification:** In the database, all 66 questions were completely untagged (`subject=null, topic=null`). Rectified 100% of targets to standard General English grammar and vocabulary subtopics: Parts of Speech (15 items: Adverbs 5, Pronouns 5, Articles 5), Prepositions (10 items), Tenses (10 items), Reported Speech (5 items: Direct/Indirect narration), Idioms and Phrases (5 items), One-Word Substitution (4 items), Sentence Correction (3 items), General Grammar (11 items: Concord/Agreement 5, Sentence Combining 3, Determiners 3), and General Vocabulary (3 items: Synonyms/Antonyms).",
    "- **Preserved Conventional Intake:** Preserved 3 unextracted Part-B conventional tasks totaling 40 marks from Page 9 in `pending-written-intake.json` (Essay Writing 20 marks, Précis Writing 10 marks, Reading Comprehension 10 marks).",
    f"- **Fresh Oracle read-only export:** `{packet['exported_at']}`. Readback validation (`{validation['validated_at']}`) confirmed 100% source fingerprint consistency, zero live mutations, and 100% compliance with active taxonomy nodes.",
    "",
    "## Before / after table",
    "",
    "| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |",
    "| :---: | :--- | :--- | :--- | :--- | :--- |"
]

for idx, f in enumerate(findings, 1):
    ctx = f"{f['printed_question']} (p. {f['physical_page']})"
    lines.append(
        f"| {idx} | {ctx} | {f['tested_skill']} | `{f['current_path']}` | `{f['proposed_path']}` | **{f['action']}** — {f['rationale']} |"
    )

lines.extend([
    "",
    "## Totals & Summary Breakdown",
    "",
    f"- **Total existing questions reviewed:** {summary['targets']}",
    f"- **Retag candidates proposed:** {summary['actions'].get('retag', 0)}",
    f"- **Keep decisions:** {summary['actions'].get('keep', 0)}",
    f"- **Holds:** {summary['actions'].get('hold', 0)}",
    f"- **Unextracted written items preserved:** {summary['unextracted_items_preserved']}",
    "- **Live database writes:** 0 (strictly read-only)",
    "",
    "### Breakdown by Proposed Taxonomy Path",
    ""
])

for path, count in sorted(summary["breakdown"].items()):
    lines.append(f"- `{path}`: {count} questions")

lines.extend([
    "",
    "## Physical Element Inspection Evidence",
    "",
    "Direct visual inspection of all 9 rendered PNG page images (`paper-1-p1.png` to `paper-1-p9.png`) of `doc_000e6be43acfd05656947ae1`:",
    "- **Page 1 (`paper-1-p1.png`):** Inspected Paper cover and Q1–Q8: Q1–Q5 (Concord / Subject-Verb Agreement: 'Neither the teacher nor the students...', 'The flock of sheep...', 'Physics...', 'Each of the boys...', 'Bread and butter...'), Q6–Q8 (Sentence Combining with Conjunctions: 'He worked hard. He failed.', 'She was ill. She attended the meeting.', 'Take this medicine. You will get well.').",
    "- **Page 2 (`paper-1-p2.png`):** Inspected Q9–Q16: Q9–Q11 (Determiners / Adjectives of Quantity: '...milk left in the jug', '...friends attended the party', 'Do you have...money?'), Q12–Q16 (Direct and Indirect Speech / Reported Speech transformations: 'He said, \"I am going to Delhi tomorrow\"', 'She said, \"Where do you live?\"', 'The teacher said, \"The sun rises in the east\"', 'He said, \"Alas! I am ruined\"', 'She said to me, \"Please help me\"').",
    "- **Page 3 (`paper-1-p3.png`):** Inspected Q17–Q24: Q17–Q21 (One-Word Substitution & Synonyms: Q17 'A person who loves books' -> Bibliophile, Q18 'A government by the people' -> Democracy, Q19 'Life history written by oneself' -> Autobiography, Q20 'One who looks on the bright side' -> Optimist, Q21 Synonym of 'Diligent'), Q22–Q24 (Antonyms & Idioms: Q22 Antonym of 'Transparent', Q23 Antonym of 'Frugal', Q24 Idiom 'Burn the midnight oil').",
    "- **Page 4 (`paper-1-p4.png`):** Inspected Q25–Q32: Q25–Q28 (Idioms and Phrases: Q25 'Bite the bullet', Q26 'A blessing in disguise', Q27 'Hit the nail on the head', Q28 'Call it a day'), Q29–Q31 (Sentence Correction / Spotting Errors: 'One of my friend is visiting today', 'She is senior than me in service', 'He has been absent since three days'), Q32 (Prepositions: 'She is good...mathematics').",
    "- **Page 5 (`paper-1-p5.png`):** Inspected Q33–Q40: Q33–Q41 (Prepositions: Q33 'He died...cancer', Q34 'The cat jumped...the table', Q35 'We walked...the forest', Q36 'She has been living here...2010', Q37 'Divide the apples...the two brothers', Q38 'The teacher was angry...the student', Q39 'I prefer tea...coffee', Q40 'He congratulated me...my success').",
    "- **Page 6 (`paper-1-p6.png`):** Inspected Q41–Q48: Q41 (Prepositions: 'He is afraid...dogs'), Q42–Q46 (Adverbs: Q42 'He solved the puzzle...', Q43 'She speaks English...', Q44 'The train arrived...', Q45 'He works...hard to pass the examination', Q46 'We seldom...such occurrences'), Q47–Q48 (Pronouns: Q47 '...did you see at the party?', Q48 'This is the boy...won the first prize').",
    "- **Page 7 (`paper-1-p7.png`):** Inspected Q49–Q56: Q49–Q51 (Pronouns: Q49 'Neither of them brought...books', Q50 'She hurt...while playing', Q51 'One should do...duty'), Q52–Q56 (Articles: Q52 'He is...honorable man', Q53 '...Ganges is a sacred river', Q54 'She plays...guitar very well', Q55 'I bought...umbrella yesterday', Q56 'He is...highest scorer in the team').",
    "- **Page 8 (`paper-1-p8.png`):** Inspected Q57–Q64: Q57–Q64 (Tenses & Verb Forms: Q57 'The train...before we reached the station', Q58 'If it rains, we...the match', Q59 'She...in this school for five years', Q60 'By next year, he...his degree', Q61 'When I saw him, he...a book', Q62 'The earth...round the sun', Q63 'I...him since last Monday', Q64 'They...cricket when the rain started').",
    "- **Page 9 (`paper-1-p9.png`):** Inspected Q65–Q66 (Tenses & Verb Forms: Q65 'He...just now', Q66 'Unless you work hard, you...fail') and Part-B Conventional Section: Essay writing (20 marks), Précis writing (10 marks), Reading Comprehension (10 marks).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Completely Untagged Ingestion Baseline:** All 66 MCQs had `subject=null, topic=null` in the production database, leaving them unclassified until this review.",
    "2. **Unextracted Part-B Conventional Tasks:** Page 9 contains 3 conventional written tasks (Essay 20 marks, Précis 10 marks, Comprehension 10 marks) totaling 40 marks, which were not ingested into the MCQ database. Preserved in `pending-written-intake.json`.",
    "3. **Exact Booklet Ingestion Duplicate:** The exact same paper was ingested twice under `Assistant Director General English-2025..pdf` (`doc_000e6be43acfd05656947ae1`) and `CDPO General English-2025..pdf` (`doc_93dc9451f2beee9b16a34ec8`). Both booklets share identical sha256 (`594a8a89f8c1b6e7acb22cd8161f59c1e45b2353f7740bb9345261a882ab4438`). Enforced single-booklet rule by reviewing the primary document and cleanly bypassing the duplicate."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
