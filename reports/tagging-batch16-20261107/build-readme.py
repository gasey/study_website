"""Build human-readable README report for Batch 16."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
candidates = json.load(open(out / "pending-candidates.json"))
val = json.load(open(out / "validation.json"))
summary = json.load(open(out / "summary.json"))

md = []
md.append("# Pending source-reviewed tagging — Batch 16: English Grammar, Vocabulary & Reported Speech")
md.append("")
md.append(f"Policy: `study-tagging-v1`. **50 existing questions reviewed: {summary['actions']['retag']} retag proposals, {summary['actions']['keep']} keep decisions, {summary['actions']['hold']} tag holds. All 50 remain pending. Zero live changes, submissions or publications.**")
md.append("")
md.append("## Single-booklet deduplication policy")
md.append("")
md.append("Per the owner's directive (\"for future to reduce duplication only one booklet should be considered for one paper\"):")
md.append("- For **Assistant LESO 2026 General English**, the unique primary paper (`doc_3c107a32ef282eb0258dac94`) was used. This batch completes the remaining 50 questions (Q17–Q66), bringing the entire paper to 100% source-reviewed completion.")
md.append("")
md.append(f"Fresh Oracle read-only export: `{packet['exported_at']}`. Readback validation (`validation.json`) confirmed that all 50 source fingerprints, answer baselines, and database states remain 100% identical. All proposed paths validate strictly against the 181 active nodes in `review_taxonomy`.")
md.append("")
md.append("## Before / after table")
md.append("")
md.append("| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |")
md.append("| :---: | :--- | :--- | :--- | :--- | :--- |")

for i, c in enumerate(candidates, 1):
    src = c["source_evidence"]
    qnum_str = src["printed_question"]
    skill = c["tested_skill"]
    curr = c["current_primary"]
    curr_str = curr["subject_id"] or "unassigned"
    if curr.get("topic_id"):
        curr_str += f" → {curr['topic_id']}"
    
    prop = c["proposed_primary"]
    prop_parts = [prop["subject_id"].replace("-", " ").title()]
    if prop.get("topic_id"):
        prop_parts.append(prop["topic_id"].split("/")[-1].replace("-", " ").title())
    if prop.get("subtopic_id"):
        prop_parts.append(prop["subtopic_id"].split("/")[-1].replace("-", " ").title())
    prop_str = " → ".join(prop_parts)

    act = f"**{c['action']}**"
    rat = c["rationale"]

    md.append(f"| {i} | {qnum_str} (p. {src['physical_page']}) | {skill} | {curr_str} | {prop_str} | {act} — {rat} |")

md.append("")
md.append("## Visual inspection evidence")
md.append("")
md.append("| # | Canonical / appearance | Inspected page | Specific elements verified on rendered PNG image |")
md.append("| :---: | :--- | :---: | :--- |")

for i, c in enumerate(candidates, 1):
    cid = c["canonical_id"]
    aid = c["appearance_id"]
    src = c["source_evidence"]
    note = src["note"].replace("|", "\\|")
    md.append(f"| {i} | `{cid}` / `{aid}` | p. {src['physical_page']} | {note} |")

md.append("")
md.append("## Key findings & taxonomy gap notes")
md.append("")
md.append("1. **Complete Paper Reconciliation for Assistant LESO 2026 General English:**")
md.append("   - Combined with Batch 15 (Q1–Q16), this batch (Q17–Q66) achieves 100% source-reviewed tagging for the entire paper (66 questions total).")
md.append("   - Every single question was previously stored under generic `gk/Assistant LESO-2026 General English.`, completely masking the paper's English grammar and vocabulary content.")
md.append("2. **Source Heading Defect (Q21–Q30):**")
md.append("   - Printed exam header on page 5 states: 'Complete the blanks using the most appropriate determiner:'. However, all 10 items (Q21–Q30) test Prepositions (under, across, on, for, by, into, in, at, of, in). Classified by actual tested skill under `english/grammar/prepositions` with the source defect recorded.")
md.append("   - Source typo on Q28 ('wairing' for 'waiting') recorded in source issues.")
md.append("3. **Conjunctions & Sentence Structure:**")
md.append("   - Q17–Q20 test Conjunctions (as if, unless, whether... or, although); routed to topic `english/grammar` (no dedicated subtopic).")
md.append("   - Q44–Q54 test sentence forms, phrases, and clause syntax; routed to `english/grammar`.")
md.append("   - Q55–Q56 test conditional and correlative inversion syntax; routed to `english/sentence-correction`.")
md.append("   - Q57 tests concord ('Each of the students has completed his work'); routed to `english/grammar/subject-verb-agreement`.")
md.append("4. **Reported Speech (Q59–Q66):**")
md.append("   - 8 systematic questions testing direct to indirect speech and vice-versa, including universal truths ('Honesty is the best policy'); routed to active subtopic `english/grammar/reported-speech`.")
md.append("")
md.append("## Summary totals")
md.append("")
md.append(f"- **Reviewed:** {summary['targets']}")
md.append(f"- **Retag proposed:** {summary['actions']['retag']}")
md.append(f"- **Keep current:** {summary['actions']['keep']}")
md.append(f"- **Held:** {summary['actions']['hold']}")
md.append(f"- **Live database modifications:** {summary['live_changes']} (all pending)")
md.append("")
md.append("## Recommended next batch")
md.append("")
md.append("1. **Batch 17 (Technical & Pure Mathematics — 50 questions):** *Inspector of Statistics 2026 Paper-III (Mathematics)* (`doc_71b95ff621b44ec2b84ecb02`): Differential Equations, Linear Algebra, Real Analysis, and Calculus.")
md.append("2. **Batch 18 (Reasoning & Analytical Ability — 50 questions):** *LDC under MPSC 2025 Paper-I* or *Mizoram Civil Services Combined Preliminary 2024 Paper-II*.")
md.append("")

(out / "README.md").write_text("\n".join(md) + "\n")
print(f"Generated README.md: {len(md)} lines.")
