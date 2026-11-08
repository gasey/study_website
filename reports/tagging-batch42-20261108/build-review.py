"""Build review packet and findings for Batch 42: Food Sub-Inspector & Receptionist 2025 General English (Series A)."""
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

# Map qnum (from physical booklet) to metadata: (page, skill, path_str, action, rationale)
specs = {
    # Page 3: Q1-Q10
    1: (3, "Parts of Speech (Adjective)", "english/grammar/parts-of-speech", "retag", "Classifies qualitative adjective 'Gentle' modifying plural noun 'words'."),
    2: (3, "Parts of Speech (Adjective)", "english/grammar/parts-of-speech", "retag", "Classifies predicative adjective 'round' describing shape of subject 'earth'."),
    3: (3, "Parts of Speech (Adverb)", "english/grammar/parts-of-speech", "retag", "Classifies intensifier degree adverb 'very' modifying predicate adjective 'happy'."),
    4: (3, "Parts of Speech (Noun)", "english/grammar/parts-of-speech", "retag", "Classifies abstract uncountable noun 'Beauty' functioning as subject of clause."),
    5: (3, "Parts of Speech (Adverb)", "english/grammar/parts-of-speech", "retag", "Classifies temporal adverb 'after' modified by degree adverb 'soon'."),
    6: (3, "Prepositions of Place", "english/grammar/prepositions", "retag", "Tests spatial preposition 'across' indicating position on the opposite side of river."),
    7: (3, "Prepositions of Cause / Agency", "english/grammar/prepositions", "retag", "Tests agentive preposition 'by' denoting destructive element ('destroyed by fire')."),
    8: (3, "Prepositions of Place", "english/grammar/prepositions", "retag", "Tests idiomatic spatial preposition 'under' ('under the same roof')."),
    9: (3, "Prepositions of Position / Law", "english/grammar/prepositions", "retag", "Tests formal preposition 'before' denoting in the presence of court / magistrate."),
    10: (3, "Prepositions of Time", "english/grammar/prepositions", "retag", "Tests temporal preposition 'since' specifying starting point in past ('since Friday last')."),
    # Page 4: Q11-Q22
    11: (4, "Subject-Verb Agreement", "english/grammar/subject-verb-agreement", "retag", "Applies agreement rule: parenthetical addition 'as well as Korean' does not affect singular subject 'French' -> 'was'."),
    12: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past perfect aspect ('had left') completed prior to arrival at station."),
    13: (4, "Tenses & Verb Forms (Subjunctive)", "english/grammar/tenses", "retag", "Tests counterfactual past wish ('I wish he had told me...') with conditional perfect consequence."),
    14: (4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests future perfect aspect ('will have used') anchored by temporal clause 'By the time the project finishes'."),
    15: (4, "Tenses & Verb Forms (Inversion)", "english/grammar/tenses", "retag", "Tests negative inversion with past perfect ('Scarcely had the bell rung when...')."),
    16: (4, "Pronouns (Distributive)", "english/grammar/parts-of-speech", "retag", "Tests distributive singular pronoun 'Each' governing singular verb 'is'."),
    17: (4, "Pronouns (Indefinite)", "english/grammar/parts-of-speech", "retag", "Tests pronoun concord: indefinite pronoun 'One' requires possessive 'one's'."),
    18: (4, "Pronouns (Interrogative)", "english/grammar/parts-of-speech", "retag", "Tests objective case interrogative pronoun 'Whom' functioning as object of meet."),
    19: (4, "Pronouns (Personal Case)", "english/grammar/parts-of-speech", "retag", "Tests objective pronoun case 'me' following governing preposition 'Between'."),
    20: (4, "Pronouns (Agreement)", "english/grammar/parts-of-speech", "retag", "Tests singular pronoun agreement 'he' following distributive subject 'Neither of the two brothers'."),
    21: (4, "Spotting Errors (Redundant Preposition)", "english/sentence-correction", "retag", "Detects incorrect prepositional phrasing: 'Despite of' -> 'Despite' / 'In spite of'."),
    22: (4, "Spotting Errors (Subject-Verb Agreement)", "english/sentence-correction", "retag", "Detects subject-verb agreement error: singular subject 'The professor' requires 'is conducting'."),
    # Page 5: Q23-Q34
    23: (5, "Spotting Errors (Pronoun Concord)", "english/sentence-correction", "retag", "Detects agreement error: distributive subject 'Each' requires singular verb 'has received'."),
    24: (5, "Spotting Errors (Negative Inversion)", "english/sentence-correction", "retag", "Detects faulty inversion: correlative 'No sooner' requires auxiliary inversion 'No sooner had the meeting begun'."),
    25: (5, "Spotting Errors (Redundancy)", "english/sentence-correction", "retag", "Detects tautological error: 'The reason why... was because' -> 'The reason why... was that'."),
    26: (5, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests academic verb choice ('replicate / verify') in scientific experimental validation."),
    27: (5, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests descriptive adjective choice ('ambiguous / equivocal') characterizing political oratory."),
    28: (5, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests descriptive adjective choice ('lucid / clear') describing pedagogical explanations."),
    29: (5, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests investigative verb choice ('unravel / deduce') in criminal detection."),
    30: (5, "Vocabulary & Word Choice", "english/vocabulary", "retag", "Tests adjective choice ('unequivocal / conclusive') describing decisive executive rulings."),
    31: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests noun 'somnambulist' for a person who walks during sleep."),
    32: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests adjective/noun 'extempore' / 'impromptu' for speech delivered without prior preparation."),
    33: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests noun 'atheist' denoting a person who rejects the existence of God."),
    34: (5, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests noun 'aviary' denoting an enclosure for housing birds."),
    # Page 6: Q35, Q36, Q41-Q43
    35: (6, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests linguistic term 'palindrome' for word or phrase reading identically forwards and backwards."),
    36: (6, "Spelling Test", "english/vocabulary", "retag", "Identifies misspelled word 'Embelish' (correct: 'Embellish')."),
    41: (6, "Sentence Sequencing (Jumbled Sentences)", "english/grammar", "keep", "Confirms exact active topic for cohesive narrative ordering on visiting the park (CABD)."),
    42: (6, "Sentence Sequencing (Jumbled Sentences)", "english/grammar", "keep", "Confirms exact active topic for cohesive chronological sequencing on Tom getting ready late."),
    43: (6, "Sentence Sequencing (Jumbled Sentences)", "english/grammar", "keep", "Confirms exact active topic for cohesive thematic sequencing on Eve's passion for landscape painting."),
    # Page 7: Q44-Q46, Q51-Q52
    44: (7, "Sentence Sequencing (Jumbled Sentences)", "english/grammar", "keep", "Confirms exact active topic for cohesive event sequencing on beach outing (BACD)."),
    45: (7, "Sentence Sequencing (Jumbled Sentences)", "english/grammar", "keep", "Confirms exact active topic for narrative paragraph sequencing on afternoon summer heat."),
    46: (7, "Sentence Structure", "english/sentence-correction", "retag", "Identifies complete grammatical independent clause: 'The boy plays football every evening.'"),
    51: (7, "Correlative Inversion", "english/grammar", "keep", "Confirms exact active topic for correlative pair 'No sooner had I reached... than the train left.'"),
    52: (7, "Conditional Inversion", "english/grammar", "keep", "Confirms exact active topic for inverted third conditional 'Had it not been for... the situation would have worsened.'"),
    # Page 8: Q53-Q60
    53: (8, "Negative Inversion", "english/grammar", "keep", "Confirms exact active topic for restrictive temporal inversion 'Not until the investigation was completed did the truth come to light.'"),
    54: (8, "Inversion Structure", "english/grammar", "keep", "Confirms exact active topic for focus inversion 'Only after years of training was he able to master the skill.'"),
    55: (8, "Negative Inversion", "english/grammar", "keep", "Confirms exact active topic for negative focus inversion 'Little did they realize...'"),
    56: (8, "Sentence Transformation (Conditionals)", "english/grammar", "keep", "Confirms exact active topic for transforming causal clause into conditional statement."),
    57: (8, "Sentence Transformation (Conditionals)", "english/grammar", "keep", "Confirms exact active topic for transforming consequence statement into counterfactual conditional."),
    58: (8, "Sentence Transformation (Conditionals)", "english/grammar", "keep", "Confirms exact active topic for transforming imperative requirement into conditional structure."),
    59: (8, "Sentence Transformation (Conditionals)", "english/grammar", "keep", "Confirms exact active topic for transforming negative causal clause into conditional statement."),
    60: (8, "Sentence Transformation (Conditionals)", "english/grammar", "keep", "Confirms exact active topic for transforming adverbial result clause into conditional statement.")
}

candidates = []
findings = []

breakdown = {}
action_counts = {"retag": 0, "keep": 0}

for it in packet["items"]:
    qn = int(it["appearance"]["qnum"])
    page, skill, path_str, action, rationale = specs[qn]
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
        "batch_id": 42,
        "policy": "study-tagging-v1"
    }
    candidates.append(cand)
    
    finding = {
        "index": len(candidates),
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "printed_question": f"Q{qn}",
        "physical_page": page,
        "tested_skill": skill,
        "current_path": cur_path,
        "proposed_path": prop_path,
        "action": action,
        "rationale": rationale
    }
    findings.append(finding)

assert len(candidates) == 52
assert len(findings) == 52

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Preserved written tasks from Section A and dropped OCR MCQs
written_intake = [
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - A (Conventional Type) (40 Marks)",
        "question_number": "1",
        "physical_page": 2,
        "marks": 10,
        "task_type": "précis_writing",
        "prompt": "Read the following passage carefully and write a precis in about one third of its length. Suggest a suitable title.",
        "source_context": "In the modern world, money is often seen as the ultimate measure of success and security... (approx 350 words on money vs happiness and fulfillment).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional written descriptive précis composition task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - A (Conventional Type) (40 Marks)",
        "question_number": "2",
        "physical_page": 2,
        "marks": 15,
        "task_type": "formal_complaint_letter",
        "prompt": "Write a letter to the Engineer in Chief, Power and Electricity Department complaining about the frequent breakdown of electricity in your locality. Sign yourself as Engliana.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional formal grievance and complaint letter drafting task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - A (Conventional Type) (40 Marks)",
        "question_number": "3",
        "physical_page": 2,
        "marks": 15,
        "task_type": "reading_comprehension",
        "prompt": "Read the following passage carefully and answer the question that follows: Comprehensive text on Exercise and Health, with sub-questions (a) to (j) totaling 15 marks.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive reading comprehension passage with fill-in-the-blank, vocabulary, and short-answer prompts, excluded from automated MCQ database ingestion."
    },
    # Dropped OCR MCQs due to consecutive empty stems under direction headers
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - B (Multiple Choice questions)",
        "question_number": "37",
        "physical_page": 6,
        "marks": 1,
        "task_type": "mcq_spelling_test",
        "prompt": "Select the incorrectly spelt word: (a) Ineffable (b) Connoisseur (c) Belligerant (d) Idiosyncrasy",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": None
        },
        "reason_unextracted": "Dropped by automated OCR ingestion due to empty question stem under Direction (Question Nos 36-40)."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - B (Multiple Choice questions)",
        "question_number": "38",
        "physical_page": 6,
        "marks": 1,
        "task_type": "mcq_spelling_test",
        "prompt": "Select the incorrectly spelt word: (a) Dilemma (b) Entrepreneur (c) Exhuberant (d) Surreptitious",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": None
        },
        "reason_unextracted": "Dropped by automated OCR ingestion due to empty question stem under Direction (Question Nos 36-40)."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - B (Multiple Choice questions)",
        "question_number": "39",
        "physical_page": 6,
        "marks": 1,
        "task_type": "mcq_spelling_test",
        "prompt": "Select the incorrectly spelt word: (a) Onomatopoeia (b) Precipituous (c) Parsimonious (d) Quintessential",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": None
        },
        "reason_unextracted": "Dropped by automated OCR ingestion due to empty question stem under Direction (Question Nos 36-40)."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - B (Multiple Choice questions)",
        "question_number": "40",
        "physical_page": 6,
        "marks": 1,
        "task_type": "mcq_spelling_test",
        "prompt": "Select the incorrectly spelt word: (a) Hambouyant (b) Convalescence (c) Harangue (d) Eccentricity",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": None
        },
        "reason_unextracted": "Dropped by automated OCR ingestion due to empty question stem under Direction (Question Nos 36-40)."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - B (Multiple Choice questions)",
        "question_number": "47",
        "physical_page": 7,
        "marks": 1,
        "task_type": "mcq_sentence_structure",
        "prompt": "Choose the correct sentence structure: (a) Although he was tired, but he continued working. (b) Although he was tired, yet he continued working. (c) Although he was tired, he continued working. (d) Although he was tired but he continued working.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/sentence-correction",
            "subtopic_id": None
        },
        "reason_unextracted": "Dropped by automated OCR ingestion due to empty question stem under Direction (Question Nos 46-50)."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - B (Multiple Choice questions)",
        "question_number": "48",
        "physical_page": 7,
        "marks": 1,
        "task_type": "mcq_sentence_structure",
        "prompt": "Choose the correct sentence structure: (a) No sooner had he left than it started raining. (b) No sooner he had left than it started raining. (c) No sooner had he left when it started raining. (d) No sooner he left than it started raining.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/sentence-correction",
            "subtopic_id": None
        },
        "reason_unextracted": "Dropped by automated OCR ingestion due to empty question stem under Direction (Question Nos 46-50)."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - B (Multiple Choice questions)",
        "question_number": "49",
        "physical_page": 7,
        "marks": 1,
        "task_type": "mcq_sentence_structure",
        "prompt": "Choose the correct sentence structure: (a) She insisted me to join the team. (b) She insisted on me joining the team. (c) She insisted that I join the team. (d) She insisted that I should joining the team.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/sentence-correction",
            "subtopic_id": None
        },
        "reason_unextracted": "Dropped by automated OCR ingestion due to empty question stem under Direction (Question Nos 46-50)."
    },
    {
        "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
        "section": "SECTION - B (Multiple Choice questions)",
        "question_number": "50",
        "physical_page": 7,
        "marks": 1,
        "task_type": "mcq_sentence_structure",
        "prompt": "Choose the correct sentence structure: (a) She prefers coffee than tea. (b) She prefers coffee more than tea. (c) She prefers coffee over tea. (d) She prefers coffee to tea.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/sentence-correction",
            "subtopic_id": None
        },
        "reason_unextracted": "Dropped by automated OCR ingestion due to empty question stem under Direction (Question Nos 46-50)."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")

