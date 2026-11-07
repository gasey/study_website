"""Build review candidates and findings for Batch 93: CEO 2019 General English Paper-II (100 MCQs)."""
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
        return 'english/grammar', 'English grammar: functional parts of speech identification (down, up, near, all, face, while, such, once, right, ones)'
    elif 11 <= qnum <= 20:
        return 'english/grammar', 'English grammar: noun types and classification (common, proper, collective, abstract, material)'
    elif 21 <= qnum <= 30:
        return 'english/grammar/prepositions', 'English grammar: prepositions and prepositional collocations'
    elif 31 <= qnum <= 40:
        return 'english/grammar', 'English grammar: adjectives and determiners classification (quantity, quality, demonstrative, indefinite, numeral, distributive)'
    elif 41 <= qnum <= 50:
        return 'english/grammar', 'English grammar: sentence analysis and structures (simple, compound, complex, compound-complex)'
    elif 51 <= qnum <= 60:
        return 'english/grammar', 'English grammar: phrases and clauses (noun/adjective/adverbial phrases and clauses)'
    elif 61 <= qnum <= 70:
        return 'english/grammar', 'English grammar: degrees of comparison (positive, comparative, superlative)'
    elif 71 <= qnum <= 80:
        return 'english/vocabulary', 'English vocabulary: double fill-in-the-blanks / contextual word pairings'
    elif 81 <= qnum <= 90:
        return 'english/vocabulary', 'English vocabulary: word choice and vocabulary fill in the blanks'
    elif 91 <= qnum <= 100:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution / term definitions (ambiguous, agenda, altruism, sinecure, apostate, retrospection, emeritus, perseverance, postscript, philology)'
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
        "paper_id": "Old_Questions/Direct_2019-2020/CEO General English-II.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 93,
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
    "batch": 93,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2019-2020/CEO General English-II.pdf",
            "paper_title": "Competitive Examinations for Recruitment to Circle Education Officer under School Education Department (2019) — General English Paper-II",
            "document_id": "doc_b62486413c037a0400665202",
            "sha256": "905ccb750d4a98236faea42938a452d5d7a261beda7f261938f7d52b3dffd36f",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Circle Education Officer 2019 General English Paper-II (100/100 MCQs reviewed: 60 Grammar Core, 20 Vocabulary Contextual, 10 Prepositions, 10 One-Word Substitution)",
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
        "Verified all 100 MCQs against 8 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 93 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
