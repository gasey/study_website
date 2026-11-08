"""Build review candidates and findings for Batch 120: Assistant Controller of Mines March-2026 General English (66 MCQs)."""
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
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification (pronoun, noun, adverb, verb, adjective, preposition, conjunction, interjection)'
    elif 11 <= qnum <= 16:
        return 'english/vocabulary', 'English vocabulary: contextual word choice and semantic precision (alleviate, steadfast, momentous, catalyst, inconsistent, mislead)'
    elif qnum in (17, 18, 21, 22, 26):
        return 'english/grammar/prepositions', 'English grammar: appropriate prepositions in context (beside, on, over, among, below)'
    elif qnum in (19, 20, 23, 24, 25):
        return 'english/grammar/parts-of-speech', 'English grammar: coordinating and subordinating conjunctions (yet, since, though, or, if)'
    elif 27 <= qnum <= 36:
        return 'english/grammar/parts-of-speech', 'English grammar: word formation and conversion across parts of speech (bravery, arrived, unlucky, easily, laughter, sweet, firmly, loneliness, wrong, proud)'
    elif 37 <= qnum <= 41:
        return 'english/grammar', 'English grammar: sentence structure and communicative function (imperative, complex, compound, assertive, optative)'
    elif 42 <= qnum <= 46:
        return 'english/grammar', 'English grammar: phrase and clause identification (adjective phrase, noun phrase, adverb phrase, adverb clause, adjective clause)'
    elif 47 <= qnum <= 51:
        return 'english/grammar/reported-speech', 'English grammar: direct and indirect speech narration conversion (imperative commands, negative advice, past assertive)'
    elif 52 <= qnum <= 56:
        return 'english/grammar', 'English grammar: phrase and clause identification in complex sentences (adverb clause, noun phrase, adjective clause, adverb phrase, noun clause)'
    elif 57 <= qnum <= 61:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution and descriptive terms (nepotism, philanthropist, ephemeral, eclectic, fastidious)'
    elif 62 <= qnum <= 66:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases meaning (barking up the wrong tree, rite of passage, end in smoke, harp on same string, give oneself airs)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_NG_2024-2027/Asistant Controller of Mines March-2026 General English..pdf"

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
        "batch_id": 120,
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
        "qnum": "Part A Q1",
        "reason": "Conventional précis writing: Social media and Instatourism passage with title requirement (14 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Part A Q2",
        "reason": "Conventional official letter drafting: Formal letter from Assistant Controller of Mines (Siaha) to Director, Commerce & Industries reporting unauthorized mineral extraction and requesting enforcement support (10 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Part A Q3",
        "reason": "Conventional reading comprehension: Jeff Bezos Princeton 2010 speech excerpt ('Cleverness is a gift, kindness is a choice') with 4 sub-questions (10 Marks). Preserved for conventional intake."
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
    "batch": 120,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Competitive Examination for Recruitment to the Post of Assistant Controller of Mines under Geology & Mining, Commerce & Industries Department, March 2026 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 66
        }
    ],
    "targets": 66,
    "completion": "100% paper completion achieved for Assistant Controller of Mines March-2026 General English (66/66 MCQs reviewed: 25 Parts of Speech [Identification, Conjunctions & Word Conversions], 15 Grammar Core [Phrases, Clauses, Sentence Classification & Communicative Functions], 6 Contextual Vocabulary, 5 Prepositions, 5 Reported Speech [Direct/Indirect], 5 One-Word Substitution, 5 Idioms & Phrases; 3 conventional written questions [34 marks total: Précis 14 marks, Official Letter Drafting 10 marks, Reading Comprehension 10 marks] documented in written intake)",
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
        "Documented Part A (Précis 14 marks, Official Letter Drafting 10 marks, Reading Comprehension 10 marks; total 34 marks) in pending-written-intake.json.",
        "Verified all 66 MCQs against 10 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 120 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
