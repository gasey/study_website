"""Build review candidates and findings for Batch 113: Junior Engineer (Agriculture) 2020 General English (80 MCQs)."""
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
    if 1 <= qnum <= 16:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases meaning'
    elif 17 <= qnum <= 32:
        return 'english/comprehension', 'English comprehension: passage reading analysis'
    elif qnum == 33:
        return 'english/vocabulary', 'English vocabulary: commonly confused words / word choice (affect vs effect)'
    elif qnum in (34, 37, 38, 39, 40):
        return 'english/grammar/prepositions', 'English grammar: preposition usage in context (to, despite, on, of, into)'
    elif qnum == 35:
        return 'english/grammar/tenses', 'English grammar: past participle verb form (has borne the brunt)'
    elif qnum == 36:
        return 'english/grammar/subject-verb-agreement', 'English grammar: subject-verb agreement concord (plural expression of quantity/time takes singular verb: Six months is)'
    elif 41 <= qnum <= 50:
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification in context'
    elif 51 <= qnum <= 54:
        return 'english/grammar', 'English grammar: sentence structure analysis (simple, compound, complex)'
    elif 55 <= qnum <= 58:
        return 'english/grammar', 'English grammar: clause analysis (noun clause, adjective clause, adverb clause)'
    elif 59 <= qnum <= 62:
        return 'english/grammar', 'English grammar: sentence synthesis and clause combinations'
    elif 63 <= qnum <= 66:
        return 'english/grammar', 'English grammar: sentence transformations (assertive, interrogative, affirmative, imperative)'
    elif qnum in (67, 68, 69, 71, 72):
        return 'english/grammar', 'English grammar: pronoun cases, tags, and sentence completions (larger than me, So do I, tag question, Whom, except him)'
    elif qnum == 70:
        return 'english/grammar/subject-verb-agreement', 'English grammar: subject-verb agreement concord (Each of the students has)'
    elif 73 <= qnum <= 76:
        return 'english/sentence-correction', 'English sentence correction: error detection and grammatical improvement (luggage, some advice, quality of fruits is, setting affects)'
    elif 77 <= qnum <= 80:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution and term definitions (lexicographer, teetotaller, florist, speleology)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Departmental_2019-2020/JE General English..pdf"

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
        "batch_id": 113,
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
        "qnum": "Section A Q1",
        "reason": "Conventional written essay: 'Write an essay on any one of the following topics: Plastic ban in India / Conservation of Natural Resources / Be the change you want to see in others / Pros and cons of Sustainable Agriculture (20 Marks)'. Preserved for conventional intake."
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
    "batch": 113,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Technical Competitive Examinations for Recruitment to the Post of Junior Engineer under Agriculture (Crop Husbandry) Department, March 2020 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 80
        }
    ],
    "targets": 80,
    "completion": "100% paper completion achieved for Junior Engineer (Agriculture) 2020 General English (80/80 MCQs reviewed: 21 Grammar Core [Sentence Structure, Clauses, Synthesis, Transformations, Case/Tags], 16 Reading Comprehension, 16 Idioms & Phrases, 10 Parts of Speech, 5 Prepositions, 4 Sentence Correction, 4 One-Word Substitution, 2 Subject-Verb Agreement, 1 Tenses, 1 Vocabulary; 1 conventional essay question documented in written intake)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 1,
    "conventional_marks_preserved": 20,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic classification into standard English curriculum taxonomy.",
        "Documented Section A (Essay writing, 20 marks) in pending-written-intake.json.",
        "Verified all 80 MCQs against 8 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 113 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
