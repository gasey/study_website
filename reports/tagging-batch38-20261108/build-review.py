"""Generate review candidates and findings for Batch 38.
Paper: Assistant Director (Food & Drugs) / CDPO General English (November, 2025) (66 MCQs)
Target: 66 MCQs.
All 66 currently untagged (subject=null, topic=null).
Single-booklet deduplication: cleanly bypasses duplicate ingestion 'CDPO General English-2025..pdf' (doc_93dc9451f2beee9b16a34ec8).
"""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

PROPOSALS = {
    # Q1-Q10: Parts of Speech
    "05cf525bca4cfda51faf": ("Q1", 3, "Parts of Speech (Introductory Adverb/Pronoun: 'There')", "english/grammar/parts-of-speech", "Identifies 'There' as an anticipatory/dummy subject pronoun or adverb of place."),
    "5b37cd37f3de5f278849": ("Q2", 3, "Parts of Speech (Personal Pronoun: 'She')", "english/grammar/parts-of-speech", "Identifies 'She' as a third-person singular feminine personal pronoun."),
    "cb149e67a097aa04f6d2": ("Q3", 3, "Parts of Speech (Interjection: 'Well')", "english/grammar/parts-of-speech", "Identifies 'Well' as an interjection expressing pause or hesitation."),
    "6d13af4202e9f5c1b6ab": ("Q4", 3, "Parts of Speech (Exclamatory Determiner: 'What')", "english/grammar/parts-of-speech", "Identifies 'What' as an exclamatory modifier in 'What a beautiful dress!'."),
    "a7200e005d8a6f9300aa": ("Q5", 3, "Parts of Speech (Action Verb: 'proceeded')", "english/grammar/parts-of-speech", "Identifies 'proceeded' as a past tense intransitive verb."),
    "c43ad013cc90f17be43b": ("Q6", 3, "Parts of Speech (Adverb of negation: 'not')", "english/grammar/parts-of-speech", "Identifies 'not' as a negative adverb modifying auxiliary verb 'do'."),
    "58a2e6321ba7230a556d": ("Q7", 3, "Parts of Speech (Reflexive Pronoun: 'himself')", "english/grammar/parts-of-speech", "Identifies 'himself' as an emphatic or reflexive pronoun."),
    "853c1600156da8e4da91": ("Q8", 3, "Parts of Speech (Indefinite Pronoun: 'few')", "english/grammar/parts-of-speech", "Identifies 'few' as an indefinite pronoun or determiner."),
    "dd1646bfe1c80ebc921e": ("Q9", 4, "Parts of Speech (Subordinating Conjunction: 'until')", "english/grammar/parts-of-speech", "Identifies 'until' as a subordinating conjunction introducing temporal clause."),
    "572861fc86febeceeb59": ("Q10", 4, "Parts of Speech (Transitive Verb: 'wish')", "english/grammar/parts-of-speech", "Identifies 'wish' as a present tense transitive verb expressing desire."),

    # Q11-Q20: Prepositions
    "7b27b48d8f45cd240fc7": ("Q11", 4, "Prepositions ('absorbed in')", "english/grammar/prepositions", "Tests fixed preposition: 'absorbed in his work'."),
    "d8d8ec371a8f6d9ee90a": ("Q12", 4, "Prepositions ('complied with')", "english/grammar/prepositions", "Tests fixed preposition governing formal verb: 'complied with the request'."),
    "f2c8415929e522f668a9": ("Q13", 4, "Prepositions ('abstain from')", "english/grammar/prepositions", "Tests fixed preposition: 'abstain from smoking'."),
    "526dd1a570f636f8bce2": ("Q14", 4, "Prepositions ('presided over')", "english/grammar/prepositions", "Tests fixed preposition: 'presided over the meeting'."),
    "c057d6c67dc1e8cc99a9": ("Q15", 4, "Prepositions ('concur with')", "english/grammar/prepositions", "Tests fixed preposition with person: 'concur with you'."),
    "1775bcb3ac1a92fc811c": ("Q16", 4, "Prepositions ('eligible for')", "english/grammar/prepositions", "Tests fixed preposition: 'eligible for the post'."),
    "cd1c99ab74f234c9a95a": ("Q17", 4, "Prepositions ('adverse to')", "english/grammar/prepositions", "Tests fixed preposition: 'adverse to my interests'."),
    "2e3d53089bbf077eb45d": ("Q18", 4, "Prepositions ('blind to')", "english/grammar/prepositions", "Tests figurative preposition: 'blind to one's faults'."),
    "aefe18436bbcbb6a5a9e": ("Q19", 4, "Prepositions ('conducive to')", "english/grammar/prepositions", "Tests fixed preposition: 'conducive to health'."),
    "eda2b8bb80f85d8417ad": ("Q20", 5, "Prepositions ('reconciled to')", "english/grammar/prepositions", "Tests fixed preposition: 'reconciled to his fate'."),

    # Q21-Q26: Clauses & Phrases
    "3cac2098f88b41fe7ae4": ("Q21", 5, "Clauses (Noun Clause: 'that he could win')", "english/grammar", "Identifies clause serving as object of infinitive 'to believe' as a noun clause."),
    "1339c8a3ab85c049e051": ("Q22", 5, "Clauses (Coordinate Clause: 'To err is human, but...')", "english/grammar", "Identifies clause linked by coordinating conjunction 'but' as coordinate clause."),
    "1d272af49bb75c59f74f": ("Q23", 5, "Clauses (Adjective Clause: 'that you gave me')", "english/grammar", "Identifies relative clause modifying noun 'book' as an adjective clause."),
    "342084f722d31e4e9843": ("Q24", 5, "Phrases (Participial Phrase: 'wearing a red shirt')", "english/grammar", "Identifies non-finite participle phrase qualifying noun 'man'."),
    "63c4c3741a4f77b76fb6": ("Q25", 5, "Clauses (Noun Clause: 'what happened')", "english/grammar", "Identifies wh-clause functioning as direct object of imperative verb 'tell' as noun clause."),
    "2778bd271d922917abf6": ("Q26", 5, "Phrases (Prepositional Phrase of purpose: 'for her health')", "english/grammar", "Identifies prepositional phrase answering adverbial question of purpose."),

    # Q27-Q31: Sentence Transformations
    "0fa055eac664accddc4d": ("Q27", 5, "Sentence Transformations (Negative to Affirmative)", "english/grammar", "Transforms 'I was not at all sure' to affirmative 'I was quite doubtful'."),
    "09cba6182a3554314486": ("Q28", 5, "Sentence Transformations (Optative to Assertive)", "english/grammar", "Transforms wish exclamation 'O that I may see her again!' to assertive statement."),
    "dc16342c2d10455a9a80": ("Q29", 6, "Sentence Transformations (Rhetorical Interrogative to Assertive)", "english/grammar", "Transforms rhetorical question 'How can I bear it?' to assertive 'I cannot bear it'."),
    "3d406e9675c5d9d52bab": ("Q30", 6, "Sentence Transformations (Affirmative to Negative)", "english/grammar", "Transforms 'It is possible that I may have been mistaken' to negative without change of sense."),
    "d3d697fa413d05b3514e": ("Q31", 6, "Sentence Transformations (Assertive to Exclamatory)", "english/grammar", "Transforms assertive 'It is sad that children are the victims' to exclamatory structure."),

    # Q32-Q36: Reported Speech
    "b57173b1846cb8f6f8c2": ("Q32", 6, "Reported Speech (Direct to Indirect: past continuous -> past perfect continuous)", "english/grammar/reported-speech", "Transforms past continuous 'was hiding' to past perfect continuous 'had been hiding'."),
    "460f872c1c974f2624db": ("Q33", 6, "Reported Speech (Indirect to Direct: past perfect -> simple past)", "english/grammar/reported-speech", "Reverses indirect reported statement to original direct quotation with quotation marks."),
    "3c7588ca4c51dea4ef5a": ("Q34", 6, "Reported Speech (Direct to Indirect Imperative / Request)", "english/grammar/reported-speech", "Transforms direct request 'Give me your book, please' to 'requested Peter to give her his book'."),
    "3fe90b19f549bbc33f0b": ("Q35", 6, "Reported Speech (Indirect to Direct Universal Truth)", "english/grammar/reported-speech", "Reverses indirect report of universal scientific fact ('earth revolves around the sun') to direct."),
    "a0f6b3baf5e70de624d9": ("Q36", 6, "Reported Speech (Direct to Indirect with temporal shift)", "english/grammar/reported-speech", "Transforms 'this morning' to 'that morning' and shifts simple past verb tense."),

    # Q37-Q43: Contextual Vocabulary & One-Word Substitution
    "7c827aa5a7cc7afada01": ("Q37", 6, "One-Word Substitution ('Spendthrift')", "english/vocabulary/one-word-substitution", "Identifies 'spendthrift' as one who spends money wastefully."),
    "475828dea85baa8dfb85": ("Q38", 6, "Contextual Vocabulary ('absconding')", "english/vocabulary", "Sentence completion with appropriate legal term 'absconding' (fleeing to escape arrest)."),
    "8c4ca365946fdfb5de77": ("Q39", 6, "One-Word Substitution ('Democracy')", "english/vocabulary/one-word-substitution", "Identifies 'democracy' as government by the people."),
    "0e30e5319399df275719": ("Q40", 6, "Contextual Vocabulary ('exonerated')", "english/vocabulary", "Sentence completion with legal acquittal term 'exonerated'."),
    "2b918525d8af5a6c14aa": ("Q41", 6, "One-Word Substitution ('Monarchy')", "english/vocabulary/one-word-substitution", "Identifies 'monarchy' as state ruled by a king or queen."),
    "b3c92d64fae4b0a069d8": ("Q42", 6, "One-Word Substitution ('Bigot')", "english/vocabulary/one-word-substitution", "Identifies 'bigot' as one obstinately devoted to own prejudices and intolerant of other religions."),
    "d697c0dff51fcbd284c0": ("Q43", 6, "Contextual Vocabulary ('compensate')", "english/vocabulary", "Sentence completion with verb 'compensate' (make suitable payment for loss)."),

    # Q44-Q46: Sentence Correction / Error Spotting
    "09734162aedc528da1be": ("Q44", 7, "Sentence Correction (Reflexive verb: 'enjoyed myself')", "english/sentence-correction", "Spots error in 'I enjoyed / during my vacation': transitive verb 'enjoy' requires reflexive object 'myself'."),
    "30e659b365aa835dd90b": ("Q45", 7, "Sentence Correction (Superfluous 'as' after appoint)", "english/sentence-correction", "Spots error in 'They appointed / him as secretary': 'as' is superfluous after appoint/elect/make."),
    "69512d3bfd1f5eeb3d75": ("Q46", 7, "Sentence Correction (Infinitive complement after plan)", "english/sentence-correction", "Spots error in preposition/gerund structure following planning."),

    # Q47-Q56: Verb Tenses
    "6a79ad100f366f1a2411": ("Q47", 7, "Tenses (Past Perfect: 'had arrived')", "english/grammar/tenses", "Tests past perfect for earlier of two past actions."),
    "e63ed9d8a77c7cdf5ed6": ("Q48", 7, "Tenses (Present Perfect: 'has rained')", "english/grammar/tenses", "Tests present perfect indicating recent past action with current relevance."),
    "c67fab0b274be1d4edbe": ("Q49", 7, "Tenses (Simple Past habitual: 'worked')", "english/grammar/tenses", "Tests simple past indicating past routine."),
    "2797b3fb5c9ea55b9bfb": ("Q50", 7, "Tenses (Future Perfect: 'will have finished')", "english/grammar/tenses", "Tests future perfect for action completed by future time marker 'by tomorrow'."),
    "84721f222ce4b086a1c2": ("Q51", 7, "Tenses (Conditional Clause: 'If you work hard...')", "english/grammar/tenses", "Tests first conditional verb harmony: present in if-clause, future in main clause."),
    "ba27408f9371a0a66341": ("Q52", 7, "Tenses (Past Continuous: 'was reading')", "english/grammar/tenses", "Tests past continuous for action ongoing when interrupted by simple past event."),
    "8a82329ca2437abbf324": ("Q53", 7, "Tenses (Present Perfect Continuous: 'has been sitting')", "english/grammar/tenses", "Tests present perfect continuous with duration marker 'for over an hour'."),
    "b2a3819a5012f27b5fe0": ("Q54", 7, "Tenses (Simple Present habitual: 'goes')", "english/grammar/tenses", "Tests third-person singular simple present verb form 'goes' with 'every evening'."),
    "7fd1bc6e2441737e5470": ("Q55", 8, "Tenses (Subjunctive Mood: 'I wish I knew')", "english/grammar/tenses", "Tests past subjunctive expressing present unrealized wish."),
    "56b8545263fd2b1969c9": ("Q56", 8, "Tenses (Present Perfect with 'yet')", "english/grammar/tenses", "Tests present perfect in negative clause governed by adverb 'yet'."),

    # Q57-Q61: Connectors / Conjunctions
    "25d0722457b410fd9bf7": ("Q57", 8, "Conjunctions ('because')", "english/grammar/parts-of-speech", "Tests causal subordinating conjunction 'because' connecting premise to result."),
    "bc775cd6465a2bf872bd": ("Q58", 8, "Conjunctions ('although')", "english/grammar/parts-of-speech", "Tests concessive conjunction 'although' linking contrasting clauses."),
    "77bf856c5449be9660d8": ("Q59", 8, "Conjunctions ('whether... or')", "english/grammar/parts-of-speech", "Tests correlative conjunction pair 'whether... or' expressing alternative conditions."),
    "b5474c840a0abbfc489b": ("Q60", 8, "Conjunctions ('provided that')", "english/grammar/parts-of-speech", "Tests conditional conjunction phrase 'provided that'."),
    "b21534ff733a7872ec62": ("Q61", 8, "Conjunctions ('unless')", "english/grammar/parts-of-speech", "Tests negative conditional subordinating conjunction 'unless'."),

    # Q62-Q66: Idioms and Phrases
    "0c423b87be0705005ac9": ("Q62", 8, "Idioms and Phrases ('A lone wolf')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'A lone wolf' (a person who prefers to be alone or act independently)."),
    "eccd97852708f9407095": ("Q63", 8, "Idioms and Phrases ('A rule of thumb')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'A rule of thumb' (a practical rule based on experience rather than theory)."),
    "1a7d1e65fdd3a1a74679": ("Q64", 8, "Idioms and Phrases ('To be cloaked in mystery')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'cloaked in mystery' (completely hidden or kept secret)."),
    "bb1fdd4ac3cf325f8a6f": ("Q65", 8, "Idioms and Phrases ('Up to one's elbows')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'Up to one's elbows' (deeply involved or very busy with something)."),
    "46e73d6c1fc867cf0b22": ("Q66", 9, "Idioms and Phrases ('To hold one's tongue')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'To hold one's tongue' (to remain silent and not speak).")
}

