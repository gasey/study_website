"""Build candidates, findings, summary, and written intake for Batch 135."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

paper_id = "Old_Questions/Direct_2014-2018/1.UDC under Tourism Deptt.-I.pdf"
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
        "proposed_taxonomy": "english/writing/essay",
        "title": "Essay Writing",
        "details": "Write an essay in about 500 words on 'The impact of social media on the Mizo youth'."
    },
    {
        "question_number": "2",
        "paper_id": paper_id,
        "marks": 25,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/precis",
        "title": "Précis Writing",
        "details": "Write a précis on the passage discussing tourism as the world's largest industry, its revenue potential, economic benefits, and environmental/socio-cultural impacts."
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
    if 1 <= qnum <= 8:
        prop = make_primary("english", "english/grammar", "english/grammar/parts-of-speech")
        reason = "Parts of speech identification (right, nears, round, like, fast, etc.) in General English Paper-I Section B."
    elif 9 <= qnum <= 16:
        prop = make_primary("english", "english/grammar", None)
        reason = "Clause identification (noun clause, adverb clause, adjective clause, co-ordinate clause) under English grammar."
    elif 17 <= qnum <= 24:
        prop = make_primary("english", "english/grammar", None)
        reason = "Sentence structure analysis (simple, compound, complex sentences) under English grammar."
    elif 25 <= qnum <= 32:
        prop = make_primary("english", "english/grammar", None)
        reason = "Functional concepts and speech acts (duty, deduction, ability, cause, degree, assertive, assumption, command) under English grammar."
    elif 33 <= qnum <= 35:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
        reason = "Phrasal verbs (call up, keep back, look up) under idioms and phrases."
    elif qnum in (36, 37):
        prop = make_primary("english", "english/grammar", None)
        reason = "Grammar: verb/infinitive usage (not to lose) and connective/adverbial clause (wherever) under English grammar."
    elif 38 <= qnum <= 40:
        prop = make_primary("english", "english/grammar", "english/grammar/tenses")
        reason = "Verb forms, modals, passive voice, and continuous tenses (had to go, is spoken, has been raining) under English grammar."
    elif 41 <= qnum <= 48:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/one-word-substitution")
        reason = "One-word substitution (closest alternative in meaning) under vocabulary."
    elif 49 <= qnum <= 57:
        prop = make_primary("english", "english/grammar", "english/grammar/prepositions")
        reason = "Appropriate prepositions and prepositional collocations under English grammar."
    elif 58 <= qnum <= 66:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
        reason = "Idioms and figurative expressions under idioms and phrases."
    elif 67 <= qnum <= 75:
        prop = make_primary("english", "english/grammar", "english/grammar/tenses")
        reason = "Verb forms, tenses, subject-verb agreement, participles, and conditionals under English grammar."
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
        "candidate_id": f"tcand_b135_{aid[:16]}",
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
        "notes": f"Batch 135 source-reviewed: UDC under Tourism 2018 Paper-I Q{qnum_str}."
    }
    pending_candidates.append(candidate)

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")

findings = [
    {
        "id": "finding_b135_section_a_written",
        "paper_id": paper_id,
        "type": "conventional_written_section",
        "severity": "info",
        "marks": 50,
        "details": "Section A contains 50 marks of conventional written questions: Question 1 Essay on 'The impact of social media on the Mizo youth' (25 marks) and Question 2 Précis Writing on the tourism industry and environmental impact (25 marks), preserved in pending-written-intake.json."
    },
    {
        "id": "finding_b135_tense_and_phrasal_refinement",
        "paper_id": paper_id,
        "type": "taxonomic_refinement",
        "severity": "info",
        "details": "Refined 12 questions (Q33–Q35 phrasal verbs to idioms-and-phrases; Q38–Q40 and Q67–Q75 verb forms/tenses to english/grammar/tenses) from generic english/grammar."
    }
]

(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")

summary = {
    "batch": 135,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examinations for Recruitment to the Post of U.D.C. under Tourism Department, June 2018 — Paper-I",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 75
        }
    ],
    "targets": 75,
    "completion": "100% paper completion achieved for UDC under Tourism 2018 Paper-I (75/75 MCQs reviewed: 26 Grammar / Clauses / Sentence Analysis / Concepts, 12 Tenses & Verb Forms, 12 Idioms & Phrasal Verbs, 9 Prepositions, 8 Parts of Speech, 8 One-Word Substitutions; Section A Essay [25 marks] and Précis [25 marks] preserved in pending-written-intake.json)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Section A (50 conventional marks: Essay 25 marks on Social Media impact on Mizo youth, Précis 25 marks on Tourism industry) preserved in pending-written-intake.json.",
        "Refined 15 MCQs to specific tenses and phrasal verbs subtopics."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 135 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
