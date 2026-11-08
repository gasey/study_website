"""Build review packet and findings for Batch 50: Direct 2014-2026 General English Booklets (70 MCQs & Tasks)."""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

def parse_path(path_str):
    if not path_str:
        return {"subject_id": "english", "topic_id": None, "subtopic_id": None}
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
    # --- PAPER 1: 1.General English Paper-I (FEO).pdf (32 items) ---
    "1c008b720da263aadd6a": ("Q1", 2, "Vocabulary in context (terribly sorry)", "english/vocabulary", "retag", "Selects contextually appropriate intensifier adverb 'terribly' denoting deep regret."),
    "d9767761219b3defafeb": ("Q2", 2, "Vocabulary in context (professionalism)", "english/vocabulary", "retag", "Selects abstract noun 'professionalism' denoting workplace competence and decorum."),
    "20fc4a56dfccf7cc866d": ("Q3", 2, "Vocabulary in context (work hard)", "english/vocabulary", "retag", "Selects manner adverb 'hard' distinguishing effort from adverb 'hardly'."),
    "b4a7e33bed0516a423aa": ("Q4", 2, "Vocabulary in context (death of best friend)", "english/vocabulary", "retag", "Selects contextually accurate emotional noun 'death' describing bereavement."),
    "504ada8189727d8625f1": ("Q5", 2, "Parts of Speech (theirs -> possessive pronoun)", "english/grammar/parts-of-speech", "retag", "Selects independent possessive pronoun 'theirs' distinguishing from determiners."),
    "76ff4b79434e727e848d": ("Q6", 2, "Tenses (goes for a walk)", "english/grammar/tenses", "retag", "Selects simple present tense 'goes' indicating regular daily habitual action."),
    "c77e015259617d3be4bf": ("Q7", 2, "Parts of Speech (cheaper -> comparative adjective)", "english/grammar/parts-of-speech", "retag", "Selects inflected comparative adjective 'cheaper' modifying noun phrase."),
    "b99652447190685f3a99": ("Q8", 2, "Parts of Speech (preferable/superior -> Latin comparative)", "english/grammar/parts-of-speech", "retag", "Selects Latin comparative adjective requiring preposition 'to'."),
    "0d682cca6fdc02fa073e": ("Q9", 2, "Parts of Speech (Although -> concessive conjunction)", "english/grammar/parts-of-speech", "retag", "Selects concessive subordinating conjunction 'Although' introducing contrastive clause."),
    "bf08550c02e40e3bb0cf": ("Q10", 2, "Prepositions (beside me on the train)", "english/grammar/prepositions", "retag", "Selects spatial proximity preposition 'beside' distinguishing from adverb 'besides'."),
    "037ef98dd5e48ba0ec2d": ("Q11", 2, "Prepositions (above mine)", "english/grammar/prepositions", "retag", "Selects spatial vertical preposition 'above' describing higher apartment level."),
    "4eb201cc5c7eac06fb6a": ("Q12", 2, "Parts of Speech (therefore -> conjunctive adverb)", "english/grammar/parts-of-speech", "retag", "Selects illative conjunctive adverb 'therefore' expressing logical consequence."),
    "377480301440d5fb0b73": ("Q13", 2, "Parts of Speech (Since -> temporal conjunction)", "english/grammar/parts-of-speech", "retag", "Selects temporal subordinating conjunction 'Since' marking duration from event."),
    "22dc5486749810a93098": ("Q14", 2, "Prepositions (look into -> investigate)", "english/grammar/prepositions", "retag", "Selects phrasal preposition 'into' completing verb 'look into' meaning investigate."),
    "cda92e9fb62f78cba40e": ("Q15", 2, "Prepositions (ran into/across -> meet unexpectedly)", "english/grammar/prepositions", "retag", "Selects preposition completing phrasal verb meaning encountering someone by chance."),
    "d5d16aa7863c2bcd3bbf": ("Q16", 2, "Prepositions (cared about/for)", "english/grammar/prepositions", "retag", "Selects dependent preposition following negative psychological verb 'cared'."),
    "eec63db18351d11cffa9": ("Q17", 3, "One-Word Substitution (piracy)", "english/vocabulary/one-word-substitution", "retag", "Identifies legal/intellectual property term 'piracy' for unauthorized reproduction."),
    "ff2e20e32629e022ed9f": ("Q18", 3, "One-Word Substitution (pro bono)", "english/vocabulary/one-word-substitution", "retag", "Identifies Latin legal phrase 'pro bono' for voluntary professional work without fee."),
    "8191f912c628ebf74083": ("Q19", 3, "One-Word Substitution (nepotism)", "english/vocabulary/one-word-substitution", "retag", "Identifies political/administrative term 'nepotism' for patronage bestowed on relatives."),
    "24df4a961db841c3da3d": ("Q20", 3, "One-Word Substitution (autocracy)", "english/vocabulary/one-word-substitution", "retag", "Identifies political system term 'autocracy' for governance by a single ruler with absolute power."),
    "192bc581a88e1801723a": ("Q21", 3, "One-Word Substitution (behemoth)", "english/vocabulary/one-word-substitution", "retag", "Identifies descriptive term 'behemoth' denoting a monstrous, colossal creature or entity."),
    "3df42a31a288f39019f6": ("Q22", 3, "One-Word Substitution (trolling)", "english/vocabulary/one-word-substitution", "retag", "Identifies digital communication term 'trolling' for intentionally provoking online hostility."),
    "497c73e99f542dcfd061": ("Q23", 3, "One-Word Substitution (metamorphosis)", "english/vocabulary/one-word-substitution", "retag", "Identifies biological/transformational term 'metamorphosis' for complete change of form."),
    "9459941fa226071d8b6f": ("Q24", 3, "One-Word Substitution (exodus)", "english/vocabulary/one-word-substitution", "retag", "Identifies historical/sociological term 'exodus' for mass departure or emigration of people."),
    "270e326232823b6f6271": ("Q25", 3, "Vocabulary in context (burdensome)", "english/vocabulary", "retag", "Selects contextual adjective 'burdensome' characterizing heavy dependency obligations."),
    "79d2879209be559a74c6": ("Q26", 3, "Vocabulary in context (defusing awkward situations)", "english/vocabulary", "retag", "Selects diplomatic verb 'defusing' denoting calming or resolving tense interpersonal situations."),
    "27751fb48fbf3fac6c6e": ("Q27", 4, "Vocabulary in context (plunged into fountain)", "english/vocabulary", "retag", "Selects dynamic movement verb 'plunged' denoting diving or jumping vigorously into water."),
    "025fec0000c1b02ea3d5": ("Q28", 4, "Vocabulary in context (series of painful events)", "english/vocabulary", "retag", "Selects noun 'series' describing a connected chronological progression of life events."),
    "ef5357f48f18fbb22038": ("Q29", 4, "Vocabulary in context (craving sweets)", "english/vocabulary", "retag", "Selects psychological desire verb 'craving' following withdrawal from tobacco."),
    "568a75ea83d07015661e": ("Q30", 4, "Vocabulary in context (negligible contribution)", "english/vocabulary", "retag", "Selects quantitative adjective 'negligible' denoting an insignificantly small contribution."),
    "11a59686b3760a4b6fed": ("Q31", 4, "Vocabulary in context (illegible handwriting)", "english/vocabulary", "retag", "Selects adjective 'illegible' distinguishing unreadable script from 'illegal' and 'ineligible'."),
    "8218752c3f7034b29232": ("Q32", 4, "Vocabulary / Idiom (knows no bounds)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiomatic collocation 'knows no bounds' meaning unlimited and excessive."),

    # --- PAPER 2: Inspector of Statistics- General English- 2017 (12 items) ---
    "cda553be0c3a9b36224d": ("Q1", 2, "Idioms & Phrases (snap one's finger)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'snap one's fingers at' meaning showing defiance, contempt, or disregard."),
    "desc-9be08f51aac4f699040a": ("Q1", 1, "Essay writing (Problems of Youth / Population / Women Education / Science)", "english/writing/essay", "retag", "Conventional descriptive essay composition task with 4 sociodemographic topics."),
    "cf87e31516d06fa3534d": ("Q2", 2, "Idioms & Phrases (French leave)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'French leave' meaning unauthorized absence or departure without permission."),
    "desc-d5c6a2a0173a61aaf5b2": ("Q2", 1, "Précis writing (True education & character formation)", "english/writing/precis", "retag", "Conventional descriptive précis condensation task on true education, moral courage, and character."),
    "93d5733e6977f12bb1d1": ("Q3", 2, "Idioms & Phrases (Adam's ale)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets humorous idiom 'Adam's ale' meaning unadulterated pure water."),
    "31ce46bafb9f4623bae7": ("Q4", 2, "Idioms & Phrases (Sum and substance)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets binomial idiom 'sum and substance' meaning the core essence or summary."),
    "fefff41af560e922cf0f": ("Q5", 2, "Idioms & Phrases (Moot Point)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets legal/academic idiom 'moot point' meaning an open question subject to debate."),
    "3f2f2ba0ba3290e64cea": ("Q6", 2, "Idioms & Phrases (Fits and starts)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'by fits and starts' meaning sporadically, irregularly, and in short bursts."),
    "912c17ed33fdd4ce5912": ("Q7", 2, "Idioms & Phrases (Queer Fish)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets colloquial idiom 'queer fish' meaning an eccentric, strange, or unconventional person."),
    "3601d8e4640461e8a3e4": ("Q8", 2, "Idioms & Phrases (Pell-Mell)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets adverbial idiom 'pell-mell' meaning in hurried, reckless confusion or disorder."),
    "921e9935fb3ec30e2fd8": ("Q9", 3, "Idioms & Phrases (Hole and Corner)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'hole-and-corner' meaning underhand, secretive, and clandestine dealings."),
    "22772902923146b677e8": ("Q10", 3, "Idioms & Phrases (Elbow Grease)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets informal idiom 'elbow grease' meaning vigorous physical hard labor and exertion."),

    # --- PAPER 3: Employment Officer under LE&IT Deptt Gen English Paper-I (7 items) ---
    "6966dd3fe6f49d4c3523": ("Q1", 2, "Idioms & Phrases (Hard-pressed)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets compound adjective idiom 'hard-pressed' meaning under severe financial or temporal strain."),
    "5c95a8880dcd93c9e20e": ("Q2", 2, "Idioms & Phrases (All at sea)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets nautical idiom 'all at sea' meaning in a state of utter confusion or disorientation."),
    "e0ee9ac657ddc11e243a": ("Q3", 2, "Idioms & Phrases (At loggerheads)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'at loggerheads' meaning in strong, intractable disagreement or contention."),
    "08f2bcabad3d8163f7af": ("Q4", 2, "Idioms & Phrases (Throw down the glove)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets chivalric idiom 'throw down the glove/gauntlet' meaning issuing an open challenge."),
    "a04bb042f70995ce5ecf": ("Q5", 2, "Idioms & Phrases (Shoot one's bolt)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets archer idiom 'shoot one's bolt' meaning exhausting all one's resources or final effort."),
    "d695c507d3f8abac450b": ("Q6", 2, "Idioms & Phrases (Carry one's point)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'carry one's point' meaning successfully overcoming opposition to win debate."),
    "a1d69b1643e02bf85a75": ("Q7", 2, "Idioms & Phrases (Drive home)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'drive home' meaning emphasizing a point so forcefully that it cannot be missed."),

    # --- PAPER 4: General English (IoF) (2 items) ---
    "desc-ee48afd6b59724020a10": ("Q1", 1, "Essay writing (Privatization / Industrial Safety / Clean Energy)", "english/writing/essay", "retag", "Conventional descriptive engineering essay composition task with industrial safety and energy topics."),
    "desc-fbb0765804ab9339426d": ("Q2", 1, "Précis writing (Industrial hygiene and factory conditions)", "english/writing/precis", "retag", "Conventional descriptive précis condensation task on industrial hygiene and occupational health."),

    # --- PAPER 5: General English(AEO) (4 items) ---
    "desc-c3408193c4cbabfb2800": ("Q1", 1, "Essay writing (Solid Waste Management / Agriculture / E-Governance)", "english/writing/essay", "retag", "Conventional descriptive agricultural and civic essay composition task with 3 options."),
    "desc-ff74493ccf0f17dec533": ("Q2", 1, "Précis writing (Economic discipline and national development)", "english/writing/precis", "retag", "Conventional descriptive précis condensation task on national economic development and citizen discipline."),
    "desc-997f2d90d9f0aff18e06": ("Q3", 1, "Official drafting (Draft Circular for Finance Department)", "english/writing/letter", "retag", "Formal administrative correspondence drafting a government circular on financial austerity measures."),
    "desc-faf395d175aae1328855": ("Q5", 2, "Sentence expansion (Proverbs & maxims)", "english/writing", "retag", "Conventional idea and proverb expansion task developing moral and philosophical themes."),

    # --- PAPER 6: Inspector under F,CS & CA Dept-2019, General English Paper I (8 items) ---
    "34b57bb9b696f7a58abc": ("Q1", 2, "Reading comprehension (Mass media and modern art connection)", "english/comprehension", "retag", "Analyzes author's argument linking modern visual culture, advertising, and abstract art."),
    "286e014768530b0ae072": ("Q2", 2, "Reading comprehension (Bourgeois art patronage)", "english/comprehension", "retag", "Extracts passage factors explaining why commercial middle classes promoted modern artistic movements."),
    "e4f00466f2a689b64def": ("Q3", 3, "Reading comprehension (Attributes of genuine creative expression)", "english/comprehension", "retag", "Evaluates criteria presented for distinguishing genuine creative impulse from commercial imitation."),
    "740b49c242f70f330ff0": ("Q4", 3, "Passage Synonyms ('apologist' -> defender/advocate)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'defender' for contextual headword 'apologist' within passage."),
    "740106503f18fb0bf719": ("Q5", 3, "Idiomatic phrase in passage ('desert island')", "english/vocabulary/idioms-and-phrases", "retag", "Interprets figurative phrase 'desert island' meaning isolated, solitary existence devoid of culture."),
    "26661d20492612dcc885": ("Q6", 4, "Reading comprehension (Definition of abstract painting)", "english/comprehension", "retag", "Extracts formal aesthetic definition of abstract art as non-representational expression."),
    "93c06e3e2f94db1ca3ac": ("Q7", 4, "Reading comprehension (Concept of bourgeoisie)", "english/comprehension", "retag", "Interprets socio-economic definition of the bourgeoisie in relation to commercial consumerism."),
    "f6aa3172f2441d81f646": ("Q8", 4, "Passage Antonyms (Opposite of 'hypocrisy' -> sincerity)", "english/vocabulary/antonyms", "retag", "Identifies lexical antonym 'sincerity' for contextual noun 'hypocrisy' within passage."),

    # --- PAPER 7: General English Paper-I 2026..pdf (5 written items W1-W5) ---
    "ebf3727aab2396f0e30f": ("Q.W1", 6, "Précis writing (Internet Addiction & neurobiology)", "english/writing/precis", "retag", "Conventional descriptive précis condensation task on compulsive Internet addiction and neuropsychiatric effects."),
    "92c68821974b1d8fa794": ("Q.W2", 6, "Reading comprehension (Scandinavian Ombudsman institution)", "english/comprehension", "retag", "Comprehensive reading comprehension task on the historical evolution, powers, and case investigation of the Swedish Ombudsman."),
    "0e93009878370deea081": ("Q.W3", 7, "Letter writing (Negative influence of misleading advertisements)", "english/writing/letter", "retag", "Formal editorial correspondence task drafting a letter to the Editor of 'The Mizoram Express' on superstitious advertisements."),
    "61b5820fc4fa1645a88e": ("Q.W4", 7, "Voice transformation (Active to Passive across 5 tenses)", "english/grammar/voice", "retag", "Grammatical voice transformation task rewriting 5 sentences from Active to Passive voice."),
    "5b0f06d627ab7b518763": ("Q.W5", 7, "Reported speech transformation (Direct to Indirect Speech)", "english/grammar/reported-speech", "retag", "Grammatical speech transformation task rewriting 5 sentences between Direct and Indirect speech.")
}

