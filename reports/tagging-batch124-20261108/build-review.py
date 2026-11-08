"""Build review candidates and findings for Batch 124: Tutor under H&FW (MCON) 2019 General English (40 MCQs)."""
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
    if 6 <= qnum <= 19:
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification (noun, pronoun, adjective, adverb, preposition, verb, conjunction)'
    elif 20 <= qnum <= 29:
        return 'english/grammar/subject-verb-agreement', 'English grammar: subject-verb agreement rules (singular/plural verbs with collective, compound, disjunctive, and distributive subjects)'
    elif 30 <= qnum <= 45:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and phrasal verbs meaning (run up, saw through, takes after, worked upon, takes up, go by, looks down upon, hear me out, hot water, smell a rat, stands well with, at a stretch, goes to heart, come to grief, when pigs fly, keeps a good table)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General English (Tutor, MCON).pdf"

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
        "batch_id": 124,
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
        "reason": "Conventional written essay: 'Write an essay on any one of the given topics not less than 300 words: Health is Wealth / Impact of personal habits on health / The responsibility of man on saving the environment / Environmental pollution and its ill-effect on man (20 Marks)'. Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Question 2",
        "reason": "Conventional précis writing: Passage on effects of travel on the mind (1/3rd length with title, 10 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Question 3",
        "reason": "Conventional job application letter: Formal letter to Director of Education applying for appointment as a teacher in the Education Department (10 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Question 4",
        "reason": "Conventional idea expansion: Paragraph expansion on proverb 'Where there's a will there's a way' (10 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Question 5",
        "reason": "Conventional reading comprehension: Football in India passage with 5 sub-questions (a-e, 10 Marks). Preserved for conventional intake."
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
    "batch": 124,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Competitive Examinations for Recruitment to the Post of Tutor under Health & Family Welfare Department (MCON), September 2019 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 40
        }
    ],
    "targets": 40,
    "completion": "100% paper completion achieved for Tutor under H&FW (MCON) 2019 General English (40/40 MCQs reviewed: 16 Idioms and Phrasal Verbs, 14 Parts of Speech Identification, 10 Subject-Verb Agreement; 5 conventional written sections [60 marks total: Essay 20 marks, Précis 10 marks, Application Letter 10 marks, Proverb Expansion 10 marks, Reading Comprehension 10 marks] documented in written intake)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 5,
    "conventional_marks_preserved": 60,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic classification into standard English curriculum taxonomy.",
        "Documented Questions 1 to 5 (60 conventional marks total: Essay 20 marks, Précis 10 marks, Job Application Letter 10 marks, Proverb Expansion 10 marks, Reading Comprehension 10 marks) in pending-written-intake.json.",
        "Verified all 40 MCQs (numbered Q6 to Q45 in source booklet) against 5 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 124 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
