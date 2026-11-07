"""Build review candidates and findings for Batch 81: Computer Operator (CB) under Mizoram Information Commission 2016 General English (80 MCQs)."""
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
    if 1 <= qnum <= 8:
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Meaning of idiom / phrase: {question[:50]}..."
    elif 9 <= qnum <= 16:
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Fill in the blank with idiom / phrase: {question[:50]}..."
    elif 17 <= qnum <= 32:
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif 33 <= qnum <= 37:
        path = "english/grammar/tenses"
        rat = f"Past and perfect tense selection: {question[:50]}..."
    elif 38 <= qnum <= 42:
        path = "english/grammar/tenses"
        rat = f"Verb form and tense selection: {question[:50]}..."
    elif qnum in (43, 46, 47, 48):
        path = "english/grammar/parts-of-speech"
        rat = f"Relative pronoun / determiner selection (what, which, only, whom): {question[:50]}..."
    elif qnum == 44:
        path = "english/grammar/prepositions"
        rat = f"Preposition selection (looking for): {question[:50]}..."
    elif qnum == 45:
        path = "english/grammar/tenses"
        rat = f"Participle / verb form (entering): {question[:50]}..."
    elif 49 <= qnum <= 56:
        path = "english/grammar"
        rat = f"Sentence structure classification (Simple, Complex, Compound): {question[:50]}..."
    elif 57 <= qnum <= 61:
        path = "english/grammar"
        rat = f"Sentence synthesis / avoiding repetition / pronoun substitution: {question[:50]}..."
    elif 62 <= qnum <= 65:
        path = "english/grammar"
        rat = f"Sentence linking / conjunctions / connectors: {question[:50]}..."
    elif 66 <= qnum <= 71:
        path = "english/vocabulary"
        rat = f"Vocabulary / word usage in context: {question[:50]}..."
    elif 72 <= qnum <= 76:
        path = "english/vocabulary/synonyms"
        rat = f"Synonym / similar meaning: {question[:50]}..."
    elif 77 <= qnum <= 80:
        path = "english/vocabulary/antonyms"
        rat = f"Antonym / opposite meaning: {question[:50]}..."
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
        "paper_id": "Old_Questions/Direct_2014-2018/1.Computer Operator (CB) under Mizoram Information Commission 2016 General English.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 81,
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
        "paper_id": "Old_Questions/Direct_2014-2018/1.Computer Operator (CB) under Mizoram Information Commission 2016 General English.pdf",
        "qnum": "Section A Q1",
        "reason": "Conventional written essay: 'Write an essay on any one of the given topics (300 words) (20 Marks): (a) Uses and abuses of social media (b) The role of youth in nation building (c) Cleanliness is next to Godliness'. Conventional section omitted from MCQ database ingestion.",
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
    "batch": 81,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/1.Computer Operator (CB) under Mizoram Information Commission 2016 General English.pdf",
            "paper_title": "Technical Competitive Examinations for Recruitment to Computer Operator (Contract) under Mizoram Information Commission (2016) — General English",
            "document_id": "doc_e4a3e87d3a010bc114cf396a",
            "sha256": "1e269ab32908628c68ebca988ef4a4ec16b9b3c4f74d08a8047970d47321e06f",
            "targets": 80
        }
    ],
    "targets": 80,
    "completion": "100% paper completion achieved for Computer Operator under Mizoram Information Commission 2016 General English (80/80 MCQs reviewed; 20-mark conventional Section A essay preserved in pending-written-intake.json)",
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
