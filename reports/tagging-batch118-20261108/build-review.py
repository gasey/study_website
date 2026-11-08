"""Build review candidates and findings for Batch 118: Translator under Art & Culture 2019 General English (58 MCQs)."""
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
    if 1 <= qnum <= 8:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases meaning (hit upon, backed up, come off, losing ground, far cry, came to grief, fast life, bone of contention)'
    elif 9 <= qnum <= 16:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases usage in context (beggars description, harp on same string, followed suit, moved heaven and earth, sixes and sevens, threw cold water, wrong side of sixty, sum and substance)'
    elif 17 <= qnum <= 26:
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification (preposition, pronoun, conjunction, verb, adverb, adjective, noun)'
    elif 27 <= qnum <= 32:
        return 'english/grammar', 'English grammar: clause analysis (adverb clause, adjective/relative clause, noun clause)'
    elif 33 <= qnum <= 37:
        return 'english/grammar', 'English grammar: sentence structure analysis (simple, compound, complex)'
    elif 38 <= qnum <= 42:
        return 'english/grammar/voice', 'English grammar: active and passive voice transformation'
    elif qnum == 43:
        return 'english/grammar/subject-verb-agreement', 'English grammar: subject-verb agreement with compound singular subject (My friend and mentor has arrived)'
    elif qnum == 44:
        return 'english/grammar', 'English grammar: linking verbs and predicate adjectives (smells sweet)'
    elif qnum == 45:
        return 'english/grammar', 'English grammar: degrees of comparison (wisest of all)'
    elif qnum == 46:
        return 'english/grammar/tenses', 'English grammar: verb conjugation and past tense usage (laid the book)'
    elif qnum == 47:
        return 'english/grammar', 'English grammar: adverb modifier structure (too good to be true)'
    elif qnum == 48:
        return 'english/grammar/parts-of-speech', 'English grammar: conditional subordinating conjunction (unless)'
    elif qnum == 49:
        return 'english/grammar/prepositions', 'English grammar: complex prepositional phrase (on behalf of)'
    elif 50 <= qnum <= 53:
        return 'english/vocabulary', 'English vocabulary: contextual word choice and distinctions (adapt, prescribe, admittance, petition)'
    elif qnum == 54:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution (Ambidexterous)'
    elif 55 <= qnum <= 56:
        return 'english/vocabulary', 'English vocabulary: appropriate collective and specific nouns (consignment, catalogue)'
    elif 57 <= qnum <= 58:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution (colleague, Ethnology)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General English (Translator).pdf"

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
        "batch_id": 118,
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
        "reason": "Conventional written essay: 'Strong cultural values keep one rooted in modern times' (400-500 words, 20 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Section A Q2",
        "reason": "Conventional summary/précis: Letter from Jawaharlal Nehru to his daughter Indira on her 13th birthday (10 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Section A Q3",
        "reason": "Conventional verse paraphrase: 'The glories of our blood and state...' (6 Marks). Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "Section A Q4",
        "reason": "Conventional translation from Mizo to English: 'Mi chungchanga ngaih dân kan siam hian hmuh hmaih kan nei châwk...' (6 Marks). Preserved for conventional intake."
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
    "batch": 118,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Translator under Art & Culture Department, May 2019 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 58
        }
    ],
    "targets": 58,
    "completion": "100% paper completion achieved for Translator under Art & Culture 2019 General English (58/58 MCQs reviewed: 16 Idioms & Phrases, 14 Grammar Core [Clauses, Sentence Analysis, Predicate Adjectives, Comparison, Modifiers], 11 Parts of Speech, 6 Contextual Vocabulary, 5 Active/Passive Voice, 3 One-Word Substitution, 1 Subject-Verb Agreement, 1 Verb Tenses, 1 Prepositions; 4 conventional written questions [42 marks total: Essay 20 marks, Précis 10 marks, Paraphrase 6 marks, Translation 6 marks] documented in written intake)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 4,
    "conventional_marks_preserved": 42,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic classification into standard English curriculum taxonomy.",
        "Documented Section A (Essay 20 marks, Précis 10 marks, Verse paraphrase 6 marks, Mizo-to-English translation 6 marks; total 42 marks) in pending-written-intake.json.",
        "Verified all 58 MCQs against 7 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 118 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
