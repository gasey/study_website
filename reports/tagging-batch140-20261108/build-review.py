"""Build candidates, findings, summary, and written intake for Batch 140."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

taxonomy_list = packet["taxonomy"]
tax_by_id = {t["id"]: t for t in taxonomy_list}

def make_primary(sid, tid=None, subid=None):
    return {
        "subject_id": sid,
        "topic_id": tid,
        "subtopic_id": subid
    }

unextracted_items = [
    {
        "question_number": "1",
        "paper_id": "Old_Questions/Direct_2014-2018/1. General English.pdf",
        "marks": 20,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/essay",
        "title": "Essay Writing",
        "details": "Write an essay on The Pleasures of Reading / Economic growth in Mizoram / Political parties in Mizoram / Role of women in churches."
    },
    {
        "question_number": "2",
        "paper_id": "Old_Questions/Direct_2014-2018/1. General English.pdf",
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/precis",
        "title": "Précis Writing",
        "details": "Write a précis on the finer instincts of man, tolerance, and world peace."
    }
]

(out / "pending-written-intake.json").write_text(json.dumps(unextracted_items, ensure_ascii=False, indent=2) + "\n")

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

for it in packet["items"]:
    snap = it["snapshot"]
    rec = snap["record"]
    aid = it["appearance_id"]
    cid = it["canonical_id"]
    cur_primary = rec["classification"]
    pid = it["appearance"]["paper_id"]
    qnum_str = str(it["appearance"]["qnum"])
    qtext = rec["question"]

    if pid.endswith("/1. General English.pdf"):
        if qnum_str in ("11", "13", "14", "15"):
            prop = make_primary("english", "english/vocabulary", None)
            reason = "Vocabulary and contextual word choice (gracious, assured, panacea, raise) in ADA 2014 General English."
        elif qnum_str == "12":
            prop = make_primary("english", "english/grammar", None)
            reason = "Prepositional / conjunction phrase usage (except that) under English grammar."
        else:
            raise ValueError(f"Unexpected qnum in ADA: {qnum_str}")
    elif "1.CDPO" in pid:
        if qnum_str in ("1", "5"):
            prop = make_primary("english", "english/writing", "english/writing/essay")
            reason = "Essay writing and idea expansion under writing."
        elif qnum_str == "3":
            prop = make_primary("english", "english/writing", "english/writing/letter")
            reason = "Official letter writing to Director, Social Welfare Department under writing."
        else:
            raise ValueError(f"Unexpected qnum in CDPO: {qnum_str}")
    elif "2. Jr. Grade of MES" in pid:
        prop = make_primary("english", "english/writing", "english/writing/essay")
        reason = "Essay writing in Jr. Grade of MES 2015 General English."
    elif pid.endswith("/21. General English.pdf"):
        if qnum_str == "1":
            prop = make_primary("english", "english/writing", "english/writing/essay")
            reason = "Essay writing in ~1000 words under writing."
        elif qnum_str == "2":
            prop = make_primary("english", "english/writing", "english/writing/precis")
            reason = "Précis writing in ~one-third length under writing."
        elif qnum_str == "3":
            prop = make_primary("english", "english/comprehension", None)
            reason = "Reading comprehension under English."
        elif qnum_str == "6":
            prop = make_primary("english", "english/vocabulary", None)
            reason = "Word pairs / homophones into meaningful sentences under vocabulary."
        elif qnum_str == "9":
            prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
            reason = "Idioms and phrases into sentences under vocabulary."
        else:
            raise ValueError(f"Unexpected qnum in 21. General English: {qnum_str}")
    elif "6.General English.pdf" in pid:
        if qnum_str == "1":
            prop = make_primary("english", "english/writing", "english/writing/essay")
            reason = "Essay writing in 800-900 words under writing."
        else:
            prop = make_primary("english", "english/vocabulary", None)
            reason = f"Vocabulary word meaning ({qtext[:35]}) under vocabulary."
    else:
        raise ValueError(f"Unknown paper: {pid}")

    tax_str = prop["subtopic_id"] or prop["topic_id"] or prop["subject_id"]
    tax_counts[tax_str] += 1

    is_same = (
        cur_primary.get("subject_id") == prop["subject_id"] and
        cur_primary.get("topic_id") == prop["topic_id"] and
        cur_primary.get("subtopic_id") == prop["subtopic_id"]
    )
    action = "keep" if is_same else "retag"
    action_counts[action] += 1

    candidate = {
        "candidate_id": f"tcand_b140_{aid[:16]}",
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": pid,
        "source_fingerprint": it["source_fingerprint"],
        "action": action,
        "review_status": "pending",
        "current_primary": cur_primary,
        "proposed_primary": prop,
        "proposed_secondary": [],
        "reason": reason,
        "policy": "study-tagging-v1",
        "notes": f"Batch 140 source-reviewed: Direct General English ({pid.split('/')[-1]}) Q{qnum_str}."
    }
    pending_candidates.append(candidate)

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")

findings = [
    {
        "id": "finding_b140_conventional_written_preservation",
        "paper_id": "Old_Questions/Direct_2014-2018/1. General English.pdf",
        "type": "conventional_written_section",
        "severity": "info",
        "marks": 30,
        "details": "Preserved Question 1 Essay on Reading / Mizoram Economy / Politics / Women (20 marks) and Question 2 Précis on Peace and Tolerance (10 marks) in pending-written-intake.json."
    },
    {
        "id": "finding_b140_direct_general_english_refinement",
        "paper_id": "multiple",
        "type": "taxonomic_refinement",
        "severity": "info",
        "details": "Refined 19 legacy subject-level tags across 5 Direct General English papers to vocabulary (10), essay writing (5), letter writing (1), précis writing (1), idioms (1), comprehension (1), and grammar (1)."
    }
]

(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")

summary = {
    "batch": 140,
    "papers": [
        {
            "paper_id": p["id"],
            "paper_title": p.get("exam_name", p["id"].split("/")[-1]),
            "document_id": next(d["id"] for d in packet["documents"] if d["paper_id"] == p["id"]),
            "sha256": next(d["sha256"] for d in packet["documents"] if d["paper_id"] == p["id"]),
            "targets": sum(1 for it in packet["items"] if it["appearance"]["paper_id"] == p["id"])
        }
        for p in packet["papers"]
    ],
    "targets": 20,
    "completion": "100% paper completion achieved for 5 Direct General English examination papers (20/20 questions reviewed: 10 Vocabulary, 5 Essay Writing, 1 Letter Writing, 1 Précis Writing, 1 Idioms & Phrases, 1 Comprehension, 1 Grammar; 2 conventional items [30 marks] preserved in pending-written-intake.json)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Preserved 2 conventional items (30 marks: Essay 20 marks, Précis 10 marks) in pending-written-intake.json.",
        "Refined 19 broad subject-level tags to specific topics and subtopics."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 140 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