summary = {
    "batch": 42,
    "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf",
    "paper_title": "Competitive Examination for Sub-Inspector under Food & Civil Supplies and Receptionist under Health & Family Welfare (May, 2025) — Paper-I General English (Series A)",
    "document_id": "doc_57d09d87766f60d8370e2547",
    "sha256": "e73c6416cb247a5ca6b7bcf96c9bbe3f5580a9b45eb59d921dd2d3c66f7df0ba",
    "single_booklet_enforced": True,
    "bypassed_duplicates": [
        {
            "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series B)..pdf",
            "document_id": "doc_ae75dbff924cd9f1cda167dc",
            "sha256": "ece288220ff9d80baf26373c3d25e4f114480ddf7642e6d4726dd039801bdcc4",
            "reason": "Permuted Series B booklet (5 MCQs partially ingested) of identical May 2025 examination. Cleanly bypassed under single-booklet deduplication rule."
        },
        {
            "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series C)..pdf",
            "document_id": "doc_a0c489d819810fcb83048888",
            "sha256": "6346e2d87b63300b66c4ea688a6b54d584285faf0f0b8654eda665d1d85d36ad",
            "reason": "Permuted Series C booklet (11 MCQs partially ingested) of identical May 2025 examination. Cleanly bypassed under single-booklet deduplication rule."
        },
        {
            "paper_id": "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series D)..pdf",
            "document_id": "doc_42a5afe2420d8ff997936b63",
            "sha256": "d207f72293d3f5f9354e053fc7b719c5a72cf232cc919c9b5e3d63906371f064",
            "reason": "Permuted Series D booklet (52 MCQs) of identical May 2025 examination. Cleanly bypassed under single-booklet deduplication rule."
        }
    ],
    "targets": 52,
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
