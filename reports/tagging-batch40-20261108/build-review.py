"""Build review packet and findings for Batch 40: AAO & Field Facilitator 2025 General English (Series A)."""
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

# Map qnum (1-indexed) to metadata: (page, skill, path_str, action, rationale)
specs = {
    # Page 4: Q1-Q12
    1: (4, "Parts of Speech (Adjective)", "english/grammar/parts-of-speech", "retag", "Classifies qualitative adjective 'brilliant' modifying noun 'politician'."),
    2: (4, "Parts of Speech (Adverb)", "english/grammar/parts-of-speech", "retag", "Classifies manner adverb 'quickly' derived from adjective quick."),
    3: (4, "Parts of Speech (Conjunction)", "english/grammar/parts-of-speech", "retag", "Classifies coordinating conjunction 'and' connecting compound subject elements."),
    4: (4, "Parts of Speech (Preposition)", "english/grammar/parts-of-speech", "retag", "Classifies preposition 'beyond' expressing exceeding limits or comprehension."),
    5: (4, "Parts of Speech (Adverb)", "english/grammar/parts-of-speech", "retag", "Classifies manner adverb 'fast' modifying intransitive verb 'ran'."),
    6: (4, "Parts of Speech (Pronoun)", "english/grammar/parts-of-speech", "retag", "Classifies demonstrative pronoun 'that' serving as subject of copula."),
    7: (4, "Parts of Speech (Adverb)", "english/grammar/parts-of-speech", "retag", "Classifies manner adverb 'sweetly' modifying verb 'sings'."),
    8: (4, "Parts of Speech (Noun)", "english/grammar/parts-of-speech", "retag", "Classifies military collective noun 'artillery'."),
    9: (4, "Parts of Speech (Noun)", "english/grammar/parts-of-speech", "retag", "Classifies abstract noun 'death' following possessive pronoun 'his'."),
    10: (4, "Parts of Speech (Adverb)", "english/grammar/parts-of-speech", "retag", "Classifies degree adverb 'almost' modifying verb 'missed'."),
    11: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests simple present habitual aspect ('does') with frequency adverbial 'every morning'."),
    12: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests simple past tense ('went') anchored by past time marker 'yesterday'."),
    # Page 5: Q13-Q25
    13: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests future perfect aspect ('will have finished') anchored by 'By this time tomorrow'."),
    14: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests simple past tense ('received') anchored by completed past time 'this forenoon'."),
    15: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past continuous aspect ('was cooking') interrupted by simple past arrival."),
    16: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests present perfect / duration aspect ('have studied') with time span 'for ten years'."),
    17: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past perfect aspect ('had left') preceding another past event ('reached')."),
    18: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past continuous aspect ('was watching') interrupted by sudden blackout."),
    19: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests simple past tense ('lost / found') describing completed action in the garden."),
    20: (5, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests first conditional consequence clause ('will stay') following present condition."),
    21: (5, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests contrastive descriptive adjective choice ('dilapidated' vs 'strong')."),
    22: (5, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'elated' ('overjoyed / ecstatic')."),
    23: (5, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'generous' ('magnanimous / benevolent')."),
    24: (5, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'ancient' ('modern / contemporary')."),
    25: (5, "Vocabulary & Word Choice", "english/vocabulary", "keep", "Confirms exact active topic for contextual adjective selection in speech delivery."),
    # Page 6: Q26-Q37
    26: (6, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'vivid' ('clear / intensely bright')."),
    27: (6, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests contextual adjective choice 'wise' describing profitable commercial decisions."),
    28: (6, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests meaning/synonym of 'contented' ('satisfied / at peace')."),
    29: (6, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'abandon' ('relinquish / forsake')."),
    30: (6, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests abstract noun choice ('dedication / diligence') commended by management."),
    31: (6, "Word Order & Syntax", "english/sentence-correction", "retag", "Tests syntactic word order and adjective placement in sentence construction."),
    32: (6, "Grammatical Accuracy", "english/sentence-correction", "retag", "Tests syntactic grammaticality and subject-verb-modifier concordance."),
    33: (6, "Sentence Completeness", "english/sentence-correction", "retag", "Tests identification of independent clause completeness and clause fragments."),
    34: (6, "Word Order & Syntax", "english/sentence-correction", "retag", "Tests correct word order in complex sentence structuring."),
    35: (6, "Sentence Structure", "english/sentence-correction", "retag", "Tests structural integrity and parallel phrasing in sentence construction."),
    36: (6, "Punctuation & Syntax", "english/sentence-correction", "retag", "Tests comma and apostrophe conventions in complex sentence punctuation."),
    37: (6, "Sentence Arrangement (PQRS)", "english/grammar", "keep", "Confirms exact active topic for cohesive sentence reordering on environmental action."),
    # Page 7: Q38-Q48
    38: (7, "Sentence Arrangement (PQRS)", "english/grammar", "keep", "Confirms exact active topic for cohesive narrative sequencing on earthquake disaster recovery."),
    39: (7, "Sentence Arrangement (PQRS)", "english/grammar", "keep", "Confirms exact active topic for cohesive paragraph sequencing on global connectivity."),
    40: (7, "Conjunctions", "english/grammar", "keep", "Confirms exact active topic for correlative and coordinating conjunction syntax."),
    41: (7, "Sentence Types (Imperative)", "english/grammar", "keep", "Confirms exact active topic for imperative sentence structure ('Close the door')."),
    42: (7, "Sentence Types (Declarative)", "english/grammar", "keep", "Confirms exact active topic for declarative statement structure with direct object."),
    43: (7, "Clause Analysis (Noun Clause)", "english/grammar", "keep", "Confirms exact active topic for dependent interrogative noun clause ('who she is')."),
    44: (7, "Clause Analysis (Participle Phrase)", "english/grammar", "keep", "Confirms exact active topic for past participle phrase modifier ('laden with fruits')."),
    45: (7, "Sentence Structures (Compound)", "english/grammar", "keep", "Confirms exact active topic for coordinate compound sentence structure ('brave but careless')."),
    46: (7, "Sentence Patterns (Exclamatory)", "english/grammar", "keep", "Confirms exact active topic for syntactic exclamatory pattern ('How + Adjective + Subject + Verb')."),
    47: (7, "Sentence Patterns (Intransitive)", "english/grammar", "keep", "Confirms exact active topic for subject + intransitive verb clause pattern ('All cheered')."),
    48: (7, "Sentence Types (Negative Imperative)", "english/grammar", "keep", "Confirms exact active topic for negative imperative command ('Never waste food')."),
    # Page 8: Q49-Q60
    49: (8, "Sentence Types (Interrogative)", "english/grammar", "keep", "Confirms exact active topic for polar interrogative inversion ('Is it early yet?')."),
    50: (8, "Sentence Patterns (SVO)", "english/grammar", "keep", "Confirms exact active topic for canonical Subject + Transitive Verb + Direct Object clause pattern."),
    51: (8, "Sentence Functions (Infinitive of Purpose)", "english/grammar", "keep", "Confirms exact active topic for adverbial infinitive expressing purpose ('to buy mints')."),
    52: (8, "Sentence Functions (Adverbial of Time)", "english/grammar", "keep", "Confirms exact active topic for temporal prepositional adjunct ('at the age of 40')."),
    53: (8, "Prepositions of Place", "english/grammar/prepositions", "retag", "Tests preposition 'in' indicating venue location ('in the conference')."),
    54: (8, "Sentence Functions (Adversative Contrast)", "english/grammar", "keep", "Confirms exact active topic for compound contrastive clause coordination ('but it started raining')."),
    55: (8, "Sentence Functions (Concessive Clause)", "english/grammar", "keep", "Confirms exact active topic for complex subordinating concessive clause ('Although she was tired...')."),
    56: (8, "Reported Speech", "english/grammar/reported-speech", "retag", "Tests direct-to-indirect narration shift of present perfect to past perfect."),
    57: (8, "Reported Speech", "english/grammar/reported-speech", "retag", "Tests indirect-to-direct narration back-shift with routine habitual aspect."),
    58: (8, "Reported Speech", "english/grammar/reported-speech", "retag", "Tests direct-to-indirect narration of rhetorical tag question complement."),
    59: (8, "Active & Passive Voice", "english/grammar/voice", "retag", "Tests active-to-passive voice transformation of simple present transitive statement."),
    60: (8, "Active & Passive Voice", "english/grammar/voice", "retag", "Tests passive-to-active voice transformation of modal imperative advice ('should be helped').")
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
        "batch_id": 40,
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

assert len(candidates) == 60
assert len(findings) == 60

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Preserved written tasks from Part-A (Pages 2-3)
written_intake = [
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/General English - Series A..pdf",
        "section": "PART- A (40 Marks)",
        "question_number": "1",
        "physical_page": 2,
        "marks": 10,
        "task_type": "précis_writing",
        "prompt": "Write a precis of the following passage and give a suitable title.",
        "source_context": "Gardening is one of the oldest and most rewarding human activities... (approx 450 words comprehensive essay on environmental, mental, and social benefits of gardening).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional written descriptive précis composition task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/General English - Series A..pdf",
        "section": "PART- A (40 Marks)",
        "question_number": "2",
        "physical_page": 2,
        "marks": 10,
        "task_type": "formal_letter_writing",
        "prompt": "You are experiencing frequent interruption of power supply in your locality and you are very much concerned about it. Write a letter to the Minister, Power & Electricity Department, Mizoram, highlighting the importance of self-reliance in power generation for the state. Sign as XYZ.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional formal ministerial representation letter drafting task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/General English - Series A..pdf",
        "section": "PART- A (40 Marks)",
        "question_number": "3",
        "physical_page": 3,
        "marks": 10,
        "task_type": "reading_comprehension",
        "prompt": "Read the given passage carefully and answer the questions that follow: Narrative passage describing elderly fruit vendor in Bara Bazar and college students exemplifying civic empathy. Sub-questions (a) to (e) totaling 10 marks.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive reading comprehension passage with contextual analysis and vocabulary sub-questions, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/General English - Series A..pdf",
        "section": "PART- A (40 Marks)",
        "question_number": "4",
        "physical_page": 3,
        "marks": 10,
        "task_type": "essay_writing",
        "prompt": "Write an essay on any one (1) of the following topics: Rainwater Harvesting and Forest Preservation in Mizoram; Urban Growth and Its Impact on Environment; Role of NGOs in Mizoram's Development; Importance of Good Governance in Mizoram.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional argumentative essay writing task with topic choices, excluded from automated MCQ database ingestion."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")

summary = {
    "batch": 40,
    "paper_id": "Old_Questions/Direct_NG_2024-2027/General English - Series A..pdf",
    "paper_title": "General Competitive Examination for Recruitment to the Posts of Assistant Accounts Officer and Field Facilitator (November, 2025) — General English (Series A)",
    "document_id": "doc_f00f463fd9dd338fb2178369",
    "sha256": "651da25575f73d3b8bb13585494cae05b038f47af67e7176b31cb43d5986901d",
    "single_booklet_enforced": True,
    "bypassed_duplicate": {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/General English - Series B..pdf",
        "document_id": "doc_9283fbe7c06c764e3084aeff",
        "sha256": "950f330d86383ce12a0ee813fadea7d1745627866eeedbf98cf501703a0f5b95",
        "reason": "Permuted Series B booklet of the identical November 2025 examination. Cleanly bypassed under single-booklet deduplication rule to prevent redundant reviews."
    },
    "targets": 60,
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
