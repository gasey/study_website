"""Build Batch 31 review candidates, findings, written intake evidence, and summary (Lecturer Serchhip 2026 General English Q1-Q66)."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
manifest = json.load(open(out / "manifest.json"))[0]

doc_title = "Competitive Examination for Recruitment of Lecturer (Contract), Govt. Higher Secondary School, Serchhip under School Education Department, Government of Mizoram (March & April, 2026) — General English"
doc_id = manifest["document_id"]
sha256 = manifest["sha256"]
paper_id = manifest["paper_id"]

def fmt_path(cls_obj):
    if not cls_obj:
        return "unassigned"
    return cls_obj.get("subtopic_id") or cls_obj.get("topic_id") or cls_obj.get("subject_id") or "unassigned"

# (page, subj, topic, subtopic, skill, rationale, obs, issues, gap)
mapping = [
    # Q1
    (1, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of adverb of manner: 'eloquently' in 'She spoke eloquently at the conference.'",
     "Syntactic analysis of manner adverb modifying verb 'spoke'. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 1: Part-A Q1 prints 'She spoke eloquently at the conference. Identify the part of speech of the underlined word'.",
     ["Stored text omits underline indicator."], None),

    # Q2
    (1, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Define grammatical category: part of speech that expresses emotion ('Interjection').",
     "Definitional grammar identifying interjection as expression of sudden feeling/emotion. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 1: Part-A Q2 prints 'Which part of speech expresses emotion?'.",
     [], None),

    # Q3
    (1, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of subordinating conjunction 'that' in 'I believe that honesty is the best policy.'",
     "Syntactic analysis of subordinating conjunction introducing noun clause. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 1: Part-A Q3 prints '“That” in the sentence, “I believe that honesty is the best policy” is a:'.",
     [], None),

    # Q4
    (1, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Differentiate syntactic functions: usage of 'fast' as an attributive adjective ('He is a fast runner').",
     "Syntactic differentiation identifying adjective function versus adverb function of homonyms. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 1: Part-A Q4 prints 'Choose the sentence where “fast” is used as an adjective.'.",
     [], None),

    # Q5
    (1, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify pronoun classification: 'hers' as possessive pronoun in 'The blue car is hers.'",
     "Syntactic analysis of possessive pronoun functioning as predicate complement. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 1: Part-A Q5 prints 'The blue car is hers. In the sentence, “hers” is a:'.",
     [], None),

    # Q6
    (1, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify coordinating conjunction in compound sentence context ('I wanted to go, but it rained.').",
     "Syntactic analysis identifying coordinating conjunction 'but'. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 1: Part-A Q6 prints 'Which sentence contains a coordinating conjunction?'.",
     [], None),

    # Q7
    (1, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify basic part of speech: 'he' as a pronoun.",
     "Grammar classification of third-person singular personal pronoun. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 1: Part-A Q7 prints 'The word “he” is a:'.",
     [], None),

    # Q8
    (1, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Differentiate syntactic functions: usage of 'light' as a noun ('Turn on the light.').",
     "Syntactic analysis identifying noun function versus verb or adjective functions. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 1: Part-A Q8 prints 'Choose the sentence where “light” is used as a noun.'.",
     [], None),

    # Q9
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of exclamatory interjection 'Alas!' in 'Alas! He is no more.'",
     "Syntactic analysis of sorrowful interjection. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q9 prints 'Identify the part of speech of the underlined word: Alas! He is no more.'.",
     ["Stored text omits underline indicator."], None),

    # Q10
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of correlative conjunction 'either' in 'Either you apologize or you leave.'",
     "Syntactic analysis of correlative coordinating conjunction. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q10 prints 'Either you apologize or you leave. In the sentence, “either” functions as a/an:'.",
     [], None),

    # Q11
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify verb from a list of parts of speech ('Run').",
     "Part of speech vocabulary and morphological classification. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q11 prints 'Which word is a verb?'.",
     [], None),

    # Q12
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Define grammatical function: part of speech that describes a noun ('Adjective').",
     "Definitional grammar identifying adjective as noun modifier. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q12 prints 'Which part of speech describes a noun?'.",
     [], None),

    # Q13
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Define grammatical function: word that replaces a noun ('Pronoun').",
     "Definitional grammar identifying pronoun as noun substitute. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q13 prints 'Which word replaces a noun?'.",
     [], None),

    # Q14
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify noun category: common noun ('City') versus proper nouns.",
     "Grammar classification distinguishing common nouns from proper names. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q14 prints 'Which is a common noun?'.",
     [], None),

    # Q15
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Define verb classification: verb that requires a direct object to complete meaning ('Transitive verb').",
     "Definitional grammar distinguishing transitive verbs from intransitive verbs. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q15 prints 'A verb that requires a direct object to complete its meaning is:'.",
     [], None),

    # Q16
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Define grammatical function: word that describes or modifies a verb ('Adverb').",
     "Definitional grammar identifying adverb as verb modifier. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q16 prints 'Which word describes a verb?'.",
     [], None),

    # Q17
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify noun category: uncountable/mass noun ('Water') versus count nouns.",
     "Grammar classification of non-count mass nouns. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q17 prints 'Which word is an uncountable noun?'.",
     [], None),

    # Q18
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Define non-finite verb forms: non-finite verb ending in '-ing' functioning as noun ('Gerund').",
     "Grammar terminology identifying gerund versus participle. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 2: Part-A Q18 prints 'A non-finite verb ending in –ing that functions as a noun is:'.",
     [], None),

    # Q19
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify pronoun category: identifying reflexive pronoun ('Himself').",
     "Grammar classification of compound personal reflexive pronouns. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q19 prints 'Which word is a reflexive pronoun?'.",
     [], None),

    # Q20
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify transitive verb among intransitive verbs ('Read').",
     "Grammar classification of verbs capable of governing direct objects. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q20 prints 'Identify the transitive verb'.",
     [], None),

    # Q21
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify verb syntax: intransitive verb in ergative structure 'The glass broke.'",
     "Syntactic analysis identifying intransitive verb usage without object. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q21 prints 'In “The glass broke,” the verb is:'.",
     [], None),

    # Q22
    (2, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of subordinating conjunction 'before' in 'Think before you act.'",
     "Syntactic analysis of temporal conjunction introducing subordinate clause. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 2: Part-A Q22 prints 'In “Think before you act,” the word “before” is,'.",
     [], None),

    # Q23
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Define grammatical function: word that modifies verb, adjective, or another adverb ('Adverb').",
     "Definitional grammar testing role of adverb. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-A Q23 prints 'A word that modifies a verb, an adjective, or another adverb is called:'.",
     [], None),

    # Q24
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of noun 'music' in 'The music is very loud.'",
     "Syntactic analysis of noun functioning as subject. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-A Q24 prints 'The music is very loud. In this sentence, “music” is a:'.",
     [], None),

    # Q25
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify linking/copular verb from a list of verbs ('Seem').",
     "Grammar classification of copular verbs connecting subject to subjective complement. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-A Q25 prints 'Which word is a linking verb?'.",
     [], None),

    # Q26
    (3, "english", "english/grammar", "english/grammar/prepositions",
     "Choose correct dependent preposition: 'by its tail' in 'Sanga grabs the snake _________ its tail.'",
     "Prepositional usage denoting point of grasp/contact ('grab by'). Refines generic subject english to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 3: Part-A Q26 prints 'Sanga grabs the snake _________ its tail.' with option (a) by.",
     [], None),

    # Q27
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of demonstrative adjective 'This' modifying noun 'house'.",
     "Syntactic analysis of demonstrative adjective before noun. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-A Q27 prints 'This house is very big. “This” is:'.",
     [], None),

    # Q28
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of indefinite pronoun 'everyone' in passive agent phrase.",
     "Syntactic analysis of universal indefinite pronoun. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-A Q28 prints 'The criminal was condemned by everyone. “everyone” is:'.",
     [], None),

    # Q29
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of descriptive adjective 'sharp' in 'She bought a sharp knife.'",
     "Syntactic analysis of attributive adjective modifying noun 'knife'. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-A Q29 prints 'She bought a sharp knife. “sharp” is:'.",
     [], None),

    # Q30
    (3, "english", "english/grammar", "english/grammar/prepositions",
     "Choose correct preposition: 'pounce upon/on' in 'The lion pounced ____ the hunter.'",
     "Prepositional phrase collocation: verb 'pounce' followed by 'upon'. Refines generic subject english to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 3: Part-A Q30 prints 'The lion pounced ____the hunter.' with option (c) upon.",
     [], None),

    # Q31
    (3, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'exemplary' in 'She was praised for her _________ behaviour...'",
     "Contextual vocabulary and moral praise descriptors. Refines generic subject english to active topic english/vocabulary.",
     "Visual inspection of page 3: Part-A Q31 prints 'She was praised for her _________ behaviour during the crisis.'.",
     [], None),

    # Q32
    (3, "english", "english/vocabulary", None,
     "Choose contextually appropriate verb: 'expand' in 'The company plans to _________ its services...'",
     "Contextual vocabulary for corporate growth. Refines generic subject english to active topic english/vocabulary.",
     "Visual inspection of page 3: Part-A Q32 prints 'The company plans to _________ its services next year...'.",
     [], None),

    # Q33
    (3, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'lucid' in 'His explanation was so _________ that everyone understood it.'",
     "Contextual vocabulary for clear and easily understood explanation. Refines generic subject english to active topic english/vocabulary.",
     "Visual inspection of page 3: Part-A Q33 prints 'His explanation was so _________ that everyone understood it.'.",
     [], None),

    # Q34
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Apply comparative quantifier for countable nouns: 'fewer' in 'She has _________ friends than her sister.'",
     "Grammar rule for comparative quantifiers: 'fewer' used with plural countable nouns. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-A Q34 prints 'She has _________ friends than her sister.' with option (b) fewer.",
     [], None),

    # Q35
    (3, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'prone' in 'Soft minded individuals are __________ to fall for all kind of traps.'",
     "Collocational vocabulary: adjective 'prone' followed by infinitive/preposition 'to'. Refines generic subject english to active topic english/vocabulary.",
     "Visual inspection of page 3: Part-A Q35 prints 'Soft minded individuals are __________ to fall for all kind of traps.'.",
     [], None),

    # Q36
    (3, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'cogent' in 'His arguments were so _________ that no one could refute them.'",
     "Contextual vocabulary for compelling, convincing argumentation. Refines generic subject english to active topic english/vocabulary.",
     "Visual inspection of page 3: Part-A Q36 prints 'His arguments were so _________ that no one could refute them.'.",
     [], None),

    # Q37
    (4, "english", "english/grammar", "english/grammar/reported-speech",
     "Apply word order in indirect questions: subject before auxiliary verb in 'He asked me where I was going.'",
     "Reported speech syntax: indirect questions follow affirmative word order (wh-word + subject + verb). Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 4: Part-A Q37 prints 'He asked me where _________ going.' with option (b) I was.",
     [], None),

    # Q38
    (4, "english", "english/grammar", "english/grammar/subject-verb-agreement",
     "Apply subject-verb agreement for distributive pronoun 'neither of': singular verb in 'Neither of the books is interesting.'",
     "Grammar agreement rule: 'neither of + plural noun' takes singular verb 'is'. Refines generic subject english to active subtopic english/grammar/subject-verb-agreement.",
     "Visual inspection of page 4: Part-A Q38 prints 'Neither of the books _________.' with option (a) is interesting.",
     [], None),

    # Q39
    (4, "english", "english/grammar", "english/grammar/subject-verb-agreement",
     "Apply subject-verb agreement for distributive pronoun 'each of': singular verb in 'Each of the players was given a medal.'",
     "Grammar agreement rule: distributive subject 'each of' takes singular verb 'was given'. Refines generic subject english to active subtopic english/grammar/subject-verb-agreement.",
     "Visual inspection of page 4: Part-A Q39 prints 'Each of the players _________.' with option (c) was given a medal.",
     [], None),

    # Q40
    (4, "english", "english/vocabulary", "english/vocabulary/synonyms",
     "Identify synonym of 'Obdurate' ('Stubborn').",
     "Lexical vocabulary synonym identification. Refines generic subject english to active subtopic english/vocabulary/synonyms.",
     "Visual inspection of page 4: Part-A Q40 prints 'Choose the word closest in meaning to “Obdurate”.'.",
     [], None),

    # Q41
    (4, "english", "english/vocabulary", "english/vocabulary/antonyms",
     "Identify antonym of 'Ephemeral' ('Permanent').",
     "Lexical vocabulary antonym identification. Refines generic subject english to active subtopic english/vocabulary/antonyms.",
     "Visual inspection of page 4: Part-A Q41 prints 'Choose the word opposite in meaning to “Ephemeral”.'.",
     [], None),

    # Q42
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose correct collective noun: 'fleet' of ships in 'A __________ of ships were seen entering the border.'",
     "Collective noun terminology in English grammar. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Part-A Q42 prints 'A __________ of ships were seen entering the border.' with option (c) fleet.",
     [], None),

    # Q43
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose correct collective noun: 'herd' of cows in 'I saw a _________ of cows in the field.'",
     "Collective noun terminology for domesticated animals. Refines generic english/vocabulary to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Part-A Q43 prints 'I saw a _________ of cows in the field.' with option (b) herd.",
     [], None),

    # Q44
    (4, "english", "english/vocabulary", "english/vocabulary/one-word-substitution",
     "Identify one-word substitution for one who compiles a dictionary ('Lexicographer').",
     "One-word substitution vocabulary. Refines generic subject english to active subtopic english/vocabulary/one-word-substitution.",
     "Visual inspection of page 4: Part-A Q44 prints 'One who compiles a dictionary is called:'.",
     [], None),

    # Q45
    (4, "english", "english/vocabulary", "english/vocabulary/one-word-substitution",
     "Identify one-word substitution for one who knows everything ('Omniscient').",
     "One-word substitution vocabulary. Refines generic subject english to active subtopic english/vocabulary/one-word-substitution.",
     "Visual inspection of page 4: Part-A Q45 prints 'One who knows everything is called:'.",
     [], None),

    # Q46
    (4, "english", "english/vocabulary", "english/vocabulary/one-word-substitution",
     "Identify one-word substitution for one who studies stars and planets ('Astronomer').",
     "One-word substitution vocabulary distinguishing astronomer from astrologer. Refines generic subject english to active subtopic english/vocabulary/one-word-substitution.",
     "Visual inspection of page 4: Part-A Q46 prints 'One who studies stars and planets is called:'.",
     [], None),

    # Q47
    (4, "english", "english/grammar", "english/grammar/tenses",
     "Apply present continuous tense for immediate ongoing event: 'is crying' in 'Listen! The baby ________.'",
     "Tense selection based on imperative sensory marker 'Listen!'. Refines generic subject english to active subtopic english/grammar/tenses.",
     "Visual inspection of page 4: Part-A Q47 prints 'Listen! The baby ________.' with option (c) is crying.",
     [], None),

    # Q48
    (4, "english", "english/grammar", "english/grammar/tenses",
     "Apply past continuous tense for interrupted action: 'were having' in 'We __________ dinner when the phone rang.'",
     "Tense selection: past continuous interrupted by simple past clause with 'when'. Refines generic subject english to active subtopic english/grammar/tenses.",
     "Visual inspection of page 4: Part-A Q48 prints 'We __________ dinner when the phone rang.' with option (b) were having.",
     [], None),

    # Q49
    (4, "english", "english/grammar", "english/grammar/tenses",
     "Apply present perfect tense with temporal adverb: 'have finished' in 'I _________ my homework already.'",
     "Tense selection: present perfect with adverb 'already' indicating completed task with present relevance. Refines generic subject english to active subtopic english/grammar/tenses.",
     "Visual inspection of page 4: Part-A Q49 prints 'I _________ my homework already.' with option (c) have finished.",
     [], None),

    # Q50
    (5, "english", "english/grammar", "english/grammar/tenses",
     "Apply 'be going to' future form for immediate prediction based on present evidence: 'is going to rain' in 'Look at those clouds!'",
     "Future expression expressing imminent event based on visual cues. Refines generic subject english to active subtopic english/grammar/tenses.",
     "Visual inspection of page 5: Part-A Q50 prints 'Look at those clouds! It _________ rain.' with option (b) is going to.",
     [], None),

    # Q51
    (5, "english", "english/grammar", "english/grammar/tenses",
     "Apply future perfect tense for completion by future deadline: 'will have completed' in 'By next year, she _________ her degree.'",
     "Tense selection: future perfect with time marker 'By next year'. Refines generic subject english to active subtopic english/grammar/tenses.",
     "Visual inspection of page 5: Part-A Q51 prints 'By next year, she _________ her degree.' with option (d) will have completed.",
     [], None),

    # Q52
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose adversative sentence connector: 'yet' in 'He was tired, _________ he continued working.'",
     "Conjunction usage linking contrasting clauses. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-A Q52 prints 'He was tired, _________ he continued working.' with option (a) yet.",
     [], None),

    # Q53
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose negative conditional connector: 'unless' in 'You cannot succeed _________ you work hard.'",
     "Conjunction usage expressing negative condition ('if not'). Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-A Q53 prints 'You cannot succeed _________ you work hard.' with option (a) unless.",
     [], None),

    # Q54
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose temporal conjunction: 'when' in 'I will call you _________ I reach home.'",
     "Conjunction usage introducing temporal condition in future time clauses. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-A Q54 prints 'I will call you _________ I reach home.' with option (a) when.",
     [], None),

    # Q55
    (5, "english", "english/grammar", None,
     "Transform assertive sentence into exclamatory sentence: 'It is a very difficult task.' -> 'What a difficult task it is!'",
     "Sentence transformation: assertive statement with intensifier to exclamatory structure. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 5: Part-A Q55 prints 'It is a very difficult task. (Identify the exclamatory form of the sentence)'.",
     [], None),

    # Q56
    (5, "english", "english/grammar", None,
     "Transform affirmative sentence into negative sentence without changing meaning: 'He is always punctual.' -> 'He is never late.'",
     "Sentence transformation: affirmative to negative antonymic substitution. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 5: Part-A Q56 prints 'He is always punctual. (Choose the correct negative form of the sentence without changing the meaning)'.",
     [], None),

    # Q57
    (5, "english", "english/grammar", None,
     "Transform affirmative declarative sentence into negative interrogative: 'They will attend the wedding.' -> 'Will they not attend the wedding?'",
     "Sentence transformation: statement to negative interrogative structure. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 5: Part-A Q57 prints 'They will attend the wedding. (Choose the correct negative interrogative form of the sentence)'.",
     [], None),

    # Q58
    (5, "english", "english/grammar", None,
     "Identify subordinate clause type: 'because he was late' as an adverb clause of reason in 'He ran fast because he was late.'",
     "Clause analysis identifying adverbial clause explaining cause. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 5: Part-A Q58 prints 'He ran fast because he was late. Identify the underlined part of the sentence:'.",
     ["Stored text omits underline indicator."], None),

    # Q59
    (5, "english", "english/grammar", None,
     "Identify subordinate clause type: 'who won the prize' as an adjective/relative clause modifying 'The girl'.",
     "Clause analysis identifying relative clause modifying noun antecedent. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 5: Part-A Q59 prints 'The girl who won the prize is my sister. Identify the underlined part of the sentence:'.",
     ["Stored text omits underline indicator."], None),

    # Q60
    (5, "english", "english/grammar", None,
     "Identify subordinate clause type: 'what you said' as a noun clause functioning as direct object of 'believes'.",
     "Clause analysis identifying noun clause serving as grammatical object. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 5: Part-A Q60 prints 'She believes what you said. Identify the underlined part of the sentence:'.",
     ["Stored text omits underline indicator."], None),

    # Q61
    (5, "english", "english/grammar", "english/grammar/prepositions",
     "Identify structural constituent: 'at his behaviour' as a prepositional phrase in 'I was surprised at his behaviour.'",
     "Syntactic analysis identifying prepositional phrase modifier. Refines generic subject english to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 5: Part-A Q61 prints 'I was surprised at his behaviour. Identify the underlined part of the sentence:'.",
     ["Stored text omits underline indicator."], None),

    # Q62
    (6, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform direct speech to indirect speech with modal backshift and time deictic shift: 'I will finish the work tomorrow' -> 'he would finish the work the next day'.",
     "Reported speech transformation rules: modal 'will' shifts to 'would', time adverb 'tomorrow' shifts to 'the next day'. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 6: Part-A Q62 prints 'He said, “I will finish the work tomorrow.” Change into indirect speech:'.",
     [], None),

    # Q63
    (6, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform wh-interrogative direct speech to indirect speech: 'Where are you going?' -> 'She asked where I was going.'",
     "Reported speech transformation rules for wh-questions: question order shifts to declarative order with past continuous tense. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 6: Part-A Q63 prints 'She said, “Where are you going?” Change into indirect speech:'.",
     [], None),

    # Q64
    (6, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform direct speech with modal 'must' and time adverb: 'today' -> 'that day' in 'The teacher said that students must complete their assignments that day.'",
     "Reported speech transformation: preservation of modal obligation 'must' with deictic shift of 'today' to 'that day'. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 6: Part-A Q64 prints 'The teacher said, “Students must complete their assignments today.” Change into indirect speech:'.",
     [], None),

    # Q65
    (6, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform direct imperative command to indirect speech using infinitive clause: 'Open the door.' -> 'He told me to open the door.'",
     "Reported speech transformation rules for imperative commands: reporting verb 'told' followed by object and 'to-infinitive'. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 6: Part-A Q65 prints 'He said to me, “Open the door.” Change into indirect speech:'.",
     [], None),

    # Q66
    (6, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform direct speech with modal ability: 'cannot' -> 'could not' and demonstrative 'this' -> 'that' in 'She said that she could not solve that problem.'",
     "Reported speech transformation rules: modal 'cannot' backshifts to 'could not', demonstrative 'this' shifts to 'that'. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 6: Part-A Q66 prints 'She said, “I cannot solve this problem.” Change into indirect speech:'.",
     [], None),
]

assert len(mapping) == len(packet["items"]) == 66

candidates = []
findings = []
breakdown = Counter()
actions = Counter()

for it, (page, subj, top, subtop, skill, rationale, obs, issues, gap) in zip(packet["items"], mapping):
    aid = it["appearance_id"]
    cid = it["canonical_id"]
    qnum = it["appearance"]["qnum"]
    snap = it["snapshot"]
    rec = snap["record"]
    cur_cls = rec.get("classification")
    cur_path = fmt_path(cur_cls)
    fp = it["source_fingerprint"]
    
    prop_cls = dict(subject_id=subj, topic_id=top, subtopic_id=subtop)
    prop_path = subtop or top or subj
    breakdown[prop_path] += 1
    
    is_keep = (cur_path == prop_path)
    action = "keep" if is_keep else "retag"
    actions[action] += 1
    
    reason = (
        f"Verified in official Question Booklet ({doc_title}, page {page}). "
        f"{rationale} "
        f"Assessed skill: {skill}."
    )
    
    cand = {
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": paper_id,
        "source_fingerprint": fp,
        "current_primary": cur_cls,
        "proposed_primary": prop_cls,
        "proposed_related": [],
        "action": action,
        "reason": reason,
        "review_status": "pending"
    }
    candidates.append(cand)
    
    finding = {
        "canonical_id": cid,
        "appearance_id": aid,
        "qnum": str(qnum),
        "printed_question": f"Part-A Q{qnum} (p.{page})",
        "paper_id": paper_id,
        "source_identity": f"Paper: {paper_id} | Item: {qnum} (p.{page})",
        "physical_page": page,
        "current_path": cur_path,
        "proposed_path": prop_path,
        "tested_skill": skill,
        "action": action,
        "rationale": reason,
        "source_issues": issues,
        "taxonomy_gap": gap
    }
    findings.append(finding)

(out / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")

(out / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")
print(f"Saved {len(findings)} detailed findings.")

written_intake = [
    {
        "canonical_id": None,
        "appearance_id": None,
        "paper_id": paper_id,
        "document_id": doc_id,
        "sha256": sha256,
        "physical_page": 6,
        "printed_question": "Part-B Q1",
        "marks": 14,
        "type": "written",
        "prompt": "Write a precis of the following passage and provide a suitable title: Approximately 80 percent of young people who possess smartphones are capable of locating a particular video on YouTube... (Digital literacy and smartphone access patterns among youth).",
        "suggested_primary": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "status": "pending_intake_evidence"
    },
    {
        "canonical_id": None,
        "appearance_id": None,
        "paper_id": paper_id,
        "document_id": doc_id,
        "sha256": sha256,
        "physical_page": 7,
        "printed_question": "Part-B Q2",
        "marks": 10,
        "type": "written",
        "prompt": "You have come across an advertisement in a newspaper for the post of a lecturer in Lianbuanga Memorial Higher Secondary School. As candidate XXX living at MINECO, write a letter to the Principal applying for the job. Provide a suitable resume without revealing your identity.",
        "suggested_primary": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/letter"
        },
        "status": "pending_intake_evidence"
    },
    {
        "canonical_id": None,
        "appearance_id": None,
        "paper_id": paper_id,
        "document_id": doc_id,
        "sha256": sha256,
        "physical_page": 7,
        "printed_question": "Part-B Q3(a)-(e)",
        "marks": 10,
        "type": "written",
        "prompt": "Read the passage below carefully and answer the questions that follow: India is an ancient land with a long and complex history... (Questions (a)-(e) on unity in diversity and meeting place of cultures, 5x2 = 10 marks).",
        "suggested_primary": {
            "subject_id": "english",
            "topic_id": "english/comprehension",
            "subtopic_id": None
        },
        "status": "pending_intake_evidence"
    }
]
(out / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")
print(f"Saved {len(written_intake)} unextracted written items in pending-written-intake.json.")

summary = {
    "batch": 31,
    "paper_id": paper_id,
    "paper_title": doc_title,
    "document_id": doc_id,
    "sha256": sha256,
    "single_booklet_enforced": True,
    "targets": len(candidates),
    "actions": dict(actions),
    "unextracted_items_preserved": len(written_intake),
    "breakdown": dict(breakdown),
    "all_pending": True,
    "live_changes": 0
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print("Saved summary.json:", json.dumps(summary, indent=2))