assert len(PROPOSALS) == len(packet["items"]) == 66

def parse_path(path_str):
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

candidates = []
findings = []
breakdown = {}

for item in packet["items"]:
    aid = item["appearance_id"]
    cid = item["canonical_id"]
    prop = PROPOSALS[aid]
    
    q_str, page, skill, path_str, rat = prop
    proposed_tax = parse_path(path_str)
    
    breakdown[path_str] = breakdown.get(path_str, 0) + 1
    
    c_rec = {
        "canonical_id": cid,
        "appearance_id": aid,
        "source_fingerprint": item["source_fingerprint"],
        "review_status": "pending",
        "action": "retag",
        "current_primary": item["snapshot"]["record"]["classification"],
        "proposed_primary": proposed_tax,
        "rationale": rat,
        "batch_id": 38,
        "policy": "study-tagging-v1"
    }
    candidates.append(c_rec)
    
    findings.append({
        "canonical_id": cid,
        "appearance_id": aid,
        "printed_question": q_str,
        "physical_page": page,
        "tested_skill": skill,
        "action": "retag",
        "current_path": (item["snapshot"]["record"]["classification"]["subject_id"] or "null") if item["snapshot"]["record"]["classification"] else "null",
        "proposed_path": path_str,
        "rationale": rat
    })

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Preserved unextracted conventional Part-A items
unextracted_items = [
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Assistant Director General English-2025..pdf",
        "document_id": "doc_000e6be43acfd05656947ae1",
        "physical_page": 1,
        "item_type": "conventional_written_essay",
        "prompt": "Part-A Q1: Write an essay in not more than 400 words on any one of the following topics (14 marks): (1) Artificial Intelligence in everyday life: boon or bane? (2) Climate change: Environmental and infrastructural challenges in North-East India. (3) The role of women in the socio-economic development of Mizoram.",
        "marks": 14,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/essay"},
        "reason_unextracted": "Conventional written essay task answering on conventional answer sheet."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Assistant Director General English-2025..pdf",
        "document_id": "doc_000e6be43acfd05656947ae1",
        "physical_page": 2,
        "item_type": "conventional_reading_comprehension",
        "prompt": "Part-A Q2: Read the following passage carefully and answer the questions that follow (10 marks total across questions i–v: Science inventions and pace of human life, questions i to iv short answers, and question v idiom 'calls the shots').",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None},
        "reason_unextracted": "Conventional reading comprehension questions answering on conventional answer sheet."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Assistant Director General English-2025..pdf",
        "document_id": "doc_000e6be43acfd05656947ae1",
        "physical_page": 3,
        "item_type": "conventional_written_letter",
        "prompt": "Part-A Q3: Imagine you're the Child Development Project Officer (CDPO) of a Rural Development Block. Write an official letter to the Director of Women & Child Development Department highlighting malnutrition challenges among children under Poshan Abhiyaan and proposing concrete interventions. (10 marks)",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/letter"},
        "reason_unextracted": "Conventional official letter writing prompt answering on conventional answer sheet."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(unextracted_items, indent=2) + "\n")

