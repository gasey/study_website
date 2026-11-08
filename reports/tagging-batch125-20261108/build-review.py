"""Build review candidates and findings for Batch 125: MES (PHED) 2019 General English (35 MCQs)."""
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

def assign_tax(qnum, q):
    if 1 <= qnum <= 5:
        return 'english/vocabulary/synonyms', 'English vocabulary: synonyms / nearest meaning in context (abominable, convivial, inhibit, candid, industrious)'
    elif 6 <= qnum <= 10:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms / opposite meaning in context (bizarre, boon, frivolous, acquit, altruism)'
    elif 11 <= qnum <= 15:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases meaning (hand over fist, talk through one\'s hat, wet behind the ears, keep eyes peeled, hold your horses)'
    elif qnum in (16, 17, 19, 21, 22, 23):
        return 'english/grammar/prepositions', 'English grammar: appropriate prepositions in context (sprang upon, devoted to, glanced at/through, comply with, intrude on, wonderful about)'
    elif qnum == 18:
        return 'english/grammar/tenses', 'English grammar: continuous aspect / verb form in context (was having my bath)'
    elif qnum in (20, 24, 25):
        return 'english/vocabulary', 'English vocabulary: contextual word choice and semantic precision (eloquent, appropriate, showed)'
    elif 26 <= qnum <= 35:
        return 'english/comprehension', 'English comprehension: passage reading analysis on Indian agriculture, farmer distress, MSP, and APMC'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General English (PHE).pdf"

for item in packet["items"]:
    cid = item["canonical_id"]
    aid = item["appearance_id"]
    rec = item["snapshot"]["record"]
    qnum_int = int(rec["qnum"])
    q_text = rec["question"]
    fingerprint = item["source_fingerprint"]
    
    cur_cls = rec.get("classification") or {"subject_id": None, "topic_id": None, "subtopic_id": None}
    
    target_tax, rationale = assign_tax(qnum_int, q_text)
    parsed = parse_path(target_tax)
    action = "keep" if parsed == cur_cls else "retag"
    
    cand = {
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": paper_id,
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 125,
        "policy": "study-tagging-v1"
    }
    pending_candidates.append(cand)
    
    findings.append({
        "qnum": str(qnum_int),
        "canonical_id": cid,
        "appearance_id": aid,
        "action": action,
        "current_taxonomy": cur_cls,
        "target_taxonomy": parsed,
        "rationale": rationale,
        "stem_excerpt": q_text[:80]
    })

findings.sort(key=lambda x: int(x["qnum"]))
pending_candidates.sort(key=lambda x: next(int(i["snapshot"]["record"]["qnum"]) for i in packet["items"] if i["appearance_id"] == x["appearance_id"]))

unextracted_items = [
    {
        "paper_id": paper_id,
        "qnum": "Question 1",
        "reason": "Conventional written essay: 'Write an essay on any one of the following: Importance of Human capital investment in the development of the state / Implications of globalization through technology / Religion and Politics (20 Marks)'. Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Question 2",
        "reason": "Conventional précis writing: 'Give the précis of the following passage in one third of its length: It is physically impossible for a well-educated, intellectual, or brave man to make money the chief object of his thoughts... (15 Marks)'. Preserved for conventional intake."
    }
]

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps(unextracted_items, ensure_ascii=False, indent=2) + "\n")

tax_counts = Counter(
    (c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"])
    for c in pending_candidates
)
action_counts = Counter(c["action"] for c in pending_candidates)

summary = {
    "batch": 125,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Technical Competitive Examinations for Junior Grade of Mizoram Engineering Service (M.E.S.) under Public Health Department, March 2019 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 35
        }
    ],
    "targets": 35,
    "completion": "100% paper completion achieved for MES (PHED) 2019 General English (35/35 MCQs reviewed: 10 Reading Comprehension [Agricultural distress passage], 6 Prepositions, 5 Synonyms, 5 Antonyms, 5 Idioms & Phrases, 3 Contextual Vocabulary, 1 Verb Tenses; 2 conventional written questions [35 marks total: Essay 20 marks, Précis 15 marks] documented in written intake)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 2,
    "conventional_marks_preserved": 35,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic classification into standard English curriculum taxonomy, including classifying Reading Comprehension questions Q26–Q35 into english/comprehension.",
        "Documented Question 1 (Essay 20 marks) and Question 2 (Précis 15 marks) in pending-written-intake.json.",
        "Verified all 35 MCQs against 5 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 125 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
