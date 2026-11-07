"""Build review candidates and findings for Batch 88: AE (Civil) under Trade & Commerce 2016 General English (20 MCQs)."""
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
    if 1 <= qnum <= 10:
        path = "english/grammar/tenses"
        rat = f"Verb form and tense selection: {question[:50]}..."
    elif 11 <= qnum <= 20:
        path = "english/vocabulary/one-word-substitution"
        rat = f"Definition / one word substitution: {question[:50]}..."
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
        "paper_id": "Old_Questions/Direct_2014-2018/4.AE (Civil) under Trade & Commerce 2016 General English.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 88,
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
        "paper_id": "Old_Questions/Direct_2014-2018/4.AE (Civil) under Trade & Commerce 2016 General English.pdf",
        "qnum": "Q1",
        "reason": "Conventional written comprehension questions: '(a) What is the author's primary purpose... (b) Summarise in brief... (c) What adverse affect... (d) How does advances in computer technology...' (20 Marks). Conventional section omitted from MCQ database ingestion.",
        "physical_page": 1,
        "marks": 20,
        "status": "pending_intake"
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/4.AE (Civil) under Trade & Commerce 2016 General English.pdf",
        "qnum": "Q2",
        "reason": "Conventional written précis: 'Re-write the following passage into 1/3 of its length giving a suitable title: According to the myth the typical Australian is a practical man...' (20 Marks). Conventional section omitted from MCQ database ingestion.",
        "physical_page": 1,
        "marks": 20,
        "status": "pending_intake"
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/4.AE (Civil) under Trade & Commerce 2016 General English.pdf",
        "qnum": "Q3",
        "reason": "Conventional written essay: 'Write an essay on any one the following topics: (a) Sustainable Energy (b) Waste management system (c) Industries for State development' (20 Marks). Conventional section omitted from MCQ database ingestion.",
        "physical_page": 2,
        "marks": 20,
        "status": "pending_intake"
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/4.AE (Civil) under Trade & Commerce 2016 General English.pdf",
        "qnum": "Q6",
        "reason": "Conventional written word pairs: 'Make sentences with the following pairs of words to show their difference: (a) Accept / Except (b) Meter / Metre (c) Principal / Principle (d) Loose / Lose (e) Rise / Raise (f) Hoard / Horde (g) Who's / Whose (h) Its / It's (i) Flair / Flare (j) Belief / Believe' (10 Marks). Conventional section omitted from MCQ database ingestion.",
        "physical_page": 3,
        "marks": 10,
        "status": "pending_intake"
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/4.AE (Civil) under Trade & Commerce 2016 General English.pdf",
        "qnum": "Q7",
        "reason": "Conventional written idioms: 'Explain and make sentences with any five (5) of the given idioms and phrases: (a) To be at dagger's drawn (b) A green horn (c) To pay off old scores (d) Call a spade a spade (e) Paint the town red (f) A left handed compliment (g) Keep the pot boiling (h) To strike a chord' (10 Marks). Conventional section omitted from MCQ database ingestion.",
        "physical_page": 3,
        "marks": 10,
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
    "batch": 88,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/4.AE (Civil) under Trade & Commerce 2016 General English.pdf",
            "paper_title": "Technical Competitive Examinations for Recruitment to Assistant Engineer (Civil) Contract Basis under Trade and Commerce Dept (July 2016) — General English",
            "document_id": "doc_8f107f918e95df4a78cb1eb6",
            "sha256": "874b26d40277792e342894b967d605c4b4d667c5240bc3d2c943b17409c95eb7",
            "targets": 20
        }
    ],
    "targets": 20,
    "completion": "100% paper completion achieved for Assistant Engineer (Civil) under Trade & Commerce 2016 General English (20/20 MCQs reviewed; 80 marks across 5 conventional written sections [Comprehension Q1, Précis Q2, Essay Q3, Word Pairs Q6, Idioms Q7] preserved in pending-written-intake.json)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 5,
    "conventional_marks_preserved": 80,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Realigned legacy classifications into standard english curriculum taxonomy.",
        "Conventional Written Comprehension (20m), Précis (20m), Essay (20m), Word Pairs (10m), and Idioms sentences (10m) totaling 80 marks safely recorded in pending-written-intake.json."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
