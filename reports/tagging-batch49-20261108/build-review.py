"""Build review packet and findings for Batch 49: Direct 2019-2022 General English Paper-I Booklets (50 MCQs & Tasks)."""
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
    # --- PAPER 1: CEO General English-I (12 items) ---
    "desc-e8b9ff73fdf0061e2422": ("Q1", 1, "Essay writing (Traditional Mizo Attire / NGOs / Work Ethics / Calamities)", "english/writing/essay", "retag", "Conventional descriptive essay composition task with 4 socioeconomic and governance topics."),
    "desc-290bad0329bfa49fbdc0": ("Q2", 1, "Letter writing (Friend / Colleague / Local Council / Traffic / RD Dept)", "english/writing/letter", "retag", "Formal and informal letter writing task with 5 situational options."),
    "desc-1d8086c938bea4e74551": ("Q3", 1, "Précis writing (Money vs true human calling)", "english/writing/precis", "retag", "Conventional descriptive précis condensation task on Ruskin's passage regarding money vs vocation."),
    "desc-47626445409e64f9ce87": ("Q5", 2, "Sentence expansion (Proverbs & philosophical maxims)", "english/writing", "retag", "Conventional idea and proverb expansion task developing moral and philosophical themes."),
    "80482d29411395a6a7ce": ("Q6", 4, "Reading comprehension (Gilray's Flower-Pot - accusations)", "english/comprehension", "retag", "Analyzes accusations made by the narrator against Gilray in J.M. Barrie's story."),
    "ed6bf7b65c3e17d05c8b": ("Q7", 4, "Reading comprehension (Gilray's Flower-Pot - implication)", "english/comprehension", "retag", "Infers narrator's implication regarding Gilray's claims of watering plant daily."),
    "79c2decf42fb7eaef073": ("Q8", 4, "Reading comprehension (Gilray's Flower-Pot - disbelief)", "english/comprehension", "retag", "Identifies reasons why the narrator disbelieves that Gilray received the plant as a gift."),
    "2b93af29fe0628074a8c": ("Q9", 4, "Reading comprehension (Gilray's Flower-Pot - excuses)", "english/comprehension", "retag", "Identifies excuses used by the narrator to justify neglect of the plant."),
    "e4bfef38f851af817e20": ("Q10", 4, "Reading comprehension (Gilray's Flower-Pot - smoking habits)", "english/comprehension", "retag", "Analyzes narrator's underlying purpose in mentioning Gilray's smoking habits."),
    "a35634d74f9248e0ed39": ("Q11", 4, "Reading comprehension (Gilray's Flower-Pot - reminder letters)", "english/comprehension", "retag", "Characterizes narrator's offended reaction upon receiving reminder letters."),
    "71a05a1471c7ecf6d504": ("Q12", 4, "Reading comprehension (Gilray's Flower-Pot - disagreeing statement)", "english/comprehension", "retag", "Infers statement with which the narrator would disagree based on narrative stance."),
    "c48a322050fd12e6aec0": ("Q13", 4, "Reading comprehension (Gilray's Flower-Pot - text conclusion)", "english/comprehension", "retag", "Identifies conclusion best supported by text regarding narrator's refusal of responsibility."),

    # --- PAPER 2: General English Paper-I (Inspector of Excise) (14 MCQs) ---
    "4984ebc285fd8b3239b3": ("Q4", 1, "Idioms & Phrases (Bite the bullet)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'bite the bullet' meaning facing an unpleasant situation with courage."),
    "7c69341404e456275413": ("Q5", 1, "Idioms & Phrases (Bone of contention)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'bone of contention' meaning the subject or point of an argument."),
    "581c8abf08eb08e8a03f": ("Q6", 1, "Idioms & Phrases (Hand over fist)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'hand over fist' meaning making money or progressing quickly and continuously."),
    "18cea95257ec26d7541a": ("Q7", 2, "Idioms & Phrases (To die in harness)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'die in harness' meaning to die while actively serving in duty or office."),
    "f98e44c22e0869439b72": ("Q8", 2, "Idioms & Phrases (No avail)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets phrase 'to no avail' meaning without any result or effect."),
    "99e66b7860f568c28250": ("Q9", 2, "Idioms & Phrases (Hard and fast)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'hard and fast' meaning strict, fixed, and unalterable rules."),
    "a100a9961834b2926613": ("Q10", 2, "Idioms & Phrases (All at sea)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'all at sea' meaning in a state of utter confusion or bewilderment."),
    "b5f6dedaf174b79366cc": ("Q12", 2, "Reading comprehension (Gandhian egalitarianism - survival condition)", "english/comprehension", "retag", "Extracts passage condition that egalitarianism cannot survive if achieved by physical coercion."),
    "813c74b9095cf4bc81af": ("Q13", 3, "Reading comprehension (Gandhian egalitarianism - preservation of name)", "english/comprehension", "retag", "Extracts psychological motivation of possessive instinct preserving name after death."),
    "435e2b18ed8db7fa08d7": ("Q14", 3, "Reading comprehension (Gandhian egalitarianism - unfinished experiment)", "english/comprehension", "retag", "Identifies establishment of an egalitarian society as the unfinished part of Gandhiji's experiment."),
    "1d46bfc0d8b2c42d3590": ("Q15", 3, "Reading comprehension (Gandhian egalitarianism - untrue statement)", "english/comprehension", "retag", "Evaluates factual accuracy against text regarding true egalitarianism vs compulsion."),
    "54d8da9d23ecb250bbd7": ("Q16", 3, "Reading comprehension (Gandhian egalitarianism - truth & non-violence)", "english/comprehension", "retag", "Extracts condition that lasting egalitarian social order must be based on truth and non-violence."),
    "2c8a312890a0f8b3fbd5": ("Q17", 3, "Reading comprehension (Gandhian egalitarianism - overturning social order)", "english/comprehension", "retag", "Infers cause of popular overturning of social orders based on coercion and oppression."),
    "5c54b599707f894df779": ("Q18", 3, "Reading comprehension (Gandhian egalitarianism - phrase 'root out')", "english/comprehension", "retag", "Interprets figurative phrase 'root out' meaning find and eradicate/remove completely."),

    # --- PAPER 3: General English Paper-I (V.O) (3 items) ---
    "94bf0f655a3b9f25236f": ("Q11", 2, "Reading comprehension (Science & religion synthesis)", "english/comprehension", "retag", "Extracts author's argument for judiciously synthesizing scientific principles and true religious spirit."),
    "0aa3d91c928c6212552c": ("Q13", 3, "Passage Synonyms ('flouted' -> mocked)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'mocked' for contextual word 'flouted' within passage."),
    "9484c042abe0352d0d47": ("Q14", 3, "Passage Antonyms ('enlightened' -> uninformed)", "english/vocabulary/antonyms", "retag", "Identifies antonym 'uninformed' for contextual adjective 'enlightened' within passage."),

    # --- PAPER 4: Informatics Officer - General English Paper-I (8 MCQs) ---
    "6a5ec06876ebefecbe1e": ("Q1", 2, "Reading comprehension (Anti-colonial struggle - advantage)", "english/comprehension", "retag", "Extracts advantage of anti-colonial struggle in forging third world national solidarity."),
    "e9c2fcb98463868cf60f": ("Q2", 2, "Reading comprehension (Anti-colonial struggle - colonial reaction)", "english/comprehension", "retag", "Analyzes colonial tactical reactions attempting to disrupt national independence movements."),
    "eda0ab4deaf4f013f2fc": ("Q3", 2, "Reading comprehension (Anti-colonial struggle - Angola & South Africa)", "english/comprehension", "retag", "Evaluates illustrative examples of Angola and South Africa cited in anti-colonial context."),
    "8d6b8e5de8ae266de624": ("Q4", 2, "Reading comprehension (Anti-colonial struggle - market relations)", "english/comprehension", "retag", "Identifies socioeconomic role played by market relations in transforming colonial territories."),
    "f7ad42da5ddbcb4ea9b2": ("Q5", 3, "Reading comprehension (Anti-colonial struggle - origin of nationalism)", "english/comprehension", "retag", "Extracts historical conditions giving rise to modern nationalism across third world nations."),
    "539900f59c656b87da6f": ("Q6", 3, "Reading comprehension (Anti-colonial struggle - distorted history)", "english/comprehension", "retag", "Analyzes colonial motives in historiographical distortion to weaken indigenous identity."),
    "e8444f7b640a52a278f8": ("Q7", 3, "Reading comprehension (Anti-colonial struggle - author's perspective)", "english/comprehension", "retag", "Synthesizes author's analytical stance and perspective toward anti-imperialist movements."),
    "b38d8fac4a438c466578": ("Q8", 3, "Reading comprehension (Anti-colonial struggle - camouflage tactics)", "english/comprehension", "retag", "Interprets colonial propaganda camouflage strategies obscuring authentic national liberation."),

    # --- PAPER 5: ASCE - General English Paper-I (5 items) ---
    "desc-5a354953da054c64df2f": ("Q1", 1, "Essay writing (Soil conservation / Infrastructure / Water security)", "english/writing/essay", "retag", "Conventional descriptive engineering essay composition task on soil and water conservation."),
    "desc-7be906497d60ff812fff": ("Q2", 1, "Précis writing (Wealth latent within mind & character)", "english/writing/precis", "retag", "Conventional descriptive précis condensation task on patience, kindness, and character development."),
    "desc-5e1e5996c1f4b75e5c34": ("Q3", 1, "Official drafting (Office Order granting earned leave)", "english/writing/letter", "retag", "Rectifies misclassified 'service-rules-and-office-procedure' baseline to active English official drafting/letter writing."),
    "desc-4a506a4c1cf683518367": ("Q5", 2, "Sentence expansion (Contentment / Great achievements / Wisdom)", "english/writing", "retag", "Conventional idea and maxim expansion task on contentment, perseverance, and wisdom."),
    "desc-ee46e0cd8a6f21be72d9": ("Q6", 2, "Reading comprehension (Mentoring programmes in corporate circles)", "english/comprehension", "retag", "Conventional reading comprehension questions and vocabulary matching on formal corporate mentoring."),

    # --- PAPER 6: Jr. Gr. of MAH Vety General English Paper-I (8 items) ---
    "dd684d8ce3736ad8251d": ("Q1(5a)", 2, "Idioms & Phrases (keep back -> conceal)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets phrasal verb/idiom 'keep back' meaning to conceal or withhold information."),
    "desc-f951ec2aa3898a54ce02": ("Q1", 1, "Essay writing (Covid-19 / African Swine Fever / Vety Economy)", "english/writing/essay", "retag", "Conventional descriptive essay composition task on African Swine Fever, veterinary economy, or Covid-19."),
    "0d2265b02e1c014a5e4c": ("Q2(5b)", 2, "Idioms & Phrases (passed himself off -> pretended to be)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'passed himself off' meaning pretended or impersonated falsely."),
    "3bdc90bd07078596d50d": ("Q3(5c)", 2, "Idioms & Phrases (runs down -> disparages)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets phrasal verb/idiom 'run down' meaning disparaging, belittling, or criticizing someone."),
    "desc-279db82fae7adb685f00": ("Q3", 1, "Letter writing (Covid-19 vaccination request to Director H&FW)", "english/writing/letter", "retag", "Formal administrative correspondence task drafting a letter to the Director H&FW on urgent Covid-19 vaccination."),
    "14361b4fadb944ce2cb0": ("Q4(5d)", 2, "Idioms & Phrases (set aside -> annulled)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets legal idiom/phrasal verb 'set aside' meaning to annul, overturn, or revoke a judicial decree."),
    "desc-84cbc6de6a5cf08ae883": ("Q4", 1, "Sentence expansion (What is this life / Belief in own eyes / Difficulties)", "english/writing", "retag", "Conventional poetic and philosophical idea expansion task on leisure, perception, and life challenges."),
    "414e26fff95885ef756d": ("Q5(5e)", 2, "Idioms & Phrases (puts on an air -> assumes)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'puts on an air' meaning assuming an artificial posture of dignity or superiority.")
}

