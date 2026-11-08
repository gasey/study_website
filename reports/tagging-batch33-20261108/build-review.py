"""Generate review candidates and findings for Batch 33.
Targets: 32 English MCQs across 2 direct 2026 General English papers:
- Instructor ITI Paper-I General English (26 MCQs)
- Inspector of Statistics Paper-I English (6 MCQs)
All 32 currently untagged (null subject/topic in DB).
"""
import json
from pathlib import Path
from datetime import datetime, timezone

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

# Map of appearance_id -> proposed taxonomy & rationale
PROPOSALS = {
    # === Inspector of Statistics Paper-I (English) (6 MCQs, all Reading Comprehension) ===
    "f3ddda9f9a79a17af82a": {
        "printed_question": "Q5",
        "physical_page": 2,
        "tested_skill": "Reading Comprehension (Science and Religion passage analysis)",
        "action": "retag",
        "rationale": "Passage comprehension question analyzing that science and religion employ different methods of inquiry. Untagged in DB; assign to active English comprehension topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None}
    },
    "caada13a28751f5b0980": {
        "printed_question": "Q6",
        "physical_page": 2,
        "tested_skill": "Reading Comprehension (Author intent / synthesis)",
        "action": "retag",
        "rationale": "Passage comprehension question on reconciling science and religion at the present juncture. Untagged in DB; assign to active English comprehension topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None}
    },
    "c03e1e42d1d897234c07": {
        "printed_question": "Q8",
        "physical_page": 2,
        "tested_skill": "Reading Comprehension (Factual / contextual assertion)",
        "action": "retag",
        "rationale": "Passage comprehension question testing true statement identification in context of science vs regimental religion. Untagged in DB; assign to active English comprehension topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None}
    },
    "d7ac4193b6a577170ba4": {
        "printed_question": "Q9",
        "physical_page": 2,
        "tested_skill": "Reading Comprehension (Negative factual identification)",
        "action": "retag",
        "rationale": "Passage comprehension question identifying which statement is not true based on text details. Untagged in DB; assign to active English comprehension topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None}
    },
    "29fbb970a60da79d01ea": {
        "printed_question": "Q10",
        "physical_page": 3,
        "tested_skill": "Reading Comprehension (Contextual detail)",
        "action": "retag",
        "rationale": "Passage comprehension question identifying how truth was treated in historical context. Untagged in DB; assign to active English comprehension topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None}
    },
    "324c19fbf1b04a0f01b9": {
        "printed_question": "Q11",
        "physical_page": 3,
        "tested_skill": "Reading Comprehension (Authorial purpose analysis)",
        "action": "retag",
        "rationale": "Passage comprehension question analyzing the objective of holy scripture authors. Untagged in DB; assign to active English comprehension topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None}
    },

    # === Instructor ITI Paper-I General English (26 MCQs) ===
    # Q1-Q5: Parts of Speech Identification
    "1723d96f0290bdf301f3": {
        "printed_question": "Q1",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Emphasizing Adjective: 'The very idea shocked everyone')",
        "action": "retag",
        "rationale": "Underlined word 'very' functions as an emphasizing adjective modifying noun 'idea'. Untagged in DB; assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "c2e6dcfdecb6d2d9e32e": {
        "printed_question": "Q2",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Preposition: 'working since morning')",
        "action": "retag",
        "rationale": "Underlined word 'since' introduces a temporal point and functions as a preposition. Untagged in DB; assign to active prepositions subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/prepositions"}
    },
    "b870bdf3a68bf2f7d83e": {
        "printed_question": "Q3",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Modal Auxiliary Verb: 'might refuse')",
        "action": "retag",
        "rationale": "Underlined word 'might' expresses possibility and functions as a modal verb. Untagged in DB; assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "551cf409bb1b4ea283fc": {
        "printed_question": "Q4",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Indefinite Pronoun: 'Nobody understood')",
        "action": "retag",
        "rationale": "Underlined word 'Nobody' stands for unspecified persons and functions as an indefinite pronoun. Untagged in DB; assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "db5fafe27ee4ee634608": {
        "printed_question": "Q5",
        "physical_page": 3,
        "tested_skill": "Parts of Speech (Noun: 'caused upheaval')",
        "action": "retag",
        "rationale": "Underlined word 'upheaval' is the direct object noun of transitive verb 'caused'. Untagged in DB; assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },

    # Q6-Q10: Rewrite by substituting parts of speech
    "b903cae6807ce7621a30": {
        "printed_question": "Q6",
        "physical_page": 3,
        "tested_skill": "Parts of Speech / Word Formation (Adverb to Noun: bravely -> bravery)",
        "action": "retag",
        "rationale": "Sentence rewrite substituting adverb 'bravely' with its abstract noun form 'bravery' ('He fought with bravery during the battle'). Assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "d8cead9f33080a3e17aa": {
        "printed_question": "Q7",
        "physical_page": 4,
        "tested_skill": "Parts of Speech / Word Formation (Adjective to Adverb: beautiful -> beautifully)",
        "action": "retag",
        "rationale": "Sentence rewrite substituting adjective 'beautiful' with its adverbial form 'beautifully' ('We woke up as the sun rose beautifully'). Assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "f094888c02614f424590": {
        "printed_question": "Q8",
        "physical_page": 4,
        "tested_skill": "Parts of Speech / Word Formation (Adjective to Noun: true -> the truth)",
        "action": "retag",
        "rationale": "Sentence rewrite substituting adjective 'true' with noun phrase 'the truth' ('If what you have told me is the truth, then I must act'). Assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "1be2cf04cbdb06082d75": {
        "printed_question": "Q9",
        "physical_page": 4,
        "tested_skill": "Parts of Speech / Word Formation (Adjective to Adverb: gentle -> gently)",
        "action": "retag",
        "rationale": "Sentence rewrite substituting adjective 'gentle' with adverb 'gently' ('The breeze blew gently in from the east'). Assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },
    "97c9e9a62ae56b2e4e48": {
        "printed_question": "Q10",
        "physical_page": 4,
        "tested_skill": "Parts of Speech / Word Formation (Adjective to Noun: happy -> happiness)",
        "action": "retag",
        "rationale": "Sentence rewrite substituting predicate adjective 'happy' with abstract noun 'happiness' ('It is a happiness for me to be in the king\\'s service'). Assign to active parts-of-speech subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/parts-of-speech"}
    },

    # Q11-Q15: Idioms and Phrases
    "72f6b71f7ce810f009e0": {
        "printed_question": "Q11",
        "physical_page": 4,
        "tested_skill": "Idioms and Phrases ('to miss the boat')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'to miss the boat' (to miss an opportunity). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },
    "798b8c494e00c4f8d193": {
        "printed_question": "Q12",
        "physical_page": 4,
        "tested_skill": "Idioms and Phrases ('to be under the weather')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'to be under the weather' (feeling slightly unwell/sick). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },
    "7507a9cd3e7f5dae6e79": {
        "printed_question": "Q13",
        "physical_page": 4,
        "tested_skill": "Idioms and Phrases ('To break the ice')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'to break the ice' (make people feel more comfortable in a social setting). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },
    "eeb3e9a1f2e3c1b19f04": {
        "printed_question": "Q14",
        "physical_page": 4,
        "tested_skill": "Idioms and Phrases ('to let the cat out of the bag')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'to let the cat out of the bag' (reveal a secret carelessly or by mistake). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },
    "83cb4086f925f626dc26": {
        "printed_question": "Q15",
        "physical_page": 5,
        "tested_skill": "Idioms and Phrases ('the ball is in your court')",
        "action": "retag",
        "rationale": "Tests meaning of idiom 'the ball is in your court' (it is your turn to act or make a decision). Assign to active idioms-and-phrases subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"}
    },

    # Q16-Q20: Contextual Vocabulary & One-Word Substitution
    "4d03e5386991bb937ea8": {
        "printed_question": "Q16",
        "physical_page": 5,
        "tested_skill": "Contextual Vocabulary ('indispensable')",
        "action": "retag",
        "rationale": "Sentence completion with appropriate adjective 'indispensable' (absolutely necessary/essential). Assign to active vocabulary topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": None}
    },
    "ce772c53df416a00413c": {
        "printed_question": "Q17",
        "physical_page": 5,
        "tested_skill": "Contextual Vocabulary ('inedible')",
        "action": "retag",
        "rationale": "Sentence completion with appropriate adjective 'inedible' (unfit to be eaten). Assign to active vocabulary topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": None}
    },
    "c43e1d1e4861e21ead01": {
        "printed_question": "Q18",
        "physical_page": 5,
        "tested_skill": "One-Word Substitution ('misogynist')",
        "action": "retag",
        "rationale": "Sentence completion identifying 'misogynist' (a person who dislikes, despises, or strongly prejudices against women). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "0cdf866943c456256ab5": {
        "printed_question": "Q19",
        "physical_page": 5,
        "tested_skill": "One-Word Substitution ('anarchy')",
        "action": "retag",
        "rationale": "Sentence completion identifying 'anarchy' (a state of disorder due to absence or non-recognition of authority). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },
    "f2c49d1a72f050ceaf6d": {
        "printed_question": "Q20",
        "physical_page": 5,
        "tested_skill": "One-Word Substitution ('obsolete')",
        "action": "retag",
        "rationale": "Sentence completion identifying 'obsolete' (no longer produced or used; out of date). Assign to active one-word substitution subtopic.",
        "proposed": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"}
    },

    # Q21-Q25: Sentence Transformations
    "5ed3a7692e3bd66b0030": {
        "printed_question": "Q21",
        "physical_page": 5,
        "tested_skill": "Sentence Transformations (Affirmative to Negative: 'It is possible that I may be wrong')",
        "action": "retag",
        "rationale": "Sentence transformation converting affirmative to negative without changing meaning ('It is not impossible that I may be wrong'). Assign to active English grammar topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": None}
    },
    "2033f1ae8d79da7308d8": {
        "printed_question": "Q22",
        "physical_page": 5,
        "tested_skill": "Degrees of Comparison (Positive to Superlative: 'Few towns in India are as big as Delhi')",
        "action": "retag",
        "rationale": "Sentence transformation converting positive degree to superlative degree ('Delhi is one of the biggest towns in India'). Assign to active English grammar topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": None}
    },
    "b622baf9a85971ec152d": {
        "printed_question": "Q23",
        "physical_page": 5,
        "tested_skill": "Sentence Transformations (Optative/Exclamatory to Assertive: 'O for a cup of water')",
        "action": "retag",
        "rationale": "Sentence transformation converting wish/exclamation to assertive statement ('I wish I had a cup of water'). Assign to active English grammar topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": None}
    },
    "fc732b874bba7b1d42de": {
        "printed_question": "Q24",
        "physical_page": 6,
        "tested_skill": "Degrees of Comparison (Superlative to Positive: 'Jane is the most beautiful girl in school')",
        "action": "retag",
        "rationale": "Sentence transformation converting superlative to positive degree ('No other girl in school is as beautiful as Jane'). Assign to active English grammar topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": None}
    },
    "8d1a70ff113eec16542f": {
        "printed_question": "Q25",
        "physical_page": 6,
        "tested_skill": "Sentence Transformations (Assertive to Imperative: 'I wish that the door may be closed at once')",
        "action": "retag",
        "rationale": "Sentence transformation converting request/wish to direct command/imperative ('Close the door at once.'). Assign to active English grammar topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": None}
    },

    # Q26: Sentence Correction
    "6f514c08f53ac3ba4201": {
        "printed_question": "Q26",
        "physical_page": 6,
        "tested_skill": "Sentence Correction / Correlative Conjunctions ('No sooner had... than')",
        "action": "retag",
        "rationale": "Identifies grammatically correct sentence using correlative inverted structure 'No sooner had she finished her speech than the audience applauded'. Assign to active sentence correction topic.",
        "proposed": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None}
    }
}

