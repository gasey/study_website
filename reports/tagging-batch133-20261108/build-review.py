"""Build review candidates and findings for Batch 133: UDC Agriculture 2018 Paper-I (75 MCQs)."""
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
        return 'english/grammar/parts-of-speech', 'English grammar: identification of parts of speech (noun, conjunction, pronoun, adverb, verb, preposition)'
    elif 9 <= qnum <= 16:
        return 'english/grammar', 'English grammar: clause identification and analysis (noun clause, adverb clause, adjective clause, co-ordinate clause)'
    elif 17 <= qnum <= 24:
        return 'english/grammar', 'English grammar: sentence structure analysis (simple, compound, and complex sentences)'
    elif 25 <= qnum <= 32:
        return 'english/grammar', 'English grammar: functional concepts and speech acts (wish, condition, ability, promise, obligation, permission, purpose)'
    elif 33 <= qnum <= 40:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: phrasal verbs and idioms (bring up, call off, give in, look into, put out, take after, turn down, hold on)'
    elif 41 <= qnum <= 48:
        return 'english/vocabulary/one-word-substitution', 'English vocabulary: one-word substitution (immigrate, obsolete, anonymous, invincible, panacea, polyglot, somnambulist, autobiography)'
    elif 49 <= qnum <= 57:
        return 'english/grammar/prepositions', 'English grammar: prepositions and prepositional phrases (on, by, at, for, of, with, into)'
    elif 58 <= qnum <= 66:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and phrases (rub shoulders with, bite the dust, hard nut to crack, in full swing, burn candles both ends, nip in the bud, see eye to eye, bolt from blue, bed of roses)'
    elif 67 <= qnum <= 75:
        return 'english/grammar/tenses', 'English grammar: verb forms, tenses, and modals (modals, past perfect, continuous, conditional)'
    else:
        raise ValueError(f"Unexpected qnum: {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2014-2018/1.UDC under Agriculture Deptt. Paper-I.pdf"

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
        "batch_id": 133,
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
        "question_number": "1",
        "paper_id": paper_id,
        "marks": 25,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/essay",
        "title": "Essay Writing",
        "details": "Write an essay in about 500 words on 'Electricity in the Service of Man'."
    },
    {
        "question_number": "2",
        "paper_id": paper_id,
        "marks": 25,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/precis",
        "title": "Précis Writing",
        "details": "Write a précis and provide a title for George Orwell's passage on sports, competitive prestige, and international contests as mimic warfare."
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
    "batch": 133,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examinations for Recruitment to the Post of U.D.C. under Agriculture (Crop Husbandry) Department, March 2018 — Paper-I",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 75
        }
    ],
    "targets": 75,
    "completion": "100% paper completion achieved for UDC under Agriculture 2018 Paper-I (75/75 MCQs reviewed: 24 Grammar / Clauses / Sentence Analysis / Speech Acts, 17 Idioms & Phrasal Verbs, 9 Prepositions, 9 Tenses & Verb Forms, 8 Parts of Speech, 8 One-Word Substitutions; Section A Essay [25 marks] and Précis [25 marks] preserved in pending-written-intake.json)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Section A (50 conventional marks: Essay 25 marks on Electricity in the Service of Man, Précis 25 marks on The Sporting Spirit) preserved in pending-written-intake.json.",
        "Reclassified and refined Section B (75 MCQs) into precise grammatical and vocabulary subtopics."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 133 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
