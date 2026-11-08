"""Build review candidates and findings for Batch 110: Computer Operator under Election Deptt 2019 General English (80 MCQs)."""
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
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases (face the music, hand to mouth, sitting on fence, thick and thin, take exception, white elephant, spur of moment, Hobson\'s choice, snake in grass, etc.)'
    elif 17 <= qnum <= 22:
        return 'english/comprehension', 'English comprehension: passage reading analysis (Passage 1: Wildlife poaching and species extinction)'
    elif 23 <= qnum <= 32:
        return 'english/comprehension', 'English comprehension: passage reading analysis (Passage 2: Abraham Lincoln and emancipation of slavery)'
    elif 33 <= qnum <= 48:
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification (any, before, his, after, yet, again, what, enough, place, that, round, above, till, on)'
    elif 49 <= qnum <= 56:
        return 'english/grammar', 'English grammar: sentence structure analysis (simple, compound, complex sentences)'
    elif 57 <= qnum <= 64:
        return 'english/grammar', 'English grammar: clause analysis (noun clause, adjective clause, adverb clause)'
    elif qnum == 65:
        return 'english/grammar', 'English grammar: determiner/quantifier in context (some advice)'
    elif qnum == 66:
        return 'english/grammar/prepositions', 'English grammar: preposition with gerund complement (fond of playing)'
    elif qnum in (67, 68):
        return 'english/grammar/subject-verb-agreement', 'English grammar: subject-verb agreement concord (The cost of articles has risen / Neither food nor water was found)'
    elif 69 <= qnum <= 72:
        return 'english/grammar', 'English grammar: adjective forms, sensory verb complements, adverbs, and conditional conjunctions (eldest, smell sweet, too good, unless)'
    elif 73 <= qnum <= 80:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms in context (vivacious, common, lethargic, enmity, frugal, relinquish, busy, perilous)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General English(Election).pdf"

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
        "batch_id": 110,
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
        "reason": "Conventional written essay: '“Democracy allows people to have different views and democracy makes us also responsible for negotiating an answer for those views.” - Aung San Suu Kyi. Write an essay in about 400 words expressing your ideas and opinion on the above statement (20 Marks)'. Preserved for conventional intake."
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
    "batch": 110,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Technical Competitive Examinations for Recruitment to the Post of Computer Operator under Election Department, December 2019 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 80
        }
    ],
    "targets": 80,
    "completion": "100% paper completion achieved for Computer Operator (Election) 2019 General English (80/80 MCQs reviewed: 21 Grammar Core [Sentence Structure, Clauses, Determiners, Adverbs, Conjunctions], 16 Parts of Speech, 16 Reading Comprehension, 16 Idioms & Phrases, 8 Antonyms, 2 Subject-Verb Agreement, 1 Preposition; 1 conventional essay question documented in written intake)",
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
print(f"Batch 110 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
