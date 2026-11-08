"""Build candidates, findings, summary, and written intake for Batch 143."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

def make_primary(sid="english", tid=None, subid=None):
    return {
        "subject_id": sid,
        "topic_id": tid,
        "subtopic_id": subid
    }

unextracted_items = []
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
    pid_short = pid.split("/")[-1]
    qnum_str = str(it["appearance"]["qnum"])
    qtext = rec["question"]

    # Classify each question
    if "Genral Enlish" in pid_short:
        if qnum_str == "1": # a loaf of bread
            prop = make_primary("english", "english/grammar", "english/grammar/parts-of-speech")
            reason = "Countable vs uncountable noun / partitive (a loaf of bread) under parts of speech."
        elif qnum_str == "2": # Everyone was
            prop = make_primary("english", "english/grammar", "english/grammar/subject-verb-agreement")
            reason = "Indefinite pronoun subject-verb agreement (Everyone was) under subject-verb agreement."
        elif qnum_str == "3": # sensible
            prop = make_primary("english", "english/grammar", "english/grammar/parts-of-speech")
            reason = "Predicate adjective following linking verb (seems sensible) under parts of speech."
        elif qnum_str == "4": # for sale
            prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
            reason = "Prepositional idiom / collocation (for sale) under idioms and phrases."
        elif qnum_str == "5": # prefer ... to
            prop = make_primary("english", "english/grammar", "english/grammar/prepositions")
            reason = "Preposition following verb 'prefer' (prefer ... to) under prepositions."
        elif qnum_str == "6": # more useful than
            prop = make_primary("english", "english/grammar", None)
            reason = "Comparative degree of adjective (more useful than) under English grammar."
        elif qnum_str == "7": # keep up with
            prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
            reason = "Phrasal verb idiom (keep up with) under idioms and phrases."
        else:
            raise ValueError(f"Unexpected qnum in Genral Enlish: {qnum_str}")

    elif "General Englsih Paper-I (EO)" in pid_short:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
        reason = f"Idiom meaning ({qtext}) under vocabulary idioms and phrases."

    elif "768a298a6ef575d791958086c0626c7519bfecc094f850d63a05377746246336" in pid_short:
        if qnum_str == "A1":
            prop = make_primary("english", "english/writing", "english/writing/precis")
            reason = "Section A précis writing (passage on environmental crisis) under english/writing/precis."
            unextracted_items.append({
                "question_number": "A1",
                "paper_id": pid,
                "marks": 25,
                "type": "conventional",
                "subject": "General English",
                "proposed_taxonomy": "english/writing/precis",
                "title": "Précis Writing",
                "details": "Write the precis of the given passage and give a suitable title (25 marks)."
            })
        elif qnum_str == "A2":
            prop = make_primary("english", "english/writing", "english/writing/letter")
            reason = "Section A letter drafting (complaint letter regarding defective laptop) under english/writing/letter."
            unextracted_items.append({
                "question_number": "A2",
                "paper_id": pid,
                "marks": 25,
                "type": "conventional",
                "subject": "General English",
                "proposed_taxonomy": "english/writing/letter",
                "title": "Letter Writing",
                "details": "Formal complaint letter to M/S System Solutions regarding defective laptop (25 marks)."
            })
        else:
            raise ValueError(f"Unexpected qnum in 768: {qnum_str}")

    elif "LDC under MPSC Paper-I 2025" in pid_short:
        if qnum_str == "B1":
            prop = make_primary("english", "english/writing", "english/writing/essay")
            reason = "Section B conventional essay writing (500 words on given topics) under english/writing/essay."
            unextracted_items.append({
                "question_number": "B1",
                "paper_id": pid,
                "marks": 25,
                "type": "conventional",
                "subject": "General English",
                "proposed_taxonomy": "english/writing/essay",
                "title": "Essay Writing",
                "details": "Write an essay on one topic: Smart Cities, Social Media and Mental Health, Climate Change (25 marks)."
            })
        elif qnum_str == "B2":
            prop = make_primary("english", "english/writing", "english/writing/precis")
            reason = "Section B conventional précis writing with suitable title under english/writing/precis."
            unextracted_items.append({
                "question_number": "B2",
                "paper_id": pid,
                "marks": 15,
                "type": "conventional",
                "subject": "General English",
                "proposed_taxonomy": "english/writing/precis",
                "title": "Précis Writing",
                "details": "Write a précis of the passage with a suitable title (15 marks)."
            })
        elif qnum_str == "B3":
            prop = make_primary("english", "english/comprehension", None)
            reason = "Section B conventional reading comprehension passage and short-answer questions under english/comprehension."
            unextracted_items.append({
                "question_number": "B3",
                "paper_id": pid,
                "marks": 10,
                "type": "conventional",
                "subject": "General English",
                "proposed_taxonomy": "english/comprehension",
                "title": "Reading Comprehension",
                "details": "Read passage and answer 5 short-answer questions (10 marks)."
            })
        else:
            raise ValueError(f"Unexpected qnum in LDC: {qnum_str}")

    tax_counts[prop["subtopic_id"] or prop["topic_id"]] += 1

    is_same = (
        cur_primary.get("subject_id") == prop["subject_id"] and
        cur_primary.get("topic_id") == prop["topic_id"] and
        cur_primary.get("subtopic_id") == prop["subtopic_id"]
    )
    action = "keep" if is_same else "retag"
    action_counts[action] += 1

    candidate = {
        "candidate_id": f"tcand_b143_{aid[:16]}",
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
        "notes": f"Batch 143 source-reviewed: Direct General English ({pid_short}) Q{qnum_str}."
    }
    pending_candidates.append(candidate)

(out / "pending-written-intake.json").write_text(json.dumps(unextracted_items, ensure_ascii=False, indent=2) + "\n")
(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")

findings = [
    {
        "id": "finding_b143_conventional_intake_preservation",
        "paper_id": "multiple",
        "type": "conventional_written_section",
        "severity": "info",
        "marks": sum(u["marks"] for u in unextracted_items),
        "details": f"Preserved 5 major conventional written questions totaling {sum(u['marks'] for u in unextracted_items)} marks across Group B Gazetted General English (Precis 25m, Letter 25m) and LDC Paper-I 2025 (Essay 25m, Precis 15m, Comprehension 10m) in pending-written-intake.json."
    },
    {
        "id": "finding_b143_misspelled_paper_titles",
        "paper_id": "Old_Questions/Direct_2014-2018/Genral Enlish..pdf",
        "type": "filename_orthography",
        "severity": "info",
        "details": "Source files with typographical titles 'Genral Enlish..pdf' (SI Excise 2014) and 'General Englsih Paper-I (EO).pdf' (Employment Officer) successfully matched and source-reviewed."
    }
]

(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")

summary = {
    "batch": 143,
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
    "targets": 18,
    "completion": "100% paper completion achieved for 4 Direct General English examination papers (18/18 questions reviewed: 8 Idioms and Phrases, 2 Parts of Speech, 2 Précis Writing, 1 Essay Writing, 1 Letter Writing, 1 Reading Comprehension, 1 Subject-Verb Agreement, 1 Prepositions, 1 Comparative Degree; 5 conventional items [100 marks] preserved in pending-written-intake.json)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Preserved 5 conventional items (100 marks: Essay 25m, Précis 40m, Letter 25m, Comprehension 10m) in pending-written-intake.json.",
        "Noted misspelled filenames 'Genral Enlish..pdf' and 'General Englsih Paper-I (EO).pdf'."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 143 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