summary = {
    "batch": 38,
    "paper_id": "Old_Questions/Direct_2025-2027/Assistant Director General English-2025..pdf",
    "paper_title": "Competitive Examination for Child Development Project Officer (CDPO) and Assistant Director (Food & Drugs) (November, 2025) — General English",
    "document_id": "doc_000e6be43acfd05656947ae1",
    "sha256": "594a8a89f8c1b6e7acb22cd8161f59c1e45b2353f7740bb9345261a882ab4438",
    "single_booklet_enforced": True,
    "bypassed_duplicate": {
        "paper_id": "Old_Questions/Direct_2025-2027/CDPO General English-2025..pdf",
        "document_id": "doc_93dc9451f2beee9b16a34ec8",
        "sha256": "594a8a89f8c1b6e7acb22cd8161f59c1e45b2353f7740bb9345261a882ab4438",
        "reason": "Exact identical sha256 duplicate ingestion of the same examination booklet under different filename."
    },
    "targets": 66,
    "completion": "100% of extracted MCQs reviewed",
    "actions": {
        "retag": 66,
        "keep": 0
    },
    "unextracted_items_preserved": len(unextracted_items),
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(unextracted_items)} unextracted items in pending-written-intake.json.")
print(f"Saved summary.json: {json.dumps(summary, indent=2)}")