assert len(proposals) == 70, f"Expected 70 proposals, got {len(proposals)}"
assert len(packet["items"]) == 70, f"Expected 70 items in packet, got {len(packet['items'])}"

candidates = []
findings = []

for item in packet["items"]:
    aid = item["appearance_id"]
    cid = item["canonical_id"]
    snap = item["snapshot"]
    rec = snap["record"]
    paper = snap["paper"]
    app = item["appearance"]

    prop = proposals.get(aid)
    if not prop:
        raise ValueError(f"Missing proposal for {aid}")
    
    qlabel, page, desc, path, action, rationale = prop
    target_tax = parse_path(path)
    cur_tax = rec.get("classification") or {"subject_id": "english", "topic_id": None, "subtopic_id": None}

    candidate = {
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": paper["id"],
        "source_fingerprint": item["source_fingerprint"],
        "review_status": "pending",
        "action": action,
        "current_primary": cur_tax,
        "proposed_primary": target_tax,
        "rationale": rationale,
        "batch_id": 50,
        "policy": "study-tagging-v1"
    }
    candidates.append(candidate)

    finding = {
        "appearance_id": aid,
        "canonical_id": cid,
        "paper_id": paper["id"],
        "paper_title": paper["title"],
        "question_number": app.get("qnum") or qlabel,
        "physical_page": page,
        "stem_excerpt": (rec.get("question") or "")[:120].strip(),
        "task_description": desc,
        "action": action,
        "current_classification": cur_tax,
        "proposed_classification": target_tax,
        "rationale": rationale
    }
    findings.append(finding)

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Conventional written tasks preserved
written_intake = [
    # Paper 1: 1.General English Paper-I (FEO).pdf
    {
        "paper_id": "Old_Questions/Direct_2014-2018/1.General English Paper-I (FEO).pdf",
        "section": "CONVENTIONAL SECTION (60 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 25,
        "task_type": "essay_writing",
        "prompt": "Write an essay in about 300 words on any one of the following: The role of fisheries in Mizoram's rural economy; Environmental preservation; Importance of sports in education.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive essay composition task with 3 options, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/1.General English Paper-I (FEO).pdf",
        "section": "CONVENTIONAL SECTION (60 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "précis_writing",
        "prompt": "Make a précis of the given passage on scientific agriculture and rural progress, supplying a suitable title.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/1.General English Paper-I (FEO).pdf",
        "section": "CONVENTIONAL SECTION (60 Marks)",
        "question_number": "3",
        "physical_page": 1,
        "marks": 20,
        "task_type": "letter_writing",
        "prompt": "Write a letter to the Director of Fisheries requesting technical assistance and fingerling supplies for cooperative village ponds.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional administrative correspondence task, excluded from automated MCQ database ingestion."
    },

    # Paper 2: Inspector of Statistics- General English- 2017..pdf
    {
        "paper_id": "Old_Questions/Direct_2014-2018/Inspector of Statistics- General English- 2017..pdf",
        "section": "CONVENTIONAL SECTION (40 Marks)",
        "question_number": "3",
        "physical_page": 1,
        "marks": 15,
        "task_type": "letter_writing",
        "prompt": "Write a letter to the Editor of a local newspaper highlighting the urgent necessity of reliable statistical data in state planning.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional editorial letter writing task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/Inspector of Statistics- General English- 2017..pdf",
        "section": "CONVENTIONAL SECTION (40 Marks)",
        "question_number": "4",
        "physical_page": 1,
        "marks": 15,
        "task_type": "proverb_expansion",
        "prompt": "Expand any 3 maxims: (a) Honesty is the best policy (b) Look before you leap (c) Strike while the iron is hot.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional proverb expansion prompt, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/Inspector of Statistics- General English- 2017..pdf",
        "section": "CONVENTIONAL SECTION (40 Marks)",
        "question_number": "5",
        "physical_page": 2,
        "marks": 10,
        "task_type": "sentence_formation_idioms",
        "prompt": "Make sentences with any 5 idioms: At a loss; Break down; Call off; Give up; Look forward to.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional idiomatic sentence composition prompt, excluded from automated MCQ database ingestion."
    },

    # Paper 3: Employment Officer under LE&IT Deptt Gen English Paper-I.pdf
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Employment Officer under LE&IT Deptt Gen English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (86 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 25,
        "task_type": "essay_writing",
        "prompt": "Write an essay on one of the following: Vocational training for youth; Digital employment exchanges; Industrial growth in northeastern states.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive employment essay composition task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Employment Officer under LE&IT Deptt Gen English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (86 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "précis_writing",
        "prompt": "Write a précis of the passage on technological disruption in global labor markets.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Employment Officer under LE&IT Deptt Gen English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (86 Marks)",
        "question_number": "3",
        "physical_page": 1,
        "marks": 15,
        "task_type": "letter_writing",
        "prompt": "Write an official letter to an employer notifying them of compliance obligations regarding employment reporting.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional administrative correspondence task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Employment Officer under LE&IT Deptt Gen English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (86 Marks)",
        "question_number": "5",
        "physical_page": 2,
        "marks": 15,
        "task_type": "proverb_expansion",
        "prompt": "Expand the idea contained in the following passages: (a) Opportunity seldom knocks twice (b) Diligence is the mother of good fortune.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional proverb expansion prompt, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Employment Officer under LE&IT Deptt Gen English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (86 Marks)",
        "question_number": "6",
        "physical_page": 3,
        "marks": 16,
        "task_type": "reading_comprehension_descriptive",
        "prompt": "Read the given passage carefully and answer the questions that follow: Passage on economic planning, human capital investment, and productivity.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive short-answer reading comprehension questions, excluded from automated MCQ database ingestion."
    },

    # Paper 4: General English (IoF).pdf
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English (IoF).pdf",
        "section": "CONVENTIONAL SECTION (60 Marks)",
        "question_number": "3",
        "physical_page": 1,
        "marks": 15,
        "task_type": "letter_writing",
        "prompt": "Write an official inspection letter to a factory management directing rectification of machinery safety guarding deficiencies.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional statutory inspection correspondence task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English (IoF).pdf",
        "section": "CONVENTIONAL SECTION (60 Marks)",
        "question_number": "4",
        "physical_page": 2,
        "marks": 15,
        "task_type": "sentence_formation_idioms",
        "prompt": "Explain any 7 phrases and make sentences with them: In black and white; Iron will; Nip in the bud; On pins and needles; Rule of thumb; Through thick and thin; Turn a deaf ear.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional idiom explanation and sentence composition prompt, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English (IoF).pdf",
        "section": "CONVENTIONAL SECTION (60 Marks)",
        "question_number": "5",
        "physical_page": 2,
        "marks": 15,
        "task_type": "proverb_expansion",
        "prompt": "Expand any 3 maxims: (a) Better safe than sorry (b) Necessity is the mother of invention (c) As you sow, so shall you reap.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional proverb expansion prompt, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English (IoF).pdf",
        "section": "CONVENTIONAL SECTION (60 Marks)",
        "question_number": "6",
        "physical_page": 3,
        "marks": 15,
        "task_type": "reading_comprehension_descriptive",
        "prompt": "Read the passage carefully and answer the questions that follow: Passage on industrial history and labor standards evolution.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional short-answer reading comprehension questions, excluded from automated MCQ database ingestion."
    },

    # Paper 5: General English(AEO).pdf
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English(AEO).pdf",
        "section": "CONVENTIONAL SECTION (30 Marks)",
        "question_number": "4",
        "physical_page": 1,
        "marks": 14,
        "task_type": "sentence_formation_idioms",
        "prompt": "Make sentences with any 7 idioms: Behind the scenes; Close shave; Day in day out; Fair play; Go through fire and water; In a nutshell; Once in a blue moon.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional idiomatic sentence composition prompt, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English(AEO).pdf",
        "section": "CONVENTIONAL SECTION (30 Marks)",
        "question_number": "6",
        "physical_page": 3,
        "marks": 16,
        "task_type": "reading_comprehension_descriptive",
        "prompt": "Read the given passage carefully and answer the questions that follow: Passage on agricultural cooperatives and market access.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive reading comprehension questions, excluded from automated MCQ database ingestion."
    },

    # Paper 6: Inspector under F,CS & CA Dept-2019, General English Paper I.pdf
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Inspector under F,CS & CA Dept-2019, General English Paper I.pdf",
        "section": "CONVENTIONAL SECTION (70 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 25,
        "task_type": "essay_writing",
        "prompt": "Write an essay on any one of the following: Consumer protection rights in India; Food security and public distribution; Role of supply departments in price stabilization.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive consumer affairs essay composition task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Inspector under F,CS & CA Dept-2019, General English Paper I.pdf",
        "section": "CONVENTIONAL SECTION (70 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "précis_writing",
        "prompt": "Write a précis of the given passage on grain storage, food preservation, and supply chain logistics.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Inspector under F,CS & CA Dept-2019, General English Paper I.pdf",
        "section": "CONVENTIONAL SECTION (70 Marks)",
        "question_number": "3",
        "physical_page": 1,
        "marks": 15,
        "task_type": "letter_writing",
        "prompt": "Write an official letter to a retail dealer regarding compliance inspection of weights and measures.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional administrative enforcement letter task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/Inspector under F,CS & CA Dept-2019, General English Paper I.pdf",
        "section": "CONVENTIONAL SECTION (70 Marks)",
        "question_number": "5",
        "physical_page": 2,
        "marks": 15,
        "task_type": "proverb_expansion",
        "prompt": "Expand the idea in any 3 passages: (a) Cut your coat according to your cloth (b) A bird in the hand is worth two in the bush (c) Practice what you preach.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional proverb expansion prompt, excluded from automated MCQ database ingestion."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")

