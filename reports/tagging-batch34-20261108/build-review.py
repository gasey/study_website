"""Generate review candidates and findings for Batch 34.
Paper: Stenographer Grade-II (Contract) under MPSC (May-2025) — Paper-I General English
Target: 40 MCQs (Part-B Q1–Q40).
All 40 currently untagged (subject=null, topic=null).
"""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

PROPOSALS = {
    # Q1-Q5: Parts of Speech
    "f300f66ac8a4ac637e3d": {
        "printed_question": "Q1",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Adverb: 'He ran fast to catch the bus')",
        "action": "retag",
        "rationale": "Identifies 'fast' as an adverb modifying the action verb 'ran'. Untagged in DB; assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "7ebe98f0a20535e25085": {
        "printed_question": "Q2",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Adjective: 'They had a hard time solving the puzzle')",
        "action": "retag",
        "rationale": "Identifies 'hard' as a qualifying adjective modifying noun 'time'. Untagged in DB; assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "2fa2a24754565c04b6b9": {
        "printed_question": "Q3",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Noun: 'She went for a run in the morning')",
        "action": "retag",
        "rationale": "Identifies 'run' as a noun preceded by indefinite article 'a' and serving as object of preposition 'for'. Untagged in DB; assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "8675e59e8e6788c6000d": {
        "printed_question": "Q4",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Reflexive Pronoun: 'Please calm yourself before the meeting')",
        "action": "retag",
        "rationale": "Identifies 'yourself' as a reflexive pronoun serving as the object of transitive verb 'calm'. Untagged in DB; assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "c86a0b6689da558fda6c": {
        "printed_question": "Q5",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Adjective used substantively as Noun: 'Only the brave deserve the fair')",
        "action": "retag",
        "rationale": "Identifies 'brave' as an adjective used substantively with definite article 'the' to represent a class of people. Assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },

    # Q6-Q15: Prepositions
    "30d41208d9cf72e5106d": {
        "printed_question": "Q6",
        "physical_page": 3,
        "tested_skill": "Prepositions ('on the recommendation of')",
        "action": "retag",
        "rationale": "Tests prepositional phrase usage: 'on the recommendation of'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "2b8cb38042c5e7dc007c": {
        "printed_question": "Q7",
        "physical_page": 3,
        "tested_skill": "Prepositions ('well versed in')",
        "action": "retag",
        "rationale": "Tests fixed preposition following adjective: 'well versed in'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "c621141345840c14621a": {
        "printed_question": "Q8",
        "physical_page": 3,
        "tested_skill": "Prepositions ('abstained from')",
        "action": "retag",
        "rationale": "Tests appropriate preposition governing verb: 'abstained from'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "9229c5b6dd7eca444b83": {
        "printed_question": "Q9",
        "physical_page": 3,
        "tested_skill": "Prepositions ('for lack of')",
        "action": "retag",
        "rationale": "Tests preposition of cause/reason: 'rejected for lack of insufficient funds'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "d94e8c05975108b19b81": {
        "printed_question": "Q10",
        "physical_page": 3,
        "tested_skill": "Prepositions ('inspired by')",
        "action": "retag",
        "rationale": "Tests agent preposition in passive context: 'inspired by'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "a6785cc76f65985bb270": {
        "printed_question": "Q11",
        "physical_page": 3,
        "tested_skill": "Prepositions ('at 6:00 a.m.')",
        "action": "retag",
        "rationale": "Tests temporal preposition specifying exact clock time: 'at'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "2dc76a81bd820d7d2d5e": {
        "printed_question": "Q12",
        "physical_page": 4,
        "tested_skill": "Prepositions ('walk to the office')",
        "action": "retag",
        "rationale": "Tests directional preposition indicating destination: 'to'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "bbe4bfd632fb7d7ed3de": {
        "printed_question": "Q13",
        "physical_page": 4,
        "tested_skill": "Prepositions ('at work')",
        "action": "retag",
        "rationale": "Tests locational/state preposition idiom: 'at work'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "5a4ffc2db425d2fbc647": {
        "printed_question": "Q14",
        "physical_page": 4,
        "tested_skill": "Prepositions ('in the classroom')",
        "action": "retag",
        "rationale": "Tests spatial preposition indicating interior location: 'in'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "15af84ad5072b247c72b": {
        "printed_question": "Q15",
        "physical_page": 4,
        "tested_skill": "Prepositions / Infinitives ('how to play')",
        "action": "retag",
        "rationale": "Tests infinitive particle marker 'to' in wh-infinitive construction: 'how to play'. Assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },

    # Q16-Q20: Tenses / Subjunctive Mood
    "4b86c985ea4ec29f1481": {
        "printed_question": "Q16",
        "physical_page": 4,
        "tested_skill": "Tenses (Past Perfect: 'had finished')",
        "action": "retag",
        "rationale": "Tests past perfect tense for an action completed prior to another past event introduced by 'By the time she arrived'. Assign to active tenses subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/tenses"}
    },
    "2abe427e0ad7c37051c6": {
        "printed_question": "Q17",
        "physical_page": 4,
        "tested_skill": "Tenses / Conditionals (Third Conditional: 'had left... would have caught')",
        "action": "retag",
        "rationale": "Tests past perfect in the if-clause of a third (unreal past) conditional sentence. Assign to active tenses subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/tenses"}
    },
    "3e2c6cf272e74876bf9c": {
        "printed_question": "Q18",
        "physical_page": 4,
        "tested_skill": "Tenses (Simple Present habitual with plural subject: 'My parents always scold me')",
        "action": "retag",
        "rationale": "Tests simple present tense indicating routine/habitual action with plural subject 'parents'. Assign to active tenses subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/tenses"}
    },
    "d9ae8133f53452950aeb": {
        "printed_question": "Q19",
        "physical_page": 4,
        "tested_skill": "Tenses / Subjunctive ('I wish I had more time')",
        "action": "retag",
        "rationale": "Tests past subjunctive expressing an unrealized present wish ('I wish I had'). Assign to active tenses subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/tenses"}
    },
    "033a2e8cbe1eac1d2809": {
        "printed_question": "Q20",
        "physical_page": 4,
        "tested_skill": "Tenses / Subjunctive ('He acts as if he were the boss')",
        "action": "retag",
        "rationale": "Tests unreal hypothetical subjunctive 'were' in clauses introduced by 'as if'. Assign to active tenses subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/tenses"}
    },

    # Q21-Q25: Idioms and Phrases
    "e4ca7a4c76fd76ff3832": {
        "printed_question": "Q21",
        "physical_page": 4,
        "tested_skill": "Idioms and Phrases ('Burning the midnight oil')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'Burning the midnight oil' (Working late into the night). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },
    "a18d4318e30e0410d914": {
        "printed_question": "Q22",
        "physical_page": 4,
        "tested_skill": "Idioms and Phrases ('Cutting corners')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'Cutting corners' (Doing something with less effort or expense / taking shortcuts). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },
    "5790a716270d8095e567": {
        "printed_question": "Q23",
        "physical_page": 5,
        "tested_skill": "Idioms and Phrases ('Throw in the towel')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'Throw in the towel' (Give up or admit defeat). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },
    "ded3c7d437dd736efc61": {
        "printed_question": "Q24",
        "physical_page": 5,
        "tested_skill": "Idioms and Phrases ('A wild goose chase')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'A wild goose chase' (A pointless or hopeless pursuit). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },
    "f0c27cd1403f7d024c76": {
        "printed_question": "Q25",
        "physical_page": 5,
        "tested_skill": "Idioms and Phrases ('Play devil\\'s advocate')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'Play devil\\'s advocate' (Argue the opposite to test ideas). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },

    # Q26-Q30: Active and Passive Voice
    "97d2c6fc4b051fc92b35": {
        "printed_question": "Q26",
        "physical_page": 5,
        "tested_skill": "Active and Passive Voice (Modal Perfect Passive: 'We should have been informed')",
        "action": "retag",
        "rationale": "Converts modal perfect active 'Someone should have informed us' to passive 'We should have been informed about the policy change'. Assign to active voice subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/voice"}
    },
    "9d1f183dc1825e4e11d5": {
        "printed_question": "Q27",
        "physical_page": 5,
        "tested_skill": "Active and Passive Voice (Past Perfect Active: 'They had served dinner')",
        "action": "retag",
        "rationale": "Converts past perfect passive 'The guests had been served dinner' to active 'They had served dinner to the guests before the host arrived'. Assign to active voice subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/voice"}
    },
    "46313644da2a876af586": {
        "printed_question": "Q28",
        "physical_page": 5,
        "tested_skill": "Active and Passive Voice (Present Continuous Active: 'The technicians are installing')",
        "action": "retag",
        "rationale": "Converts present continuous passive 'A new system is being installed' to active 'The technicians are installing a new system'. Assign to active voice subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/voice"}
    },
    "06e64d1efc8e4d8fa939": {
        "printed_question": "Q29",
        "physical_page": 5,
        "tested_skill": "Active and Passive Voice (Modal Perfect Active: 'They should have submitted')",
        "action": "retag",
        "rationale": "Converts modal perfect passive 'The documents should have been submitted' to active 'They should have submitted the documents by now'. Assign to active voice subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/voice"}
    },
    "81c92f03e33c30103f9a": {
        "printed_question": "Q30",
        "physical_page": 5,
        "tested_skill": "Active and Passive Voice (Present Perfect Continuous Passive transformation)",
        "action": "retag",
        "rationale": "Identifies passive transformation of present perfect continuous verb construction: 'Extra tasks have been being given...'. Assign to active voice subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/voice"}
    },

    # Q31-Q40: One-Word Substitution
    "4f245700c4500baf8004": {
        "printed_question": "Q31",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Claustrophobia')",
        "action": "retag",
        "rationale": "Identifies 'Claustrophobia' (Fear of confined spaces). Untagged in DB; assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "79dc1eee26942b0570b9": {
        "printed_question": "Q32",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Cartographer')",
        "action": "retag",
        "rationale": "Identifies 'Cartographer' (A person who draws maps). Untagged in DB; assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "87f32ae80e9d6291a8fe": {
        "printed_question": "Q33",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Elegy')",
        "action": "retag",
        "rationale": "Identifies 'Elegy' (A poem or speech of serious reflection, typically for the deceased). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "5ee9f36f0471d005f6c4": {
        "printed_question": "Q34",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Omnivore')",
        "action": "retag",
        "rationale": "Identifies 'Omnivore' (An animal that feeds on plants and animals). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "426ddb662572b20583c5": {
        "printed_question": "Q35",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Noctambulist')",
        "action": "retag",
        "rationale": "Identifies 'Noctambulist' (One who walks in sleep / somnambulist). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "e0f4004aa99c44ea9a03": {
        "printed_question": "Q36",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Autism')",
        "action": "retag",
        "rationale": "Identifies 'Autism' (A developmental condition caused by differences in the brain). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "3c6edece86e1ab3fbc36": {
        "printed_question": "Q37",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Lactose intolerance')",
        "action": "retag",
        "rationale": "Identifies 'Lactose intolerance' (Allergy/inability to digest milk and milk products). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "7fd2c69d53b09d615d87": {
        "printed_question": "Q38",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Hypsophobia')",
        "action": "retag",
        "rationale": "Identifies 'Hypsophobia' / acrophobia (An irrational fear of heights). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "d893a44c19eea5d7d725": {
        "printed_question": "Q39",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Zealotry')",
        "action": "retag",
        "rationale": "Identifies 'Zealotry' (Religious, political or ideological fanaticism). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "2ea8c99e1300f439e72f": {
        "printed_question": "Q40",
        "physical_page": 6,
        "tested_skill": "One-Word Substitution ('Workaholic')",
        "action": "retag",
        "rationale": "Identifies 'Workaholic' (A person who works compulsively). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    }
}

