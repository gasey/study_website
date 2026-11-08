"""Build review packet and findings for Batch 48: Direct 2022-2023 General English Booklets (75 MCQs/tasks)."""
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
    # --- PAPER 1: General English Paper-I (CAO) (14 MCQs) ---
    "87c9824cef58d2175b36": ("Q4", 1, "Idioms & Phrases (getting into a row)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'getting into a row' meaning picking up a quarrel or fight over trivial matters."),
    "7d29be8c54cbd8614cbb": ("Q5", 1, "Idioms & Phrases (cry wolf)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'cry wolf' meaning raising a false alarm or warning."),
    "5de76f2e623bd49066ab": ("Q6", 1, "Idioms & Phrases (taken the wind out of my sails)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'take the wind out of one's sails' meaning rendering words or actions ineffective."),
    "04be20878b5c8e2c08da": ("Q7", 2, "Idioms & Phrases (at fingertips)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'at fingertips' meaning readily available and easily accessible."),
    "b3483cf898c9d157091c": ("Q8", 2, "Idioms & Phrases (put foot down)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'put foot down' meaning being firm or asserting unyielding authority."),
    "cc8409e5a7ced3de2372": ("Q9", 2, "Idioms & Phrases (blowing hot and cold)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'blowing hot and cold' meaning being friendly one moment and unfriendly the next."),
    "eec35556952e5ef8b006": ("Q10", 2, "Idioms & Phrases (on their toes)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'on one's toes' meaning alert, vigilant, and ready for action throughout the day."),
    "316106ad885ab676b6af": ("Q11", 2, "Idioms & Phrases (cut coat according to cloth)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'cut coat according to cloth' meaning living strictly within one's income or resources."),
    "252d0d5c2321fbe8f60f": ("Q12", 2, "Idioms & Phrases (fell on stony ground)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'fell on stony ground' meaning having little success or being ignored by listeners."),
    "e41cb37cd5961047f993": ("Q13", 2, "Idioms & Phrases (out of spirits)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'out of spirits' meaning gloomy, melancholy, or low in mood."),
    "9ee716665ed078a1e831": ("Q14", 2, "Idioms & Phrases (lose head)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'lose head' meaning losing self-control or getting angry in public."),
    "20eb47b26ee7ec4690d5": ("Q15", 2, "Idioms & Phrases (made my day)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'make one's day' meaning giving great joy, affirmation, or pleasure."),
    "6bc747980d83927febcd": ("Q16", 2, "Idioms & Phrases (washed hands off)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'wash hands off' meaning dissociating oneself from responsibility once matter reached court."),
    "d241136ac5ee4d0e9997": ("Q17", 2, "Idioms & Phrases (let hair down)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'let hair down' meaning behaving uninhibitedly and really enjoying oneself."),

    # --- PAPER 2: Geologist Junior under Commerce Deptt - Gen English-I (6 conventional items) ---
    "desc-0d47878dfaa7a0832f31": ("Q1", 1, "Essay writing (Sustainable Development / Climate / Social Networking)", "english/writing/essay", "retag", "Conventional descriptive essay composition task on sustainable development, climate change, or social networking."),
    "desc-22a461d2d6315cf9b4f1": ("Q2", 1, "Précis writing (Value of books & solitude)", "english/writing/precis", "retag", "Conventional descriptive précis condensation task on the value of books, reading, and solitary reflection."),
    "desc-ccd21508f413220e9bbb": ("Q3(a)", 1, "Letter writing (Superintendent of Police on cyber crime)", "english/writing/letter", "retag", "Formal official correspondence task drafting a letter to the Superintendent of Police regarding rising cyber crime."),
    "desc-b27741e0b86dd8107765": ("Q3(b)", 1, "Letter writing (Village Council on quarry safety awareness)", "english/writing/letter", "retag", "Official administrative correspondence task drafting a letter to a Village Council requesting co-operation for highway quarry safety awareness."),
    "desc-43c78f17d9282273de48": ("Q5", 2, "Sentence expansion (Proverbs)", "english/writing", "retag", "Conventional idea and proverb expansion task developing moral and philosophical themes."),
    "desc-1b8005c0d0474efb5930": ("Q6", 2, "Reading comprehension (Class inequality & inheritance)", "english/comprehension", "retag", "Conventional reading comprehension questions and vocabulary in context on social inequality and inheritance."),

    # --- PAPER 3: Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English (20 MCQs) ---
    "f0714f4273b1a0bdf95e": ("Q5(a)", 3, "Idioms & Phrases (green-eyed friends)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'green-eyed' meaning jealous or envious."),
    "128b9d44982c21dd5025": ("Q5(b)", 3, "Idioms & Phrases (left high and dry)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'left high and dry' meaning abandoned in a helpless or vulnerable situation."),
    "e807d58b03a819df6b35": ("Q5(c)", 3, "Idioms & Phrases (feather in your cap)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'feather in your cap' meaning an additional honor, distinction, or achievement."),
    "d74151d9a04726bf273b": ("Q5(d)", 3, "Idioms & Phrases (burning question)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'burning question' meaning a widely and urgently debated issue."),
    "f2c0ec9925db471c0efb": ("Q5(e)", 3, "Idioms & Phrases (have cake and eat it too)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'have cake and eat it too' meaning enjoying advantages both ways simultaneously."),
    "b28b51394d2cb014f4f9": ("Q5(f)", 3, "Idioms & Phrases (sitting on the fence)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'sitting on the fence' meaning hesitating between two options or avoiding a firm choice."),
    "09861ddaaaceb5ddebeb": ("Q5(g)", 3, "Idioms & Phrases (took him to task)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'take to task' meaning reprimanding or rebuking someone for negligence."),
    "fe5348e5cd4418b4ddf6": ("Q5(h)", 3, "Idioms & Phrases (make head or tail of)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'make head or tail of' meaning understanding or deciphering a strange affair."),
    "98c8ca8e60bc236c6b55": ("Q5(i)", 3, "Idioms & Phrases (pulling my leg)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'pulling someone's leg' meaning teasing or befooling playfully."),
    "093c1e924d1ae9f668b4": ("Q5(j)", 3, "Idioms & Phrases (in doldrums)", "english/vocabulary/idioms-and-phrases", "retag", "Interprets idiom 'in doldrums' meaning in an uncertain, stagnant, or depressed state."),
    "bee9a7159d3f9d90ccc0": ("Q7(a)", 4, "Vocabulary in context (eruption)", "english/vocabulary", "retag", "Selects contextually accurate geological noun 'eruption' denoting volcanic catastrophic activity."),
    "dc74d413da8d98419e7d": ("Q7(b)", 4, "Vocabulary in context (favouritism)", "english/vocabulary", "retag", "Selects contextually appropriate administrative noun 'favouritism' for biased appointments."),
    "d5a3065362de66b48f33": ("Q7(c)", 4, "Vocabulary in context (respectable)", "english/vocabulary", "retag", "Selects appropriate descriptive adjective 'respectable' distinguishing from 'respective' and 'responsible'."),
    "568a7aaeb7fa9f647f0b": ("Q7(d)", 4, "Vocabulary in context (inevitable)", "english/vocabulary", "retag", "Selects contextual adjective 'inevitable' expressing unavoidable certainty of an outcome."),
    "9dc334e5d36d2fc5f381": ("Q7(e)", 4, "Vocabulary in context (scalded)", "english/vocabulary", "retag", "Selects precise verb 'scalded' denoting burning or injuring by boiling liquid."),
    "a7e0fadd64ba950bf470": ("Q7(f)", 4, "Vocabulary in context (impair)", "english/vocabulary", "retag", "Selects appropriate physiological verb 'impair' meaning weaken or damage faculties."),
    "b900ddbe08c682cdb4c4": ("Q7(g)", 4, "Vocabulary in context (exercise)", "english/vocabulary", "retag", "Selects correct collocation verb 'exercise' with abstract noun 'restraint'."),
    "70ff0fa83a1ba79f7967": ("Q7(h)", 4, "Vocabulary in context (sumptuous)", "english/vocabulary", "retag", "Selects descriptive hospitality adjective 'sumptuous' denoting lavish, costly meal."),
    "4bb369371be8c8b00eae": ("Q7(i)", 4, "Vocabulary in context (averted)", "english/vocabulary", "retag", "Selects preventative verb 'averted' meaning warding off or turning away a disaster."),
    "fd44ad749b127c7fd290": ("Q7(j)", 4, "Vocabulary in context (altercation)", "english/vocabulary", "retag", "Selects noun 'altercation' distinguishing dispute/quarrel from 'alteration' and 'aberration'."),

    # --- PAPER 4: Jr. Grade of MES (Electrical Wing) under P & E Deptt., General English - 2022 (35 MCQs) ---
    "b0c568b4072c55522e72": ("Q3(a)", 2, "Passage Synonyms (depend on -> count on)", "english/vocabulary/synonyms", "retag", "Identifies phrasal verb synonym 'count on' for 'depend on' within Chief Seathl passage context."),
    "32cb6dcf8d1a077a2b22": ("Q3(b)", 2, "Passage Synonyms (unfamiliar -> strange)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'strange' for 'unfamiliar' within Chief Seathl passage context."),
    "ec94f757c2ccc03a58a3": ("Q3(c)", 2, "Passage Synonyms (consume -> devour)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'devour' for 'consume' within Chief Seathl passage context."),
    "f6586ef84555145dcdcb": ("Q3(d)", 2, "Passage Synonyms (Savage -> uncivilised)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'uncivilised' for 'savage' within Chief Seathl passage context."),
    "5f8b55a93444a9276a5a": ("Q3(e)", 2, "Passage Synonyms (befalls -> happens to)", "english/vocabulary/synonyms", "retag", "Identifies phrasal synonym 'happens to' for 'befalls' within Chief Seathl passage context."),
    "ccb09fac4e361b4c3831": ("Q4", 3, "Parts of Speech (spider -> noun)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined word 'spider' as noun."),
    "6c074499eef7457a1091": ("Q5", 3, "Parts of Speech (little -> adjective)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined quantifier 'little' as adjective modifying 'gravy'."),
    "03712146e2a666e6d2b8": ("Q6", 3, "Parts of Speech (sells -> verb)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined action word 'sells' as verb."),
    "9769f7d47f51558b67e5": ("Q7", 3, "Parts of Speech (They -> pronoun)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined subject 'They' as personal pronoun."),
    "4f9bafe4da150fbcf504": ("Q8", 3, "Parts of Speech (spreads -> verb)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined predicate 'spreads' as verb."),
    "4754f64ddfdc63ff16a4": ("Q9", 3, "Parts of Speech (and -> conjunction)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined coordinating link 'and' as conjunction."),
    "9c8b2c0cf95f239782d1": ("Q10", 3, "Parts of Speech (soundly -> adverb)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined modifier 'soundly' as adverb of manner."),
    "74370a64dce16c3062e3": ("Q11", 3, "Parts of Speech (into -> preposition)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined relational particle 'into' as preposition."),
    "8260e6f1a90c397aac0e": ("Q12", 3, "Parts of Speech (Alas! -> interjection)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined exclamatory particle 'Alas!' as interjection."),
    "0d97c7fa297d590c74ba": ("Q13", 3, "Parts of Speech (Our -> pronoun)", "english/grammar/parts-of-speech", "retag", "Identifies grammatical part of speech of underlined possessive word 'Our' as pronoun/possessive determiner."),
    "7f47394959eb2ebd2ef9": ("Q14", 4, "Tenses (shall remain close -> Future indefinite)", "english/grammar/tenses", "retag", "Identifies modal auxiliary future verb structure 'shall remain' as Future indefinite tense."),
    "f2a2610431bac1ee6892": ("Q15", 4, "Tenses (is raining -> Present continuous)", "english/grammar/tenses", "retag", "Identifies continuous auxiliary verb structure 'is raining' as Present continuous tense."),
    "8456b1896f9b35ee3e7c": ("Q16", 4, "Tenses (has stood -> Present perfect)", "english/grammar/tenses", "retag", "Identifies auxiliary perfect verb structure 'has stood' as Present perfect tense."),
    "0d47ba97c918f206921b": ("Q17", 4, "Tenses (will have finished -> Future perfect)", "english/grammar/tenses", "retag", "Identifies composite auxiliary construction 'will have finished' as Future perfect tense."),
    "ffbff9ff60147c383ed4": ("Q18", 4, "Tenses (has been looking -> Present perfect continuous)", "english/grammar/tenses", "retag", "Identifies progressive auxiliary construction 'has been looking' as Present perfect continuous tense."),
    "d94f25e88ce136f782aa": ("Q19", 4, "Tenses (lights -> Present indefinite)", "english/grammar/tenses", "retag", "Identifies simple third-person singular present verb 'lights' as Present indefinite tense."),
    "f5b1fedc96188f1627c0": ("Q20", 4, "Tenses (Did ... smoke -> Past indefinite)", "english/grammar/tenses", "retag", "Identifies interrogative past auxiliary structure 'Did you ever smoke' as Past indefinite tense."),
    "57e31d83ff27e1c76d68": ("Q21", 4, "Tenses (had run -> Past perfect)", "english/grammar/tenses", "retag", "Identifies past perfect auxiliary structure 'had run' as Past perfect tense."),
    "12cdd11823da279b3944": ("Q22", 4, "Tenses (had been ringing -> Past perfect continuous)", "english/grammar/tenses", "retag", "Identifies progressive past auxiliary construction 'had been ringing' as Past perfect continuous tense."),
    "ec7a6426e786a9685b20": ("Q23", 4, "Tenses (cuts -> Present indefinite)", "english/grammar/tenses", "retag", "Identifies base inflected verb 'cuts' as Present indefinite tense."),
    "1aef0b7bdd8aeb1ffecd": ("Q24", 4, "Synonyms (hamper -> hinder)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'hinder' for headword 'hamper'."),
    "98f6d73551f506f6c261": ("Q25", 4, "Synonyms (assignment -> task)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'task' for headword 'assignment'."),
    "5eba39bf56d22c211b45": ("Q26", 5, "Synonyms (burden -> load)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'load' for headword 'burden'."),
    "31b4a5f0f303a0921fbe": ("Q27", 5, "Synonyms (antagonistic -> hostile)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'hostile' for headword 'antagonistic'."),
    "bcac6d375397d03da5a7": ("Q28", 5, "Synonyms (belligerent -> aggressive)", "english/vocabulary/synonyms", "retag", "Identifies lexical synonym 'aggressive' for headword 'belligerent'."),
    "b9627546066455c02095": ("Q29", 5, "Antonyms (adversity -> prosperity)", "english/vocabulary/antonyms", "retag", "Identifies opposite meaning 'prosperity' for headword 'adversity'."),
    "514bcb384f60794325bc": ("Q30", 5, "Antonyms (enrich -> impoverish)", "english/vocabulary/antonyms", "retag", "Identifies opposite meaning 'impoverish' for headword 'enrich'."),
    "fd424e9e9b909f8b20ce": ("Q31", 5, "Antonyms (Coarse -> fine)", "english/vocabulary/antonyms", "retag", "Identifies opposite meaning 'fine' for headword 'Coarse'."),
    "073c324b9df213b615fa": ("Q32", 5, "Antonyms (Important -> trivial)", "english/vocabulary/antonyms", "retag", "Identifies opposite meaning 'trivial' for headword 'Important'."),
    "a676dfa8910ebe42aecf": ("Q33", 5, "Antonyms (repulsive -> attractive)", "english/vocabulary/antonyms", "retag", "Identifies opposite meaning 'attractive' for headword 'repulsive'.")
}