# Summary stats
action_counts = {}
for c in candidates:
    action_counts[c["action"]] = action_counts.get(c["action"], 0) + 1

breakdown = {}
for c in candidates:
    prop = c["proposed_primary"]
    key = prop["subtopic_id"] or prop["topic_id"] or prop["subject_id"]
    breakdown[key] = breakdown.get(key, 0) + 1

summary = {
    "batch": 50,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/1.General English Paper-I (FEO).pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Posts of Fishery Extension Officer - General English",
            "document_id": "doc_197d853e438e227a2ae7f15f",
            "sha256": "66a78c66d2600094e9f3b890a5015b3c3c72714c62b53580436d4f9bf35a0dcb",
            "targets": 32
        },
        {
            "paper_id": "Old_Questions/Direct_2014-2018/Inspector of Statistics- General English- 2017..pdf",
            "paper_title": "Inspector of Statistics - General English",
            "document_id": "doc_08d6b0f9b9e23606217a0ed3",
            "sha256": "892f8621446c137fc908483ba5a9d8cb84c9c1fb7058ccb9aa77f1ff18d61cb1",
            "targets": 12
        },
        {
            "paper_id": "Old_Questions/Direct_2019-2020/Employment Officer under LE&IT Deptt Gen English Paper-I.pdf",
            "paper_title": "Technical Competitive Examinations for Recruitment to the Post of Employment Officer - General English Paper I",
            "document_id": "doc_115a2dd346bc29a73812bf40",
            "sha256": "d9aae7de4fb3ea6868d44747ebc7908b9fdfcf4b971a2e73752e50529d8463c6",
            "targets": 7
        },
        {
            "paper_id": "Old_Questions/Direct_2019-2020/General English (IoF).pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Post of Inspector of Factories - General English",
            "document_id": "doc_7eb8775038672312345754e3",
            "sha256": "79e16ea2e0904dbe4383189e47e30d704d2cc7b116d41829e0eb6a7c4ae6d498",
            "targets": 2
        },
        {
            "paper_id": "Old_Questions/Direct_2019-2020/General English(AEO).pdf",
            "paper_title": "MPSC Technical Competitive Examinations",
            "document_id": "doc_f75f6fa112041692130f684b",
            "sha256": "38ba8b0b6b6795982e5ee6162391ce4d852bf2c554e24ebc6d9bc57662cf05d9",
            "targets": 4
        },
        {
            "paper_id": "Old_Questions/Direct_2019-2020/Inspector under F,CS & CA Dept-2019, General English Paper I.pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Post of Grade-V of Mizoram Food, Civil Supplies & Consumer Affairs Service (Inspector)",
            "document_id": "doc_de0249ac406ac702e8477528",
            "sha256": "6e477cfee196a54f67b55f110759081e7d23f338ff957fc85779ec19d08dd856",
            "targets": 8
        },
        {
            "paper_id": "Old_Questions/Direct_NG_2024-2027/General English Paper-I 2026..pdf",
            "paper_title": "Common Competitive Examination for Group 'B' Non-Gazetted (Technical) - Paper I (General English)",
            "document_id": "doc_7f704f41cc87a988ef58e762",
            "sha256": "5ffb4d4cf3a8a1b6a7a0b3ef50ecb18ec4e1f7dcfbfca022c069b8d4e9d66042",
            "targets": 5
        }
    ],
    "single_booklet_deduplication": {
        "enforced": True,
        "primary_booklet": "Direct_NG_2024-2027/General English Paper-I 2026..pdf reviewed as primary (Series A); Series B, C, and D cleanly bypassed",
        "bypassed_siblings": [
            "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series B)..pdf",
            "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series C)..pdf",
            "Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series D)..pdf"
        ],
        "redundant_reviews_saved": 68
    },
    "targets": 70,
    "completion": "100% paper completion achieved across all 7 target examination papers",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "conventional_marks_preserved": 346,
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted conventional items.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