assert len(PROPOSALS) == len(packet["items"]) == 32

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
        "batch_id": 33,
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

# Preserved unextracted conventional & dropped items
unextracted_items = [
    # === ITI Instructor Paper-I ===
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
        "document_id": "doc_0b0f26b428ddfe44c54aef08",
        "physical_page": 1,
        "item_type": "conventional_written_precis",
        "prompt": "Write a precis of the following passage in about one third of the original length and suggest a suitable title. (10 marks) [Passage on modern skill-based training and the role of instructors in Industrial Training Institutes].",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/precis"},
        "reason_unextracted": "Conventional written précis task answering on separate answer sheet; excluded from automated objective MCQ ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
        "document_id": "doc_0b0f26b428ddfe44c54aef08",
        "physical_page": 1,
        "item_type": "conventional_written_letter",
        "prompt": "Many students avoid vocational training and choose general academic courses without a proper career plan. Write a letter to the Editor of the daily newspaper Zawlkhawpui discussing this issue and suggesting ways to increase awareness of skilled jobs. Address yourself as XXX. (10 marks)",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/letter"},
        "reason_unextracted": "Conventional written letter to the editor prompt answering on separate answer sheet; excluded from automated objective MCQ ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
        "document_id": "doc_0b0f26b428ddfe44c54aef08",
        "physical_page": 2,
        "item_type": "conventional_reading_comprehension",
        "prompt": "Read the following passage carefully and answer the following questions: (i) What is the main purpose of industrial training? (2m) (ii) Why do some trainees fail to benefit fully from training? (2m) (iii) What role do instructors play in the training process? (2m) (iv) How can industrial training be made more effective? (2m) (v) Find a word from the passage similar in meaning to 'self-control' (1m: discipline) (vi) Find a word from the passage opposite in meaning to 'comprehensive' (1m: incomplete).",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None},
        "reason_unextracted": "Conventional short-answer reading comprehension questions answering on separate answer sheet; excluded from automated objective MCQ ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
        "document_id": "doc_0b0f26b428ddfe44c54aef08",
        "physical_page": 2,
        "item_type": "conventional_written_essay",
        "prompt": "Write an essay on any one (1) of the following topics in about 250 words: (1) The Importance of discipline in building a successful skilled career. (2) Intermarriage and Mizo Women's Rights. (3) Role of Information Technology in Skill Development. (10 marks)",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/essay"},
        "reason_unextracted": "Conventional written essay prompt answering on separate answer sheet; excluded from automated objective MCQ ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
        "document_id": "doc_0b0f26b428ddfe44c54aef08",
        "physical_page": 6,
        "item_type": "mcq_dropped_duplicate_stem",
        "prompt": "Choose the correct sentence: 27. (a) Under no circumstances should you break the rules. (b) Under no circumstances you should break the rules. (c) Under no circumstances should break you the rules. (d) Under no circumstances you should be break the rules.",
        "marks": 2,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None},
        "reason_unextracted": "OCR deduplication drop due to identical repeated section instruction 'Choose the correct sentence:' across Q26–Q30."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
        "document_id": "doc_0b0f26b428ddfe44c54aef08",
        "physical_page": 6,
        "item_type": "mcq_dropped_duplicate_stem",
        "prompt": "Choose the correct sentence: 28. (a) So was difficult the exam that many failed. (b) So difficult the exam was that many failed. (c) So the exam was difficult that many failed. (d) So difficult was the exam that many failed.",
        "marks": 2,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None},
        "reason_unextracted": "OCR deduplication drop due to identical repeated section instruction 'Choose the correct sentence:' across Q26–Q30."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
        "document_id": "doc_0b0f26b428ddfe44c54aef08",
        "physical_page": 6,
        "item_type": "mcq_dropped_duplicate_stem",
        "prompt": "Choose the correct sentence: 29. (a) The more harder you work, the more successful you become. (b) The harder you work, the more successful you become. (c) The harder you work, more successful you become. (d) More harder you work, the more successful you become.",
        "marks": 2,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None},
        "reason_unextracted": "OCR deduplication drop due to identical repeated section instruction 'Choose the correct sentence:' across Q26–Q30."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
        "document_id": "doc_0b0f26b428ddfe44c54aef08",
        "physical_page": 6,
        "item_type": "mcq_dropped_duplicate_stem",
        "prompt": "Choose the correct sentence: 30. (a) Not only did he lose the documents, but he also failed to report it. (b) Not only he lose the documents, but he also failed to report it. (c) Not only he lost the documents but also failed to report it. (d) Not only did he lost the documents, but he also failed to report it.",
        "marks": 2,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None},
        "reason_unextracted": "OCR deduplication drop due to identical repeated section instruction 'Choose the correct sentence:' across Q26–Q30."
    },

    # === Inspector of Statistics Paper-I ===
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 1,
        "item_type": "conventional_written_essay",
        "prompt": "Write an essay choosing one of the topics given below: (a) Sairang Rail Station: A Catalyst for Infrastructure Development in Mizoram (b) Mental Health and Work Environment (c) Strengthening Good Governance through Official Statistics (d) The Digital Generation: How Technology is Changing Childhood and Youth. (20 marks)",
        "marks": 20,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/essay"},
        "reason_unextracted": "Conventional written essay task answering on conventional answer booklet."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 1,
        "item_type": "conventional_written_precis",
        "prompt": "Write a precis of the following passage: [Passage on Self-reliance as the pilgrim's best staff and the worker's best tool, and modern education shortcomings]. (10 marks)",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/precis"},
        "reason_unextracted": "Conventional written précis task answering on conventional answer booklet."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 2,
        "item_type": "conventional_reading_comprehension_short_answer",
        "prompt": "3. Why does man worship the force of nature? (2 marks)",
        "marks": 2,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None},
        "reason_unextracted": "Conventional subjective short-answer question embedded in reading comprehension passage section."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 2,
        "item_type": "conventional_reading_comprehension_short_answer",
        "prompt": "4. Why is it said in the passage that 'science emerged as a saviour of mankind'? (2 marks)",
        "marks": 2,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None},
        "reason_unextracted": "Conventional subjective short-answer question embedded in reading comprehension passage section."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 2,
        "item_type": "conventional_reading_comprehension_vocabulary",
        "prompt": "7. Choose the antonym of the word 'non-contradictory' (2 marks)",
        "marks": 2,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/antonyms"},
        "reason_unextracted": "Conventional short-answer antonym question without multiple choice options."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 3,
        "item_type": "conventional_reading_comprehension_vocabulary",
        "prompt": "12. Find the synonym of the word 'dazzled/impressed'. (2 marks)",
        "marks": 2,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/synonyms"},
        "reason_unextracted": "Conventional short-answer synonym question without multiple choice options."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 3,
        "item_type": "conventional_homophones_sentence_making",
        "prompt": "13. Make sentences with any five to bring out the difference in their meaning (5x2=10 marks): (a) Emerge/Immerse (b) Pair/Pare (c) Teem/Team (d) Antique/Antic (e) Compliment/Complement (f) Hail/Hale (g) Wave/Waive (h) Proscribe/Prescribe.",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": None},
        "reason_unextracted": "Conventional subjective sentence-making task testing homophones/confusable word pairs."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 3,
        "item_type": "conventional_one_word_substitution",
        "prompt": "14. Supply suitable one-word substitutes for any ten of the following (10x2=20 marks): (a) Incapable of making errors (b) Fluent and clear in speech (c) One who hates war, loves peace (d) A remedy for all ills (e) Exactly as it was spoken or written (f) A connoisseur of food (g) An imaginary name assumed by an author (h) Medicine given to counteract poison (i) One who lives in solitude (j) An examination of living tissue (k) An official pardon (l) Flower fastened in a circle.",
        "marks": 20,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/one-word-substitution"},
        "reason_unextracted": "Conventional one-word substitution prompts without multiple choice options."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 3,
        "item_type": "conventional_synonyms",
        "prompt": "15. Supply appropriate synonyms for any five of the following (5x2=10 marks): (a) Concur (b) Overbearing (c) Mitigate (d) Prodigy (e) Vagrant (f) Brittle (g) Disdain.",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/synonyms"},
        "reason_unextracted": "Conventional synonym supply prompts without multiple choice options."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 3,
        "item_type": "conventional_antonyms",
        "prompt": "16. Supply appropriate antonyms for any five of the following (5x2=10 marks): (a) Moderate (b) Jubilant (c) Eccentric (d) Nepotism (e) Transient (f) Spurious (g) Abound.",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/antonyms"},
        "reason_unextracted": "Conventional antonym supply prompts without multiple choice options."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 3,
        "item_type": "conventional_idioms_sentence_making",
        "prompt": "17. Make sentences with any five of the following idioms/phrases to bring out their meaning (5x2=10 marks): (a) Hold water (b) Bird's eye view (c) Apple-pie order (d) To miss the bus (e) A small fry (f) Gordian knot (g) Damp squib.",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/vocabulary", "subtopic_id": "english/vocabulary/idioms-and-phrases"},
        "reason_unextracted": "Conventional subjective sentence-making task testing idioms."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 3,
        "item_type": "conventional_voice",
        "prompt": "18. Change the voice (5x2=10 marks): (a) The chef is cooking a special dish (b) How did you open the door? (c) Tea shall not be taken by me today (d) By whom were you insulted? (e) Mistakes were made.",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": "english/grammar/voice"},
        "reason_unextracted": "Conventional voice conversion task without multiple choice options."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 4,
        "item_type": "conventional_question_tags",
        "prompt": "19. Complete the following by using question tags (5x2=10 marks): (a) Let us go, _______? (b) He isn't very happy with it _________? (c) Mind your business, _________? (d) Keep your mouth shut ______? (e) Don't break the glass _________?",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": None},
        "reason_unextracted": "Conventional question tags completion task without multiple choice options."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
        "document_id": "doc_b61ba36d95d17e4c2a561cb8",
        "physical_page": 4,
        "item_type": "conventional_sentence_transformations",
        "prompt": "20. Rewrite the following sentences as directed (10x2=20 marks): (a) How long have you _________ him? (verb know) (b) The sun was shining. We went for a walk. (Compound) (c) Having finished his work, he went home. (Complex) (d) You have to pay or you cannot leave this place. (Simple) (e) She said, 'You see, you cannot meet the principal'. (Indirect speech) (f) Portia exclaimed with sorrow that she was ruined. (Direct speech) (g) Waste not, want not. (Begin with if) (h) I do not know her nature any better than you. (positive degree) (i) His prompt reply will able us to take timely action. (Correct/improve) (j) Shall we ever forget these happy days. (using never).",
        "marks": 20,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": None},
        "reason_unextracted": "Conventional sentence transformation / synthesis tasks without multiple choice options."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(unextracted_items, indent=2) + "\n")

summary = {
    "batch": 33,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf",
            "paper_title": "Competitive Examination for Recruitment to the Post of Instructor, ITI under Labour, Employment, Skill Development & Entrepreneurship Department, Government of Mizoram (April-2026) — Paper-I General English",
            "document_id": "doc_0b0f26b428ddfe44c54aef08",
            "sha256": "23534dd43b1bfc4aa67cda0ffa409b3f72201ea2da6e219c42123a4a6adcb1b6",
            "targets": 26,
            "completion": "100% of extracted MCQs reviewed"
        },
        {
            "paper_id": "Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf",
            "paper_title": "Competitive Examination for Inspector of Statistics under Planning & Programme Implementation Department, Government of Mizoram (March-2026) — Paper-I General English",
            "document_id": "doc_b61ba36d95d17e4c2a561cb8",
            "sha256": "58f0cf1cd9de99cd9c8b61ebcc519a3c7f4288d539f7eeed8f517cd681639477",
            "targets": 6,
            "completion": "100% of extracted MCQs reviewed"
        }
    ],
    "targets": 32,
    "actions": {
        "retag": 32,
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
