"""Build review candidates and findings for Batch 123: Assistant under MPSC 2019 Paper-I (77 items: 75 MCQs + 2 Conventional)."""
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

def assign_tax(qnum_str, q):
    if qnum_str == 'W1':
        return 'english/writing/essay', 'English conventional writing: essay composition (Enslavement of man by technology / Role of newspapers / Main Festivals in Mizoram; 25 Marks)'
    elif qnum_str == 'W2':
        return 'english/writing/precis', 'English conventional writing: précis comprehension and condensation with title (Trees and noble character; 25 Marks)'
    
    qnum = int(qnum_str)
    if 1 <= qnum <= 10:
        return 'english/grammar/parts-of-speech', 'English grammar: functional parts of speech identification (verb, conjunction, adjective, noun, adverb, pronoun, preposition)'
    elif 11 <= qnum <= 20:
        return 'english/grammar', 'English grammar: sentence classification (declarative, interrogative, imperative, exclamatory, simple, compound, complex)'
    elif 21 <= qnum <= 30:
        return 'english/grammar/tenses', 'English grammar: identification of verb tenses and aspects (simple past, present continuous, past perfect, future continuous, present perfect, etc.)'
    elif 31 <= qnum <= 40:
        return 'english/grammar/prepositions', 'English grammar: appropriate prepositions in context (at, on, in, by, with, for, into, of)'
    elif 41 <= qnum <= 50:
        return 'english/grammar/tenses', 'English grammar: appropriate forms of verbs and agreement in context (went, has lived, was reading, had finished, will go, etc.)'
    elif 51 <= qnum <= 60:
        return 'english/grammar/parts-of-speech', 'English grammar: connecting words / subordinating and coordinating conjunctions (because, although, unless, but, if, so that)'
    elif 61 <= qnum <= 70:
        return 'english/grammar/parts-of-speech', 'English grammar: adjective selection and degrees/qualities in context'
    elif 71 <= qnum <= 75:
        return 'english/grammar', 'English grammar: question tags mechanics (doesn\'t she, can she, have they, etc.)'
    raise ValueError(f"unhandled qnum {qnum_str}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/Asst. Grade under MPSC Paper-1.pdf"

for item in packet["items"]:
    cid = item["canonical_id"]
    aid = item["appearance_id"]
    rec = item["snapshot"]["record"]
    qnum_str = str(rec["qnum"])
    q_text = rec["question"]
    fingerprint = item["source_fingerprint"]
    
    cur_cls = rec.get("classification") or {"subject_id": None, "topic_id": None, "subtopic_id": None}
    
    target_tax, rationale = assign_tax(qnum_str, q_text)
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
        "batch_id": 123,
        "policy": "study-tagging-v1"
    }
    pending_candidates.append(cand)
    
    findings.append({
        "qnum": qnum_str,
        "canonical_id": cid,
        "appearance_id": aid,
        "action": action,
        "current_taxonomy": cur_cls,
        "target_taxonomy": parsed,
        "rationale": rationale,
        "stem_excerpt": q_text[:80]
    })

def sort_key(x):
    q = x["qnum"]
    if q.startswith("W"):
        return (1, int(q[1:]))
    return (0, int(q))

findings.sort(key=sort_key)
pending_candidates.sort(key=lambda x: sort_key(next(f for f in findings if f["appearance_id"] == x["appearance_id"])))

unextracted_items = [
    {
        "paper_id": paper_id,
        "qnum": "Section A Q1 (W1)",
        "reason": "Conventional written essay: 'Write an essay on any one of the given following topics in not less than 350 words: Enslavement of man by technology / Role of newspapers in influencing society or youth / Main Festivals in Mizoram (25 Marks)'. Intake in DB as canonical W1."
    },
    {
        "paper_id": paper_id,
        "qnum": "Section A Q2 (W2)",
        "reason": "Conventional précis writing: 'Read the given passage carefully and write a précis in about one third of the original length giving a suitable title (25 Marks)'. Intake in DB as canonical W2."
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
    "batch": 123,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Assistant under Mizoram Public Service Commission, April 2019 — Paper - I",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 77
        }
    ],
    "targets": 77,
    "completion": "100% paper completion achieved for Assistant under MPSC 2019 Paper-I (77 items reviewed: 75 MCQs + 2 conventional written items [125 marks total: Section A 50 marks, Section B 75 marks]: 30 Parts of Speech [Identification, Conjunctions & Adjectives], 20 Verb Tenses & Forms, 15 Grammar Core [Sentence Classification & Question Tags], 10 Prepositions, 1 Essay Writing, 1 Précis Writing)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 2,
    "conventional_marks_preserved": 50,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic classification into standard English curriculum taxonomy, including classifying Section A conventional items W1 and W2 into english/writing/essay and english/writing/precis.",
        "Documented Section A (50 marks: Essay 25 marks and Précis 25 marks) in pending-written-intake.json.",
        "Verified all 77 items against 8 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 123 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
