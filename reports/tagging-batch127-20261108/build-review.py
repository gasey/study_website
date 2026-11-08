"""Build review candidates and findings for Batch 127: Circle Officer April-2026 Paper-I (Series A) (60 MCQs)."""
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
        return 'english/grammar/parts-of-speech', 'English grammar: identification of parts of speech (noun, pronoun, adjective, adverb, verb, preposition, conjunction)'
    elif 11 <= qnum <= 20:
        return 'english/grammar/prepositions', 'English grammar: prepositions and prepositional phrases (fawning upon, lost to, lying at hand, limit to, joy at, passion for, cured of, acquitted of, committed to)'
    elif 21 <= qnum <= 30:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms (senility/virility, warily/carelessly, grumpy/pleasant, vicious/virtuous, vanity/modesty, sturdy/weak, intently/casually, gradually/brisk, abstemious/self-indulgent, mendacious/truthful)'
    elif 31 <= qnum <= 35:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idiomatic expressions and phrases (go abegging, tread on toes, damp squib, bore the palm, jack of all trades)'
    elif 36 <= qnum <= 40:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitutions (sceptic, omniscient, epitaph, amnesty, expatriate)'
    elif 41 <= qnum <= 45:
        return 'english/grammar', 'English grammar: clause identification and analysis (adjective clause, adverb clause, noun clause, conditional clause)'
    elif 46 <= qnum <= 50:
        return 'english/grammar/reported-speech', 'English grammar: reported speech (direct to indirect speech and indirect to direct speech conversion)'
    elif 51 <= qnum <= 58:
        return 'english/grammar', 'English grammar: sentence transformation (interrogative, affirmative, exclamatory, negative, simple, complex, and compound sentences)'
    elif 59 <= qnum <= 60:
        return 'english/sentence-correction', 'English sentence correction: grammatical syntax and usage correction (pronoun order and subjunctive suggestion clause syntax)'
    else:
        raise ValueError(f"Unexpected qnum: {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2025-2027/Circle Officer April-2026 Paper-I (Series A)..pdf"

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
        "batch_id": 127,
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
        "question_number": "1",
        "paper_id": paper_id,
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/essay",
        "title": "Essay Writing",
        "details": "Write an essay choosing one of the topics: (a) The role of NGOs in community development, (b) Minimum Government, Maximum Governance, (c) Challenges faced by working women in modern society."
    },
    {
        "question_number": "2",
        "paper_id": paper_id,
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/precis",
        "title": "Précis Writing",
        "details": "Write a precis of the passage on urbanisation, rural development, and bridging the developmental gap in about one-third of the words content. Give a suitable title."
    },
    {
        "question_number": "3",
        "paper_id": paper_id,
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/letter",
        "title": "Letter Drafting",
        "details": "Write a Letter to the Mayor of Aizawl Municipal Corporation highlighting the rising incidence of burglary in various localities of Aizawl city and urging him to implement concrete measures to address the issue, including some remedial suggestions."
    },
    {
        "question_number": "4",
        "paper_id": paper_id,
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/comprehension",
        "title": "Reading Comprehension",
        "details": "Read passage on youth, social media influence, mental health, and cyberbullying, answering questions (a)-(d) short descriptive (8 marks) and (e)-(f) vocabulary MCQs (curated, inherently) (2 marks)."
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
    "batch": 127,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Competitive Examination for Recruitment to the Post of Circle Officer under Social Welfare, Women and Child Development Department, April 2026 — Paper-I (Series A)",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 60
        }
    ],
    "targets": 60,
    "completion": "100% paper completion achieved for Circle Officer April 2026 Paper-I (60/60 MCQs reviewed: 13 Grammar/Clauses/Transformation, 10 Parts of Speech, 10 Prepositions, 10 Antonyms, 5 Idioms & Phrases, 5 One-Word Substitutions, 5 Reported Speech, 2 Sentence Correction; 4 conventional items [40 marks] documented in pending-written-intake.json)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Part A conventional section (40 marks: Essay [10 marks], Précis [10 marks], Letter to Mayor on burglary [10 marks], Reading Comprehension [10 marks]) preserved in pending-written-intake.json.",
        "Part B (60 MCQs) fully reviewed and mapped to granular English taxonomy from generic top-level 'english' tag."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 127 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
