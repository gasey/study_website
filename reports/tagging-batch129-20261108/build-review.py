"""Build review candidates and findings for Batch 129: Museum Guide 2020 General English (50 MCQs)."""
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
    if 1 <= qnum <= 10:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and phrases (hole and corner, plough the sands, raw deal, scot-free, with a grain of salt, wild-goose chase, fair and square, eat humble pie, chew the cud, blow hot and cold)'
    elif 11 <= qnum <= 20:
        return 'english/comprehension', 'English comprehension: reading comprehension passage analysis on newspaper, the press, and freedom of speech'
    elif 21 <= qnum <= 30:
        return 'english/grammar/parts-of-speech', 'English grammar: identification of parts of speech (noun, pronoun, adjective, adverb, verb, preposition, conjunction)'
    elif 31 <= qnum <= 35:
        return 'english/grammar', 'English grammar: sentence analysis and structure (simple, compound, and complex sentences)'
    elif 36 <= qnum <= 40:
        return 'english/grammar', 'English grammar: sentence transformation and forms (degrees of comparison, assertive, affirmative, and negative forms)'
    elif 41 <= qnum <= 45:
        return 'english/grammar/subject-verb-agreement', 'English grammar: subject-verb agreement and determiners (either/neither, means sufficient, distributive and compound subjects)'
    elif 46 <= qnum <= 50:
        return 'english/vocabulary/synonyms', 'English vocabulary: contextual synonyms (exonerated, clandestine, promulgate, segregation, ubiquitous)'
    else:
        raise ValueError(f"Unexpected qnum: {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/Museum Guide General Englsih.pdf"

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
        "batch_id": 129,
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
        "question_number": "I",
        "paper_id": paper_id,
        "marks": 20,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/essay",
        "title": "Essay Writing",
        "details": "Write an essay on any one of the given topics in not less than 300 words: (1) Country Life versus Town Life, (2) Choice of Professions, (3) Youth and Social Media."
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
    "batch": 129,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Competitive Examinations for Recruitment to the Post of Museum Guide under Art & Culture Department, February 2020 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 50
        }
    ],
    "targets": 50,
    "completion": "100% paper completion achieved for Museum Guide February 2020 General English (50/50 MCQs reviewed: 10 Idioms & Phrases, 10 Reading Comprehension, 10 Parts of Speech, 10 Grammar / Sentence Structure & Transformation, 5 Subject-Verb Agreement, 5 Synonyms; Section A Essay [20 marks] preserved in pending-written-intake.json)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Reclassified legacy misattributions where comprehension questions on the press were tagged under 'journalism' or 'general-studies' into 'english/comprehension'.",
        "Preserved Section A (20 conventional marks: Essay on Country vs Town Life / Choice of Professions / Youth and Social Media) in pending-written-intake.json."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 129 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
