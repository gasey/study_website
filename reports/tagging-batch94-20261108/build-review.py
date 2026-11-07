"""Build review candidates and findings for Batch 94: Tourist Officer 2019 General English Paper-II (100 MCQs)."""
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
        return 'english/grammar', 'English grammar: parts of speech identification (pronoun, verb, noun, adjective, conjunction, numeral, adverb, preposition)'
    elif 11 <= qnum <= 20:
        return 'english/grammar/tenses', 'English grammar: verb forms, aspects, and tenses'
    elif qnum in (21, 22, 23, 26, 27, 29):
        return 'english/grammar/prepositions', 'English grammar: preposition selection in context'
    elif qnum in (24, 25, 28, 30):
        return 'english/grammar', 'English grammar: connectors and conjunctions'
    elif 31 <= qnum <= 40:
        return 'english/grammar', 'English grammar: adjectives, determiners, and adverbs'
    elif 41 <= qnum <= 50:
        return 'english/grammar', 'English grammar: sentence transformations (interrogative, degree conversion, affirmative, negative, assertive)'
    elif 51 <= qnum <= 60:
        return 'english/grammar', 'English grammar: sentence type conversions (simple, compound, complex)'
    elif 61 <= qnum <= 70:
        return 'english/grammar', 'English grammar: sentence synthesis and clause combination'
    elif 71 <= qnum <= 80:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases'
    elif 81 <= qnum <= 85:
        return 'english/vocabulary/synonyms', 'English vocabulary: synonyms / nearest meaning'
    elif 86 <= qnum <= 90:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms / opposite meaning'
    elif 91 <= qnum <= 100:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution / term definitions (anarchy, edible, teetotaller, insatiable, obnoxious, indefatigable, posthumously, virtuoso, impregnable, nepotism)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

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
        "paper_id": "Old_Questions/Direct_2019-2020/T.O General English Paper-II.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 94,
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
    "batch": 94,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2019-2020/T.O General English Paper-II.pdf",
            "paper_title": "Competitive Examinations for Recruitment to Tourist Officer under Tourism Department (2019) — General English Paper-II",
            "document_id": "doc_91a4e2e762e15e99c2db9bc7",
            "sha256": "4f8b865c093b1c831caa7cdfb303e6c46de8db7b07f58d4ea8337a739d13fd4a",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Tourist Officer 2019 General English Paper-II (100/100 MCQs reviewed: 54 Grammar Core, 10 Tenses, 10 Idioms, 10 One-Word Substitution, 6 Prepositions, 5 Synonyms, 5 Antonyms)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy blanket gk classifications into standard english curriculum taxonomy.",
        "Verified all 100 MCQs against 10 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 94 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