assert len(proposals) == 50, f"Expected 50 proposals, got {len(proposals)}"
assert len(packet["items"]) == 50, f"Expected 50 items in packet, got {len(packet['items'])}"

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
        "batch_id": 49,
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
    # Paper 1: CEO General English-I
    {
        "paper_id": "Old_Questions/Direct_2019-2020/CEO General English-I.pdf",
        "section": "CONVENTIONAL SECTION",
        "question_number": "4",
        "physical_page": 1,
        "marks": 14,
        "task_type": "idiom_explanation",
        "prompt": "Explain any 7 (seven) of the following phrases: Twist someone's arm; Blow off steam; Cut to the chase; Compare apples and oranges; Spill the beans; A hard nut to crack; Let the dust settle; Between a rock and a hard place.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional descriptive idiom explanation prompt (7 of 8 items), unextracted into appearances bank."
    },

    # Paper 2: General English Paper-I (Inspector of Excise)
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (Inspector of Excise).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 25,
        "task_type": "essay_writing",
        "prompt": "Write an essay on one of the following topics: Role of youth in nation building; Tourism prospects in Mizoram; Environmental degradation and global warming; Substance abuse and its impact on Mizo society.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive essay composition task with 4 options, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (Inspector of Excise).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "précis_writing",
        "prompt": "Write a précis of the given passage giving a suitable title: Passage on scientific method, observation, and impartial verification of facts.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (Inspector of Excise).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "3",
        "physical_page": 1,
        "marks": 15,
        "task_type": "letter_writing",
        "prompt": "Write a letter to the editor of a local daily regarding the nuisance of reckless two-wheeler driving in urban areas.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional editorial letter writing task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (Inspector of Excise).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "18",
        "physical_page": 3,
        "marks": 15,
        "task_type": "proverb_expansion",
        "prompt": "Expand the given proverbs: (a) Prevention is better than cure OR (b) Where there is a will, there is a way.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional proverb expansion task with moral/practical examples, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (Inspector of Excise).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "19",
        "physical_page": 4,
        "marks": 7,
        "task_type": "reading_comprehension_true_false",
        "prompt": "State whether the given statements are True or False (7 items based on passage on environmental protection).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional written comprehension True/False evaluation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (Inspector of Excise).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "20",
        "physical_page": 4,
        "marks": 9,
        "task_type": "reading_comprehension_short_answer",
        "prompt": "Answer the comprehension questions in about 30-40 words (3 questions on ecological conservation).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive short-answer reading comprehension questions, excluded from automated MCQ database ingestion."
    },

    # Paper 3: General English Paper-I (V.O)
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (V.O).pdf",
        "section": "CONVENTIONAL SECTION (45 Marks)",
        "question_number": "4",
        "physical_page": 1,
        "marks": 14,
        "task_type": "sentence_formation_idioms",
        "prompt": "Explain any 7 of the following phrases and make sentences with them: At the eleventh hour; Beat about the bush; Bury the hatchet; Call a spade a spade; Feather in one's cap; Once in a blue moon; Turn a deaf ear; Wild goose chase; Through thick and thin; To make both ends meet.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional idiom explanation and sentence making prompt (7 of 10 items), unextracted into appearances bank."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (V.O).pdf",
        "section": "CONVENTIONAL SECTION (45 Marks)",
        "question_number": "5",
        "physical_page": 2,
        "marks": 15,
        "task_type": "proverb_expansion",
        "prompt": "Expand any 3 of the following: (a) Slow and steady wins the race (b) Actions speak louder than words (c) Every cloud has a silver lining (d) All that glitters is not gold (e) A stitch in time saves nine.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional proverb expansion prompt (3 of 5 items), unextracted into appearances bank."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (V.O).pdf",
        "section": "CONVENTIONAL SECTION (45 Marks)",
        "question_number": "6",
        "physical_page": 3,
        "marks": 16,
        "task_type": "reading_comprehension_descriptive",
        "prompt": "Read the passage carefully and answer the questions that follow: Passage on educational reform and creative thinking (4 short-answer questions + 4 vocabulary synonyms).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional short-answer reading comprehension questions and vocabulary matching, unextracted into appearances bank."
    },

    # Paper 4: Informatics Officer - General English Paper-I
    {
        "paper_id": "Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (85 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 25,
        "task_type": "essay_writing",
        "prompt": "Write an essay on one of the following: Digital India and governance; Artificial intelligence: Prospects and perils; Climate change impacts on northeastern India.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive essay composition task with technical options, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (85 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "précis_writing",
        "prompt": "Write a précis of the passage on scientific inquiry and technological advancement, supplying a suitable title.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (85 Marks)",
        "question_number": "3",
        "physical_page": 1,
        "marks": 15,
        "task_type": "letter_writing",
        "prompt": "Write an official letter to the Director of ICT regarding cybersecurity upgrades in departmental data servers.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional official correspondence task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (85 Marks)",
        "question_number": "4",
        "physical_page": 1,
        "marks": 15,
        "task_type": "sentence_formation_idioms",
        "prompt": "Make sentences with any 5 idioms: Apple of discord; Bite the bullet; Castles in the air; Down to earth; Face the music; Greasing the palm.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional idiomatic sentence composition prompt, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION (85 Marks)",
        "question_number": "5",
        "physical_page": 2,
        "marks": 15,
        "task_type": "proverb_expansion",
        "prompt": "Expand any 3 maxims: (a) Knowledge is power (b) Pen is mightier than sword (c) Rome was not built in a day.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional proverb expansion prompt, excluded from automated MCQ database ingestion."
    },

    # Paper 5: ASCE - General English Paper-I
    {
        "paper_id": "Old_Questions/Direct_2021-2022/ASCE - General English Paper-I.pdf",
        "section": "CONVENTIONAL SECTION",
        "question_number": "4",
        "physical_page": 1,
        "marks": 14,
        "task_type": "sentence_formation_idioms",
        "prompt": "Make sentences using any 7 of the following idioms/phrases: Beat about the bush; Break the ice; Burn the midnight oil; Cry over spilt milk; Hit the nail on the head; Kill two birds with one stone; Let the cat out of the bag; Piece of cake; Through thick and thin; Under the weather.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional idiomatic sentence composition prompt (7 of 10 items), unextracted into appearances bank."
    },

    # Paper 6: Jr. Gr. of MAH Vety General English Paper-I
    {
        "paper_id": "Old_Questions/Direct_2021-2022/Jr. Gr. of MAH Vety General English Paper-I..pdf",
        "section": "CONVENTIONAL SECTION (30 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "précis_writing",
        "prompt": "Make a précis of the given passage: Senator George Graham Vest's Eulogy on the Dog (fidelity, nobility, and eternal loyalty of man's best friend).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2021-2022/Jr. Gr. of MAH Vety General English Paper-I..pdf",
        "section": "CONVENTIONAL SECTION (30 Marks)",
        "question_number": "6",
        "physical_page": 2,
        "marks": 15,
        "task_type": "reading_comprehension_descriptive",
        "prompt": "Read the given passage carefully and answer the questions that follow: Passage on religion, spiritual goods, and Jesus Christ's teachings on wealth as a trust (5 questions x 3 marks).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional short-answer reading comprehension questions, excluded from automated MCQ database ingestion."
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
    "batch": 49,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2019-2020/CEO General English-I.pdf",
            "paper_title": "COMPETITIVE EXAMINATIONS FOR RECRUITMENT TO THE POST OF CIRCLE EDUCATION OFFICER UNDER SCHOOL EDUCATION DEPARTMENT",
            "document_id": "doc_74d9b3f2ded9bc5c2e9c8b74",
            "sha256": "142a50d03870f82329b313ef09eb58ee98914d7b2756858e33cb8e67f08df7d6",
            "targets": 12
        },
        {
            "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (Inspector of Excise).pdf",
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Inspector under Excise & Narcotics Department, General English Paper - I",
            "document_id": "doc_da993afc1d299ca9ec8df13c",
            "sha256": "f791396b59fbc118873099908cf6c4d75d319a27e7ca94b7dbef674a2fbc89b5",
            "targets": 14
        },
        {
            "paper_id": "Old_Questions/Direct_2019-2020/General English Paper-I (V.O).pdf",
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Junior Grade of MAH & VS I.E. Veterinary Officer - General English Paper I",
            "document_id": "doc_1ab13cb407d3fde6a1a38251",
            "sha256": "88f2ebae7791b7b514b8dbf9cc8b72506ea49a150bc01fb20a9a81b37fae5138",
            "targets": 3
        },
        {
            "paper_id": "Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-I.pdf",
            "paper_title": "Technical Competitive Examinations for Recruitment to the Post of Informatics Officer - General English Paper I",
            "document_id": "doc_5250924536dbee082db7539f",
            "sha256": "32ae9b4f1a89629f17a61d153835f8e5d0e7041a66be2fc59781177b91ee76c2",
            "targets": 8
        },
        {
            "paper_id": "Old_Questions/Direct_2021-2022/ASCE - General English Paper-I.pdf",
            "paper_title": "ASSISTANT SOIL CONSERVATION ENGINEER (ASCE) - GENERAL ENGLISH PAPER I",
            "document_id": "doc_1244a8721bec769394f9b3a7",
            "sha256": "3624e1ee946a6fefa1a5ea11a5416035272a806c99cff98418ff55dd331b6510",
            "targets": 5
        },
        {
            "paper_id": "Old_Questions/Direct_2021-2022/Jr. Gr. of MAH Vety General English Paper-I..pdf",
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Junior Grade of MAH & VS (Veterinary Officer) - General English Paper I",
            "document_id": "doc_38ddaa760769d6b08c77b1a7",
            "sha256": "beb29cb4145a6af52427a147ceb44749cb242e9734e55e0a6d511ea993f3458b",
            "targets": 8
        }
    ],
    "single_booklet_deduplication": {
        "enforced": True,
        "primary_booklet": "Single booklet examinations across all 6 targets",
        "bypassed_siblings": [],
        "redundant_reviews_saved": 0
    },
    "targets": 50,
    "completion": "100% of extracted MCQs and descriptive items reviewed across all 6 Direct 2019-2022 General English Paper-I booklets",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "conventional_marks_preserved": 274,
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted conventional items.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
