"""Build candidates, findings, summary, and written intake for Batch 134."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

paper_id = "Old_Questions/Direct_2014-2018/1.UDC under SAD Paper-I.pdf"
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
        "details": "Write an essay in about 500 words on 'Moral values should be made as a compulsory subject in schools'."
    },
    {
        "question_number": "2",
        "paper_id": paper_id,
        "marks": 25,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/precis",
        "title": "Précis Writing",
        "details": "Write a précis on Lord Chesterfield's letter to his son regarding future expenses, generosity, economy, and avoiding vices."
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
        reason = "Parts of speech identification (still, once, for, above, etc.) in General English Paper-I Section B."
    elif 9 <= qnum <= 16:
        prop = make_primary("english", "english/grammar", None)
        reason = "Clause identification (noun clause, adverb clause, adjective clause, co-ordinate clause) under English grammar."
    elif 17 <= qnum <= 24:
        prop = make_primary("english", "english/grammar", None)
        reason = "Sentence structure analysis (simple, compound, complex sentences) under English grammar."
    elif 25 <= qnum <= 32:
        prop = make_primary("english", "english/grammar", None)
        reason = "Functional concepts and speech acts (possibility, polite request, determination, simultaneous action, regret, promise) under English grammar."
    elif 33 <= qnum <= 40:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
        reason = "Phrasal verbs (put down, assured of, gives off, took to their heels, worn out, etc.) under idioms and phrases."
    elif 41 <= qnum <= 48:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/one-word-substitution")
        reason = "One-word substitution (germicide, linguist, turncoat, revel, filicide, articulate, verbose) under vocabulary."
    elif 49 <= qnum <= 57:
        prop = make_primary("english", "english/grammar", "english/grammar/prepositions")
        reason = "Appropriate prepositions and prepositional collocations under English grammar."
    elif 58 <= qnum <= 66:
        prop = make_primary("english", "english/vocabulary", "english/vocabulary/idioms-and-phrases")
        reason = "Idioms and figurative expressions (snap fingers at, maiden speech, apple of discord, elbow room, etc.) under idioms and phrases."
    elif 67 <= qnum <= 75:
        prop = make_primary("english", "english/grammar", "english/grammar/tenses")
        reason = "Verb forms, tenses, subject-verb agreement, and conditionals under English grammar."
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
        "candidate_id": f"tcand_b134_{aid[:16]}",
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
        "notes": f"Batch 134 source-reviewed: UDC under SAD 2018 Paper-I Q{qnum_str}."
    }
    pending_candidates.append(candidate)

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")

findings = [
    {
        "id": "finding_b134_section_a_written",
        "paper_id": paper_id,
        "type": "conventional_written_section",
        "severity": "info",
        "marks": 50,
        "details": "Section A contains 50 marks of conventional written questions: Question 1 Essay on 'Moral values should be made as a compulsory subject in schools' (25 marks) and Question 2 Précis Writing on Lord Chesterfield's letter to his son (25 marks), preserved in pending-written-intake.json."
    },
    {
        "id": "finding_b134_clause_analysis_retag",
        "paper_id": paper_id,
        "type": "taxonomic_refinement",
        "severity": "info",
        "details": "Clauses (Q9–Q16), Sentence Structure (Q17–Q24), and Concepts/Speech Acts (Q25–Q32) were previously tagged broadly under parts-of-speech or sentence-correction; refined to english/grammar topic level."
    }
]

(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")

summary = {
    "batch": 134,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examinations for Recruitment to the Post of U.D.C. under Secretariat Administration Department, February 2018 — Paper-I",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 75
        }
    ],
    "targets": 75,
    "completion": "100% paper completion achieved for UDC under SAD 2018 Paper-I (75/75 MCQs reviewed: 24 Grammar / Clauses / Sentence Analysis / Speech Acts, 17 Idioms & Phrasal Verbs, 9 Prepositions, 9 Tenses & Verb Forms, 8 Parts of Speech, 8 One-Word Substitutions; Section A Essay [25 marks] and Précis [25 marks] preserved in pending-written-intake.json)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Section A (50 conventional marks: Essay 25 marks on Moral Values, Précis 25 marks on Lord Chesterfield) preserved in pending-written-intake.json.",
        "Refined 24 grammar MCQs from parts-of-speech to english/grammar topic."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 134 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
