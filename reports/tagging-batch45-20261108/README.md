# Pending source-reviewed tagging — Batch 45: ADA, AA & ATA General English (60 MCQs)

Policy: `study-tagging-v1`. **60 existing questions reviewed: 58 retag proposals, 2 keep decisions, 0 tag holds. All 60 remain pending. Zero live changes, submissions or publications.**

## Target Paper & 100% Paper Completion Milestone

This batch achieves 100% source review of the extracted MCQs for the companion General English paper to the Batch 44 Arithmetic booklet:
- *Competitive Examinations for Recruitment to the Posts of Assistant Auditor, Assistant Treasury Accountant & Assistant Divisional Accountant under Finance Department, Government of Mizoram (January 2019) — General English* (`Old_Questions/Direct_2019-2020/ADA, AA & ATA General English.pdf`, `doc_28eafb04c21bfc501a33c583`, 60 MCQs, 100% paper completion).

## Single-Booklet Deduplication Status

- **Booklet Status:** Single-booklet direct recruitment examination with no alternate series or duplicate copies in the repository.

## Untagged Baseline Rectification

In the production database, all 60 items had unclassified coarse baseline tags (`current_subject: 'gk'`, `current_topic: 'ADA, AA & ATA General English'`). All 60 have been reviewed against official question text and structured into precise active taxonomy paths:
- `english/grammar/parts-of-speech` (25 items):
  - Nouns: abstract noun ('Laughter'), collective noun ('crowd'), common noun ('Grammar').
  - Verbs & Verbals: transitive verb ('hurt'), gerunds ('Hunting', 'hoarding', 'Swimming', 'Giving', 'receiving', 'smoking'), participles / participial adjectives ('swimming pool', 'losing game', 'standing building').
  - Adjectives: predicate adjective ('true'), substantive descriptive adjective ('courageous').
  - Adverbs: adverb of degree ('quite'), adverb of manner ('fast').
  - Interjections: 'Bravo!'.
  - Conjunctions: adversative ('but'), concessive ('though'), causal ('Since'), explanatory ('for'), alternative ('else'), temporal ('before'), negative conditional ('Unless').
  - Spatial Preposition: 'over'.
- `english/grammar` (19 items):
  - Modal Notions & Sentence Functions (10 items): possibility ('may'), obligation ('must'), direct command / order ('Get out'), polite request ('Would you kindly'), habitual action ('usually travel'), purpose ('to save his friend', 'just to see you'), wish / prayer ('May you be blessed'), moral duty ('must stand for what is right'), condition ('only if').
  - Traditional Sentence Types (9 items): interrogative ('Who among the two boys...'), assertive declarative ('Nature is the best physician' [KEEP], 'Daphne is the tallest...', 'Today is a fine day'), imperative ('Have mercy on us', 'Shut the door at once'), exclamatory ('How very cold the night is!'), optative/blessing ('May you have all the joy...'), negative statement ('You cannot have all the riches...').
- `english/grammar/prepositions` (7 items):
  - Prepositions of time ('since yesterday'), objective preposition ('fought for the crown'), motion ('into my parlour'), idiomatic usage ('rise with the lark', 'By the name of God'), position ('sits among his boys', 'across her breast' [KEEP]).
- `english/grammar/subject-verb-agreement` (9 items):
  - Prepositional intervener ('quality of the mangoes was'), 'one of' singular agreement ('one of the volcanic eruptions takes place'), compound subject with and ('Fire and water do not agree'), single composite unit ('horse and carriage is'), correlative conjunction ('Neither praise nor blame seems'), branch of science ('Physics is'), collective noun divided ('Committee were divided'), proper book title ('The Arabian Nights is'), fraction of uncountable whole ('Three parts of the business is left').
- **Fresh Oracle read-only export:** `2026-11-07T20:48:12.871085+00:00`. Readback validation (`2026-11-07T20:50:14.219340+00:00`) confirmed 100% source fingerprint consistency, zero live mutations, and 100% compliance with active taxonomy nodes.

## Before / after table

| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | Q1 (p. 2) | Parts of Speech (Transitive Verb) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'hurt' functioning as a transitive verb in the predicate. |
| 2 | Q2 (p. 2) | Parts of Speech (Common Noun) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'Grammar' functioning as a noun naming a systematic body of rules. |
| 3 | Q3 (p. 2) | Parts of Speech (Predicate Adjective) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'true' functioning as a predicate adjective following linking verb 'sounds'. |
| 4 | Q4 (p. 2) | Noun Classes (Abstract Noun) | `english` | `english/grammar/parts-of-speech` | **retag** — Classifies 'Laughter' as an abstract noun denoting a state or emotion. |
| 5 | Q5 (p. 2) | Noun Classes (Collective Noun) | `english` | `english/grammar/parts-of-speech` | **retag** — Classifies 'crowd' as a collective noun denoting a collection of persons. |
| 6 | Q6 (p. 2) | Parts of Speech (Adverb of Degree) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'quite' functioning as an adverb of degree modifying adjective 'big'. |
| 7 | Q7 (p. 2) | Parts of Speech (Adverb of Manner) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'fast' functioning as an adverb of manner modifying verb 'runs'. |
| 8 | Q8 (p. 2) | Parts of Speech (Interjection) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies exclamatory word 'Bravo!' as an interjection expressing praise/approval. |
| 9 | Q9 (p. 2) | Parts of Speech (Descriptive Adjective) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'courageous' functioning as a descriptive adjective used substantively with definite article. |
| 10 | Q10 (p. 2) | Parts of Speech (Preposition) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'over' functioning as a spatial preposition showing relation between 'balloon' and 'fan'. |
| 11 | Q11 (p. 3) | Modal Notions (Possibility) | `english` | `english/grammar` | **retag** — Identifies modal auxiliary 'may' expressing possibility in 'It may rain tomorrow'. |
| 12 | Q12 (p. 3) | Modal Notions (Obligation) | `english` | `english/grammar` | **retag** — Identifies modal auxiliary 'must' expressing moral duty and obligation in 'One must always respect the elders'. |
| 13 | Q13 (p. 3) | Sentence Function (Order / Command) | `english` | `english/grammar` | **retag** — Identifies imperative sentence 'Get out of the room now' functioning as a direct order. |
| 14 | Q14 (p. 3) | Sentence Function (Polite Request) | `english` | `english/grammar` | **retag** — Identifies conditional modal question with 'Would you kindly' functioning as a polite request. |
| 15 | Q15 (p. 3) | Aspect & Habitual Action | `english` | `english/grammar` | **retag** — Identifies simple present with frequency adverb 'usually' expressing habitual action. |
| 16 | Q16 (p. 3) | Clause Purpose | `english` | `english/grammar` | **retag** — Identifies infinitive phrase 'to save his friend' expressing purpose. |
| 17 | Q17 (p. 3) | Optative Mood (Wish / Prayer) | `english` | `english/grammar` | **retag** — Identifies optative construction 'May you be blessed' expressing a wish or blessing. |
| 18 | Q18 (p. 3) | Modal Notions (Moral Obligation / Advice) | `english` | `english/grammar` | **retag** — Identifies modal 'must' expressing ethical duty/advice in 'You must stand for what is right'. |
| 19 | Q19 (p. 3) | Clause Purpose | `english` | `english/grammar` | **retag** — Identifies infinitive of purpose 'just to see you' denoting intention. |
| 20 | Q20 (p. 3) | Conditional Sentence | `english` | `english/grammar` | **retag** — Identifies subordinate clause introduced by 'only if' expressing condition. |
| 21 | Q21 (p. 3) | Prepositions of Time | `english` | `english/grammar/prepositions` | **retag** — Selects 'since' denoting a point of origin in time with negative perfect tense. |
| 22 | Q22 (p. 3) | Dependent Prepositions (fight for) | `english` | `english/grammar/prepositions` | **retag** — Selects preposition 'for' expressing the objective/prize in 'fought for the crown'. |
| 23 | Q23 (p. 4) | Prepositions of Direction / Motion | `english` | `english/grammar/prepositions` | **retag** — Selects preposition of motion 'into' in poetic quotation 'walk into my parlour'. |
| 24 | Q24 (p. 4) | Idiomatic Preposition (with the lark) | `english` | `english/grammar/prepositions` | **retag** — Selects preposition 'with' in traditional idiom 'rise with the lark' meaning very early. |
| 25 | Q25 (p. 4) | Fixed Prepositional Idiom (by God) | `english` | `english/grammar/prepositions` | **retag** — Selects 'By' for swearing an oath in 'By the name of God he swore'. |
| 26 | Q26 (p. 4) | Prepositions of Position (among) | `english` | `english/grammar/prepositions` | **retag** — Selects 'among' for position surrounded by plural persons ('sits among his boys'). |
| 27 | Q27 (p. 4) | Prepositions of Position (across) | `english/grammar/prepositions` | `english/grammar/prepositions` | **keep** — Confirms exact active subtopic for spatial preposition 'across' ('Her arms across her breast she laid'). |
| 28 | Q28 (p. 4) | Adversative Conjunction (but) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects coordinating conjunction 'but' introducing an unexpected contrast ('ran fast, but I missed'). |
| 29 | Q29 (p. 4) | Concessive Conjunction (though) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects subordinating conjunction of concession 'though' ('finished first though he began late'). |
| 30 | Q30 (p. 4) | Causal Conjunction (Since) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects subordinating conjunction 'Since' expressing reason/cause ('Since duty calls us we must obey'). |
| 31 | Q31 (p. 4) | Explanatory Coordinating Conjunction (for) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects coordinating conjunction 'for' denoting reason in biblical proverb ('for they shall obtain mercy'). |
| 32 | Q32 (p. 4) | Alternative Conjunction (else) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects alternative conjunction 'else' meaning otherwise ('Give me the drink, else I shall die'). |
| 33 | Q33 (p. 4) | Temporal Conjunction (before) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects subordinating temporal conjunction 'before' ('died before I was born'). |
| 34 | Q34 (p. 4) | Conditional Conjunction (Unless) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects negative conditional conjunction 'Unless' ('Unless you tell me the truth...'). |
| 35 | Q35 (p. 5) | Verbals (Gerund as Subject) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'Hunting' functioning as a verbal noun / gerund subject of sentence. |
| 36 | Q36 (p. 5) | Verbals (Gerund as Prepositional Object) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'hoarding' functioning as a gerund object of preposition 'of'. |
| 37 | Q37 (p. 5) | Verbals (Participial Adjective) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'swimming' in 'swimming pool' as a participle/noun-adjunct functioning adjectivally. |
| 38 | Q38 (p. 5) | Verbals (Gerund as Subject) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'Swimming' functioning as a gerund subject. |
| 39 | Q39 (p. 5) | Verbals (Participial Adjective) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'losing' modifying noun 'game' as a present participle. |
| 40 | Q40 (p. 5) | Verbals (Gerund in Comparison) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'Giving' and 'receiving' functioning as gerunds compared with 'better than'. |
| 41 | Q41 (p. 5) | Verbals (Participial Adjective) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'standing' modifying 'building' as a present participle. |
| 42 | Q42 (p. 5) | Verbals (Gerund as Subject Complement) | `english` | `english/grammar/parts-of-speech` | **retag** — Identifies 'smoking' functioning as a gerund predicate complement after 'is'. |
| 43 | Q43 (p. 5) | Sentence Classification (Interrogative) | `english` | `english/grammar` | **retag** — Classifies question with inverted structure and question mark as an interrogative sentence. |
| 44 | Q44 (p. 5) | Sentence Classification (Assertive) | `english/grammar` | `english/grammar` | **keep** — Confirms active topic for declarative statement 'Nature is the best physician'. |
| 45 | Q45 (p. 5) | Sentence Classification (Imperative) | `english` | `english/grammar` | **retag** — Classifies prayer/request 'Have mercy on us' with implied subject 'you' as an imperative sentence. |
| 46 | Q46 (p. 5) | Sentence Classification (Assertive) | `english` | `english/grammar` | **retag** — Classifies declarative sentence 'Daphne is the tallest girl in her class' as assertive. |
| 47 | Q47 (p. 5) | Sentence Classification (Exclamatory) | `english` | `english/grammar` | **retag** — Classifies exclamatory statement 'How very cold the night is!' expressing strong emotion. |
| 48 | Q48 (p. 6) | Sentence Classification (Exclamatory / Optative) | `english` | `english/grammar` | **retag** — Classifies blessing/wish 'May you have all the joy...' in traditional sentence taxonomy. |
| 49 | Q49 (p. 6) | Sentence Classification (Negative) | `english` | `english/grammar` | **retag** — Classifies negative declarative statement 'You cannot have all the riches...'. |
| 50 | Q50 (p. 6) | Sentence Classification (Assertive) | `english` | `english/grammar` | **retag** — Classifies affirmative declarative statement 'Today is a fine day' as assertive. |
| 51 | Q51 (p. 6) | Sentence Classification (Imperative) | `english` | `english/grammar` | **retag** — Classifies direct command 'Shut the door at once' as an imperative sentence. |
| 52 | Q52 (p. 6) | Subject-Verb Agreement (Prepositional Intervener) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects singular past verb 'was' agreeing with head noun 'quality', not intervening plural 'mangoes'. |
| 53 | Q53 (p. 6) | Subject-Verb Agreement (One of + Plural Noun) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects singular verb 'takes' agreeing with singular subject 'one'. |
| 54 | Q54 (p. 6) | Subject-Verb Agreement (Compound Subject) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects plural auxiliary 'do' with compound subject joined by and ('Fire and water do not agree'). |
| 55 | Q55 (p. 6) | Subject-Verb Agreement (Single Combined Unit) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects singular verb 'is' for compound subject expressing a single integrated unit ('The horse and carriage is at the door'). |
| 56 | Q56 (p. 6) | Subject-Verb Agreement (Correlative Conjunction) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects singular verb 'seems' agreeing with nearer singular subject 'blame' in 'Neither praise nor blame'. |
| 57 | Q57 (p. 6) | Subject-Verb Agreement (Singular Field of Study) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects singular verb 'is' for subject 'Physics' naming a branch of science. |
| 58 | Q58 (p. 6) | Subject-Verb Agreement (Collective Noun Divided) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects plural verb 'are' / 'were' for collective noun 'Committee' acting individually / divided in opinion. |
| 59 | Q59 (p. 7) | Subject-Verb Agreement (Book Title as Proper Noun) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects singular verb 'is' for title of a single book 'The Arabian Nights'. |
| 60 | Q60 (p. 7) | Subject-Verb Agreement (Fraction of an Uncountable Whole) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects singular verb 'is' for fraction of singular/uncountable whole 'Three parts of the business is left'. |

