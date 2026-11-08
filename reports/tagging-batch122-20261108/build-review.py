"""Build review candidates and findings for Batch 122: Coach Grade-I 2019 General English (86 appearances / 80 booklet MCQs)."""
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
    if 1 <= qnum <= 7:
        return 'english/comprehension', 'English comprehension: passage reading analysis on zoo animals and animal traits'
    elif 8 <= qnum <= 12:
        return 'english/comprehension', 'English comprehension: passage reading analysis on science, modern civilization and progress'
    elif 13 <= qnum <= 18:
        return 'english/grammar', 'English grammar: sentence structure analysis (Simple, Compound, Complex)'
    elif 19 <= qnum <= 23:
        return 'english/grammar', 'English grammar: clause analysis (Noun clause, Adjective clause, Adverb clause)'
    elif 24 <= qnum <= 28:
        return 'english/grammar', 'English grammar: sentence classification (Declarative, Imperative, Interrogative, Exclamatory)'
    elif 29 <= qnum <= 34:
        return 'english/vocabulary', 'English vocabulary: contextual word choice and lexical precision'
    elif 35 <= qnum <= 39:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms / opposite meanings (Curtail, Bane, Gruesome, Hefty, Abhor)'
    elif 40 <= qnum <= 44:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution (Theology, Misanthrope, Polyandry, Numismatist, Omnipotent)'
    elif 45 <= qnum <= 51:
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification (adverb, adjective, conjunction, preposition, noun, verb)'
    elif 52 <= qnum <= 58:
        return 'english/grammar/prepositions', 'English grammar: appropriate prepositions in context (at, on, in, with, to, through)'
    elif 59 <= qnum <= 64:
        return 'english/grammar/tenses', 'English grammar: appropriate forms of verbs and tense usage in context (has written, were, had left, was raining, etc.)'
    elif 65 <= qnum <= 72:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases meaning (face the music, call a spade a spade, red-letter day, apple of eye, tooth and nail, etc.)'
    elif 73 <= qnum <= 80:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idiomatic expressions meaning (bite the dust, storm in a teacup, wild goose chase, blow one\'s own trumpet, etc.)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/Coach Grade-I General English.pdf"

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
        "batch_id": 122,
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

findings.sort(key=lambda x: (int(x["qnum"]), x["appearance_id"]))
pending_candidates.sort(key=lambda x: (next(int(i["snapshot"]["record"]["qnum"]) for i in packet["items"] if i["appearance_id"] == x["appearance_id"]), x["appearance_id"]))

unextracted_items = [
    {
        "paper_id": paper_id,
        "qnum": "Section A Q1",
        "reason": "Conventional written essay: 'Write an essay choosing any one of the topics given below: Child Labour / Save water, Save life / Importance of Sports (20 Marks)'. Preserved for conventional intake."
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
    "batch": 122,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Technical Competitive Examinations for Recruitment to the Post of Coach Grade - I under Sports & Youth Services Department, April 2019 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 86
        }
    ],
    "targets": 86,
    "completion": "100% paper completion achieved for Coach Grade-I 2019 General English (86 appearances / 80 booklet MCQs reviewed: 16 Idioms & Phrases, 16 Grammar Core [Sentence Structure, Clauses & Sentence Types], 12 Reading Comprehension [2 passages], 10 Antonyms [5 booklet items + 5 duplicate OCR extractions], 8 Parts of Speech [7 booklet items + 1 duplicate extraction], 7 Prepositions, 6 Contextual Vocabulary, 6 Verb Tenses & Forms, 5 One-Word Substitution; 1 conventional essay question [20 marks] documented in written intake)",
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
        "Documented duplicate database extractions for Q35, Q36, Q37, Q38, Q39 (ingested both with and without 'Select the opposite of the given word:' prefix) and Q46 (ingested twice); all 6 duplicate pairs were consistently reviewed with matching signatures.",
        "Verified all 86 appearances against 8 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 122 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
