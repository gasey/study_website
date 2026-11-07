"""Build review candidates and findings for Batch 62: MCS Combined 2023 Preliminary Exam Paper-II Series A (100 MCQs)."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

def parse_path(path_str):
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

def assign_tax(qnum, question):
    if qnum in (1, 4, 5, 6, 7, 10, 12, 13, 14, 15, 16, 17, 60, 61):
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif qnum in (2, 11):
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Passage idiom or figurative expression: {question[:50]}..."
    elif qnum in (3, 8):
        path = "english/vocabulary/synonyms"
        rat = f"Passage vocabulary synonym: {question[:50]}..."
    elif qnum == 9:
        path = "english/vocabulary/antonyms"
        rat = "Passage vocabulary antonym: opposite in meaning to 'stimulate'."
    elif qnum in (21, 22, 23):
        path = "english/vocabulary"
        rat = f"Contextual vocabulary and word choice: {question[:50]}..."
    elif (18 <= qnum <= 20) or (24 <= qnum <= 34) or (52 <= qnum <= 53) or (56 <= qnum <= 57) or (qnum == 59) or (62 <= qnum <= 64) or (qnum == 67):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Interpersonal skills, communication, leadership, and administrative situational judgment: {question[:50]}..."
    elif qnum in (35, 36, 37, 47, 48):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Blood relations or personal identity deduction: {question[:50]}..."
    elif qnum in (38, 80):
        path = "reasoning-and-aptitude/series"
        rat = f"Letter or number series pattern: {question[:50]}..."
    elif 39 <= qnum <= 43:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Statement and arguments logical evaluation: {question[:50]}..."
    elif 44 <= qnum <= 46:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Syllogism and logical validity: {question[:50]}..."
    elif 49 <= qnum <= 51:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Odd word out verbal classification: {question[:50]}..."
    elif qnum == 54:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = "Intelligence and ranking test puzzle."
    elif qnum == 55:
        path = "mathematics/algebra/linear-equations"
        rat = "Age algebra linear equation problem."
    elif qnum in (58, 84):
        path = "mathematics/arithmetic"
        rat = f"Basic arithmetic / divisibility: {question[:50]}..."
    elif qnum in (65, 69, 79, 83, 92):
        path = "reasoning-and-aptitude/numerical-ability"
        rat = f"Numerical ability, dice, figure matrix, round-robin, or Venn sets: {question[:50]}..."
    elif qnum == 66:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = "Meaningful sequence arrangement of words."
    elif qnum in (68, 82):
        path = "mathematics/arithmetic"
        rat = f"Compound interest and effective rate arithmetic: {question[:50]}..."
    elif qnum in (70, 87):
        path = "mathematics/arithmetic"
        rat = f"Time and work arithmetic: {question[:50]}..."
    elif qnum == 71:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = "Direction sense test and distance calculation."
    elif qnum in (72, 76, 77):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Coding-decoding pattern: {question[:50]}..."
    elif qnum in (73, 91):
        path = "reasoning-and-aptitude/data-interpretation"
        rat = f"Data interpretation from charts/diagrams: {question[:50]}..."
    elif qnum == 74:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = "Ranking position in a class."
    elif qnum == 75:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = "Verbal analogy: Hill : Mountain :: ? : Pain."
    elif qnum == 78:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = "Ranking comparison in debate."
    elif qnum in (81, 96):
        path = "mathematics/arithmetic/ratio-and-proportion"
        rat = f"Ratio and proportion / mixture arithmetic: {question[:50]}..."
    elif qnum in (85, 86, 95):
        path = "mathematics/arithmetic"
        rat = f"Surds, radicals, and order of numbers: {question[:50]}..."
    elif qnum == 88:
        path = "mathematics/arithmetic"
        rat = "Speed, distance, and time calculation."
    elif qnum == 89:
        path = "mathematics/arithmetic/percentages"
        rat = "Percentage equation evaluation."
    elif qnum == 90:
        path = "mathematics/arithmetic/profit-and-loss"
        rat = "Profit and loss calculation on selling price."
    elif qnum == 93:
        path = "mathematics/algebra"
        rat = "Arithmetic progression (AP) number of terms."
    elif qnum == 94:
        path = "mathematics/mensuration/area"
        rat = "Mensuration: perimeter conversion from circle to square."
    elif qnum == 97:
        path = "mathematics/algebra/algebraic-expressions"
        rat = "GCD and LCM of algebraic polynomials."
    elif qnum == 98:
        path = "mathematics/algebra/quadratic-equations"
        rat = "Zeroes of quadratic polynomial (2x² + 7x − 4)."
    elif qnum == 99:
        path = "mathematics/mensuration/volume"
        rat = "Mensuration: volume of rectangular planks and pit."
    elif qnum == 100:
        path = "mathematics/arithmetic/averages"
        rat = "Mean / average calculation when an item is excluded."
    else:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"General reasoning question: {question[:50]}..."
    return path, rat

pending_candidates = []
findings = []

for item in packet["items"]:
    cid = item["canonical_id"]
    aid = item["appearance_id"]
    rec = item["snapshot"]["record"]
    qnum = int(rec["qnum"])
    q_text = rec["question"]
    fingerprint = item["source_fingerprint"]
    
    cur_cls = rec.get("classification") or {"subject_id": None, "topic_id": None, "subtopic_id": None}
    
    target_tax, rationale = assign_tax(qnum, q_text)
    parsed = parse_path(target_tax)
    action = "keep" if parsed == cur_cls else "retag"
    
    cand = {
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": "Old_Questions/Direct_2023-2025/MCS Combined 2023 Preliminary Exam Paper-II Series 'A'..pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 62,
        "policy": "study-tagging-v1"
    }
    pending_candidates.append(cand)
    
    findings.append({
        "qnum": qnum,
        "canonical_id": cid,
        "appearance_id": aid,
        "action": action,
        "current_taxonomy": cur_cls,
        "target_taxonomy": parsed,
        "rationale": rationale,
        "stem_excerpt": q_text[:80]
    })

findings.sort(key=lambda x: x["qnum"])
pending_candidates.sort(key=lambda x: int(next(i["snapshot"]["record"]["qnum"] for i in packet["items"] if i["appearance_id"] == x["appearance_id"])))

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps([], ensure_ascii=False, indent=2) + "\n")

retags = sum(1 for c in pending_candidates if c["action"] == "retag")
keeps = sum(1 for c in pending_candidates if c["action"] == "keep")
holds = sum(1 for c in pending_candidates if c["action"] == "hold")

from collections import Counter
breakdown = Counter(c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"] for c in pending_candidates)

summary = {
    "batch": 62,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2023-2025/MCS Combined 2023 Preliminary Exam Paper-II Series 'A'..pdf",
            "paper_title": "Mizoram Civil Services Combined Preliminary Examination 2023 — Paper II (Series A: Aptitude, Arithmetic & Comprehension)",
            "document_id": "doc_1f45222ca9e6101529b723e7",
            "sha256": "abb3ede197e2ab5b06401eb79cd337c71aa0654810238e6aa6bdcab61650cd89",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for MCS Combined 2023 Preliminary Paper-II Series A (100/100 MCQs; Series B, C, D bypassed under single-booklet deduplication)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Single-Booklet Deduplication: MCS Combined 2023 Prelims Paper-II contains 4 letter permutation booklets (Series A, B, C, D); Series A was reviewed as primary booklet, successfully achieving single-booklet deduplication without repeating reviews for B, C, and D.",
        "Cross-Disciplinary Retagging: Corrected baseline classification where decision-making was tagged under commerce (Q63) and mean/round-robin/sets were tagged under statistics (Q83, Q92, Q100)."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