## Totals & Summary Breakdown

- **Total existing questions reviewed:** 60
- **Retag candidates proposed:** 58
- **Keep decisions:** 2
- **Holds:** 0
- **Unextracted written items preserved:** 2
- **Conventional marks preserved:** 40
- **Live database writes:** 0 (strictly read-only)

### Breakdown by Proposed Taxonomy Path

- `english/grammar`: 19 questions
- `english/grammar/parts-of-speech`: 25 questions
- `english/grammar/prepositions`: 7 questions
- `english/grammar/subject-verb-agreement`: 9 questions

## Physical Element Inspection Evidence

Direct visual inspection of all 7 rendered PNG page images of `doc_28eafb04c21bfc501a33c583`:
- **Cover Page / Section A (Page 1):** Inspected Title, Instructions: General English, 3 hours, Full Marks: 100. Preserved Section A Conventional Tasks (40 marks):
  1. Task 1 (p. 1, 20 marks): Essay writing on Man and Environment / Importance of Education / Women in Mizo society / IT at present time.
  2. Task 2 (p. 1, 20 marks): Précis writing on Albert Einstein's passage on human interdependence and mutual cooperation.
- **Section B Parts of Speech (Page 2):** Inspected Q1–Q10: transitive verb ('hurt'), noun ('Grammar'), predicate adjective ('true'), abstract noun ('Laughter'), collective noun ('crowd'), degree adverb ('quite'), manner adverb ('fast'), interjection ('Bravo!'), substantive adjective ('courageous'), spatial preposition ('over').
- **Section B Modal Notions & Prepositions (Pages 3–4):** Inspected Q11–Q27: possibility ('may'), obligation ('must'), order ('Get out'), request ('Would you kindly'), habitual ('usually'), purpose ('to save his friend'), wish ('May you be blessed'), advice ('must stand'), purpose ('just to see you'), condition ('only if'), prepositions ('since yesterday', 'for the crown', 'into my parlour', 'with the lark', 'By the name of God', 'among his boys', 'across her breast').
- **Section B Conjunctions & Verbals (Pages 4–5):** Inspected Q28–Q42: conjunctions ('but', 'though', 'Since', 'for', 'else', 'before', 'Unless'), gerunds and participles ('Hunting tigers', 'hoarding money', 'swimming pool', 'Swimming', 'losing game', 'Giving is better than receiving', 'standing building', 'smoking').
- **Section B Sentence Analysis & Subject-Verb Agreement (Pages 5–7):** Inspected Q43–Q60: interrogative ('Who among the two boys...'), assertive ('Nature is the best physician', 'Daphne is the tallest...', 'Today is a fine day'), imperative ('Have mercy on us', 'Shut the door at once'), exclamatory ('How very cold the night is!'), optative ('May you have all the joy...'), negative ('You cannot have all the riches...'), subject-verb agreement ('quality ... was', 'one of ... takes', 'Fire and water do', 'horse and carriage is', 'Neither ... seems', 'Physics is', 'Committee were', 'The Arabian Nights is', 'Three parts ... is').

## Documented Source, Extraction & Option Defects

1. **Rectification of Unclassified Baseline Tags:** All 60 MCQs in production had coarse `current_subject: 'gk'` and `current_topic: 'ADA, AA & ATA General English'`. All have been structured into precise English taxonomy nodes.
2. **Preservation of 40 Marks of Section A Conventional Written Work:** Documented Task 1 (Essay 20m) and Task 2 (Précis 20m) in `pending-written-intake.json`.
3. **100% Extracted MCQ Fidelity:** All 60 printed Section B MCQs are present and consecutively numbered without gaps or OCR drops.
