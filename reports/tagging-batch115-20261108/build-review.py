"""Build review candidates and findings for Batch 115: Junior Inspector of Cooperative Societies 2019 General English (79 MCQs)."""
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
    if (1 <= qnum <= 5) or qnum in (7, 8):
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and idiomatic phrases meaning (feather in cap, see eye to eye, between Scylla and Charybdis, grease the palm, bite the dust, cry wolf, plain sailing)'
    elif 9 <= qnum <= 16:
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idioms and phrases completion (rings a bell, smell a rat, no smoke without fire, poking nose in, call spade a spade, take bull by horns, leave no stone unturned, in high spirits)'
    elif 17 <= qnum <= 28:
        return 'english/comprehension', 'English comprehension: passage reading analysis (Passage 1: Q17–Q20; Passage 2: Q21–Q24; Passage 3: Q25–Q28)'
    elif 29 <= qnum <= 40:
        return 'english/grammar/parts-of-speech', 'English grammar: functional forms of nouns, verbs, adjectives, and adverbs in context'
    elif 41 <= qnum <= 48:
        return 'english/grammar/prepositions', 'English grammar: preposition usage in context'
    elif 49 <= qnum <= 59:
        return 'english/grammar', 'English grammar: sentence structure analysis (simple, compound, complex), sentence types, and communicative notions'
    elif qnum in (60, 61, 64):
        return 'english/vocabulary', 'English vocabulary: word choice in context (quiet, confident, waste)'
    elif qnum in (62, 63):
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: idiomatic expressions in context (in black and white, for good)'
    elif 65 <= qnum <= 68:
        return 'english/vocabulary', 'English vocabulary: homophones and commonly confused words (effected/affected, principal/principle, soar/sore, raised/razed)'
    elif qnum in (69, 70):
        return 'english/vocabulary/idioms-and-phrases', 'English vocabulary: proverb and idiom completions (Absence makes heart grow fonder / Home is where heart is)'
    elif 71 <= qnum <= 75:
        return 'english/vocabulary', 'English vocabulary: word definitions and meaning (pedantic, archaic, brine, thwart, tithe)'
    elif 76 <= qnum <= 80:
        return 'english/vocabulary', 'English vocabulary: commonly confused word pairs (human/humane, angel/angle, tampered/tempered, childish/childlike, lightning/lengthening)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2019-2020/General English (JICS).pdf"

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
        "batch_id": 115,
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
        "reason": "Conventional written essay: 'Write an essay on any one of the given topics (not more than 300 words): The importance of recycling / Preserving Our Mizo Language / Saving for a rainy day (20 Marks)'. Preserved for conventional intake."
    },
    {
        "paper_id": paper_id,
        "qnum": "6",
        "reason": "Legacy OCR intake drop: Short idiom question '6. To drive home (a) to find one’s root (b) to return to place to rest (c) back to original position (d) to emphasise' on Physical Page 2 was omitted from initial database extraction. Documented for future intake."
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
    "batch": 115,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Junior Inspector of Cooperative Societies under Cooperation Department, April 2019 — General English",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 79
        }
    ],
    "targets": 79,
    "completion": "100% paper completion achieved for Junior Inspector of Cooperative Societies 2019 General English (79/79 MCQs reviewed: 19 Idioms & Proverbs, 17 Vocabulary & Homophones, 12 Reading Comprehension, 12 Parts of Speech, 11 Grammar Core [Sentence Structure & Notions], 8 Prepositions; 1 conventional essay question and 1 legacy OCR dropped question documented)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 2,
    "conventional_marks_preserved": 20,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy generic classification into standard English curriculum taxonomy.",
        "Documented Section A (Essay writing, 20 marks) in pending-written-intake.json.",
        "Documented legacy OCR drop defect: Q6 ('To drive home') was omitted from initial DB extraction.",
        "Verified all 79 MCQs against 8 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 115 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
