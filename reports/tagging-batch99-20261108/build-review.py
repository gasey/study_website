"""Build review candidates and findings for Batch 99: Veterinary Officer (V.O) 2019 General English Paper-II (100 MCQs)."""
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
        return 'english/grammar', 'English grammar: functional parts of speech identification (better, cut, down, else, less, like, near, only, round, that)'
    elif 11 <= qnum <= 20:
        return 'english/grammar/prepositions', 'English grammar: preposition selection in context (abide by, accused of, abstain from, adhere to, adapt to, agree with, aware of, aspire to, approve of, blind to)'
    elif 21 <= qnum <= 30:
        return 'english/grammar', 'English grammar: adjective classification (quality, quantity, demonstrative, distributive, interrogative, numeral, proper)'
    elif 31 <= qnum <= 40:
        return 'english/grammar', 'English grammar: modal auxiliaries (could, can, may, might, must, should, would, ought to)'
    elif 41 <= qnum <= 50:
        return 'english/grammar', 'English grammar: sentence types analysis (simple, compound, complex)'
    elif 51 <= qnum <= 60:
        return 'english/grammar', 'English grammar: phrase types identification (noun phrase, adjective phrase, adverb phrase)'
    elif 61 <= qnum <= 70:
        return 'english/grammar', 'English grammar: sentence types & communicative notions (affirmative, negative, interrogative, exclamatory, comparative, assertive)'
    elif 71 <= qnum <= 80:
        return 'english/sentence-correction', 'English sentence correction: phrase improvement and grammatical error substitution'
    elif 81 <= qnum <= 90:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution / term definitions (boutique, bailiwick, teetotaler, plagiarism, misologist, bombastic, pedantic, maxim, idiosyncrasy, kleptomania)'
    elif qnum == 91:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms (chronic -> acute)'
    elif qnum in (92, 96, 99):
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: proverbs, idioms, and similes (cut your coat according to your cloth, black will take no other hue, as graceful as a swan)'
    elif qnum == 97:
        return 'english/vocabulary/synonyms', 'English vocabulary: synonyms / closest meaning (launch -> begin)'
    elif qnum in (93, 94, 95, 98, 100):
        return 'english/vocabulary', 'English vocabulary: animal genders, collective nouns, foreign phrases, and verbal analogies'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General English Paper-II (V.O).pdf"

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
        "batch_id": 99,
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
    "batch": 99,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Competitive Examinations for Recruitment to the Post of Veterinary Officer (V.O) (2019) — General English Paper-II",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Veterinary Officer 2019 General English Paper-II (100/100 MCQs reviewed: 60 Grammar Core, 10 Prepositions, 10 Sentence Correction, 10 One-Word Substitution, 5 General Vocabulary & Analogies, 3 Idioms & Phrases, 1 Synonym, 1 Antonym)",
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
        "Verified all 100 MCQs against 8 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 99 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
