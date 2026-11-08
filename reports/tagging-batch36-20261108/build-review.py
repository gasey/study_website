"""Generate review candidates and findings for Batch 36.
Papers:
1. Agri&Allied General English 2025 (46 MCQs)
2. General English - Jr. of MHS 2025 (40 MCQs)
Total: 86 MCQs.
All 86 currently untagged (subject=null, topic=null).
"""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

# Dict of appearance_id -> (printed_q, page, skill, proposed_path, rationale)
PROPOSALS = {
    # === Agri&Allied General English 2025 (46 MCQs) ===
    # Q1-Q10: Parts of Speech
    "a432e7cc79c3bcaac975": ("Q1", 4, "Parts of Speech (Transitive Verb: 'tasted')", "english/grammar/parts-of-speech", "Identifies 'tasted' as a transitive action verb taking direct object 'the soup'."),
    "31d7c6347438f2b3be0b": ("Q2", 4, "Parts of Speech (Adverb of frequency: 'always')", "english/grammar/parts-of-speech", "Identifies 'always' as an adverb of frequency modifying verb 'cries'."),
    "e68fbecdc79c545d7249": ("Q3", 4, "Parts of Speech (Conjunction: 'Although')", "english/grammar/parts-of-speech", "Identifies 'Although' as a subordinating conjunction introducing concessive clause."),
    "2bea45fab1ad166c4b9a": ("Q4", 4, "Parts of Speech (Adverb of degree: 'quite')", "english/grammar/parts-of-speech", "Identifies 'quite' as an adverb of degree modifying adjective 'detailed'."),
    "4484df9dc50f3a4977a8": ("Q5", 4, "Parts of Speech (Demonstrative Adjective: 'that')", "english/grammar/parts-of-speech", "Identifies 'that' as a demonstrative adjective modifying noun 'house'."),
    "9fa0fd36816ffd21e0c9": ("Q6", 4, "Parts of Speech (Abstract Noun: 'courage')", "english/grammar/parts-of-speech", "Identifies 'courage' as an uncountable abstract noun."),
    "3615cbf60d6871338fea": ("Q7", 4, "Parts of Speech (Adjective: 'costly')", "english/grammar/parts-of-speech", "Identifies 'costly' as an adjective modifying noun 'array'."),
    "dd5fe95120b214e587cd": ("Q8", 4, "Parts of Speech (Adverb of degree: 'very')", "english/grammar/parts-of-speech", "Identifies 'very' as an adverb of degree modifying adjective 'clever'."),
    "9a2c8b9f0b358953360f": ("Q9", 5, "Parts of Speech (Superlative Adverb: 'least')", "english/grammar/parts-of-speech", "Identifies 'least' as an adverb modifying adjective 'expensive' in superlative degree."),
    "cef61db9e82c3911523e": ("Q10", 5, "Parts of Speech (Relative Pronoun: 'who')", "english/grammar/parts-of-speech", "Identifies 'who' as a relative pronoun introducing adjective clause."),
    
    # Q11-Q15: Idioms & Vocabulary
    "2d99b31378dfe28c6afd": ("Q11", 5, "Idioms & Proverbs ('Where ignorance is bliss, it is folly to be wise')", "english/vocabulary/idioms-and-phrases", "Tests proverb meaning: when not knowing something prevents worry, wisdom is useless."),
    "e278a88f6244ab3dca94": ("Q12", 5, "Vocabulary / Linguistic Terms ('Heteronym')", "english/vocabulary", "Identifies definition of heteronym: word with different pronunciation and meaning from another but identical spelling."),
    "3d8d28a0f8990f5a28e3": ("Q13", 5, "Idioms & Phrases ('a white elephant')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'a white elephant' (a possession that is useless and expensive to maintain)."),
    "c76f2afa25268ead72a5": ("Q14", 5, "Idioms & Phrases ('all greek to me')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'all greek to me' (incomprehensible / impossible to understand)."),
    "c6d4196a46f1a97a7374": ("Q15", 5, "Idioms & Phrases ('break a leg')", "english/vocabulary/idioms-and-phrases", "Identifies meaning of idiom 'break a leg' (wishing good luck, especially in theatrical performance)."),
    
    # Q16-Q20: Contextual Vocabulary
    "01056b577e1e8b6aa700": ("Q16", 5, "Contextual Vocabulary ('patience')", "english/vocabulary", "Sentence completion with appropriate abstract noun in context."),
    "28efff8bf813a0614344": ("Q17", 5, "Contextual Vocabulary ('bane')", "english/vocabulary", "Sentence completion with appropriate noun 'bane' (cause of great distress or annoyance)."),
    "71b888995fe2b5e1bca5": ("Q18", 5, "Contextual Vocabulary / Confusable words ('complemented')", "english/vocabulary", "Sentence completion distinguishing 'complemented' (completed/enhanced) from 'complimented'."),
    "badee66af21e49c13ce9": ("Q19", 5, "Contextual Vocabulary ('tiptoed')", "english/vocabulary", "Sentence completion with appropriate descriptive movement verb 'tiptoed'."),
    "e6e8e677b591a02bbccf": ("Q20", 6, "Contextual Vocabulary ('dismayed')", "english/vocabulary", "Sentence completion with appropriate participle adjective 'dismayed'."),
    
    # Q21-Q25: Connectors / Conjunctions
    "217d4406d1098949a031": ("Q21", 6, "Connectors / Prepositions ('prefer... to')", "english/grammar/prepositions", "Tests fixed preposition governing comparative preference: 'prefer thriller to romance'."),
    "b2e8713af2c97e225233": ("Q22", 6, "Connectors / Prepositions ('Besides')", "english/grammar/prepositions", "Tests additive preposition 'Besides' (in addition to)."),
    "ac6ad9cb50a4c7878448": ("Q23", 6, "Connectors / Conjunctions ('while')", "english/grammar/parts-of-speech", "Tests temporal conjunction 'while' introducing simultaneous action."),
    "8ffa627a121edd0d15e0": ("Q24", 6, "Connectors / Prepositions ('Despite')", "english/grammar/prepositions", "Tests concessive preposition 'Despite' preceding noun phrase."),
    "88b977df5384233d029f": ("Q25", 6, "Connectors / Conjunctions ('or else')", "english/grammar/parts-of-speech", "Tests alternative coordinating conjunction 'or else' introducing consequence."),
    
    # Q26-Q30: Prepositions
    "543eb4e0d047d1d029b3": ("Q26", 6, "Prepositions ('into the room')", "english/grammar/prepositions", "Tests preposition of motion toward interior: 'walked into'."),
    "3c7e3cb745b635505270": ("Q27", 6, "Prepositions ('acquitted of')", "english/grammar/prepositions", "Tests fixed preposition following legal verb: 'acquitted of all charges'."),
    "9ffcaad165f4b469f5c6": ("Q28", 6, "Prepositions ('Besides studying')", "english/grammar/prepositions", "Tests additive preposition 'Besides' governing gerund."),
    "ba96efa8da824d57ab93": ("Q29", 6, "Prepositions ('triumphs over')", "english/grammar/prepositions", "Tests preposition governing verb of conquest: 'triumphs over difficulties'."),
    "b5fbc78f23752eb0d081": ("Q30", 6, "Prepositions ('sparing of')", "english/grammar/prepositions", "Tests fixed preposition: 'sparing of expenditure'."),
    
    # Q31-Q40: Adjectives & Quantifiers
    "1a3f5cb7855ff42811f0": ("Q31", 7, "Degrees of Comparison ('the most charming')", "english/grammar/parts-of-speech", "Tests superlative degree of comparison of adjective."),
    "4dba09bc22815ffc2510": ("Q32", 7, "Quantifiers ('much rain')", "english/grammar/parts-of-speech", "Tests quantifier 'much' with uncountable noun 'rain' in negative clause."),
    "09b08e30e8f99c1536d6": ("Q33", 7, "Determiners ('The little food')", "english/grammar/parts-of-speech", "Tests specific minimal quantifier 'The little' modifying uncountable noun."),
    "8a9708b0ce2189637803": ("Q34", 7, "Degrees of Comparison ('the greatest villain')", "english/grammar/parts-of-speech", "Tests superlative degree of comparison with definite article."),
    "a7bee0b1a3de602c79a1": ("Q35", 7, "Kinds of Adjectives ('Adjective of Quantity')", "english/grammar/parts-of-speech", "Identifies 'enough' as an adjective of quantity."),
    "665069815c18b85cdcc7": ("Q36", 7, "Possessive Adjectives ('his / their')", "english/grammar/parts-of-speech", "Tests singular/plural agreement with possessive determiners."),
    "2897b13fc18f8ad7f443": ("Q37", 7, "Quantifiers ('many vacations')", "english/grammar/parts-of-speech", "Tests quantifier 'many' with countable plural noun 'vacations'."),
    "dff5eddd86d9ee28abcf": ("Q38", 7, "Articles / Determiners ('the head of his family')", "english/grammar/articles", "Tests definite article 'the' preceding specified unique title/role."),
    "d1d5e66d770c6e548414": ("Q39", 7, "Quantifiers ('sufficient credible evidence')", "english/grammar/parts-of-speech", "Tests appropriate quantitative adjective modifying uncountable noun 'evidence'."),
    "83ebde0468545aed53cc": ("Q40", 7, "Distributive Pronouns ('Each of us')", "english/grammar/parts-of-speech", "Tests distributive pronoun 'Each' taking singular verb."),
    
    # Q41: Sentence Structure
    "a03233fe93c875f0ca02": ("Q41", 7, "Sentence Structures (SVO / SVOC analysis)", "english/grammar", "Identifies correct syntactic clause patterns in English."),
    
    # Q46-Q50: Clauses
    "96f9d0bd93a5c7720101": ("Q46", 8, "Clauses (Adverb clause of reason: 'As he worked hard')", "english/grammar", "Identifies subordinate clause indicating cause/reason as an adverb clause of reason."),
    "35654921ab26793234d4": ("Q47", 8, "Clauses (Noun clause: 'that he would fail')", "english/grammar", "Identifies clause serving as object of transitive verb 'feared' as a noun clause."),
    "3e445073813af4a9b3ad": ("Q48", 8, "Clauses (Adverb clause of place: 'where you like')", "english/grammar", "Identifies subordinate clause indicating location as an adverb clause of place."),
    "d717fa53f72c0c65538e": ("Q49", 8, "Clauses (Noun clause: 'How the budget got in')", "english/grammar", "Identifies wh-clause serving as grammatical subject of sentence as a noun clause."),
    "45d22657c053992f545d": ("Q50", 8, "Clauses (Noun clause: 'that Latin is no longer spoken...')", "english/grammar", "Identifies that-clause serving as object of transitive verb 'know' as a noun clause."),

    # === General English - Jr. of MHS 2025 (40 MCQs) ===
    # Q1-Q5: Tenses
    "8736a5168c4daf04f4c1": ("Q1", 4, "Tenses (Simple Present habitual: 'rains')", "english/grammar/tenses", "Tests simple present tense for general climate fact: 'It rains a lot in Mizoram...'."),
    "81eee74d65a9c42726ce": ("Q2", 4, "Tenses (Present Perfect Continuous: 'has been looking')", "english/grammar/tenses", "Tests present perfect continuous tense with time marker 'since this morning'."),
    "59483e888af766b04dc2": ("Q3", 4, "Tenses (Future Continuous / Modal infinitive: 'will be waiting')", "english/grammar/tenses", "Tests future continuous / infinitive verb form with modal 'will'."),
    "574e2776dfc1b6798d9c": ("Q4", 4, "Tenses (Past Continuous: 'were playing')", "english/grammar/tenses", "Tests past continuous tense interrupted by simple past event 'started to rain'."),
    "0cb1a26e82953ef1e642": ("Q5", 4, "Tenses (Present Continuous: 'am writing')", "english/grammar/tenses", "Tests present continuous tense indicating current action of writing letter."),

    # Q6-Q10: Prepositions
    "d62d274330f522474a65": ("Q6", 4, "Prepositions ('above us')", "english/grammar/prepositions", "Tests spatial preposition indicating overhead position: 'stars above us'."),
    "7148fc93040828adbdbb": ("Q7", 4, "Prepositions ('out of the window')", "english/grammar/prepositions", "Tests compound preposition of exit/motion: 'out of the window'."),
    "18ceeea07ecba66e7113": ("Q8", 4, "Prepositions ('under the blankets')", "english/grammar/prepositions", "Tests spatial preposition indicating concealment beneath: 'under the blankets'."),
    "8f3424d57fa8ad0be341": ("Q9", 4, "Prepositions ('on me')", "english/grammar/prepositions", "Tests idiom preposition: 'had no money on me' (in one's physical possession)."),
    "76b8f6b8e93030d1314c": ("Q10", 4, "Prepositions ('glanced at')", "english/grammar/prepositions", "Tests fixed preposition governing visual verb: 'glanced at the letter'."),

    # Q11-Q15: Idioms and Phrases
    "c1d52bc4d5fb980f038e": ("Q11", 5, "Idioms and Phrases ('To get your act together')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'To get your act together' (To get organized and do things effectively)."),
    "c0312ba5bf81e7686d65": ("Q12", 5, "Idioms and Phrases ('To be snowed under')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'To be snowed under' (To be overwhelmed / very busy with work)."),
    "a5572d11b0037e0c35d1": ("Q13", 5, "Idioms and Phrases ('To stick to your guns')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'To stick to your guns' (To refuse to compromise or change convictions)."),
    "07863476f8671d292d52": ("Q14", 5, "Idioms and Phrases ('To reach one's majority')", "english/vocabulary/idioms-and-phrases", "Tests meaning of legal idiom 'To reach one's majority' (To reach legal adult age)."),
    "9f5089860940684d304d": ("Q15", 5, "Idioms and Phrases ('Takes two to tango')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'Takes two to tango' (Both parties share responsibility)."),

    # Q16-Q20: One-Word Substitution
    "f417b1c7484b6c1e4804": ("Q16", 5, "One-Word Substitution ('Conscientious')", "english/vocabulary/one-word-substitution", "Identifies 'Conscientious' (Governed by a strict sense of duty)."),
    "7182fdd46b461822f386": ("Q17", 5, "One-Word Substitution ('Articulate')", "english/vocabulary/one-word-substitution", "Identifies 'Articulate' (Fluent and clear in speech)."),
    "78d6ece4fee8277ef5e0": ("Q18", 5, "One-Word Substitution ('Epitaph')", "english/vocabulary/one-word-substitution", "Identifies 'Epitaph' (An inscription on a tomb or headstone)."),
    "d73725d9ada455732332": ("Q19", 5, "One-Word Substitution ('Amnesia')", "english/vocabulary/one-word-substitution", "Identifies 'Amnesia' (Partial or total loss of memory)."),
    "c8d25e2d8f0e68d1f2f7": ("Q20", 5, "One-Word Substitution ('Altruist')", "english/vocabulary/one-word-substitution", "Identifies 'Altruist' (One who is concerned with the welfare of others)."),

    # Q21-Q25: Idioms in sentence context
    "97dbee21b83f4723f466": ("Q21", 6, "Idioms in Context ('in the offing')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'in the offing' (about to start / likely to happen soon)."),
    "40f0a1f131e115ea9043": ("Q22", 6, "Idioms in Context ('a bird's eye view')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'a bird's eye view' (a general overview from above)."),
    "e33386cbf0c17f060e57": ("Q23", 6, "Idioms in Context ('dropping like flies')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'dropping like flies' (falling ill or collapsing in large numbers)."),
    "9d066414cdc6d90e556f": ("Q24", 6, "Idioms in Context ('cut my teeth on')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'cut one's teeth on' (acquire initial experience)."),
    "9661ac69ed7b4cd45a70": ("Q25", 6, "Idioms in Context ('taken the wind out of my sails')", "english/vocabulary/idioms-and-phrases", "Tests meaning of idiom 'taken the wind out of one's sails' (deprived of confidence or advantage)."),

    # Q26-Q30: Sentence Correction / Error Spotting
    "1dbc1d58dea5946f3efb": ("Q26", 6, "Sentence Correction (Homophone spelling: 'fair-weather friend')", "english/sentence-correction", "Corrects 'fare weather' to 'fair-weather friend'."),
    "0f6c9271a8047c6ff1f8": ("Q27", 6, "Sentence Correction (Preposition: 'between' two sisters vs 'among')", "english/sentence-correction", "Corrects 'divided among the two sisters' to 'divided between the two sisters'."),
    "5aeb7781dbefbc35f918": ("Q28", 6, "Sentence Correction (Relative pronoun agreement: 'one of the best stories that have')", "english/sentence-correction", "Corrects relative clause verb agreement following plural antecedent."),
    "f7d883d3c2386b912c05": ("Q29", 6, "Sentence Correction (Adverb formation: 'outright' vs nonstandard 'outrightly')", "english/sentence-correction", "Corrects non-standard 'outrightly' to 'outright'."),
    "f8e7f45c929acafc3738": ("Q30", 6, "Sentence Correction (Comparative preposition: 'different from' vs 'different than')", "english/sentence-correction", "Corrects 'different than' to standard 'different from'."),

    # Q31-Q35: Homophones / Confusable Words
    "74d41d714348ae35d8fb": ("Q31", 6, "Homophones / Confusable Words ('their' vs 'there' / 'they're')", "english/vocabulary", "Distinguishes possessive determiner 'their' from adverbs/contractions."),
    "470a7bc5f30b54b5f3bd": ("Q32", 6, "Homophones / Confusable Words ('sale' vs 'sail')", "english/vocabulary", "Distinguishes commercial noun 'sale' from navigation verb/noun 'sail'."),
    "d9b87911549b362ce70e": ("Q33", 7, "Homophones / Confusable Words ('route' vs 'root' / 'rout')", "english/vocabulary", "Distinguishes travel path 'route' from plant 'root' and defeat 'rout'."),
    "52bd14edc058fa6c5c81": ("Q34", 7, "Homophones / Confusable Words ('site' vs 'sight' / 'cite')", "english/vocabulary", "Distinguishes physical location 'site' from vision 'sight' and quotation 'cite'."),
    "ff95d46d9958eb98ecde": ("Q35", 7, "Homophones / Confusable Words ('chords' vs 'cords')", "english/vocabulary", "Distinguishes musical harmonic notes 'chords' from ropes/strings 'cords'."),

    # Q36-Q40: Syntax, Voice, Synonyms & Antonyms
    "1020f9560df3876d0c26": ("Q36", 7, "Sentence Transformations (Simple to Compound sentence)", "english/grammar", "Transforms simple clause to compound sentence using coordinating conjunction."),
    "64c8ec7f8afe4f161364": ("Q37", 7, "Active and Passive Voice (Simple Past: 'The fish was eaten by the cat')", "english/grammar/voice", "Converts simple past active to passive: 'The cat ate the fish' -> 'The fish was eaten by the cat'."),
    "de307e83e2015d5f99aa": ("Q38", 7, "Synonyms ('Indifferent')", "english/vocabulary/synonyms", "Identifies closest synonym of 'Indifferent' (unconcerned / detached)."),
    "24aefaec0afb0a7ddf1a": ("Q39", 7, "Antonyms ('Generous')", "english/vocabulary/antonyms", "Identifies closest antonym of 'Generous' (stingy / parsimonious)."),
    "d850c5b9e1de4a163503": ("Q40", 7, "Confusable Words ('affect' vs 'effect')", "english/vocabulary", "Distinguishes verb 'affect' (to influence/harm) from noun 'effect'.")
}

