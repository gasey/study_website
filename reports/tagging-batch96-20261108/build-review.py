"""Build review candidates and findings for Batch 96: Inspector FCS&CA 2019 General English Paper-II (100 MCQs)."""
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
        return 'english/grammar', 'English grammar: functional parts of speech identification (verb, adverb, noun, adjective, pronoun, conjunction, preposition)'
    elif 11 <= qnum <= 20:
        return 'english/grammar/tenses', 'English grammar: verb tense selection and form completions'
    elif 21 <= qnum <= 30:
        return 'english/grammar/prepositions', 'English grammar: preposition selection in context'
    elif 31 <= qnum <= 40:
        return 'english/grammar/tenses', 'English grammar: tense identification of verb forms'
    elif 41 <= qnum <= 50:
        return 'english/grammar', 'English grammar: sentence transformations (degrees of comparison, negative, assertive, affirmative, interrogative)'
    elif 51 <= qnum <= 60:
        return 'english/grammar', 'English grammar: sentence structure conversion (simple, compound, complex)'
    elif 61 <= qnum <= 70:
        return 'english/grammar', 'English grammar: sentence synthesis and clause combinations'
    elif 71 <= qnum <= 80:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases (not playing with full deck, a steal, above the salt, at sixes and sevens, Big Apple, fifth wheel, in a nutshell, shift gears, bitter pill to swallow, stool pigeon)'
    elif 81 <= qnum <= 90:
        return 'english/vocabulary/synonyms', 'English vocabulary: synonyms / closest meaning (fervent, dossier, panache, august, irrelevant, camouflage, unorthodox, behest, antithesis, paradigm)'
    elif 91 <= qnum <= 100:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution / definitions (idyllic, paraphernalia, novice, sycophant, zenith, nemesis, embezzle, hoi polloi, referendum, advocate)'
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
        "paper_id": "Old_Questions/Direct_2019-2020/Inspector under F,CS & CA Dept-2019, General English Paper II..pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 96,
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
    "batch": 96,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2019-2020/Inspector under F,CS & CA Dept-2019, General English Paper II..pdf",
            "paper_title": "Competitive Examinations for Recruitment to Grade-V of Mizoram Food, Civil Supplies & Consumer Affairs Service (Inspector) (2019) — General English Paper-II",
            "document_id": "doc_1bae5c6e6df2c18914fb9558",
            "sha256": "94f7fcbb4bb4a692b4e47d89bf3a64a002807712aa94a2869cb3a3f806f933a6",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Inspector FCS&CA 2019 General English Paper-II (100/100 MCQs reviewed: 40 Grammar Core, 20 Tenses, 10 Prepositions, 10 Idioms, 10 Synonyms, 10 One-Word Substitution)",
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
print(f"Batch 96 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