assert len(proposals) == 75, f"Expected 75 proposals, got {len(proposals)}"
assert len(packet["items"]) == 75, f"Expected 75 items in packet, got {len(packet['items'])}"

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
        "batch_id": 48,
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
    # Paper 1: General English Paper-I (CAO)
    {
        "paper_id": "Old_Questions/Direct_2022-2023/General English Paper-I (CAO).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 25,
        "task_type": "essay_writing",
        "prompt": "Write an essay on one of the following topics: Traffic in Aizawl; Pollution and its control mechanism; General practices in 'Saving or investments' by the mizo; The effect of drug and alcohol in the society.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive essay composition task with 4 local socioeconomic topics, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/General English Paper-I (CAO).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 15,
        "task_type": "précis_writing",
        "prompt": "Read the passage carefully and write a precis in about 1/3rd of its original giving a suitable title: Nelson, as a child, was not of a strong body... (137 words on childhood bravery of Nelson).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/General English Paper-I (CAO).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "3",
        "physical_page": 1,
        "marks": 15,
        "task_type": "letter_writing",
        "prompt": "Write a letter to the editor of Vanglaini about the deplorable state of the roads in your area.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "reason_unextracted": "Conventional editorial letter writing task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/General English Paper-I (CAO).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "18",
        "physical_page": 2,
        "marks": 15,
        "task_type": "proverb_expansion",
        "prompt": "Expand the given proverbs in passages giving suitable examples wherever possible: (a) Make hay while the sun shines OR (b) A stitch in time saves nine.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional proverb expansion task with moral/practical examples, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/General English Paper-I (CAO).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "19",
        "physical_page": 3,
        "marks": 7,
        "task_type": "reading_comprehension_true_false",
        "prompt": "State whether the following sentences are True or False (7 items based on passage regarding Hiroshima and Nagasaki atomic bomb survivors).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional written comprehension True/False evaluation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/General English Paper-I (CAO).pdf",
        "section": "SECTION - A (Conventional Tasks) (70 Marks)",
        "question_number": "20",
        "physical_page": 3,
        "marks": 9,
        "task_type": "reading_comprehension_short_answer",
        "prompt": "Answer each of the following questions in about 30-40 words (3 questions on atomic bomb impact, overseas survivors, and Japan's surrender).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive short-answer reading comprehension questions, excluded from automated MCQ database ingestion."
    },

    # Paper 2: Geologist Junior under Commerce Deptt - Gen English-I
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Geologist Junior under Commerce Deptt - Gen English-I..pdf",
        "section": "CONVENTIONAL SECTION",
        "question_number": "4",
        "physical_page": 1,
        "marks": 14,
        "task_type": "sentence_formation_idioms",
        "prompt": "Make sentences with any seven of the following idioms and phrases: At sixes and sevens; Bolt from the blue; Call a spade a spade; From pillar to post; Hobson's choice; Kith and kin; Pull strings; Yeoman's service; Wear and tear; Nip in the bud.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional idiomatic sentence composition prompt (7 of 10 items), unextracted into appearances bank."
    },

    # Paper 3: Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English..pdf",
        "section": "CONVENTIONAL SECTION (80 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 20,
        "task_type": "essay_writing",
        "prompt": "Write an essay choosing one of the topics given below: Medical Tourism: A New Trend in Tourism; Moral and Ethics of Public Servants; Students and Politics.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive essay composition task with 3 options, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English..pdf",
        "section": "CONVENTIONAL SECTION (80 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 20,
        "task_type": "reading_comprehension_descriptive",
        "prompt": "Read the given passage carefully and answer the questions that follow: Passage on what an educated person should know across arts, architecture, literature, music vs science/philosophy (5 questions + 5 vocabulary synonyms).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional short-answer reading comprehension questions and vocabulary matching, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English..pdf",
        "section": "CONVENTIONAL SECTION (80 Marks)",
        "question_number": "3",
        "physical_page": 2,
        "marks": 20,
        "task_type": "précis_writing",
        "prompt": "Make a precis of the given passage in about one-third of its original length. Supply a suitable title: Passage analyzing India's latent strength in science and technology vs management shortcomings.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English..pdf",
        "section": "CONVENTIONAL SECTION (80 Marks)",
        "question_number": "4",
        "physical_page": 2,
        "marks": 10,
        "task_type": "sentence_correction",
        "prompt": "Correct the following sentences (10 sentences testing prepositional redundancy, reported verbs, double negatives, and subject-verb agreement).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/sentence-correction",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional written sentence correction task without MCQ options, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English..pdf",
        "section": "CONVENTIONAL SECTION (80 Marks)",
        "question_number": "6",
        "physical_page": 3,
        "marks": 10,
        "task_type": "sentence_formation_word_pairs",
        "prompt": "Make sentences with the following pair of words to show their differences: Vocation / Vacation; Principle / Principal; Bail / Bale; council / councel; Ceiling / sealing.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional homophone/word-pair contrastive sentence composition task, excluded from automated MCQ database ingestion."
    },

    # Paper 4: Jr. Grade of MES (Electrical Wing) under P & E Deptt., General English - 2022
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Jr. Grade of MES (Electrical Wing) under P & E Deptt., General English - 2022...pdf",
        "section": "CONVENTIONAL SECTION (65 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 20,
        "task_type": "essay_writing",
        "prompt": "Write an essay in any one of the given topics: Bamboo link roads as a measure to sustainable development in Mizoram; The socio-economic impact of Covid -19 pandemic and Lock down in Mizoram; Tourism and the future aspect of Tourism in Mizoram.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive engineering and socioeconomic essay composition task with 3 options, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Jr. Grade of MES (Electrical Wing) under P & E Deptt., General English - 2022...pdf",
        "section": "CONVENTIONAL SECTION (65 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 20,
        "task_type": "précis_writing",
        "prompt": "Write a précis of the given passage: Extensive passage on clear and logical thinking as the prerequisite to good writing, disciplined practice, and audience awareness.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Jr. Grade of MES (Electrical Wing) under P & E Deptt., General English - 2022...pdf",
        "section": "CONVENTIONAL SECTION (65 Marks)",
        "question_number": "3(f)-(j)",
        "physical_page": 3,
        "marks": 15,
        "task_type": "reading_comprehension_descriptive",
        "prompt": "Answer the descriptive questions on Chief Seathl's letter: (f) contrast of Red Indian vs White man attitudes to earth, (g) criticism of White man's ways, (h) impression of Chief Seathl, (i) plea for nature preservation, (j) suitable title.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional short-answer reading comprehension questions (5 items x 3 marks), excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2022-2023/Jr. Grade of MES (Electrical Wing) under P & E Deptt., General English - 2022...pdf",
        "section": "CONVENTIONAL SECTION (65 Marks)",
        "question_number": "34",
        "physical_page": 5,
        "marks": 10,
        "task_type": "sentence_formation_idioms",
        "prompt": "Make a meaningful sentence with each phrase given: 'Cost me an arm and a leg'; 'pulling someone's leg'; 'Best of both worlds'; 'hit the sack'; 'twist my arm'.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/vocabulary",
            "subtopic_id": "english/vocabulary/idioms-and-phrases"
        },
        "reason_unextracted": "Conventional idiomatic sentence composition prompt (5 items x 2 marks), unextracted into appearances bank."
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
    "batch": 48,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2022-2023/General English Paper-I (CAO).pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Post of Grade-V of MSCS (Cooperative Audit Officer) - General English Paper - I",
            "document_id": "doc_09ecdb100f668625c85b57c4",
            "sha256": "4e8c54c9b4551b88336d068fc9eab335c38b76b84b2607944240035096cbd302",
            "targets": 14
        },
        {
            "paper_id": "Old_Questions/Direct_2022-2023/Geologist Junior under Commerce Deptt - Gen English-I..pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Post of Geologist Junior - General English Paper I",
            "document_id": "doc_7a32498eb36e71f5a1ac6918",
            "sha256": "3c33df8305e94a767b4a970afb4345106b52504cf79b47dc6b527c7116990f9b",
            "targets": 6
        },
        {
            "paper_id": "Old_Questions/Direct_2022-2023/Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English..pdf",
            "paper_title": "General English - Grade-III of Mizoram Health Service (GDMO and Dental Surgeon Sub-Cadre)",
            "document_id": "doc_062a465c96890fff341e8db7",
            "sha256": "f0e37ecc4e9541d9b15c4e3579853ce9c8ca50ed0e4e514ebf56f1abd22936c6",
            "targets": 20
        },
        {
            "paper_id": "Old_Questions/Direct_2022-2023/Jr. Grade of MES (Electrical Wing) under P & E Deptt., General English - 2022...pdf",
            "paper_title": "Technical Competitive Examinations for Junior Grade of Mizoram Engineering Service, P&E Cadre (Electrical Wing) - General English",
            "document_id": "doc_4e9059a592b86e3de860b4f1",
            "sha256": "53c9edca1c8085ab3620d3fa2575d670331af24fd6e8dbeb6fd7f052ded61b4f",
            "targets": 35
        }
    ],
    "single_booklet_deduplication": {
        "enforced": True,
        "primary_booklet": "Single booklet examinations across all 4 targets",
        "bypassed_siblings": [],
        "redundant_reviews_saved": 0
    },
    "targets": 75,
    "completion": "100% of extracted MCQs and descriptive items reviewed across all 4 Direct 2022-2023 General English booklets",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "conventional_marks_preserved": 245,
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted conventional items.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
