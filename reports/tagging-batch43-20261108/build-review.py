"""Build review packet and findings for Batch 43: 4 Direct English Papers (81 items)."""
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

# Proposals mapped by appearance_id
proposals = {
    # --- PAPER 1: Sericulture Extension Officer (20 MCQs) ---
    "060b153c333c776ed695": ("Q3(ii)", 2, "Reading Comprehension (Inference)", "english/comprehension", "retag", "Rectifies sociology misclassification: evaluates passage illustration of class factor in political aspirations."),
    "0f2efc166cd1a45ce30e": ("Q9(ii)", 4, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests noun 'cynic' denoting one who sneers at the aims and beliefs of fellow human beings."),
    "1c514f5ff4569b8bc5be": ("Q9(v)", 4, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests linguistic term 'phonetics' for the scientific study of speech sounds."),
    "245afa38cc774208e97a": ("Q7(i)", 3, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'persuasions' ('beliefs / convictions') in sociopolitical context."),
    "262fc3ecfa1611b3c6ce": ("Q8(iv)", 3, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'deft' ('clumsy / awkward')."),
    "3baac9088b13d441d136": ("Q3(i)", 2, "Reading Comprehension (Detail)", "english/comprehension", "retag", "Analyzes phrase meaning 'Fusion of political and communal aspirations' within passage context."),
    "4dfaea29ef601088b0c9": ("Q3(v)", 2, "Reading Comprehension (Detail)", "english/comprehension", "retag", "Identifies author's proposed solution for tackling communal politics in the passage."),
    "58d37967ab26fc405e2c": ("Q8(ii)", 3, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'dejected' ('cheerful / elated')."),
    "5b9ff598c3fdb7e791e9": ("Q8(i)", 3, "Antonyms", "english/vocabulary/antonyms", "keep", "Confirms exact active subtopic for antonym of 'delayed' ('expedited / hastened')."),
    "5c5ecfe6f4c0ccacc137": ("Q7(v)", 3, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'pernicious' ('harmful / destructive')."),
    "6bc2da81e698f98196b1": ("Q8(v)", 4, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'urbane' ('uncouth / rude')."),
    "813d78961c5a67703031": ("Q9(i)", 4, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests noun 'aesthete' for a person with highly developed sensitivity to beauty and art."),
    "82355a18b3557afa980b": ("Q8(iii)", 3, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'literal' ('figurative / metaphorical')."),
    "948c16c7d4086153f1ba": ("Q3(iii)", 2, "Reading Comprehension (Detail)", "english/comprehension", "retag", "Analyzes political exploitation of religion based on passage arguments."),
    "a9956980a99c4aa137e0": ("Q7(ii)", 3, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'rescind' ('revoke / repeal / annul')."),
    "ab2bb39553e94a8e9e8f": ("Q9(iv)", 4, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests adjective 'gregarious' / 'sociable' for one who enjoys spending time with others."),
    "b0317d5412719411a569": ("Q9(iii)", 4, "One-Word Substitution", "english/vocabulary/one-word-substitution", "retag", "Tests noun 'xenophobia' denoting prejudice or hatred against people from other countries."),
    "b20a33e0b83a2fd34206": ("Q7(iii)", 3, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'frailties' ('weaknesses / foibles')."),
    "d396d0e9221cdaaf42f9": ("Q3(iv)", 2, "Reading Comprehension (Inference)", "english/comprehension", "retag", "Analyzes passage rationale for raising communal feelings to frenzy."),
    "f0b955a387c8f70c7b4e": ("Q7(iv)", 3, "Synonyms", "english/vocabulary/synonyms", "retag", "Tests synonym of 'insatiable' ('unquenchable / voracious')."),

    # --- PAPER 2: Jr. Grade of MES (Combined)-2025 (21 MCQs) ---
    "06771946493982f301d0": ("Q9(i)", 4, "Clause Analysis (Noun Clause)", "english/grammar", "retag", "Identifies dependent noun clause functioning as direct object of reporting verb."),
    "2c1a678b49c512c8d22d": ("Q7(v)", 3, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests present continuous tense aspect ('Listen! John is singing...')."),
    "46c623dab9bc42373bae": ("Q9(iii)", 4, "Clause Analysis (Adverb Clause)", "english/grammar", "keep", "Confirms exact active topic for subordinating adverbial clause of reason / cause."),
    "494fa852165f855d8e31": ("Q2(d)", 2, "Contextual Vocabulary", "english/comprehension", "retag", "Analyzes contextual vocabulary meaning of 'solemn' ('grave / serious') within passage."),
    "574086f66912f125db25": ("Q5(d)", 2, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'Friction' ('harmony / agreement')."),
    "5fe9dc86938802d6c9b6": ("Q5(a)", 2, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'Strident' ('soft / subdued / soothing')."),
    "619cae311910c8f3eaca": ("Q7(iii)", 3, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests subjunctive / modal verb complementation ('It is strange that he should say so')."),
    "6c3d34692ac31ed40ea1": ("Q8(iii)", 3, "Prepositions", "english/grammar/prepositions", "retag", "Tests fixed adjective-preposition collocation 'well-known for'."),
    "6c78a79577576e6f156f": ("Q9(iv)", 4, "Clause Analysis (Adverb Clause)", "english/grammar", "retag", "Identifies subordinating adverbial clause of condition ('If you work hard...')."),
    "820ce16fa09c093881a6": ("Q5(e)", 2, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'Conceptual' ('concrete / physical')."),
    "97bbee8fccbf20aea9c8": ("Q9(ii)", 4, "Clause Analysis (Adjective Clause)", "english/grammar", "retag", "Identifies relative adjective clause modifying antecedent noun ('who won the prize')."),
    "9c16ba8d18286024ca10": ("Q8(ii)", 3, "Prepositions", "english/grammar/prepositions", "retag", "Tests phrasal verb preposition 'looks after' denoting caretaking."),
    "9d440848d5de1226effd": ("Q7(ii)", 3, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past continuous / past habit aspect ('Ram lived / was living in Mumbai for five years')."),
    "a5e22dd0d9ad8357ba30": ("Q5(b)", 2, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'Dank' ('dry / arid')."),
    "aa7d8de7ac1e12bb20c4": ("Q8(iv)", 3, "Prepositions", "english/grammar/prepositions", "retag", "Tests spatial preposition 'through' indicating traversal of examination or passage."),
    "ae7d76bfe8f6bb520f2a": ("Q9(v)", 4, "Clause Analysis (Adverb Clause)", "english/grammar", "retag", "Identifies subordinating adverbial clause of time ('When the bell rang...')."),
    "b2f0ccd797e7cd1f10da": ("Q8(v)", 3, "Prepositions", "english/grammar/prepositions", "retag", "Tests fixed verb-preposition collocation 'cautioned against' governing noun complement."),
    "b807b98510ed257d004b": ("Q5(c)", 2, "Antonyms", "english/vocabulary/antonyms", "retag", "Tests antonym of 'Component' ('whole / entirety')."),
    "c4938036f69e62f5c291": ("Q8(i)", 3, "Prepositions", "english/grammar/prepositions", "retag", "Tests fixed adjective-preposition collocation 'proud of'."),
    "dad7532ab64f004a58ca": ("Q7(iv)", 3, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past continuous aspect ('One clown was balancing a ball while another was juggling')."),
    "ffc9b0521ca0b6518086": ("Q7(i)", 3, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests present continuous aspect ('Be quiet! The baby is sleeping')."),

    # --- PAPER 3: Jr. Grade of MPE & SS (30 MCQs) ---
    "f9bf78a7613297513c97": ("Q1", 2, "Clause Analysis (Adjective Clause)", "english/grammar", "retag", "Identifies defining relative clause 'who topped the examination'."),
    "dd873cfefd0189a67752": ("Q2", 2, "Clause Analysis (Adverb Clause)", "english/grammar", "retag", "Identifies adverbial clause of purpose 'so that no one could notice her absence'."),
    "78e7d0bae2eb30f02b04": ("Q3", 2, "Clause Analysis (Noun Clause)", "english/grammar", "retag", "Identifies interrogative noun clause 'where the treasure had been hidden'."),
    "7857e9369917faa96a49": ("Q4", 2, "Clause Analysis (Adverb / Noun Clause)", "english/grammar", "retag", "Identifies clause of reason 'why I refused the offer'."),
    "4ac43b0fc8f64b7a23bd": ("Q5", 2, "Clause Analysis (Adverb Clause of Manner)", "english/grammar", "retag", "Identifies modal adverbial clause of manner 'as if he owned the entire company'."),
    "283045328a0236d3cf49": ("Q6", 2, "Subject-Verb Agreement", "english/grammar/subject-verb-agreement", "retag", "Tests agreement: parenthetical 'along with his friends' does not change singular subject 'He' -> 'is going'."),
    "5c73c09648a19b5824ed": ("Q7", 2, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests future perfect aspect ('will have already left') with temporal anchor 'By the time we reach'."),
    "ba8ad9fbeb37b116d775": ("Q8", 2, "Tenses & Verb Forms (Subjunctive)", "english/grammar/tenses", "retag", "Tests subjunctive past tense complement ('I'd rather you did not discuss...') following preference idiom."),
    "c901010d6c633f144256": ("Q9", 2, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests present perfect / duration aspect ('has worked / has been working') following concessive clause."),
    "ff44043eb83d07345252": ("Q10", 2, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests passive future perfect aspect ('will have been completed') before new director takes office."),
    "8504b26eefda5c84b992": ("Q11", 3, "Parts of Speech (Pronoun)", "english/grammar/parts-of-speech", "retag", "Classifies indefinite pronoun 'One' serving as subject of modal statement."),
    "c0881c4201ce9521aaf0": ("Q12", 3, "Parts of Speech (Adjective)", "english/grammar/parts-of-speech", "retag", "Classifies qualitative adjective 'wise' modifying subject noun 'king'."),
    "c4aaca73dff8ac6bcb2d": ("Q13", 3, "Parts of Speech (Conjunction)", "english/grammar/parts-of-speech", "retag", "Classifies conjunctive adverb / adversative connective 'however' joining contrasting clauses."),
    "b8920e82ecf7c0729f10": ("Q14", 3, "Parts of Speech (Interjection)", "english/grammar/parts-of-speech", "retag", "Classifies emotional interjection 'Hurrah!' expressing exultant triumph."),
    "cf6d8c1703f96714868c": ("Q15", 3, "Parts of Speech (Verb)", "english/grammar/parts-of-speech", "retag", "Classifies past participle verb form 'borne' (from bear) in past perfect construction."),
    "51871a61d0e7b4b3c604": ("Q16", 3, "Prepositions of Place", "english/grammar/prepositions", "retag", "Tests spatial prepositions for city and nation: 'in Aizawl, in India' (or 'at Aizawl in India')."),
    "eb4f99197e561f4bf179": ("Q17", 3, "Prepositions of Direction / Motion", "english/grammar/prepositions", "retag", "Tests dynamic motion preposition 'into' indicating transfer inside a vessel ('into the cup')."),
    "4121e5fbe435ccb1f65c": ("Q18", 3, "Prepositions of Time", "english/grammar/prepositions", "retag", "Tests temporal preposition 'since' governing definite past starting point ('since last week')."),
    "79b173cb65815d0f9dd9": ("Q19", 3, "Prepositions of Time", "english/grammar/prepositions", "retag", "Tests terminal temporal preposition 'until' / 'till' ('stay at the hotel until Sunday')."),
    "58c8851673cc3f8c10d7": ("Q20", 3, "Prepositions of Place", "english/grammar/prepositions", "retag", "Tests spatial preposition 'in' / 'on' ('sitting in an armchair / on a chair')."),
    "3ce8d364f929dfd058b5": ("Q21", 3, "Prepositions of Instrument", "english/grammar/prepositions", "retag", "Tests instrumental preposition 'with' used with inanimate tools ('beaten with a ruler')."),
    "2bc142117c8b899331f4": ("Q22", 3, "Prepositions of Place", "english/grammar/prepositions", "retag", "Tests surface contact preposition 'on' ('put the files on the table')."),
    "dfe9412289f8709aac32": ("Q23", 3, "Prepositions of Duration", "english/grammar/prepositions", "retag", "Tests temporal preposition 'for' indicating duration of time span ('for more than four hours')."),
    "0d936a3b96298893a160": ("Q24", 3, "Prepositions of Time", "english/grammar/prepositions", "retag", "Tests deadline preposition 'by' indicating no later than ('finish my work by evening')."),
    "1c0a55b887c6e5794f0d": ("Q25", 3, "Prepositions of Relative Position", "english/grammar/prepositions", "retag", "Tests vertical level preposition 'above' / 'below' ('tenants living above our floor')."),
    "0644600aafabe24780c9": ("Q26", 4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests simple present habitual aspect ('teaches') matching singular subject 'Miss Sarah'."),
    "40c82ca79d1f382dd6b3": ("Q27", 4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past continuous aspect ('was crossing') interrupted by simple past shout."),
    "1e6a8396f432b457a2c0": ("Q28", 4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests past perfect continuous / past perfect aspect ('had studied / studied') prior to examination."),
    "c140e4804eac32910d1e": ("Q29", 4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests simple past sequence of completed actions in narrative ('arrived, we found')."),
    "48cf9df0255360f1a8a3": ("Q30", 4, "Tenses & Verb Forms", "english/grammar/tenses", "retag", "Tests future perfect aspect ('will have finished') anchored by deadline 'by the end of the month'."),

    # --- PAPER 4: Group B(NG) Technical (10 composite items) ---
    "0a72d95346e4dc34cf70": ("QW1", 1, "Précis Writing", "english/writing/precis", "retag", "Conventional task: Summarize reading passage in approximately one-third length with title."),
    "2e20710db59c4f98b1ac": ("QW2", 1, "Reading Comprehension", "english/comprehension", "retag", "Descriptive task: Reading comprehension passage analysis and short-answer prompts."),
    "5f340d55b7148b02391d": ("QW4", 2, "Letter Writing", "english/writing/letter", "retag", "Conventional formal letter drafting to public authorities regarding civic/community issues."),
    "0108398f9c91dcbdc4ea": ("QW5", 2, "Prepositions (Multi-part)", "english/grammar/prepositions", "retag", "Evaluates multi-sentence blanks testing appropriate prepositions of place, time, and agency."),
    "167b49e587e70d26192d": ("QW6", 2, "Tenses & Verb Forms (Multi-part)", "english/grammar/tenses", "retag", "Evaluates multi-sentence blanks testing correct verb inflections and tense sequences."),
    "ac1092e4ca216fa8940d": ("QW7", 3, "Voice Transformation (Multi-part)", "english/grammar/voice", "retag", "Evaluates active-to-passive and passive-to-active sentence transformations."),
    "f422b6d7a13d5f6f196a": ("QW8", 3, "Reported Speech (Multi-part)", "english/grammar/reported-speech", "retag", "Evaluates direct-to-indirect and indirect-to-direct narration transformations."),
    "e4327ab35f337a2d64fb": ("QW9", 3, "One-Word Substitution & Usage", "english/vocabulary/one-word-substitution", "retag", "Evaluates one-word substitution selection and sentence contextual usage."),
    "88d8242ada801c393edc": ("QW10", 4, "Synonyms (Multi-part)", "english/vocabulary/synonyms", "retag", "Evaluates multiple lexical items for exact or closest synonyms."),
    "c12096dd9b36af0c6ad6": ("QW11", 4, "Antonyms (Multi-part)", "english/vocabulary/antonyms", "retag", "Evaluates multiple lexical items for exact opposite antonyms.")
}

candidates = []
findings = []

breakdown = {}
action_counts = {"retag": 0, "keep": 0}

for it in packet["items"]:
    aid = it["appearance_id"]
    qn_str, page, skill, path_str, action, rationale = proposals[aid]
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
        "batch_id": 43,
        "policy": "study-tagging-v1"
    }
    candidates.append(cand)
    
    finding = {
        "index": len(candidates),
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "printed_question": qn_str,
        "physical_page": page,
        "tested_skill": skill,
        "current_path": cur_path,
        "proposed_path": prop_path,
        "action": action,
        "rationale": rationale
    }
    findings.append(finding)

assert len(candidates) == 81
assert len(findings) == 81

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Preserved written conventional tasks
written_intake = [
    {
        "paper_id": "Old_Questions/Direct_2025-2027/General English..pdf",
        "section": "Section-A (Conventional Tasks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 10,
        "task_type": "précis_writing",
        "prompt": "Write a précis of the following passage and give a suitable title: Passage on sericulture and natural silk production.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis composition task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/General English..pdf",
        "section": "Section-A (Conventional Tasks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "formal_complaint_letter",
        "prompt": "Write a complaint to the Director of Sericulture Department, Mizoram regarding supply of defective silkworm seeds. Sign as XYZ.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional formal grievance and complaint letter drafting task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Jr. Grade of MES (Combined)-2025 - General English..pdf",
        "section": "Section-A (Conventional Tasks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 20,
        "task_type": "essay_writing",
        "prompt": "Write an essay on any one of the following: Technological Innovations in Modern Engineering; Renewable Energy Sources in Hill States; Sustainable Urban Development.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional argumentative essay writing task with topic options, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Jr. Grade of MPE & SS, General English..pdf",
        "section": "Section-A (Conventional Tasks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 20,
        "task_type": "essay_writing",
        "prompt": "Write an essay on any one of the following: Economic Planning and Sustainable Growth; Role of Statistics in Policy Formulation; Demographic Challenges in India.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional argumentative essay writing task with socioeconomic topic choices, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Jr. Grade of MPE & SS, General English..pdf",
        "section": "Section-A (Conventional Tasks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "précis_writing",
        "prompt": "Write the precis of the following passage in about one-third of its original length: Comprehensive text on statistical analysis and economic forecasting.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis composition task, excluded from automated MCQ database ingestion."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")

summary = {
    "batch": 43,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2025-2027/General English..pdf",
            "paper_title": "Competitive Examination for the Post of Sericulture Extension Officer — General English",
            "document_id": "doc_3e7d37598a061cd1d52da2ad",
            "sha256": "bd1cc994fe5114678f1effe579d1d78826c7af67750d22041ed92b0736d79f69",
            "targets": 20
        },
        {
            "paper_id": "Old_Questions/Direct_2025-2027/Jr. Grade of MES (Combined)-2025 - General English..pdf",
            "paper_title": "Technical Competitive Examination for Junior Grade of Mizoram Engineering Service (Combined) — General English",
            "document_id": "doc_682ab0cad0fd9c4e525e91a9",
            "sha256": "bd2c02c41f1ba5d56c7fda32b8a7567f0b0e705ecb4f4821093a436be58ec2c1",
            "targets": 21
        },
        {
            "paper_id": "Old_Questions/Direct_2025-2027/Jr. Grade of MPE & SS, General English..pdf",
            "paper_title": "General Competitive Examination for Recruitment to the Post of Junior Grade of Mizoram Planning, Economic & Statistical Service — General English",
            "document_id": "doc_895b0f62c2314d435e125458",
            "sha256": "05ecdd81bffbdbbd8717d207dee80c03e3d26f80883b1ad53e61083594129807",
            "targets": 30
        },
        {
            "paper_id": "Old_Questions/Direct_NG_2024-2027/Group B(NG) (Technical)Paper-I (General English)-2024..pdf",
            "paper_title": "Group B(NG) (Technical) Paper-I (General English)-2024",
            "document_id": "doc_d50623457f36f5aeab231741",
            "sha256": "40b8b1fe611a4c55604040790fdb9befc1294bde19b3a3e0daf101655de236fc",
            "targets": 10
        }
    ],
    "targets": 81,
    "completion": "100% of extracted items reviewed across all 4 booklets",
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
