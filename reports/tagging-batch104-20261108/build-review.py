"""Build review candidates and findings for Batch 104: District Organiser (March 2020) General English (80 MCQs)."""
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
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases (give a wide berth, flesh creep, rub wrong way, gets on nerves, high and dry, speak volumes, etc.)'
    elif 17 <= qnum <= 23:
        return 'english/comprehension', 'English comprehension: reading passage questions on society and extravagance'
    elif 24 <= qnum <= 28:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms / opposite meaning to words from passage (admired, extravagant, despised, careful, popularity)'
    elif 29 <= qnum <= 36:
        return 'english/grammar', 'English grammar: functional parts of speech identification (still, off, round, better, but, etc.)'
    elif 37 <= qnum <= 42:
        return 'english/grammar/tenses', 'English grammar: verb tense selection and form completions in context (moves, has gone, went, had started, etc.)'
    elif 43 <= qnum <= 48:
        return 'english/grammar/prepositions', 'English grammar: appropriate prepositions in context (on diet, by, in, into, etc.)'
    elif 49 <= qnum <= 58:
        return 'english/grammar', 'English grammar: sentence kind analysis (simple, compound, complex)'
    elif 59 <= qnum <= 64:
        return 'english/grammar', 'English grammar: sentence type identification (affirmative, negative, interrogative, exclamatory, imperative, assertive)'
    elif qnum in (65, 67, 74):
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: similes, collocations, and phrasal verbs (firm as a rock, fair share, taken after)'
    elif qnum in (66, 68, 69, 70, 71, 72, 73):
        return 'english/vocabulary', 'English vocabulary: contextual vocabulary selection (scalded, dispersed, wince, exercise restraint, sumptuous, averted, neglected)'
    elif 75 <= qnum <= 80:
        return 'english/vocabulary/synonyms', 'English vocabulary: synonyms / nearest in meaning to underlined words (vigilant, etc.)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General English(DO, March).pdf"

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
        "batch_id": 104,
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
    "batch": 104,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examinations for Recruitment to the Post of District Organiser (Contract) (March 2020) — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 80
        }
    ],
    "targets": 80,
    "completion": "100% paper completion achieved for District Organiser March 2020 General English (80/80 MCQs reviewed: 24 Grammar Core, 19 Idioms & Phrases, 7 Reading Comprehension, 7 Contextual Vocabulary, 6 Tenses, 6 Prepositions, 6 Synonyms, 5 Antonyms)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic and cross-subject classifications (e.g. economy/agriculture drops) into standard English curriculum taxonomy.",
        "Verified all 80 MCQs against 8 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 104 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
