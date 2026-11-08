"""Build review packet and findings for Batch 39: CEO General English 2025."""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

def parse_path(path_str):
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

# Define metadata for all 66 questions
# Map qnum (1-indexed) to metadata: (page, skill, path_str, action, rationale)
specs = {
    # Page 3: Q1-Q11
    1: (3, "Parts of Speech (Noun)", "english/grammar/parts-of-speech", "retag", "Classifies abstract noun 'happiness' following possessive determiner 'her'."),
    2: (3, "Parts of Speech (Modal Verb)", "english/grammar/parts-of-speech", "retag", "Classifies modal auxiliary verb 'must' expressing obligation."),
    3: (3, "Parts of Speech (Adverb)", "english/grammar/parts-of-speech", "retag", "Classifies degree adverb 'almost' modifying adjective 'ripe'."),
    4: (3, "Parts of Speech (Preposition)", "english/grammar/parts-of-speech", "retag", "Classifies preposition 'among' indicating distribution among multiple entities."),
    5: (3, "Parts of Speech (Conjunction)", "english/grammar/parts-of-speech", "retag", "Classifies coordinating explanatory conjunction 'for' connecting independent clauses."),
    6: (3, "Prepositions of Place", "english/grammar/prepositions", "retag", "Tests spatial preposition 'beside' denoting next to / at the side of."),
    7: (3, "Prepositions of Time", "english/grammar/prepositions", "retag", "Tests temporal preposition 'in' used with months ('in March')."),
    8: (3, "Prepositions of Time", "english/grammar/prepositions", "retag", "Tests temporal preposition 'in' / 'within' denoting within the span of a month."),
    9: (3, "Prepositions / Conjunctions of Time", "english/grammar/prepositions", "retag", "Tests temporal connective 'since' indicating point of past departure."),
    10: (3, "Coordinating Conjunctions", "english/grammar", "retag", "Tests adversative conjunction 'but' expressing contrast between effort and outcome."),
    11: (3, "Coordinating Conjunctions", "english/grammar", "retag", "Tests disjunctive conjunction 'or' expressing alternative consequence ('or you will miss the train')."),
    # Page 4: Q12-Q23
    12: (4, "Dependent Prepositions", "english/grammar/prepositions", "retag", "Tests fixed preposition 'to' following comparative verb 'prefer' ('prefer coffee to tea')."),
    13: (4, "Dependent Prepositions", "english/grammar/prepositions", "retag", "Tests adjective-preposition collocation 'excited about' anticipating future travel."),
    14: (4, "Dependent Prepositions", "english/grammar/prepositions", "retag", "Tests verb-preposition collocation 'insisted on' governing gerund complement."),
    15: (4, "Dependent Prepositions", "english/grammar/prepositions", "retag", "Tests verb-preposition collocation 'recovering from' denoting convalescence from trauma."),
    16: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past continuous / past tense aspect describing pillar instability during climbing."),
    17: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests present perfect continuous aspect ('has been working') initiated with 'since 2022'."),
    18: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests simple present tense ('rises') expressing universal scientific truth."),
    19: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past tense verb ('remembered') complementing past perfect relative clause."),
    20: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests interrogative past/present perfect verb ('Who took / has taken my laptop?')."),
    21: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests future continuous / simple future aspect ('will run / will be running') for scheduled race."),
    22: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests present tense stative verb ('wants') expressing future aspiration."),
    23: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests sequence of tenses in past time ('rushed home after he received...')."),
    # Page 5: Q24-Q33
    24: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past continuous tense ('was examining') interrupted by sudden past occurrence in hall."),
    25: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past tense / past perfect ('landed / had landed') for sequence of airline deboarding."),
    26: (5, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests adjective choice 'eminent' describing distinguished legal practitioner."),
    27: (5, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests academic verb choice 'cite' denoting attribution of bibliographic sources."),
    28: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests noun 'mercenary' denoting one motivated primarily by financial gain."),
    29: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests noun 'philanderer' describing one unfaithful in romantic relationships."),
    30: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests definition 'polygyny' / 'polygamy' for custom of multiple wives."),
    31: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests definition 'astronomer' for scientist studying celestial bodies."),
    32: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests definition 'anatomy' for scientific study of bodily structure."),
    33: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests definition 'pessimist' for one focused on negative outcomes."),
    # Page 6: Q34-Q43
    34: (6, "Idioms & Phrases", "english/vocabulary/idioms-and-phrases", "retag", "Tests figurative idiom 'to bury the hatchet' meaning to make peace / resolve feud."),
    35: (6, "Idioms & Phrases", "english/vocabulary/idioms-and-phrases", "retag", "Tests idiom 'a fair weather friend' denoting an untrustworthy, self-serving associate."),
    36: (6, "Idioms & Phrases", "english/vocabulary/idioms-and-phrases", "retag", "Tests idiom 'to throw dust in one's eyes' meaning to mislead or deceive."),
    37: (6, "Idioms & Phrases", "english/vocabulary/idioms-and-phrases", "keep", "Confirms exact active subtopic for idiom 'a wild goose chase' meaning futile pursuit."),
    38: (6, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'admire' ('despise / condemn')."),
    39: (6, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'contrary' ('agreeable / compliant')."),
    40: (6, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'repulsive' ('attractive / alluring')."),
    41: (6, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'demolish' ('construct / build')."),
    42: (6, "Tense Transformations", "english/grammar/tenses", "retag", "Tests syntactic transformation into Future Perfect Continuous ('will have been burning')."),
    43: (6, "Tense Transformations", "english/grammar/tenses", "retag", "Tests syntactic transformation into Past Continuous ('was spreading')."),
    # Page 7: Q44-Q51
    44: (7, "Tense Transformations", "english/grammar/tenses", "retag", "Tests syntactic transformation into Present Indefinite ('refuses')."),
    45: (7, "Tense Transformations", "english/grammar/tenses", "keep", "Confirms exact active subtopic for transformation into Past Perfect ('had reaped')."),
    46: (7, "Tense Transformations", "english/grammar/tenses", "retag", "Tests syntactic transformation into Future Indefinite ('Who will knock at the door?')."),
    47: (7, "Reported Speech", "english/grammar/reported-speech", "retag", "Tests direct-to-indirect narration transformation of present perfect continuous to past perfect continuous."),
    48: (7, "Reported Speech", "english/grammar/reported-speech", "retag", "Tests direct-to-indirect narration transformation of past continuous to past perfect continuous."),
    49: (7, "Reported Speech", "english/grammar/reported-speech", "retag", "Tests indirect-to-direct narration back-transformation of negative assertion."),
    50: (7, "Reported Speech", "english/grammar/reported-speech", "retag", "Tests direct-to-indirect narration of wh-interrogative question."),
    51: (7, "Reported Speech", "english/grammar/reported-speech", "retag", "Tests direct-to-indirect narration of past simple assertion with temporal/spatial deictic shift ('here' -> 'there')."),
    # Page 8: Q52-Q61
    52: (8, "Relative Pronouns", "english/grammar/parts-of-speech", "retag", "Tests objective relative pronoun 'whom' referring to person as object of marry."),
    53: (8, "Concessive Conjunctions", "english/grammar", "retag", "Tests subordinating concessive conjunction 'although' linking weather to clothing."),
    54: (8, "Causal Conjunctions", "english/grammar", "retag", "Tests subordinating causal conjunction 'since' expressing motive/condition."),
    55: (8, "Alternative Conjunctions", "english/grammar", "retag", "Tests interrogative/alternative subordinating conjunction 'whether' introducing alternatives."),
    56: (8, "Prepositions of Concession", "english/grammar/prepositions", "retag", "Tests concessive preposition 'despite' governing participle phrase complement."),
    57: (8, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'eloquence' ('articulateness / fluency')."),
    58: (8, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'feeble' ('weak / frail')."),
    59: (8, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'incongruous' ('incompatible / inappropriate')."),
    60: (8, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'nonchalant' ('indifferent / unconcerned')."),
    61: (8, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'despise' ('scorn / detest')."),
    # Page 9: Q62-Q66
    62: (9, "Sentence Transformations", "english/grammar", "retag", "Tests transformation into negative sentence without changing meaning ('Nobody is absent')."),
    63: (9, "Sentence Transformations", "english/grammar", "retag", "Tests transformation into assertive sentence ('Everybody accepts that she sings well')."),
    64: (9, "Sentence Transformations", "english/grammar", "retag", "Tests transformation of declarative into exclamatory sentence ('What a lovely day it was!')."),
    65: (9, "Sentence Transformations", "english/grammar", "retag", "Tests transformation of statement into rhetorical interrogative sentence ('What is the use of crying over spilt milk?')."),
    66: (9, "Sentence Transformations", "english/grammar", "retag", "Tests transformation of negative interrogative into negative statement.")
}

candidates = []
findings = []

breakdown = {}
action_counts = {"retag": 0, "keep": 0}

for idx, it in enumerate(packet["items"], 1):
    qnum = idx
    page, skill, path_str, action, rationale = specs[qnum]
    proposed_tax = parse_path(path_str)
    
    cur_class = it["snapshot"]["record"]["classification"]
    cur_sub = cur_class.get("subject_id")
    cur_top = cur_class.get("topic_id")
    cur_subtop = cur_class.get("subtopic_id")
    
    # format current path cleanly
    if cur_subtop:
        cur_path = cur_subtop
    elif cur_top:
        cur_path = cur_top
    elif cur_sub:
        cur_path = cur_sub
    else:
        cur_path = "untagged"
    
    prop_path = path_str
    
    breakdown[prop_path] = breakdown.get(prop_path, 0) + 1
    action_counts[action] = action_counts.get(action, 0) + 1
    
    cand = {
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "paper_id": it["appearance"]["paper_id"],
        "source_fingerprint": it["source_fingerprint"],
        "review_status": "pending",
        "action": action,
        "current_primary": cur_class,
        "proposed_primary": proposed_tax,
        "rationale": rationale,
        "batch_id": 39,
        "policy": "study-tagging-v1"
    }
    candidates.append(cand)
    
    finding = {
        "index": idx,
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "printed_question": f"Q{idx}",
        "physical_page": page,
        "tested_skill": skill,
        "current_path": cur_path,
        "proposed_path": prop_path,
        "action": action,
        "rationale": rationale
    }
    findings.append(finding)

assert len(candidates) == 66
assert len(findings) == 66

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Preserved written tasks
written_intake = [
    {
        "paper_id": "Old_Questions/Direct_2025-2027/CEO General English - 2025..pdf",
        "section": "PART- A (34 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 14,
        "task_type": "précis_writing",
        "prompt": "Write a précis of the following passage and provide an appropriate title.",
        "source_context": "Reading or the enjoyment of books has always been regarded among the charms of cultured life... (approx 300 words passage on reading as liberation from bodily prison).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional written descriptive task requiring manual student composition, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/CEO General English - 2025..pdf",
        "section": "PART- A (34 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 10,
        "task_type": "formal_application_letter",
        "prompt": "Write a formal application as XYZ for the post of Lecturer in Social Science addressed to the Principal, MYG Higher Secondary School, Bawngkawn, Aizawl, Mizoram in response to the advertisment in The Aizawl Post, Vol. XVII, Issue 21 of 12th August 2025.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional formal job application letter drafting task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/CEO General English - 2025..pdf",
        "section": "PART- A (34 Marks)",
        "question_number": "3",
        "physical_page": 2,
        "marks": 10,
        "task_type": "reading_comprehension",
        "prompt": "Read the following passage and answer the questions given at the end: Toward the end of her day in London Mrs. Drover went round to her shut-up house... Questions (i) to (v) carrying 2 marks each.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive reading comprehension passage with short-answer and vocabulary sub-questions, excluded from automated MCQ database ingestion."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")

summary = {
    "batch": 39,
    "paper_id": "Old_Questions/Direct_2025-2027/CEO General English - 2025..pdf",
    "paper_title": "Competitive Examination for Recruitment to the Post of Circle Education Officer under School Education Department (November, 2025) — General English",
    "document_id": "doc_db5ba5b3fe26ca319535f622",
    "sha256": "a3b617a9b67098ab26fcb4798a8d0d931136c363c524da23a789a27d602b6b92",
    "targets": 66,
    "completion": "100% of extracted MCQs reviewed",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted items in pending-written-intake.json.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
