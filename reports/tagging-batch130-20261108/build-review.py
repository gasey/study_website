"""Build review candidates and findings for Batch 130: AAP General English (15 MCQs) and MES General English (20 MCQs) (35 MCQs total)."""
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

def assign_tax(paper_id, qnum_str, q_text):
    if "AAP General English.pdf" in paper_id:
        if qnum_str.startswith("Q7") or qnum_str.startswith("7"):
            return 'english/vocabulary/synonyms', 'English vocabulary: synonyms (frantic, humdrum, alacrity, attenuate, chimera)'
        elif qnum_str.startswith("Q8") or qnum_str.startswith("8"):
            return 'english/vocabulary/antonyms', 'English vocabulary: antonyms (ameliorate, fecundity, plethora, continence, decrepit)'
        elif qnum_str.startswith("Q10") or qnum_str.startswith("10"):
            return 'english/comprehension', 'English comprehension: passage comprehension on fate, human will, and responsibility'
        else:
            raise ValueError(f"Unknown AAP qnum: {qnum_str}")
    elif "MES General Englsih.pdf" in paper_id:
        qnum = int(qnum_str.replace("Q", ""))
        if qnum in (1, 3):
            return 'english/grammar/prepositions', 'English grammar: prepositions and positional particles (beside, for)'
        elif qnum in (2, 4, 5, 6, 9, 10):
            return 'english/grammar/subject-verb-agreement', 'English grammar: subject-verb agreement (compound subjects, collective nouns, inverted clauses)'
        elif qnum in (7, 8, 11, 12, 14, 15, 16, 20):
            return 'english/vocabulary', 'English vocabulary: confusing words and homophones (sore/soar, proceeds/precedes, farther/further, eligible/ineligible, latest/last, loose/lose, latter/later)'
        elif qnum in (13, 17, 18, 19):
            return 'english/grammar', 'English grammar: degrees of comparison and determiners (longer, interesting, nearest, many/much)'
        else:
            raise ValueError(f"Unknown MES qnum: {qnum_str}")
    else:
        raise ValueError(f"Unknown paper: {paper_id}")

pending_candidates = []
findings = []

for item in packet["items"]:
    cid = item["canonical_id"]
    aid = item["appearance_id"]
    rec = item["snapshot"]["record"]
    paper_id = item["snapshot"]["paper"]["id"]
    qnum_str = str(rec["qnum"])
    q_text = rec["question"]
    fingerprint = item["source_fingerprint"]
    
    cur_cls = rec.get("classification") or {"subject_id": None, "topic_id": None, "subtopic_id": None}
    
    target_tax, rationale = assign_tax(paper_id, qnum_str, q_text)
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
        "batch_id": 130,
        "policy": "study-tagging-v1"
    }
    pending_candidates.append(cand)
    
    findings.append({
        "paper": paper_id.split("/")[-1],
        "qnum": qnum_str,
        "canonical_id": cid,
        "appearance_id": aid,
        "action": action,
        "current_taxonomy": cur_cls,
        "target_taxonomy": parsed,
        "rationale": rationale,
        "stem_excerpt": q_text[:80]
    })

findings.sort(key=lambda x: (x["paper"], x["qnum"]))
pending_candidates.sort(key=lambda x: (x["paper_id"], x["canonical_id"]))

