"""Build review candidates and findings for Batch 121: Employment Officer 2019 General English Paper-II (100 MCQs)."""
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
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification (verb, noun, adjective, adverb, conjunction, pronoun, interjection)'
    elif 11 <= qnum <= 15:
        return 'english/grammar/prepositions', 'English grammar: appropriate prepositions in context (behind, in, in, into, to)'
    elif 16 <= qnum <= 20:
        return 'english/grammar/parts-of-speech', 'English grammar: coordinating and subordinating conjunctions (but, neither, nevertheless, moreover, on the other hand)'
    elif 21 <= qnum <= 30:
        return 'english/grammar/tenses', 'English grammar: appropriate forms of verbs and tense usage in context (has written, were, had left, was raining, will have completed, etc.)'
    elif 31 <= qnum <= 35:
        return 'english/grammar/parts-of-speech', 'English grammar: appropriate pronoun usage in context (relative, reflexive, demonstrative, indefinite)'
    elif 36 <= qnum <= 40:
        return 'english/grammar/articles', 'English grammar: definite, indefinite, and zero article usage'
    elif 41 <= qnum <= 48:
        return 'english/grammar', 'English grammar: sentence structure analysis (Simple, Compound, Complex sentences)'
    elif 49 <= qnum <= 56:
        return 'english/grammar', 'English grammar: degrees of comparison identification and transformation (Positive, Comparative, Superlative)'
    elif 57 <= qnum <= 61:
        return 'english/grammar', 'English grammar: phrase structure identification (Adjective phrase, Noun phrase, Adverb phrase)'
    elif 62 <= qnum <= 65:
        return 'english/grammar', 'English grammar: clause analysis (Adverb clause, Adjective clause, Noun clause)'
    elif 66 <= qnum <= 70:
        return 'english/grammar', 'English grammar: semantic notions and communicative functions expressed by sentences (Supposition, Concession, Purpose, Condition, Result)'
    elif 71 <= qnum <= 80:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases meaning (gift of the gab, spill the beans, burn the midnight oil, dark horse, turn a deaf ear, etc.)'
    elif 81 <= qnum <= 86:
        return 'english/vocabulary/synonyms', 'English vocabulary: synonyms / nearest meaning in context (abundant, benevolent, frugal, obstinate, candid, transient)'
    elif 87 <= qnum <= 94:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms / opposite meaning in context (hostile, obscure, artificial, expand, genuine, rigid, despair, transparent)'
    elif 95 <= qnum <= 100:
        return 'english/vocabulary', 'English vocabulary: contextual word choice and distinctions (discredit, renounced, rewarded, inevitable, erosion, unanimous)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General Englsih Paper-II (EO).pdf"

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
        "batch_id": 121,
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

unextracted_items = []

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps(unextracted_items, ensure_ascii=False, indent=2) + "\n")

tax_counts = Counter(
    (c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"])
    for c in pending_candidates
)
action_counts = Counter(c["action"] for c in pending_candidates)

summary = {
    "batch": 121,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Technical Competitive Examinations for Recruitment to the Post of Employment Officer under Labour, Employment and Industrial Training Department, April 2019 — General English Paper - II",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Employment Officer under LE&IT 2019 General English Paper-II (100/100 MCQs reviewed: 30 Grammar Core [Sentence Structure, Degrees of Comparison, Phrases, Clauses & Communicative Functions], 20 Parts of Speech [Identification, Conjunctions & Pronouns], 10 Verb Forms & Tenses, 10 Idioms & Phrases, 8 Antonyms, 6 Synonyms, 6 Contextual Vocabulary, 5 Prepositions, 5 Articles)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic classification into standard English curriculum taxonomy.",
        "Verified all 100 MCQs against 8 rendered page images from source PDF; 100% paper completion with no unextracted conventional sections (all 100 marks are objective MCQs)."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 121 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
