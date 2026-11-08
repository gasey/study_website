"""Build candidates, findings, summary, and written intake for Batch 137."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

paper_id = "Old_Questions/Direct_2020-2021/UDC Direct under Taxation Deptt - Paper-I.pdf"
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
        "paper_id": paper_id,
        "marks": 25,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/precis",
        "title": "Précis Writing",
        "details": "Read passage and write précis in about one-third length with title, on ancient Indian science, Sanskrit grammar (Panini), medicine (Charaka, Dhanvantari), surgery (Sushruta), astronomy, and animal hospitals."
    },
    {
        "question_number": "2",
        "paper_id": paper_id,
        "marks": 25,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/essay",
        "title": "Essay Writing",
        "details": "Write an essay in about 500 words on one of the topics: Saving planet Earth, Revival of Chapchar Kut in Mizoram, The Role of the YMA in Mizoram, or Corruption and its effect on Society."
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
    qnum_str = it["appearance"]["qnum"]
    qnum = int("".join(c for c in qnum_str if c.isdigit()))

    # Determine proposed primary based on section & question number
    if 1 <= qnum <= 10:
        prop = make_primary("english", "english/grammar", "english/grammar/parts-of-speech")
        reason = "Parts of speech identification (kindly, love, some, danger, over, half, oh god, hey, yourself, whom) in General English Paper-I Section B."
    elif 11 <= qnum <= 20:
        prop = make_primary("english", "english/grammar", "english/grammar/tenses")
        reason = "Tense form identification (Future Indefinite, Present Continuous, Past Perfect Continuous, etc.) under English grammar."
    elif 21 <= qnum <= 30:
        prop = make_primary("english", "english/grammar", None)
        reason = "Sentence classification (Affirmative, Negative, Interrogative, Imperative, Exclamatory) under English grammar."
    elif 31 <= qnum <= 40:
        prop = make_primary("english", "english/vocabulary", None)
        reason = "Homophones and vocabulary word choice (beech/beach, knot/not, whether/weather, etc.) under vocabulary."
    elif 41 <= qnum <= 50:
        prop = make_primary("english", "english/grammar", "english/grammar/subject-verb-agreement")
        reason = "Subject-verb and pronoun agreement under English grammar."
    elif 51 <= qnum <= 60:
        prop = make_primary("english", "english/grammar", "english/grammar/prepositions")
        reason = "Prepositions and prepositional phrases under English grammar."
    elif 61 <= qnum <= 68:
        prop = make_primary("english", "english/grammar", "english/grammar/parts-of-speech")
        reason = "Collective nouns (groups or collections: library of books, mob of rioters, school of fish, etc.) under parts of speech."
    elif 69 <= qnum <= 75:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
        reason = "Similes and idiomatic comparisons (as cunning as a fox, as quick as lightning, etc.) under idioms and phrases."
    else:
        raise ValueError(f"Unexpected qnum: {qnum}")

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
        "candidate_id": f"tcand_b137_{aid[:16]}",
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": paper_id,
        "source_fingerprint": it["source_fingerprint"],
        "action": action,
        "review_status": "pending",
        "current_primary": cur_primary,
        "proposed_primary": prop,
        "proposed_secondary": [],
        "reason": reason,
        "policy": "study-tagging-v1",
        "notes": f"Batch 137 source-reviewed: UDC under Taxation 2021 Paper-I Q{qnum_str}."
    }
    pending_candidates.append(candidate)

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")

findings = [
    {
        "id": "finding_b137_section_a_written",
        "paper_id": paper_id,
        "type": "conventional_written_section",
        "severity": "info",
        "marks": 50,
        "details": "Section A contains 50 marks of conventional written questions: Question 1 Précis Writing on ancient Indian science and Panini's Sanskrit grammar (25 marks) and Question 2 Essay Writing on topics including Saving Planet Earth, Chapchar Kut, YMA, and Corruption (25 marks), preserved in pending-written-intake.json."
    },
    {
        "id": "finding_b137_collective_nouns_and_similes",
        "paper_id": paper_id,
        "type": "taxonomic_refinement",
        "severity": "info",
        "details": "Refined 15 questions from broad english/vocabulary: Q61–Q68 collective nouns to english/grammar/parts-of-speech, and Q69–Q75 similes/comparisons to english/vocabulary/idioms-and-phrases."
    }
]

(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")

summary = {
    "batch": 137,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Upper Division Clerk (U.D.C.) under Taxation Department, March 2021 — Paper-I",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 75
        }
    ],
    "targets": 75,
    "completion": "100% paper completion achieved for UDC under Taxation 2021 Paper-I (75/75 MCQs reviewed: 18 Parts of Speech & Collective Nouns, 10 Tenses, 10 Subject-Verb Agreement, 10 Prepositions, 10 Sentence Types, 10 Homophones/Vocabulary, 7 Similes/Idioms; Section A Précis [25 marks] and Essay [25 marks] preserved in pending-written-intake.json)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Section A (50 conventional marks: Précis 25 marks on Ancient Indian Science, Essay 25 marks on 4 options) preserved in pending-written-intake.json.",
        "Refined 15 collective noun and simile questions from broad vocabulary."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 137 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