assert len(PROPOSALS) == len(packet["items"]) == 40

candidates = []
findings = []
breakdown = {}

for item in packet["items"]:
    aid = item["appearance_id"]
    cid = item["canonical_id"]
    prop = PROPOSALS[aid]
    
    proposed_tax = prop["proposed"]
    path_parts = [proposed_tax["subject_id"]]
    if proposed_tax.get("topic_id"):
        path_parts.append(proposed_tax["topic_id"].split("/")[-1])
    if proposed_tax.get("subtopic_id"):
        path_parts.append(proposed_tax["subtopic_id"].split("/")[-1])
    norm_path = "/".join(path_parts)
    breakdown[norm_path] = breakdown.get(norm_path, 0) + 1
    
    c_rec = {
        "canonical_id": cid,
        "appearance_id": aid,
        "source_fingerprint": item["source_fingerprint"],
        "review_status": "pending",
        "action": prop["action"],
        "current_primary": item["snapshot"]["record"]["classification"],
        "proposed_primary": proposed_tax,
        "rationale": prop["rationale"],
        "batch_id": 34,
        "policy": "study-tagging-v1"
    }
    candidates.append(c_rec)
    
    findings.append({
        "canonical_id": cid,
        "appearance_id": aid,
        "printed_question": prop["printed_question"],
        "physical_page": prop["physical_page"],
        "tested_skill": prop["tested_skill"],
        "action": prop["action"],
        "current_path": (item["snapshot"]["record"]["classification"]["subject_id"] or "null") if item["snapshot"]["record"]["classification"] else "null",
        "proposed_path": norm_path,
        "rationale": prop["rationale"]
    })

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Preserved unextracted conventional items from Part-A
unextracted_items = [
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Stenographer Grade-II (Contract) under MPSC - Paper-I (General English)..pdf",
        "document_id": "doc_5f0d589624f2eb0f9031863f",
        "physical_page": 1,
        "item_type": "conventional_written_essay",
        "prompt": "Write an essay on any one of the topics in not more than 300 words (20 marks): (1) The importance of good communication skills in office work. (2) Workplace ethics and professionalism. (3) Digital India: Opportunities and challenges.",
        "marks": 20,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/essay"},
        "reason_unextracted": "Conventional written essay task answering on separate answer booklet; excluded from automated objective MCQ ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Stenographer Grade-II (Contract) under MPSC - Paper-I (General English)..pdf",
        "document_id": "doc_5f0d589624f2eb0f9031863f",
        "physical_page": 1,
        "item_type": "conventional_reading_comprehension",
        "prompt": "Read the following passage carefully and answer the questions that follow (30 marks total across questions a–l: talent vs hard work, Thomas Alva Edison example, perseverance, and vocabulary questions k(i) innate, k(ii) surpassed, l(i) failure, l(ii) rigid).",
        "marks": 30,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None},
        "reason_unextracted": "Conventional short-answer reading comprehension questions answering on separate answer booklet; excluded from automated objective MCQ ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Stenographer Grade-II (Contract) under MPSC - Paper-I (General English)..pdf",
        "document_id": "doc_5f0d589624f2eb0f9031863f",
        "physical_page": 2,
        "item_type": "conventional_written_precis",
        "prompt": "Read the following passage carefully and write a precis in about one third of its length. Suggest a suitable title (10 marks) [Passage on Academic degrees vs common sense and practical wisdom in real life].",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/precis"},
        "reason_unextracted": "Conventional written précis task answering on separate answer booklet; excluded from automated objective MCQ ingestion."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(unextracted_items, indent=2) + "\n")

summary = {
    "batch": 34,
    "paper_id": "Old_Questions/Direct_NG_2024-2027/Stenographer Grade-II (Contract) under MPSC - Paper-I (General English)..pdf",
    "paper_title": "Competitive Examination for the Post of Stenographer Grade-II (Contract) under Mizoram Public Service Commission (May-2025) — Paper-I General English",
    "document_id": "doc_5f0d589624f2eb0f9031863f",
    "sha256": "aa21fba8e0cae4d2ba59d2a0a32f23d67399eabcf54c885896eb329479f29699",
    "targets": 40,
    "completion": "100% of extracted MCQs reviewed",
    "actions": {
        "retag": 40,
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