assert len(PROPOSALS) == len(packet["items"]) == 86

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
        "batch_id": 36,
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

# Preserved unextracted conventional & dropped items
unextracted_items = [
    # Agri&Allied Section A
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf",
        "document_id": "doc_74fb44237ebef4588c005e8a",
        "physical_page": 1,
        "item_type": "conventional_written_precis",
        "prompt": "Section-A Q1: Write a precis of the following passage in about one third of the original length and suggest a suitable title (10 marks) [Passage on morality serving as the spiritual and ethical compass of society].",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/precis"},
        "reason_unextracted": "Conventional written précis task answering on conventional answer sheet."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf",
        "document_id": "doc_74fb44237ebef4588c005e8a",
        "physical_page": 2,
        "item_type": "conventional_reading_comprehension",
        "prompt": "Section-A Q2: Read the passage carefully and answer the questions that follow (20 marks: Economic inequality and modern society, questions a to f).",
        "marks": 20,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None},
        "reason_unextracted": "Conventional short-answer reading comprehension questions answering on conventional answer sheet."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf",
        "document_id": "doc_74fb44237ebef4588c005e8a",
        "physical_page": 3,
        "item_type": "conventional_sentence_transformations",
        "prompt": "Section-A Q4: Change the sentences as directed (10x1=10 marks): (a) Complex sentence (b) Simple sentence (c) Compound sentence (d) Change the voice (e) Change the voice, etc.",
        "marks": 10,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/grammar", "subtopic_id": None},
        "reason_unextracted": "Conventional subjective sentence transformation and voice change tasks."
    },
    # Agri&Allied Section B dropped MCQs (Q42-Q45)
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf",
        "document_id": "doc_74fb44237ebef4588c005e8a",
        "physical_page": 8,
        "item_type": "mcq_dropped_duplicate_stem",
        "prompt": "Choose the correct sentence: 42. (a) You are paying less attention to your studies than you used to do. (b) You pay less attention to your studies than you used to do. (c) You are paying less attention to your studies than you use to do. (d) You pay less attention to your studies than you use to do.",
        "marks": 1,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None},
        "reason_unextracted": "OCR deduplication drop due to empty question stem under repeated direction 'Choose the correct sentence:' across Q41–Q45."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf",
        "document_id": "doc_74fb44237ebef4588c005e8a",
        "physical_page": 8,
        "item_type": "mcq_dropped_duplicate_stem",
        "prompt": "Choose the correct sentence: 43. (a) EM Forster wrote in a passage to India. (b) EM Forster wrote a passage to India. (c) EM Forster wrote 'A Passage to India'. (d) EM Forster wrote in 'A Passage to India'.",
        "marks": 1,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None},
        "reason_unextracted": "OCR deduplication drop due to empty question stem under repeated direction 'Choose the correct sentence:' across Q41–Q45."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf",
        "document_id": "doc_74fb44237ebef4588c005e8a",
        "physical_page": 8,
        "item_type": "mcq_dropped_duplicate_stem",
        "prompt": "Choose the correct sentence: 44. (a) My birthday will fall on Sunday next year. (b) My birthday falls on Sunday next year. (c) My birthday will fall on a Sunday next year. (d) My birthday falls on a Sunday next year.",
        "marks": 1,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None},
        "reason_unextracted": "OCR deduplication drop due to empty question stem under repeated direction 'Choose the correct sentence:' across Q41–Q45."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf",
        "document_id": "doc_74fb44237ebef4588c005e8a",
        "physical_page": 8,
        "item_type": "mcq_dropped_duplicate_stem",
        "prompt": "Choose the correct sentence: 45. (a) Everyone must respect their superiors. (b) Everyone should respect their superiors. (c) Everyone should respect his superior. (d) Each one should respect his superior.",
        "marks": 1,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/sentence-correction", "subtopic_id": None},
        "reason_unextracted": "OCR deduplication drop due to empty question stem under repeated direction 'Choose the correct sentence:' across Q41–Q45."
    },
    # Jr. of MHS Section A
    {
        "paper_id": "Old_Questions/Direct_2025-2027/General English - Jr. of MHS, 2025..pdf",
        "document_id": "doc_dab76ba7bd50a3f08ac483d2",
        "physical_page": 1,
        "item_type": "conventional_written_essay",
        "prompt": "Section-A Q1: Write an essay on any one of the following (20 marks): (a) The role of family in creating a well-adjusted society (b) Physical health leads to mental health (c) Hospital acquired infection- Prevention and Control.",
        "marks": 20,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/essay"},
        "reason_unextracted": "Conventional written essay task answering on conventional answer sheet."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/General English - Jr. of MHS, 2025..pdf",
        "document_id": "doc_dab76ba7bd50a3f08ac483d2",
        "physical_page": 1,
        "item_type": "conventional_written_precis",
        "prompt": "Section-A Q2: Write a precis of the following passage. Supply a suitable title (20 marks) [John Ruskin passage on money as secondary object for brave and educated doctors, soldiers, and clergymen].",
        "marks": 20,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/writing", "subtopic_id": "english/writing/precis"},
        "reason_unextracted": "Conventional written précis task answering on conventional answer sheet."
    },
    {
        "paper_id": "Old_Questions/Direct_2025-2027/General English - Jr. of MHS, 2025..pdf",
        "document_id": "doc_dab76ba7bd50a3f08ac483d2",
        "physical_page": 2,
        "item_type": "conventional_reading_comprehension",
        "prompt": "Section-A Q3–Q12: Read the passage, and answer the questions based on the given passage (20 marks total across questions 3 to 12: Independent opinions and beliefs, social growth, and generation values).",
        "marks": 20,
        "suggested_taxonomy": {"subject_id": "english", "topic_id": "english/comprehension", "subtopic_id": None},
        "reason_unextracted": "Conventional reading comprehension questions answering on conventional answer sheet."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(unextracted_items, indent=2) + "\n")

summary = {
    "batch": 36,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf",
            "paper_title": "Competitive Examination (Combined Technical) for Recruitment to the Posts of Agriculture & Allied Services, Government of Mizoram (November-2025) — General English",
            "document_id": "doc_74fb44237ebef4588c005e8a",
            "sha256": "896a3876c120fae7600dcea6bfb9745a6082af38464edb7addb9002e0c80aa5a",
            "targets": 46,
            "completion": "100% of extracted MCQs reviewed"
        },
        {
            "paper_id": "Old_Questions/Direct_2025-2027/General English - Jr. of MHS, 2025..pdf",
            "paper_title": "Technical Competitive Examination for Junior Grade of Mizoram Health Services (Combined) under Health & Family Welfare Department, Government of Mizoram (September-2025) — General English",
            "document_id": "doc_dab76ba7bd50a3f08ac483d2",
            "sha256": "e506b03f45c1244ccbe4c7ff6ce8363764835848bb22687bf8a4f91187d90367",
            "targets": 40,
            "completion": "100% of extracted MCQs reviewed"
        }
    ],
    "targets": 86,
    "actions": {
        "retag": 86,
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
