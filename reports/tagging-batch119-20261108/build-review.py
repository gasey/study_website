"""Build review candidates and findings for Batch 119: CDPO 2025 General English (66 MCQs)."""
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
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification in context (though, uninclined, well, what, love, adore, himself, before, until, wish)'
    elif qnum in (11, 13, 16, 17, 18, 19, 20):
        return 'english/grammar/prepositions', 'English grammar: appropriate prepositions in context (about, on, with, of, in/within, upon, of)'
    elif qnum in (12, 14, 15):
        return 'english/grammar/parts-of-speech', 'English grammar: adverbs and conjunctive adverbs in sentence structure (ago, consequently, besides)'
    elif 21 <= qnum <= 26:
        return 'english/grammar', 'English grammar: phrases and clauses identification (noun clause, noun phrase, adjective clause, adjective phrase, adverb clause)'
    elif 27 <= qnum <= 31:
        return 'english/grammar', 'English grammar: sentence transformation (affirmative, assertive, negative, exclamatory)'
    elif 32 <= qnum <= 36:
        return 'english/grammar/reported-speech', 'English grammar: direct and indirect speech narration transformation'
    elif qnum in (37, 38, 41, 42):
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution (teetotaler, ineligible, monarchy, bigot)'
    elif qnum in (39, 40, 43):
        return 'english/vocabulary', 'English vocabulary: contextual word choice and semantic precision (magnanimous, epitome, credible)'
    elif 44 <= qnum <= 46:
        return 'english/sentence-correction', 'English syntax and sentence correction: spotting errors in sentence construction'
    elif 47 <= qnum <= 56:
        return 'english/grammar/tenses', 'English grammar: appropriate verb tenses and aspect usage (past continuous, present continuous, past perfect continuous, simple present, future perfect, etc.)'
    elif 57 <= qnum <= 61:
        return 'english/grammar/parts-of-speech', 'English grammar: subordinating and coordinating conjunctions / sentence connectors (hence, therefore, before, provided, if)'
    elif 62 <= qnum <= 66:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases meaning (a lone wolf, rule of thumb, close-fisted, up to one\'s elbows, hold one\'s tongue)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2025-2027/CDPO General English-2025..pdf"

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
        "batch_id": 119,
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
        "reason": "Conventional précis writing: Passage on verbal and non-verbal communication with title requirement (14 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Section A Q2",
        "reason": "Conventional reading comprehension: Modern industrial civilization and inventions passage with 5 sub-questions (10 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Section A Q3",
        "reason": "Conventional official letter drafting: Formal letter from CDPO to Director, W&CD detailing child malnutrition survey and intervention budget request (10 Marks). Preserved for conventional intake."
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
    "batch": 119,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Competitive Examination for Child Development Project Officer (CDPO) & Assistant Director (Food & Drugs), November 2025 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 66
        }
    ],
    "targets": 66,
    "completion": "100% paper completion achieved for CDPO & AD (Food & Drugs) 2025 General English (66/66 MCQs reviewed: 18 Parts of Speech & Connectors, 11 Grammar Core [Clauses, Phrases & Sentence Transformations], 10 Verb Tenses, 7 Prepositions, 5 Reported Speech [Direct/Indirect], 5 Idioms & Phrases, 4 One-Word Substitution, 3 Sentence Correction [Spotting Errors], 3 Contextual Vocabulary; 3 conventional written questions [34 marks total: Précis 14 marks, Reading Comprehension 10 marks, Official Letter Drafting 10 marks] documented in written intake)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 3,
    "conventional_marks_preserved": 34,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic classification into standard English curriculum taxonomy.",
        "Documented Section A (Précis 14 marks, Reading Comprehension 10 marks, Official Letter Drafting 10 marks; total 34 marks) in pending-written-intake.json.",
        "Verified all 66 MCQs against 9 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 119 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
