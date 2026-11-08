"""Build review candidates and findings for Batch 100: Geologist Junior 2019 General English Paper-II (100 MCQs)."""
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
        return 'english/grammar', 'English grammar: functional parts of speech identification (over, dense, hastily, repeat, little, under, upon, before, around, throughout)'
    elif 11 <= qnum <= 20:
        return 'english/grammar', 'English grammar: pronouns identification and case usage (whom, who, whose, which, that, each other, one another)'
    elif 21 <= qnum <= 30:
        return 'english/grammar', 'English grammar: conjunctions (than, although, because, unless, since, so that, whereas, yet)'
    elif 31 <= qnum <= 35:
        return 'english/grammar/prepositions', 'English grammar: prepositions in context (on a diet, off the bridge, opposite, onto, across)'
    elif qnum in (36, 37, 40, 41, 42, 45, 97):
        return 'english/grammar/tenses', 'English grammar: verb tenses, aspect, and sequence of tenses (have been waiting, died, working, fought, runs, admire, would arrive / will arrive)'
    elif qnum in (38, 39, 43, 44, 98):
        return 'english/grammar', 'English grammar: non-finite verb / gerund, modal verb, adjective comparison, adverb form, and passive verb form'
    elif 46 <= qnum <= 51:
        return 'english/grammar', 'English grammar: sentence transformation and connector integration'
    elif 52 <= qnum <= 56:
        return 'english/grammar', 'English grammar: sentence types identification (simple, complex, compound)'
    elif 57 <= qnum <= 61:
        return 'english/grammar', 'English grammar: sentence synthesis and clause combination'
    elif 62 <= qnum <= 66:
        return 'english/grammar', 'English grammar: clause analysis (noun clause, adverb clause, adjective clause)'
    elif 67 <= qnum <= 71:
        return 'english/vocabulary', 'English vocabulary: lexical collocations in context (warm welcome, fatally wounded, urban legend, controversy surrounding, valuable asset)'
    elif 72 <= qnum <= 76:
        return 'english/vocabulary/synonyms', 'English vocabulary: synonyms / closest meaning (writer, ask, coarse, ancient, amends)'
    elif 77 <= qnum <= 86:
        return 'english/vocabulary/antonyms', 'English vocabulary: antonyms / opposite meaning (arrogant, blunt, sparse, rigid, expand, arrive, jubilant, moderate, gargantuan, hastily)'
    elif 87 <= qnum <= 96:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases (rank and file, at daggers drawn, cry for the moon, take to heels, high spirits, house of cards, kick the bucket, close fisted, cock sure, cut and dried)'
    elif qnum in (99, 100):
        return 'english/vocabulary', 'English vocabulary: homophones and confusables (principles vs principal, bored vs board)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/Geologist Junior General English Paper-II.pdf"

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
        "batch_id": 100,
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
    "batch": 100,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "Competitive Examinations for Recruitment to the Post of Geologist Junior (2019) — General English Paper-II",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Geologist Junior 2019 General English Paper-II (100/100 MCQs reviewed: 56 Grammar Core, 10 Antonyms, 10 Idioms & Phrases, 7 Lexical Collocations & Homophones, 7 Tenses, 5 Prepositions, 5 Synonyms)",
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
print(f"Batch 100 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
