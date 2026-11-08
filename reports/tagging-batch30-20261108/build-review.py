"""Build Batch 30 review candidates, findings, written intake evidence, and summary (Radiotherapy Technologist April-2026 Paper-I General English Q1-Q60)."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
manifest = json.load(open(out / "manifest.json"))[0]

doc_title = "Competitive Examination for Recruitment to the Post of Radiotherapy Technologist (Contract) under Health & Family Welfare Department, Government of Mizoram (April, 2026) — Paper-I (General English)"
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
     "Identify part of speech of 'while' functioning as a noun in 'Sit down and rest a while.'",
     "Syntactic analysis of homonym 'while' preceded by indefinite article 'a' denoting duration/noun. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q1 prints 'Sit down and rest a while.' under Direction 'Identify the parts of Speech of the underlined words'.",
     ["Stored text omits underline indicator."], None),

    # Q2
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of preposition 'among' in 'He distributed his wealth among the poor.'",
     "Syntactic analysis of preposition governing multiple entities. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q2 prints 'He distributed his wealth among the poor.' with 'among' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q3
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of degree adverb 'so' in 'I am so sorry.'",
     "Syntactic analysis of intensifying adverb modifying predicate adjective 'sorry'. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q3 prints 'I am so sorry.' with 'so' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q4
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of coordinating conjunction 'yet' in 'He is willing, yet unable.'",
     "Syntactic analysis of adversative coordinating conjunction linking two adjectives. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q4 prints 'He is willing, yet unable.' with 'yet' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q5
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of exclamatory interjection 'Hello!' in 'Hello! How do you do?'",
     "Syntactic analysis of salutation/interjection expressing greeting. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q5 prints 'Hello! How do you do?' with 'Hello!' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q6
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of participial adjective 'emaciated' in 'There were pictures of emaciated children...'",
     "Syntactic analysis of attributive adjective modifying noun 'children'. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q6 prints 'There were pictures of emaciated children on the cover of the magazine.' with 'emaciated' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q7
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of comparative particle/adverb 'more' in 'The book is more interesting than the last one.'",
     "Syntactic analysis of degree modifier in comparative structure. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q7 prints 'The book is more interesting than the last one.' with 'more' underlined; answer is (b) Adverb.",
     ["Stored text omits underline indicator."], None),

    # Q8
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of subordinating conjunction 'after' in 'He called me after he had finished eating.'",
     "Syntactic analysis of subordinating conjunction introducing temporal clause. Refines misclassified english/vocabulary to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q8 prints 'He called me after he had finished eating.' with 'after' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q9
    (3, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of quantitative determiner/adjective 'a few' in 'Last year the company made a profit of a few million.'",
     "Syntactic analysis of indefinite numeral adjective/determiner modifying numeral noun. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 3: Section-B Q9 prints 'Last year the company made a profit of a few million.' with 'a few' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q10
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Identify part of speech of reciprocal pronoun 'one another' in 'The two countries went to war with one another over oil prices.'",
     "Syntactic analysis of reciprocal pronoun expressing mutual relationship. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q10 prints 'The two countries went to war with one another over oil prices.' with 'one another' underlined.",
     ["Stored text omits underline indicator."], None),

    # Q11
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify noun category: 'bravery' as an abstract noun in 'The soldiers were rewarded for their bravery.'",
     "Grammar classification of abstract qualities versus concrete nouns. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q11 prints 'The soldiers were rewarded for their bravery. (Type of noun)'.",
     [], None),

    # Q12
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify noun category: 'afterthought' as an abstract noun in 'She only asked me to her party as an afterthought.'",
     "Grammar classification of abstract mental concepts. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q12 prints 'She only asked me to her party as an afterthought. (Type of noun)'.",
     [], None),

    # Q13
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify noun usage: proper noun used as a common noun with definite article in 'Kalidas is often called the Shakespeare of India.'",
     "Grammar classification of proper nouns metaphorically converted to common nouns. Refines misclassified english/vocabulary to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q13 prints 'Kalidas is often called the Shakespeare of India. (Type of noun)'.",
     ["Misclassified under english/vocabulary in database; corrected to english/grammar/parts-of-speech."], None),

    # Q14
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify noun category: 'jury' as a collective noun in 'The jury has retired to consider its verdict.'",
     "Grammar classification of collective group nouns. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q14 prints 'The jury has retired to consider its verdict. (Type of noun)'.",
     [], None),

    # Q15
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify noun category: 'Rice' as a material noun in 'Rice is a staple food.'",
     "Grammar classification of material/substance nouns. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q15 prints 'Rice is a staple food. (Type of noun)'.",
     [], None),

    # Q16
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify noun category: 'Wisdom' as an abstract noun in 'Wisdom is always better than strength.'",
     "Grammar classification of intangible virtues and qualities. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q16 prints 'Wisdom is always better than strength. (Type of noun)'.",
     [], None),

    # Q17
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify verb category: 'seems' as a linking/copular verb in 'He seems happy today.'",
     "Grammar classification of linking verbs connecting subject to subjective complement. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q17 prints 'He seems happy today. (Type of verb)'.",
     [], None),

    # Q18
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify adverb category: 'beautifully' as an adverb of manner in 'She danced beautifully.'",
     "Grammar classification of adverbs modifying verb by manner. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q18 prints 'She danced beautifully. (Type of adverb)'.",
     [], None),

    # Q19
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify adjective category: 'Each' as a distributive adjective in 'Each child received a present.'",
     "Grammar classification of distributive adjectives modifying nouns individually. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q19 prints 'Each child received a present. (Type of adjective)'.",
     [], None),

    # Q20
    (4, "english", "english/grammar", "english/grammar/parts-of-speech",
     "Classify pronoun category: 'himself' as a reflexive pronoun in 'He hurt himself while playing.'",
     "Grammar classification of reflexive pronouns reflecting action back to the subject. Refines english/grammar to active subtopic english/grammar/parts-of-speech.",
     "Visual inspection of page 4: Section-B Q20 prints 'He hurt himself while playing. (Type of pronoun)'.",
     [], None),

    # Q21
    (4, "english", "english/vocabulary", "english/vocabulary/antonyms",
     "Identify antonym of 'colossal' ('petite').",
     "Vocabulary antonym identification. Refines english/vocabulary to active subtopic english/vocabulary/antonyms.",
     "Visual inspection of page 4: Section-B Q21 prints 'His colossal frame stood out among the contestants (Antonym)'.",
     [], None),

    # Q22
    (5, "english", "english/vocabulary", "english/vocabulary/antonyms",
     "Identify antonym of 'luscious' ('bland').",
     "Vocabulary antonym identification for sensory taste descriptors. Refines english/vocabulary to active subtopic english/vocabulary/antonyms.",
     "Visual inspection of page 5: Section-B Q22 prints 'The luscious sweetmeats were a hit with the quests. (Antonym)' with typo 'quests' for 'guests'.",
     ["Printed stem contains typo 'quests' instead of 'guests'."], None),

    # Q23
    (5, "english", "english/vocabulary", "english/vocabulary/antonyms",
     "Identify antonym of 'indolent' ('diligent').",
     "Vocabulary antonym identification for personality traits. Refines english/vocabulary to active subtopic english/vocabulary/antonyms.",
     "Visual inspection of page 5: Section-B Q23 prints 'The student’s indolent nature was the cause for his poor performance. (Antonym)'.",
     [], None),

    # Q24
    (5, "english", "english/vocabulary", "english/vocabulary/antonyms",
     "Identify antonym of 'denounced' ('approve').",
     "Vocabulary antonym identification for verbs of judgment/criticism. Refines english/vocabulary to active subtopic english/vocabulary/antonyms.",
     "Visual inspection of page 5: Section-B Q24 prints 'The government’s economic policy has been denounced on all sides. (Antonym)'.",
     [], None),

    # Q25
    (5, "english", "english/vocabulary", "english/vocabulary/antonyms",
     "Identify antonym of 'abundant' ('scarce').",
     "Vocabulary antonym identification for quantifiers. Refines english/vocabulary to active subtopic english/vocabulary/antonyms.",
     "Visual inspection of page 5: Section-B Q25 prints 'The garden is abundant with colourful flowers. (Antonym)'.",
     [], None),

    # Q26
    (5, "english", "english/vocabulary", "english/vocabulary/synonyms",
     "Identify synonym of 'bold' ('courageous').",
     "Vocabulary synonym identification. Refines english/vocabulary to active subtopic english/vocabulary/synonyms.",
     "Visual inspection of page 5: Section-B Q26 prints 'The bold move paid off in the end. (Synonym)'.",
     [], None),

    # Q27
    (5, "english", "english/vocabulary", "english/vocabulary/synonyms",
     "Identify synonym of 'fragile' ('delicate').",
     "Vocabulary synonym identification. Refines english/vocabulary to active subtopic english/vocabulary/synonyms.",
     "Visual inspection of page 5: Section-B Q27 prints 'This vase is fragile. (Synonym)'.",
     [], None),

    # Q28
    (5, "english", "english/vocabulary", "english/vocabulary/synonyms",
     "Identify synonym of 'gregarious' ('sociable').",
     "Vocabulary synonym identification for social character traits. Refines english/vocabulary to active subtopic english/vocabulary/synonyms.",
     "Visual inspection of page 5: Section-B Q28 prints 'My sister is a gregarious person. (Synonym)'.",
     [], None),

    # Q29
    (5, "english", "english/vocabulary", "english/vocabulary/synonyms",
     "Identify synonym of 'still' ('quiet' / calm).",
     "Vocabulary synonym identification for environmental states. Refines english/vocabulary to active subtopic english/vocabulary/synonyms.",
     "Visual inspection of page 5: Section-B Q29 prints 'It’s nice and still in this room. (Synonym)'.",
     [], None),

    # Q30
    (5, "english", "english/vocabulary", "english/vocabulary/synonyms",
     "Identify synonym of 'eccentric' ('unusual' / unconventional).",
     "Vocabulary synonym identification for distinctive behavior. Refines english/vocabulary to active subtopic english/vocabulary/synonyms.",
     "Visual inspection of page 5: Section-B Q30 prints 'His eccentric style makes him stand out. (Synonym)'.",
     [], None),

    # Q31
    (5, "english", "english/vocabulary", None,
     "Choose contextually appropriate adjective: 'stiffer' in 'As we get older, our muscles start to become _____.'",
     "Contextual vocabulary and physiological descriptions. Refines misclassified english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 5: Section-B Q31 prints 'As we get older, our muscles start to become _____.' under Direction 'Choose the correct word to fill in the blanks'.",
     [], None),

    # Q32
    (5, "english", "english/vocabulary", None,
     "Choose contextually appropriate verb: 'felicitated' in 'The students _____ the teachers on Teachers’ Day.'",
     "Contextual vocabulary distinguishing 'felicitate' (congratulate/honor) from 'facilitate'. Refines misclassified english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 5: Section-B Q32 prints 'The students _____ the teachers on Teachers’ Day.'.",
     [], None),

    # Q33
    (5, "english", "english/vocabulary", None,
     "Choose contextually appropriate verb: 'saw' in 'John _____ me coming to his table and smiled.'",
     "Contextual verb selection for visual perception. Refines misclassified english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 5: Section-B Q33 prints 'John _____ me coming to his table and smiled.'.",
     [], None),

    # Q34
    (6, "english", "english/vocabulary", None,
     "Choose contextually appropriate noun: 'astrologer' in 'The _____ claims to be able to predict your future by studying the stars.'",
     "Contextual vocabulary distinguishing astrologer from astronomer. Refines misclassified english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 6: Section-B Q34 prints 'The _____ claims to be able to predict your future by studying the stars.'.",
     [], None),

    # Q35
    (6, "english", "english/vocabulary", None,
     "Choose contextually appropriate verb: 'reprimanded' in 'The manager _____ the assistant severely for his rude behaviour.'",
     "Contextual vocabulary for disciplinary action. Refines misclassified english/grammar to active topic english/vocabulary.",
     "Visual inspection of page 6: Section-B Q35 prints 'The manager _____ the assistant severely for his rude behaviour.'.",
     [], None),

    # Q36
    (6, "english", "english/grammar", "english/grammar/subject-verb-agreement",
     "Apply subject-verb agreement rule for correlative conjunctions 'neither...nor': verb agrees with nearer subject ('children have').",
     "Grammar agreement rule: when compound subjects are joined by 'neither...nor', verb agrees with proximate plural noun. Refines english/grammar to active subtopic english/grammar/subject-verb-agreement.",
     "Visual inspection of page 6: Section-B Q36 prints 'Neither the father nor the children _____ reached.' with option (a) have.",
     [], None),

    # Q37
    (6, "english", "english/grammar", "english/grammar/subject-verb-agreement",
     "Apply subject-verb agreement rule for uncountable quantity: 'A lot of food is left out.'",
     "Grammar agreement rule: 'a lot of' followed by uncountable noun takes singular verb. Refines english/grammar to active subtopic english/grammar/subject-verb-agreement.",
     "Visual inspection of page 6: Section-B Q37 prints 'A lot of food _____ left out.' with option (b) is.",
     [], None),

    # Q38
    (6, "english", "english/grammar", "english/grammar/subject-verb-agreement",
     "Apply subject-verb agreement rule for singular individual holding dual titles: 'My employer and benefactor has come.'",
     "Grammar agreement rule: two nouns referring to the same individual governed by a single possessive pronoun take singular verb. Refines english/grammar to active subtopic english/grammar/subject-verb-agreement.",
     "Visual inspection of page 6: Section-B Q38 prints 'My employer and benefactor _____ come.' with option (b) has.",
     [], None),

    # Q39
    (6, "english", "english/grammar", "english/grammar/subject-verb-agreement",
     "Apply subject-verb agreement rule with intervening prepositional phrase: 'The Book store, with its contents, was insured.'",
     "Grammar agreement rule: parenthetical or prepositional phrases with 'with/as well as' do not alter singular subject number. Refines english/grammar to active subtopic english/grammar/subject-verb-agreement.",
     "Visual inspection of page 6: Section-B Q39 prints 'The Book store, with its contents, _____ insured.' with option (a) was.",
     [], None),

    # Q40
    (6, "english", "english/grammar", "english/grammar/subject-verb-agreement",
     "Apply subject-verb agreement rule for singular uncountable noun: 'The news... is true.'",
     "Grammar agreement rule: 'news' is singular uncountable taking singular verb. Refines english/grammar to active subtopic english/grammar/subject-verb-agreement.",
     "Visual inspection of page 6: Section-B Q40 prints 'The news being telecasted about the man _____ true.' with option (c) is.",
     [], None),

    # Q41
    (6, "english", "english/grammar", None,
     "Classify sentence by function/communicative purpose: Declarative statement in 'Gabriel is one of the best hockey player on the team.'",
     "Sentence classification identifying declarative mood. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 6: Section-B Q41 prints 'Gabriel is one of the best hockey player on the team.' under Direction 'Identify the kinds of sentences given below'.",
     [], None),

    # Q42
    (6, "english", "english/grammar", None,
     "Classify sentence by function: Exclamatory sentence in 'The house is on fire!'",
     "Sentence classification identifying exclamatory sentence conveying strong alarm. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 6: Section-B Q42 prints 'The house is on fire!'.",
     [], None),

    # Q43
    (6, "english", "english/grammar", None,
     "Classify sentence by function: Imperative sentence in 'Turn in your homework'",
     "Sentence classification identifying imperative mood expressing command/instruction. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 6: Section-B Q43 prints 'Turn in your homework'.",
     [], None),

    # Q44
    (6, "english", "english/grammar", None,
     "Classify sentence by function: Imperative sentence in 'Tell me where you found those glasses'",
     "Sentence classification identifying imperative sentence commanding direct speech. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 6: Section-B Q44 prints 'Tell me where you found those glasses'.",
     [], None),

    # Q45
    (6, "english", "english/grammar", None,
     "Classify sentence by function: Interrogative sentence in 'May I come in?'",
     "Sentence classification identifying modal interrogative request for permission. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 6: Section-B Q45 prints 'May I come in?'.",
     [], None),

    # Q46
    (6, "english", "english/grammar", None,
     "Classify sentence by function: Declarative/Assertive sentence in 'She likes cold coffee.'",
     "Sentence classification identifying assertive affirmative statement. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 6: Section-B Q46 prints 'She likes cold coffee.'.",
     [], None),

    # Q47
    (7, "english", "english/grammar", None,
     "Classify sentence by function: Imperative sentence in 'Bring me some water.'",
     "Sentence classification identifying imperative command/request. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q47 prints 'Bring me some water.'.",
     [], None),

    # Q48
    (7, "english", "english/grammar", None,
     "Classify sentence by communicative function: Command in 'Don’t be back late.'",
     "Sentence classification identifying negative imperative prohibition/command. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q48 prints 'Don’t be back late.' with option (a) Command.",
     [], None),

    # Q49
    (7, "english", "english/grammar", None,
     "Classify sentence by communicative function: Polite Request in 'Would you answer the phone?'",
     "Sentence classification identifying modal interrogative polite request. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q49 prints 'Would you answer the phone?' with option (c) Request (with printed typo 'Pupose').",
     ["Printed option (a) contains typo 'Pupose'."], None),

    # Q50
    (7, "english", "english/grammar", None,
     "Classify sentence by function: Imperative sentence in 'Call me later.'",
     "Sentence classification identifying imperative instruction. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q50 prints 'Call me later.'.",
     [], None),

    # Q51
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Complex sentence containing adverbial clause of reason in 'I was late because I missed my train.'",
     "Sentence structure analysis: independent clause joined to subordinate causal clause. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q51 prints 'I was late because I missed my train.' under Direction 'Identify the correct sentence structure for each of the given sentences'.",
     [], None),

    # Q52
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Compound sentence joined by coordinating conjunction in 'I like walking but my dog likes running.'",
     "Sentence structure analysis: two coordinate independent clauses linked by 'but'. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q52 prints 'I like walking but my dog likes running.'.",
     [], None),

    # Q53
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Compound sentence in 'Birds fly and they migrate to the south.'",
     "Sentence structure analysis: two coordinate clauses linked by 'and'. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q53 prints 'Birds fly and they migrate to the south.'.",
     [], None),

    # Q54
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Simple sentence containing single finite verb in 'On Thursday, I threw water at three funny boys.'",
     "Sentence structure analysis: single main clause with prepositional phrase adjuncts. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q54 prints 'On Thursday, I threw water at three funny boys.'.",
     [], None),

    # Q55
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Simple sentence in 'She often reads books.'",
     "Sentence structure analysis: single independent clause. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q55 prints 'She often reads books.'.",
     [], None),

    # Q56
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Simple sentence in 'She bought a new dress.'",
     "Sentence structure analysis: simple monoclausal subject-verb-object structure. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q56 prints 'She bought a new dress.'.",
     [], None),

    # Q57
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Complex sentence with relative clause in 'I remember the day that we met.'",
     "Sentence structure analysis: main clause accompanied by relative/adjective clause. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q57 prints 'I remember the day that we met.'.",
     [], None),

    # Q58
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Compound-Complex sentence in 'If I am selected for the post I will have to commute seven miles to work, so I have decided that it is not worth it.'",
     "Sentence structure analysis: multiple independent clauses connected by 'so' alongside subordinate conditional and noun clauses. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q58 prints full compound-complex multi-clause sentence.",
     [], None),

    # Q59
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Complex sentence with concessive clause in 'He loves to read even though he is sick.'",
     "Sentence structure analysis: independent clause with subordinate adverbial clause of concession. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q59 prints 'He loves to read even though he is sick.'.",
     [], None),

    # Q60
    (7, "english", "english/grammar", None,
     "Classify sentence by clause structure: Simple sentence containing non-finite infinitive phrase in 'Man struggles hard to earn a living.'",
     "Sentence structure analysis: single finite verb accompanied by infinitive of purpose. Baseline already correctly tagged; action KEEP.",
     "Visual inspection of page 7: Section-B Q60 prints 'Man struggles hard to earn a living.'.",
     [], None),
]

assert len(mapping) == len(packet["items"]) == 60

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
        "printed_question": f"Section-B Q{qnum} (p.{page})",
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
        "printed_question": "Section-A Q1",
        "marks": 10,
        "type": "written",
        "prompt": "Write an essay on any one of the given topics: Artificial Intelligence and Healthcare – pros and cons / Importance of Psychology and Mental Health lessons / Scope and Potential of Health Tourism in Mizoram.",
        "suggested_primary": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
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
        "printed_question": "Section-A Q2",
        "marks": 10,
        "type": "written",
        "prompt": "Write a précis of the following passage in about 1/3 of its original length, giving it suitable title: Trees give shade for the benefit of others, and while they themselves must stand directly in the sun and endure the scorching heat...",
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
        "physical_page": 2,
        "printed_question": "Section-A Q3",
        "marks": 10,
        "type": "written",
        "prompt": "Write a letter to the Minister, Health and Family Welfare Department, requesting for at least two qualified doctors to be posted in your village due to outbreaks and shortage of medical personnel. Sign yourself as ABC of XXX, YZ District.",
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
        "printed_question": "Section-A Q4(a)-(e)",
        "marks": 10,
        "type": "written",
        "prompt": "Read the following passage and answer the questions given below: Many people believe that science and religion are contrary to each other... (Questions (a)-(e), 5x2 = 10 marks).",
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
    "batch": 30,
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