unextracted_items = [
    # AAP General English conventional items
    {
        "question_number": "1",
        "paper_id": "Old_Questions/Direct_2019-2020/AAP General English.pdf",
        "marks": 20,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/essay",
        "title": "Essay Writing",
        "details": "Write an essay on: (1) Influence of technological progress, (2) Sociological impact of Covid-19, (3) Tradition and modernity."
    },
    {
        "question_number": "2",
        "paper_id": "Old_Questions/Direct_2019-2020/AAP General English.pdf",
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/precis",
        "title": "Précis Writing",
        "details": "Give the précis of the passage on earthquakes as the enemy beneath our feet in about one-third length."
    },
    {
        "question_number": "3",
        "paper_id": "Old_Questions/Direct_2019-2020/AAP General English.pdf",
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/letter",
        "title": "Letter Drafting",
        "details": "Write a letter to your client regarding clearance of pending payment."
    },
    {
        "question_number": "4",
        "paper_id": "Old_Questions/Direct_2019-2020/AAP General English.pdf",
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing",
        "title": "Proverb Expansion",
        "details": "Expand: (a) Necessity is the mother of invention, (b) Virtue has its own reward, (c) Knowledge is power."
    },
    {
        "question_number": "5",
        "paper_id": "Old_Questions/Direct_2019-2020/AAP General English.pdf",
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/grammar/prepositions",
        "title": "Prepositions Fill in the Blanks",
        "details": "Fill in the blanks with appropriate prepositions (10 items: sorry for, gropes for/after, annoyed with, improvement in, committed to, leaned against, ran across, choose between, enter into, control over)."
    },
    {
        "question_number": "6",
        "paper_id": "Old_Questions/Direct_2019-2020/AAP General English.pdf",
        "marks": 4,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/grammar/tenses",
        "title": "Verb Forms and Tenses",
        "details": "Fill in the blanks with correct verb forms (4 items: have written, was, wrote, started)."
    },
    {
        "question_number": "9",
        "paper_id": "Old_Questions/Direct_2019-2020/AAP General English.pdf",
        "marks": 16,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/vocabulary/idioms-and-phrases",
        "title": "Idioms and Phrases Sentence Making",
        "details": "Make sentences with any 8 idioms (spill the beans, cry over spilt milk, in the doldrums, icing on the cake, come hell or high water, apple of one's eye, ball is in your court, break the ice, house of cards)."
    },
    # MES General English conventional items
    {
        "question_number": "1",
        "paper_id": "Old_Questions/Direct_2019-2020/MES General Englsih.pdf",
        "marks": 20,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/essay",
        "title": "Essay Writing",
        "details": "Write an essay in about 300 words: (1) Environment Vs Growth, (2) Road connectivity and Development in Mizoram, (3) Mizoram in relation to Citizens Amendment Act."
    },
    {
        "question_number": "2",
        "paper_id": "Old_Questions/Direct_2019-2020/MES General Englsih.pdf",
        "marks": 20,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/comprehension",
        "title": "Reading Comprehension Descriptive",
        "details": "Descriptive reading comprehension questions on modern civilization, science, and human values (4 questions, 5 marks each)."
    },
    {
        "question_number": "3",
        "paper_id": "Old_Questions/Direct_2019-2020/MES General Englsih.pdf",
        "marks": 20,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/writing/precis",
        "title": "Précis Writing",
        "details": "Write a précis of passage by Nehru on roots, culture, and nationalism."
    },
    {
        "question_number": "6",
        "paper_id": "Old_Questions/Direct_2019-2020/MES General Englsih.pdf",
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/sentence-correction",
        "title": "Sentence Correction",
        "details": "Correct 10 sentences with common grammatical errors (almost read half, if I lose/lost, one of the boys was, strength lies, elected her president, like the stars, told me, watch and pray, discussed the matter, affects his health)."
    },
    {
        "question_number": "7",
        "paper_id": "Old_Questions/Direct_2019-2020/MES General Englsih.pdf",
        "marks": 10,
        "type": "conventional",
        "subject": "General English",
        "proposed_taxonomy": "english/vocabulary/idioms-and-phrases",
        "title": "Idioms Sentence Making",
        "details": "Make sentences with 5 idioms (make both ends meet, draw off, in a nutshell, go about, by fits and starts, turn up, give vent to)."
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
    "batch": 130,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2019-2020/AAP General English.pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Post of Assistant Public Prosecutor under Lokayukta, Vigilance Department, November 2020 — General English",
            "document_id": next(d["id"] for d in packet["documents"] if d["paper_id"] == "Old_Questions/Direct_2019-2020/AAP General English.pdf"),
            "sha256": next(d["sha256"] for d in packet["documents"] if d["paper_id"] == "Old_Questions/Direct_2019-2020/AAP General English.pdf"),
            "targets": 15
        },
        {
            "paper_id": "Old_Questions/Direct_2019-2020/MES General Englsih.pdf",
            "paper_title": "Technical Competitive Examinations for Junior Grade of Mizoram Engineering Service (M.E.S.) under PWD, March 2020 — General English",
            "document_id": next(d["id"] for d in packet["documents"] if d["paper_id"] == "Old_Questions/Direct_2019-2020/MES General Englsih.pdf"),
            "sha256": next(d["sha256"] for d in packet["documents"] if d["paper_id"] == "Old_Questions/Direct_2019-2020/MES General Englsih.pdf"),
            "targets": 20
        }
    ],
    "targets": 35,
    "completion": "100% paper completion achieved across both papers: AAP General English 2020 (15 MCQs: 5 Synonyms, 5 Antonyms, 5 Reading Comprehension; 7 conventional items [80 marks] preserved) and MES General English 2020 (20 MCQs: 8 Confusing Words / Homophones, 6 Subject-Verb Agreement, 4 Grammar / Determiners, 2 Prepositions; 5 conventional items [80 marks] preserved).",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "conventional_marks_preserved": sum(u["marks"] for u in unextracted_items),
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Reclassified legacy 'gk' tags on General English papers into proper english/vocabulary, english/comprehension, and english/grammar subtopics.",
        "Documented 12 conventional written sections (160 conventional marks total across both papers) in pending-written-intake.json."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 130 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
