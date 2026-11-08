"""Build Batch 32 review candidates, findings, written intake evidence, and summary (Asst Controller of Mines March-2026 General English Q1-Q66)."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
manifest = json.load(open(out / "manifest.json"))[0]

doc_title = "Competitive Examination for Recruitment to the Post of Assistant Controller of Mines under Geology & Mining, Commerce & Industries Department, Government of Mizoram (March-2026) — General English"
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
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of possessive pronoun 'mine' in 'These dogs are mine, not hers.'",
     "Syntactic analysis of independent possessive pronoun functioning as subject complement. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q1 prints 'These dogs are mine, not hers.' under Direction 'Identify the part of speech of the underlined words'.",
     ["Stored text omits underline indicator."], None),

    # Q2
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of frequency adverb 'Always' in 'Always help others when you can.'",
     "Syntactic analysis of adverb of frequency modifying imperative verb 'help'. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q2 prints 'Always help others when you can.' with 'Always' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q3
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of coordinating conjunction 'else' in 'Work hard else you will fail.'",
     "Syntactic analysis of alternative conjunction linking coordinate clauses. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q3 prints 'Work hard else you will fail.' with 'else' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q4
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of temporal adverb 'already' in 'I have already finished my work.'",
     "Syntactic analysis of adverb of time modifying present perfect verb. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q4 prints 'I have already finished my work.' with 'already' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q5
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of degree/manner adverb 'truly' in 'He is truly a generous man.'",
     "Syntactic analysis of modifying adverb. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q5 prints 'He is truly a generous man.' with 'truly' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q6
    (3, "english", "english/grammar", "english/grammar/prepositions",
     "Identify part of speech of preposition 'within' in 'You must submit the form within three days.'",
     "Syntactic analysis of preposition of time governing noun phrase. Refines generic subject english to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 3: Part-B Q6 prints 'You must submit the form within three days.' with 'within' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q7
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of comparative determiner/adjective 'more' in 'We need more information before making a decision.'",
     "Syntactic analysis of quantifier adjective modifying uncountable noun 'information'. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q7 prints 'We need more information before making a decision.' with 'more' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q8
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of quantitative adjective 'little' in 'He has little knowledge of the subject.'",
     "Syntactic analysis of quantitative adjective modifying uncountable noun 'knowledge'. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q8 prints 'He has little knowledge of the subject.' with 'little' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q9
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of degree adverb 'enough' in 'She is old enough to travel alone.'",
     "Syntactic analysis of post-positive degree adverb modifying adjective 'old'. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q9 prints 'She is old enough to travel alone.' with 'enough' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q10
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of emphatic pronoun 'himself' in 'The manager himself inspected the mine.'",
     "Syntactic analysis of emphatic/intensive pronoun emphasizing subject. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Part-B Q10 prints 'The manager himself inspected the mine.' with 'himself' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q11
    (4, "english", "english/vocabulary", None,
     "Choose contextually appropriate verb: 'alleviate' in 'The new policies will _______ the administrative burden...'",
     "Contextual vocabulary and formal policy register. Refines generic english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 4: Part-B Q11 prints 'The new policies will _______ the administrative burden on small-scale miners.' with option (b) alleviate.",
     [], None),

    # Q12
    (4, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'steadfast' in 'Despite the challenges, the department remained _______ in its commitment...'",
     "Contextual vocabulary for unwavering determination. Refines generic english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 4: Part-B Q12 prints 'Despite the challenges, the department remained _______ in its commitment to transparency.' with option (b) steadfast.",
     [], None),

    # Q13
    (4, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'momentous' in 'The discovery of the new lithium reserve was a _______ event...'",
     "Contextual vocabulary for historic, significant occasions. Refines generic english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 4: Part-B Q13 prints 'The discovery of the new lithium reserve was a _______ event...' with option (b) momentous.",
     [], None),

    # Q14
    (4, "english", "english/vocabulary", None,
     "Choose contextually appropriate noun: 'catalyst' in 'The new regulation acts as a _______ for innovation...'",
     "Contextual vocabulary for an agent of change/stimulus. Refines generic english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 4: Part-B Q14 prints 'The new regulation acts as a _______ for innovation...' with option (b) catalyst.",
     [], None),

    # Q15
    (4, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'fraudulent' in 'The report was rejected because the data was _______...'",
     "Contextual vocabulary for fabricated or dishonest information. Refines generic english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 4: Part-B Q15 prints 'The report was rejected because the data was _______...' with option (a) fraudulent.",
     [], None),

    # Q16
    (4, "english", "english/vocabulary", None,
     "Choose contextually appropriate verb: 'placate' in 'The company tried to _______ the villagers by promising jobs...'",
     "Contextual vocabulary for pacifying or appeasing concerns. Refines generic english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 4: Part-B Q16 prints 'The company tried to _______ the villagers by promising jobs...' with option (c) placate.",
     [], None),

    # Q17
    (4, "english", "english/grammar", "english/grammar/prepositions",
     "Choose correct preposition of location: 'by the road' in 'The beggar was sitting ______ the road.'",
     "Prepositional usage denoting proximity to road. Refines generic english/grammar to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 4: Part-B Q17 prints 'The beggar was sitting ______ the road.' with option (a) by.",
     [], None),

    # Q18
    (4, "english", "english/grammar", "english/grammar/prepositions",
     "Choose correct dependent preposition: 'congratulated him on' in 'I congratulated him _____ his success...'",
     "Prepositional collocation: verb 'congratulate' takes preposition 'on'. Refines generic english/grammar to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 4: Part-B Q18 prints 'I congratulated him _____ his success in the examination.' with option (d) on.",
     [], None),

    # Q19
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose coordinating conjunction: 'yet' in 'I am beautiful ______ I am humble.'",
     "Conjunction usage expressing contrast between qualities. Refines generic english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Part-B Q19 prints 'I am beautiful ______ I am humble.' with option (a) yet.",
     [], None),

    # Q20
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose temporal subordinating conjunction: 'since' in 'Many things have happened ______ we last met.'",
     "Conjunction usage denoting elapsed time starting from past event. Refines generic english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Part-B Q20 prints 'Many things have happened ______ we last met.' with option (a) since.",
     [], None),

    # Q21
    (5, "english", "english/grammar", "english/grammar/prepositions",
     "Choose dependent preposition: 'presided over' in 'The principal presided _____ the meeting.'",
     "Prepositional phrase collocation: verb 'preside' takes 'over'. Refines generic english/grammar to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 5: Part-B Q21 prints 'The principal presided _____ the meeting.' with option (c) over.",
     [], None),

    # Q22
    (5, "english", "english/grammar", "english/grammar/prepositions",
     "Choose preposition of distribution: 'among' five boys in 'The food was divided equally ______ the five boys.'",
     "Prepositional rule: 'among' used for distribution among more than two individuals. Refines generic english/grammar to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 5: Part-B Q22 prints 'The food was divided equally ______ the five boys.' with option (d) among.",
     [], None),

    # Q23
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose concessive subordinating conjunction: 'though' in 'I wore only a shirt ____ it was very cold.'",
     "Conjunction usage introducing adverb clause of concession. Refines generic english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-B Q23 prints 'I wore only a shirt ____ it was very cold.' with option (d) though.",
     [], None),

    # Q24
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose alternative conjunction: 'otherwise' in 'Complete this level, _____ you must forfeit the game.'",
     "Conjunction usage expressing consequence of non-compliance. Refines generic english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-B Q24 prints 'Complete this level, _____ you must forfeit the game.' with option (b) otherwise.",
     [], None),

    # Q25
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Choose conditional subordinating conjunction: 'if' in 'He will come _____ I call him.'",
     "Conjunction usage introducing conditional clause. Refines generic english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-B Q25 prints 'He will come _____ I call him.' with option (c) if.",
     [], None),

    # Q26
    (5, "english", "english/grammar", "english/grammar/prepositions",
     "Choose preposition of relative vertical position: 'above' in 'Their floor is directly ______ ours.'",
     "Preposition of vertical location. Refines generic english/grammar to active subtopic english/grammar/prepositions.",
     "Visual inspection of page 5: Part-B Q26 prints 'Their floor is directly ______ ours.' with option (a) above.",
     [], None),

    # Q27
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform adverb 'bravely' to abstract noun 'bravery' in sentence context.",
     "Derivational morphology: converting manner adverb to noun form. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-B Q27 prints 'The soldiers fought bravely, but they were ultimately defeated. (to noun)' with option (c) The soldiers fought with bravery...",
     [], None),

    # Q28
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform verb 'disrupted' to abstract noun 'disruption' in sentence context.",
     "Derivational morphology: converting verb to noun form. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-B Q28 prints 'The late arrival of the Chief Guest completely disrupted the schedule. (to noun)' with option (b) ...caused complete disruption...",
     [], None),

    # Q29
    (5, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform sentence adverb 'Unluckily' to predicate adjective 'unlucky' in sentence context.",
     "Derivational morphology: converting adverb to adjective form. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 5: Part-B Q29 prints 'Unluckily, we were caught in a storm. (to adjective)' with option (c) It was unlucky that we were caught in a storm.",
     [], None),

    # Q30
    (6, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform noun phrase 'with great ease' to manner adverb 'easily' in sentence context.",
     "Syntactic transformation: converting prepositional phrase to manner adverb. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 6: Part-B Q30 prints 'She handled the diplomats with great ease. (adverb)' with option (d) She handled the diplomats easily.",
     [], None),

    # Q31
    (6, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform verb phrase 'laughed loudly' to noun phrase 'loud laughter' in sentence context.",
     "Syntactic transformation: converting verb to nominal form. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 6: Part-B Q31 prints 'He laughed loudly, which startled the sleeping baby. (to noun)' with option (b) His loud laughter startled the sleeping baby.",
     [], None),

    # Q32
    (6, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform abstract noun 'sweetness' to descriptive adjective 'sweet' in sentence context.",
     "Derivational morphology: converting noun to adjective. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 6: Part-B Q32 prints 'The sweetness of her voice was captivating. (to adjective)' with option (a) Her sweet voice was captivating.",
     [], None),

    # Q33
    (6, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform adjective 'firm' to manner adverb 'firmly' in sentence context.",
     "Derivational morphology: converting adjective to adverb. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 6: Part-B Q33 prints 'I want you to be firm in holding on to your beliefs. (adverb)' with option (a) I want you to hold firmly to your beliefs.",
     [], None),

    # Q34
    (6, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform predicate adjective 'lonely' to abstract noun 'loneliness' in sentence context.",
     "Derivational morphology: converting adjective to abstract noun. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 6: Part-B Q34 prints 'Even among a crowd, she felt lonely. (to noun)' with option (d) Even among a crowd, she felt a sense of loneliness.",
     [], None),

    # Q35
    (6, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform adverb 'wrongly' to attributive adjective 'wrong' in sentence context.",
     "Derivational morphology: converting adverb to adjective. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 6: Part-B Q35 prints 'He was wrongly accused of theft. (adjective)' with option (a) The accusation against him was wrong.",
     [], None),

    # Q36
    (6, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Transform noun phrase 'take great pride' to predicate adjective 'proud' in sentence context.",
     "Syntactic transformation: converting noun expression to adjective. Refines generic subject english to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 6: Part-B Q36 prints 'I take great pride in your achievements. (to adjective)' with option (d) I am proud of your achievements.",
     [], None),

    # Q37
    (7, "english", "english/grammar", None,
     "Classify sentence by function/mood: Imperative sentence in 'Please submit your verification documents...'",
     "Sentence classification identifying polite imperative request/instruction. Refines generic english/grammar to verified topic.",
     "Visual inspection of page 7: Part-B Q37 prints 'Identify the type of sentence: “Please submit your verification documents by the end of the day.”' with option (b) Imperative.",
     [], None),

    # Q38
    (7, "english", "english/grammar", None,
     "Identify complex sentence structure containing subordinate clause of concession ('Although the weather was harsh...').",
     "Sentence classification distinguishing complex sentence from compound sentences. Refines generic english/grammar to verified topic.",
     "Visual inspection of page 7: Part-B Q38 prints 'Which of the following is a ‘Complex’ sentence?' with option (b).",
     [], None),

    # Q39
    (7, "english", "english/grammar", None,
     "Identify compound sentence structure joined by coordinating conjunction: 'The motor started, and the lights flickered.'",
     "Sentence classification identifying two independent clauses joined by 'and'. Refines generic english/grammar to verified topic.",
     "Visual inspection of page 7: Part-B Q39 prints 'Identify the structure: “The motor started, and the lights flickered.”' with option (b) Compound.",
     [], None),

    # Q40
    (7, "english", "english/grammar", None,
     "Classify sentence by function/mood: Assertive/Declarative statement in 'The notification regarding the mining lease will be issued next week.'",
     "Sentence classification identifying affirmative declarative mood. Refines generic english/grammar to verified topic.",
     "Visual inspection of page 7: Part-B Q40 prints 'Identify the type of sentence: “The notification regarding the mining lease will be issued next week.”' with option (a) Assertive.",
     [], None),

    # Q41
    (7, "english", "english/grammar", None,
     "Identify optative sentence expressing a wish/prayer: 'May the newly appointed officers succeed in their mission.'",
     "Sentence classification identifying optative sentence constructed with modal 'May'. Refines generic english/grammar to verified topic.",
     "Visual inspection of page 7: Part-B Q41 prints 'Choose the sentence that functions as an ‘Optative’ sentence:' with option (b).",
     [], None),

    # Q42
    (7, "english", "english/grammar", None,
     "Identify phrase constituent: 'with the gold medal' as an adjective phrase modifying 'The man'.",
     "Phrase analysis identifying prepositional phrase functioning as adjective. Refines misclassified english/vocabulary to active topic english/grammar.",
     "Visual inspection of page 7: Part-B Q42 prints 'Identify the underlined phrase: “The man with the gold medal is my brother.”' with option (b) Adjective phrase.",
     [], None),

    # Q43
    (7, "english", "english/grammar", None,
     "Identify phrase constituent: 'To win the national championship' as a noun phrase/infinitive functioning as subject.",
     "Phrase analysis identifying infinitive phrase functioning as noun subject. Refines misclassified english/vocabulary to active topic english/grammar.",
     "Visual inspection of page 7: Part-B Q43 prints 'Identify the underlined phrase: “To win the national championship is his dream.”' with option (a) Noun phrase.",
     [], None),

    # Q44
    (7, "english", "english/grammar", None,
     "Identify phrase constituent: 'with extreme caution' as an adverb phrase modifying verb 'drove'.",
     "Phrase analysis identifying prepositional phrase functioning as adverb of manner. Refines misclassified english/vocabulary to active topic english/grammar.",
     "Visual inspection of page 7: Part-B Q44 prints 'Identify the underlined phrase: “He drove the car with extreme caution.”' with option (c) Adverb phrase.",
     [], None),

    # Q45
    (7, "english", "english/grammar", None,
     "Identify clause constituent: 'because he was assigned to inspect the quarry' as an adverb clause of reason.",
     "Clause analysis identifying subordinate adverbial clause explaining motivation. Refines generic english/grammar to verified topic.",
     "Visual inspection of page 7: Part-B Q45 prints 'In the sentence “The geologist visited the site because he was assigned to inspect the quarry”, the underlined portion is:' with option (b) Adverb clause of reason.",
     [], None),

    # Q46
    (7, "english", "english/grammar", None,
     "Identify clause constituent: 'who completed the training' as an adjective/relative clause modifying 'The workers'.",
     "Clause analysis identifying relative clause describing antecedent noun. Refines generic english/grammar to verified topic.",
     "Visual inspection of page 7: Part-B Q46 prints 'Identify the underlined clause: “The workers who completed the safety training received certificates.”' with option (c) Adjective clause.",
     [], None),

    # Q47
    (8, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform direct imperative command to indirect speech: 'Show me your permit' -> 'The officer ordered the worker to show him his permit.'",
     "Reported speech transformation rules for commands: reporting verb 'ordered' followed by object and 'to-infinitive'. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 8: Part-B Q47 prints 'The officer said to the worker, “Show me your permit.”' with option (a).",
     [], None),

    # Q48
    (8, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform negative direct command to indirect speech: 'Don’t enter the restricted area' -> 'He ordered/told me not to enter...'",
     "Reported speech transformation rules: negative imperative with 'not to + verb'. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 8: Part-B Q48 prints 'He said to me, “Don’t enter the restricted area.”' with option (c) He told me not to enter the restricted area.",
     [], None),

    # Q49
    (8, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform indirect command back to direct speech: 'The supervisor ordered the workers to wear their safety helmets.' -> '“Wear your safety helmets,” said the supervisor.'",
     "Reported speech inverse transformation restoring direct imperative statement. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 8: Part-B Q49 prints indirect command with option (b) direct imperative.",
     [], None),

    # Q50
    (8, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform indirect warning back to direct speech: 'The father warned his son not to waste his time.' -> '“Do not waste your time,” said the father to his son.'",
     "Reported speech inverse transformation restoring negative imperative. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 8: Part-B Q50 prints indirect warning with option (b) direct speech.",
     [], None),

    # Q51
    (8, "english", "english/grammar", "english/grammar/reported-speech",
     "Transform direct speech in present perfect to indirect speech in past perfect: 'I have submitted the report' -> 'The clerk said that he had submitted the report.'",
     "Reported speech tense backshift: present perfect 'have submitted' shifts to past perfect 'had submitted'. Refines generic subject english to active subtopic english/grammar/reported-speech.",
     "Visual inspection of page 8: Part-B Q51 prints '“I have submitted the report,” said the clerk.' with option (a).",
     [], None),

    # Q52
    (8, "english", "english/grammar", None,
     "Identify clause constituent: 'where he lives' as a noun clause functioning as direct object of 'cannot find'.",
     "Clause analysis identifying noun clause direct object. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 8: Part-B Q52 prints 'We cannot find where he lives.' with option (a) noun clause.",
     [], None),

    # Q53
    (8, "english", "english/grammar", None,
     "Identify clause constituent: 'how it happened' as a noun clause functioning as direct object of 'do not know'.",
     "Clause analysis identifying wh-noun clause direct object. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 8: Part-B Q53 prints 'I do not know how it happened.' with option (d) noun clause.",
     [], None),

    # Q54
    (8, "english", "english/grammar", None,
     "Identify clause constituent: 'that you lent me' as an adjective clause modifying noun 'The book'.",
     "Clause analysis identifying relative/adjective clause. Refines generic english/grammar to verified topic.",
     "Visual inspection of page 8: Part-B Q54 prints 'The book that you lent me was very informative.' with option (c) adjective clause.",
     [], None),

    # Q55
    (8, "english", "english/grammar", None,
     "Identify phrase constituent: 'for two hours' as an adverb phrase of duration modifying verb 'has been waiting'.",
     "Phrase analysis identifying prepositional phrase functioning as adverb of time/duration. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 9: Part-B Q55 prints 'She has been waiting for two hours.' with option (a) adverb phrase.",
     [], None),

    # Q56
    (8, "english", "english/grammar", None,
     "Identify clause constituent: 'What he said' as a noun clause functioning as grammatical subject of sentence.",
     "Clause analysis identifying nominal relative clause as subject. Refines generic subject english to active topic english/grammar.",
     "Visual inspection of page 9: Part-B Q56 prints 'What he said surprised everyone present there.' with option (b) noun clause.",
     [], None),

    # Q57
    (9, "english", "english/vocabulary", "english/vocabulary/one-word-substitution",
     "Identify one-word substitution for favoritism shown to relatives in appointment/business: 'nepotism'.",
     "One-word substitution vocabulary. Refines generic english/grammar to active subtopic english/vocabulary/one-word-substitution.",
     "Visual inspection of page 9: Part-B Q57 prints 'The former Head was accused of ______ since so many of his relatives were appointed.' with option (c) nepotism.",
     [], None),

    # Q58
    (9, "english", "english/vocabulary", "english/vocabulary/one-word-substitution",
     "Identify one-word substitution for one who donates generously to good causes: 'philanthropist'.",
     "One-word substitution vocabulary. Refines generic english/grammar to active subtopic english/vocabulary/one-word-substitution.",
     "Visual inspection of page 9: Part-B Q58 prints 'The late millionaire was a famous ______, who donated generously...' with option (b) philanthropist.",
     [], None),

    # Q59
    (9, "english", "english/vocabulary", "english/vocabulary/one-word-substitution",
     "Identify one-word substitution for lasting only a very short time: 'ephemeral' / 'transient'.",
     "One-word substitution vocabulary. Refines generic english/grammar to active subtopic english/vocabulary/one-word-substitution.",
     "Visual inspection of page 9: Part-B Q59 prints 'Life is so ______, with everything fading away so quickly.' with option (c) transient.",
     [], None),

    # Q60
    (9, "english", "english/vocabulary", "english/vocabulary/one-word-substitution",
     "Identify one-word substitution for drawing ideas from broad and diverse sources: 'eclectic'.",
     "One-word substitution vocabulary. Refines generic english/grammar to active subtopic english/vocabulary/one-word-substitution.",
     "Visual inspection of page 9: Part-B Q60 prints 'His designs are derived from many diverse sources, and are truly ______.' with option (a) eclectic.",
     [], None),

    # Q61
    (9, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'particular' / 'fastidious' in 'She was very ______ about her diet...'",
     "Contextual vocabulary for being selective/careful about food. Refines generic english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 9: Part-B Q61 prints 'She was very ______ about her diet, opting to eat only locally grown vegetables.' with option (b) particular.",
     [], None),

    # Q62
    (9, "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
     "Identify idiomatic meaning: 'Barking up the wrong tree' (pursuing a mistaken line of thought or course of action).",
     "Idiomatic English usage. Refines generic subject english to active subtopic english/vocabulary/idioms-and-phrases.",
     "Visual inspection of page 9: Part-B Q62 prints 'Barking up the wrong tree' with option (d) looking for solutions in the wrong place.",
     [], None),

    # Q63
    (9, "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
     "Identify idiomatic meaning: 'a rite of passage' (a ceremony or event marking an important stage in someone's life).",
     "Idiomatic English usage. Refines generic subject english to active subtopic english/vocabulary/idioms-and-phrases.",
     "Visual inspection of page 9: Part-B Q63 prints 'a rite of passage' with option (c) an event marking a new stage in life.",
     [], None),

    # Q64
    (10, "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
     "Identify idiomatic meaning: 'to end in smoke' (to come to nothing / yield no practical result).",
     "Idiomatic English usage. Refines generic subject english to active subtopic english/vocabulary/idioms-and-phrases.",
     "Visual inspection of page 10: Part-B Q64 prints 'to end in smoke' with option (a) to come to nothing.",
     [], None),

    # Q65
    (10, "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
     "Identify idiomatic meaning: 'to harp on the same string' (to dwell on or repeat a subject tiresomely).",
     "Idiomatic English usage. Refines generic subject english to active subtopic english/vocabulary/idioms-and-phrases.",
     "Visual inspection of page 10: Part-B Q65 prints 'to harp on the same string' with option (c) to repeat the same words again and again.",
     [], None),

    # Q66
    (10, "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
     "Identify idiomatic meaning: 'to give oneself airs' (to behave arrogantly or pretentiously).",
     "Idiomatic English usage. Refines generic subject english to active subtopic english/vocabulary/idioms-and-phrases.",
     "Visual inspection of page 10: Part-B Q66 prints 'to give oneself airs' with option (b) to behave arrogantly.",
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
        "printed_question": f"Part-B Q{qnum} (p.{page})",
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
        "physical_page": 1,
        "printed_question": "Part-A Q1",
        "marks": 14,
        "type": "written",
        "prompt": "Write a precis of the following passage, giving it a suitable title: Social media has revolutionized tourism by acting as a primary source for travel inspiration, research, and booking, with 75% of people using it to decide on destinations... ('Instatourism', visual storytelling, aesthetics, overtourism).",
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
        "physical_page": 1,
        "printed_question": "Part-A Q2",
        "marks": 10,
        "type": "written",
        "prompt": "You are the Assistant Controller of Mines posted in Siaha district. Illegal mining activities have been reported in a remote area under your jurisdiction. Preliminary verification indicates unauthorized extraction and transportation of minerals. Write a letter to the Director, Commerce & Industries Department, Govt. of Mizoram reporting the situation, outlining the steps taken so far, and requesting additional manpower and technological support to curb the illegal activity. Sign as XYZ of ABC Locality (Veng), Aizawl.",
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
        "physical_page": 2,
        "printed_question": "Part-A Q3(i)-(iv)",
        "marks": 10,
        "type": "written",
        "prompt": "Read the following passage, and answer the questions below: As a kid, I spent my summers with my grandparents on their ranch in Texas… (Extracted from Jeff Bezos 2010 Princeton speech on kindness versus cleverness). Questions (i)-(iv) totaling 10 marks (2+3+3+2).",
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
    "batch": 32,
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
