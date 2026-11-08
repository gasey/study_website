"""Build review candidates and findings for Batch 108: Librarian under H&FW (Lunglei) 2019 General English (80 MCQs)."""
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
        return 'english/grammar/parts-of-speech', 'English grammar: parts of speech identification (preposition, adverb, conjunction, collective noun, indefinite pronoun, interjection, noun, adjective, adverb, conjunction)'
    elif 11 <= qnum <= 15:
        return 'english/grammar/tenses', 'English grammar: verb forms and tenses in context (drinks, have been playing, had caught, is growing, saw)'
    elif 16 <= qnum <= 20:
        return 'english/grammar/parts-of-speech', 'English grammar: pronouns selection (one\'s, whom, Each, what, that)'
    elif 21 <= qnum <= 25:
        return 'english/grammar/articles', 'English grammar: article determination and zero article (elected chairman, a university, a white, an S.D.O., The English)'
    elif 26 <= qnum <= 35:
        return 'english/grammar', 'English grammar: sentence structure analysis (simple, compound, complex sentences)'
    elif 36 <= qnum <= 40:
        return 'english/grammar', 'English grammar: sentence types and communicative notions (interrogative, declarative, assertive, imperative, request)'
    elif 41 <= qnum <= 56:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases (at sixes and sevens, wrong side of sixty, white feather, cross-purposes, for good, turned corner, blow own trumpet, piece of cake, under weather, sitting on fence, leave no stone unturned, etc.)'
    elif 57 <= qnum <= 62:
        return 'english/vocabulary', 'English vocabulary: word choice in context (fatally, accused, alienated, adequate, acquisition, common)'
    elif 63 <= qnum <= 74:
        return 'english/comprehension', 'English comprehension: passage reading analysis (Passage 1: Information and knowledge; Passage 2: Science and religion)'
    elif 75 <= qnum <= 80:
        return 'english/vocabulary/synonyms', 'English vocabulary: synonyms in context (mitigate, empathy, monotonous, scrupulous, deteriorating, impromptu)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General English (Lib.-Lunglei).pdf"

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
        "batch_id": 108,
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
        "reason": "Conventional written essay: 'Write an essay on any one of the following: The most memorable book that I have read / Ways to make Aizawl a better place / Smart phones in a student’s life (20 Marks)'. Preserved for conventional intake."
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
    "batch": 108,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Competitive Examinations for Recruitment to the Post of Librarian under Health & Family Welfare Department (Lunglei), May 2019 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 80
        }
    ],
    "targets": 80,
    "completion": "100% paper completion achieved for Librarian (Lunglei) 2019 General English (80/80 MCQs reviewed: 16 Idioms & Phrases, 15 Parts of Speech & Pronouns, 15 Grammar Core [Sentence Structure & Types], 12 Reading Comprehension, 6 Vocabulary in Context, 6 Synonyms, 5 Articles, 5 Tenses; 1 conventional essay question documented in written intake)",
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
print(f"Batch 108 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
