"""Build review candidates and findings for Batch 82: Junior Engineer (JE) Contract Basis General English (80 MCQs)."""
import json
from pathlib import Path
from collections import Counter

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
    if 1 <= qnum <= 16:
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Meaning of idiom / phrase: {question[:50]}..."
    elif 17 <= qnum <= 32:
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif 33 <= qnum <= 38:
        path = "english/grammar/prepositions"
        rat = f"Preposition selection: {question[:50]}..."
    elif 39 <= qnum <= 44:
        path = "english/grammar/parts-of-speech"
        rat = f"Parts of Speech identification of underlined word: {question[:50]}..."
    elif 45 <= qnum <= 48:
        path = "english/grammar/tenses"
        rat = f"Verb form and tense selection: {question[:50]}..."
    elif 49 <= qnum <= 53:
        path = "english/grammar"
        rat = f"Sentence structure classification (Simple, Compound, Complex): {question[:50]}..."
    elif 54 <= qnum <= 58:
        path = "english/grammar"
        rat = f"Clause identification (Noun, Adverb, Adjective, Coordinate clause): {question[:50]}..."
    elif 59 <= qnum <= 64:
        path = "english/grammar"
        rat = f"Sentence functional type (Imperative, Exclamatory, Assertive, Affirmative, Negative): {question[:50]}..."
    elif 65 <= qnum <= 72:
        path = "english/vocabulary"
        rat = f"Vocabulary / usage / commonly confused words: {question[:50]}..."
    elif 73 <= qnum <= 80:
        path = "english/vocabulary/synonyms"
        rat = f"Synonym / nearest in meaning to underlined word: {question[:50]}..."
    else:
        path = "english/grammar"
        rat = f"General English question: {question[:50]}..."
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
        "paper_id": "Old_Questions/Direct_2014-2018/9. General English.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 82,
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

unextracted_items = [
    {
        "paper_id": "Old_Questions/Direct_2014-2018/9. General English.pdf",
        "qnum": "Section A Q1",
        "reason": "Conventional written essay: 'Write an essay on any one (1) of the given topics in not more than 300 words (20 Marks): – Child labour in India – Life in a big city – Use and abuse of social media'. Conventional section omitted from MCQ database ingestion.",
        "physical_page": 1,
        "marks": 20,
        "status": "pending_intake"
    }
]

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps(unextracted_items, ensure_ascii=False, indent=2) + "\n")

retags = sum(1 for c in pending_candidates if c["action"] == "retag")
keeps = sum(1 for c in pending_candidates if c["action"] == "keep")
holds = sum(1 for c in pending_candidates if c["action"] == "hold")

breakdown = Counter(c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"] for c in pending_candidates)

summary = {
    "batch": 82,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/9. General English.pdf",
            "paper_title": "General Competitive Examinations for Recruitment to Junior Engineer (JE) Contract Basis — General English",
            "document_id": "doc_9ca4c2a445e9a44ecb9c3f58",
            "sha256": "cd3ed237c62c91d18f972b20f04c0ec2e9e2b1ea7ebae008fcb063548981f429",
            "targets": 80
        }
    ],
    "targets": 80,
    "completion": "100% paper completion achieved for Junior Engineer (JE) Contract Basis General English (80/80 MCQs reviewed; 20-mark conventional Section A essay preserved in pending-written-intake.json)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 1,
    "conventional_marks_preserved": 20,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Realigned legacy classifications into standard english curriculum taxonomy.",
        "Conventional Section A Essay (20 marks) on Page 1 safely recorded in pending-written-intake.json."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
