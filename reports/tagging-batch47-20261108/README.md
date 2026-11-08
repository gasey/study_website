# Pending source-reviewed tagging — Batch 47: Direct 2023-2025 General English Booklets (78 MCQs)

Policy: `study-tagging-v1`. **78 existing questions reviewed: 78 retag proposals, 0 keep decisions, 0 tag holds. All 78 remain pending. Zero live changes, submissions or publications.**

## Target Papers & 100% Paper Completion Milestone

This batch achieves 100% source review of the extracted MCQs across all 4 remaining Direct 2023–2025 General English examination booklets:
1. *General Competitive Examinations for Recruitment to the Post of Jr. Grade of Mizoram Forest Service (Asst. Conservator of Forests) (2023) — General English* (`Old_Questions/Direct_2023-2025/ACF-2023-General English..pdf`, `doc_b5f51992824cdf78ca9eb105`, 10 MCQs, 100% paper completion).
2. *Technical Competitive Examination for Informatics Officer under ICT Department (November 2024) — General English Paper-I* (`Old_Questions/Direct_2023-2025/Informatics Officer General English Paper-I 2024..pdf`, `doc_e46ac6fab7a2eb8bf138f169`, 8 MCQs, 100% paper completion).
3. *Technical Competitive Examinations for Junior Grade of Mizoram Engineering Service, P&E Cadre (Electrical Wing) and Assistant Architect (July 2023) — General English* (`Old_Questions/Direct_2023-2025/Jr. Grade of MES (Electrical Wing) under P&E Deptt., General English..pdf`, `doc_210c8de409ca07cc3de1ad76`, 10 MCQs, 100% paper completion).
4. *Technical Competitive Examinations for Junior Grade of Mizoram Legal Service (MLS) under Law & Judicial Department (July 2023) — English* (`Old_Questions/Direct_2023-2025/Jr. Grade of MLS under Law & Judicial Deptt. - English..pdf`, `doc_e13e10e93f23cf05cda8960a`, 50 MCQs, 100% paper completion).

## Single-Booklet Deduplication Status

- **Booklet Status:** All 4 papers are standalone single-booklet direct examinations with zero duplicate series or multi-folder ingestions.

## Misclassification & Untagged Baseline Rectifications

Source inspection identified and cleanly rectified multiple baseline tagging defects:
- **Rectification of 'town-planning' Subject Misclassification:** Item `mpsc-cli-informatics-officer-general-english-paper-i-2024-007` ('What role do green roofs play in sustainable urban planning?') was erroneously tagged under `town-planning` due to passage keywords. Rectified to active taxonomy `english/comprehension`.
- **77 Coarse / Untagged Items Structured:** Rectified 77 bare `english` or placeholder baseline items to precise active subtopics:
  - `english/vocabulary/one-word-substitution` (10 items): MES Electrical Wing Q6(a)–(j) ('timid', 'peer', 'emigrant', 'faux pas', 'diffident', 'complacent', 'hypocrite', 'ordination', 'immune', 'polyglot').
  - `english/vocabulary/idioms-and-phrases` (15 items): ACF Q1–Q10 ('make head or tail', 'burning question', 'gift of the gab', 'take to task', 'take to one's heels', 'get cold feet', 'red-letter day', 'sit on the fence', 'clean breast', 'green-eyed friends') and MLS Q46–Q50 ('hit the sack', 'cut corners', 'draw the line', 'dime a dozen', 'snowball effect').
  - `english/vocabulary/synonyms` (5 items): MLS Q1–Q5 ('plebeian', 'sterling', 'indispensable', 'resilient', 'hilarious').
  - `english/vocabulary/antonyms` (5 items): MLS Q6–Q10 ('impoverished', 'insolvent', 'admiring', 'tenacious', 'subtle').
  - `english/grammar/prepositions` (5 items): MLS Q11–Q15 (spatial 'above', distribution 'among', instrument 'with', emotion 'over', phrasal verb 'put me up').
  - `english/grammar/parts-of-speech` (5 items): MLS Q16–Q20 conjunctions ('if', 'lest', 'despite', 'so', 'although').
  - `english/grammar/tenses` (10 items): MLS Q21–Q30 (present perfect continuous 'has been living', simple present 'cries', simple past 'ran', future continuous 'will be meeting', present singular 'wants', present perfect 'have written', narrative past 'went', bare infinitive 'send', past auxiliary 'did', modal base verb 'agree').
  - `english/grammar/subject-verb-agreement` (5 items): MLS Q31–Q35 ('Either he or I am', 'Rama as well as ... likes', 'You, who are', 'A black and a white cow were', collective noun 'mob was').
  - `english/grammar/reported-speech` (5 items): MLS Q36–Q40 (direct to indirect speech for imperatives, modal questions, past-to-past-perfect shifts, future will-to-would, and exclamatory sentences).
  - `english/grammar/voice` (5 items): MLS Q41–Q45 (quasi-passive middle voice 'Sugar tastes sweet', present continuous passive 'is being written', past simple passive 'were seen', infinitive of obligation passive 'is to be assisted', present perfect passive 'have been chopped').
  - `english/comprehension` (8 items): Informatics Officer Q6(a)–(h) reading comprehension items on sustainable urban planning and challenges.
- **Fresh Oracle read-only export:** `2026-11-07T21:01:32.092045+00:00`. Readback validation (`2026-11-07T21:05:31.719732+00:00`) confirmed 100% source fingerprint consistency, zero live mutations, and 100% compliance with active taxonomy nodes.

## Before / after table

| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | Q6(a) (p. 1) | One-Word Substitution (timid) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies 'timid' for one who lacks courage or confidence. |
| 2 | Q6(b) (p. 1) | One-Word Substitution (peer) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies 'peer' for one equal in rank or status. |
| 3 | Q6(c) (p. 1) | One-Word Substitution (emigrant) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Distinguishes 'emigrant' for a person leaving native country to settle abroad. |
| 4 | Q6(d) (p. 1) | One-Word Substitution (faux pas) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies loan phrase 'faux pas' for an embarrassing social mistake or blunder. |
| 5 | Q6(e) (p. 1) | One-Word Substitution (diffident) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies 'diffident' for one shy and unwilling to face a situation. |
| 6 | Q6(f) (p. 1) | One-Word Substitution (complacent) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies 'complacent' for one who is smugly self-satisfied. |
| 7 | Q6(g) (p. 1) | One-Word Substitution (hypocrite) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies 'hypocrite' for one pretending to hold beliefs or virtues they do not possess. |
| 8 | Q6(h) (p. 1) | One-Word Substitution (ordination) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies 'ordination' for the sacred ceremony admitting a person to holy ministry/priesthood. |
| 9 | Q6(i) (p. 1) | One-Word Substitution (immune) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies 'immune' for being free or protected from disease/infection. |
| 10 | Q6(j) (p. 1) | One-Word Substitution (polyglot) | `english` | `english/vocabulary/one-word-substitution` | **retag** — Identifies 'polyglot' for one who knows and speaks many languages. |
| 11 | Q1 (p. 2) | Idioms & Phrases (make head or tail of) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'make head or tail of' meaning to understand or make sense of something. |
| 12 | Q2 (p. 2) | Idioms & Phrases (burning question) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'burning question' meaning a crucial and urgent matter of the day. |
| 13 | Q3 (p. 2) | Idioms & Phrases (gift of the gab) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'gift of the gab' meaning natural eloquence and fluency in persuasive speech. |
| 14 | Q4 (p. 2) | Idioms & Phrases (take to task) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'take to task' meaning to rebuke, reprimand, or scold someone for a fault. |
| 15 | Q5 (p. 2) | Idioms & Phrases (take to one's heels) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'take to one's heels' meaning to run away hastily or take to flight. |
| 16 | Q6 (p. 2) | Idioms & Phrases (get cold feet) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'get cold feet' meaning to become nervous, fearful, or hesitant before performance. |
| 17 | Q7 (p. 2) | Idioms & Phrases (red-letter day) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'red-letter day' meaning a memorable, auspicious, or joyously significant occasion. |
| 18 | Q8 (p. 2) | Idioms & Phrases (sit on the fence) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'sit on the fence' meaning to remain neutral or avoid making a decision between two sides. |
| 19 | Q9 (p. 2) | Idioms & Phrases (make a clean breast of) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'make a clean breast of' meaning to make a full and frank confession of guilt. |
| 20 | Q10 (p. 2) | Idioms & Phrases (green-eyed friends) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets figurative idiom 'green-eyed' denoting jealousy or envious feelings. |
| 21 | Q1 (p. 2) | Synonyms (plebeian) | `english` | `english/vocabulary/synonyms` | **retag** — Identifies 'Low class' as closest synonym for 'plebeian'. |
| 22 | Q2 (p. 2) | Synonyms (sterling) | `english` | `english/vocabulary/synonyms` | **retag** — Identifies 'Excellent' as closest synonym for 'sterling' qualities. |
| 23 | Q3 (p. 2) | Synonyms (indispensable) | `english` | `english/vocabulary/synonyms` | **retag** — Identifies 'Essential' as closest synonym for 'indispensable' advice. |
| 24 | Q4 (p. 2) | Synonyms (resilient) | `english` | `english/vocabulary/synonyms` | **retag** — Identifies 'Strong' as closest synonym for 'resilient' capacity to recover. |
| 25 | Q5 (p. 2) | Synonyms (hilarious) | `english` | `english/vocabulary/synonyms` | **retag** — Identifies 'Extremely funny' as closest synonym for 'hilarious'. |
| 26 | Q6 (p. 2) | Antonyms (impoverished) | `english` | `english/vocabulary/antonyms` | **retag** — Identifies 'Rich' as exact antonym of 'impoverished'. |
| 27 | Q7 (p. 2) | Antonyms (insolvent) | `english` | `english/vocabulary/antonyms` | **retag** — Identifies 'Prosperous' as exact antonym of 'insolvent'. |
| 28 | Q8 (p. 2) | Antonyms (admiring) | `english` | `english/vocabulary/antonyms` | **retag** — Identifies 'Scornful' as exact antonym of 'admiring'. |
| 29 | Q9 (p. 2) | Antonyms (tenacious) | `english` | `english/vocabulary/antonyms` | **retag** — Identifies 'Weak' as exact antonym of 'tenacious'. |
| 30 | Q10 (p. 2) | Antonyms (subtle) | `english` | `english/vocabulary/antonyms` | **retag** — Identifies 'Blatant' as exact antonym of 'subtle'. |
| 31 | Q11 (p. 3) | Prepositions of Place (above) | `english` | `english/grammar/prepositions` | **retag** — Selects spatial preposition 'above' denoting higher elevation in 'apartment above mine'. |
| 32 | Q12 (p. 3) | Prepositions of Distribution (among) | `english` | `english/grammar/prepositions` | **retag** — Selects 'among' for distribution among more than two individuals ('among the students'). |
| 33 | Q13 (p. 3) | Prepositions of Instrument (with) | `english` | `english/grammar/prepositions` | **retag** — Selects preposition of instrument 'with' for inanimate tool ('beaten with a stick'). |
| 34 | Q14 (p. 3) | Prepositions of Cause (over) | `english` | `english/grammar/prepositions` | **retag** — Selects preposition 'over' denoting cause of grief ('crying over her broken heart'). |
| 35 | Q15 (p. 3) | Phrasal Verbs (put up) | `english` | `english/grammar/prepositions` | **retag** — Selects preposition/particle 'up' in separable phrasal verb 'put me up' meaning provide lodging. |
| 36 | Q16 (p. 3) | Conditional Conjunction (if) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects conditional subordinating conjunction 'if' in 'forgive you if you truly repent'. |
| 37 | Q17 (p. 3) | Negative Conditional Conjunction (lest) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects conjunction of prevention 'lest' meaning in order that not ('Keep quiet lest he sees you'). |
| 38 | Q18 (p. 3) | Concessive Preposition (despite) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects preposition of concession 'despite' governing noun phrase ('succeeded despite the obstacles'). |
| 39 | Q19 (p. 3) | Coordinating Conjunction (so) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects result conjunction 'so' linking premise to action ('You asked, so I came'). |
| 40 | Q20 (p. 3) | Concessive Subordinator (although) | `english` | `english/grammar/parts-of-speech` | **retag** — Selects concessive conjunction 'although' introducing contrast ('good time although it rained'). |
| 41 | Q21 (p. 4) | Tenses (Present Perfect Continuous) | `english` | `english/grammar/tenses` | **retag** — Selects present perfect continuous 'has been living' for action beginning in past with 'ever since' and continuing. |
| 42 | Q22 (p. 4) | Tenses (Simple Present for Habitual) | `english` | `english/grammar/tenses` | **retag** — Selects simple present 'cries' for recurring habitual reaction with 'every time'. |
| 43 | Q23 (p. 4) | Tenses (Past Simple with Past Continuous) | `english` | `english/grammar/tenses` | **retag** — Selects simple past 'ran' for completed point action interrupting background state ('while she was on vacation'). |
| 44 | Q24 (p. 4) | Tenses (Future Continuous) | `english` | `english/grammar/tenses` | **retag** — Selects future continuous 'will be meeting' for ongoing planned activity over future timeframe. |
| 45 | Q25 (p. 4) | Tenses (Simple Present Singular) | `english` | `english/grammar/tenses` | **retag** — Selects third-person singular present 'wants' agreeing with singular subject 'Principal'. |
| 46 | Q26 (p. 4) | Tenses (Present Perfect with Past Participle) | `english` | `english/grammar/tenses` | **retag** — Selects grammatically correct present perfect 'have written' using proper past participle 'written'. |
| 47 | Q27 (p. 4) | Tenses (Past Simple Narrative) | `english` | `english/grammar/tenses` | **retag** — Selects simple past 'went' maintaining past tense sequence with 'was a sunny day'. |
| 48 | Q28 (p. 4) | Verb Forms (Bare Infinitive after to) | `english` | `english/grammar/tenses` | **retag** — Selects base form 'send' following infinitive marker 'to'. |
| 49 | Q29 (p. 4) | Auxiliary Verbs (Past Auxiliary with last night) | `english` | `english/grammar/tenses` | **retag** — Selects past auxiliary 'did' with time adverbial 'last night' in 'She did not want'. |
| 50 | Q30 (p. 4) | Modal Syntax (Base Verb after Modal) | `english` | `english/grammar/tenses` | **retag** — Selects uninflected base verb 'agree' following modal auxiliary 'must'. |
| 51 | Q31 (p. 5) | Subject-Verb Agreement (Either ... or Proximity) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Applies proximity rule where verb agrees with nearest pronoun subject 'I' ('Either he or I am mistaken'). |
| 52 | Q32 (p. 5) | Subject-Verb Agreement (Parenthetical as well as) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Enforces rule that parenthetical phrase introduced by 'as well as' does not affect singular subject 'Rama' ('Rama ... likes curry'). |
| 53 | Q33 (p. 5) | Subject-Verb Agreement (Relative Pronoun Antecedent) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects plural verb 'are' agreeing with second-person antecedent 'You' in 'You, who are my friend'. |
| 54 | Q34 (p. 5) | Subject-Verb Agreement (Separate Articles Two Items) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Enforces rule that repeated article 'A black and a white cow' denotes two distinct animals taking plural verb 'were'. |
| 55 | Q35 (p. 5) | Subject-Verb Agreement (Collective Noun Singular Action) | `english` | `english/grammar/subject-verb-agreement` | **retag** — Selects singular passive auxiliary 'was / has been' for collective noun 'mob' acting as a unified body. |
| 56 | Q36 (p. 5) | Reported Speech (Imperative Command) | `english` | `english/grammar/reported-speech` | **retag** — Transforms direct command to reported speech with infinitive reporting clause ('The king ordered them to execute that man immediately'). |
| 57 | Q37 (p. 5) | Reported Speech (Yes/No Question & Request) | `english` | `english/grammar/reported-speech` | **retag** — Transforms direct modal question to indirect speech with 'asked if / politely requested'. |
| 58 | Q38 (p. 5) | Reported Speech (Past Simple to Past Perfect) | `english` | `english/grammar/reported-speech` | **retag** — Shifts simple past 'saw' to past perfect 'had seen' and converts 'last night' to 'the previous night'. |
| 59 | Q39 (p. 5) | Reported Speech (Future Modal will to would) | `english` | `english/grammar/reported-speech` | **retag** — Shifts modal 'will' to past conditional 'would' and changes object pronouns accordingly ('told Ram that she would call him'). |
| 60 | Q40 (p. 5) | Reported Speech (Exclamatory Sentence) | `english` | `english/grammar/reported-speech` | **retag** — Transforms exclamatory sentence with interjection 'Hurrah!' into reported form with 'exclaimed with joy that they had won'. |
| 61 | Q41 (p. 6) | Voice Transformation (Quasi-Passive Verb) | `english` | `english/grammar/voice` | **retag** — Transforms quasi-passive middle voice sentence 'Sugar tastes sweet' into passive equivalent 'Sugar is sweet when it is tasted'. |
| 62 | Q42 (p. 6) | Voice Transformation (Present Continuous Passive) | `english` | `english/grammar/voice` | **retag** — Transforms present continuous active into passive using 'is being written'. |
| 63 | Q43 (p. 6) | Voice Transformation (Past Simple Passive) | `english` | `english/grammar/voice` | **retag** — Transforms past simple active into passive using 'were seen by me'. |
| 64 | Q44 (p. 6) | Voice Transformation (Infinitive of Obligation Passive) | `english` | `english/grammar/voice` | **retag** — Transforms active infinitive of obligation 'are to assist' into passive form 'is to be assisted'. |
| 65 | Q45 (p. 6) | Voice Transformation (Present Perfect Passive) | `english` | `english/grammar/voice` | **retag** — Transforms present perfect active into passive using 'have been chopped'. |
| 66 | Q46 (p. 6) | Idioms & Phrases (hit the sack) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets colloquial idiom 'hit the sack' meaning to go to bed or go to sleep. |
| 67 | Q47 (p. 6) | Idioms & Phrases (cut corners) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'cut corners' meaning to do something in the easiest or cheapest way often sacrificing quality. |
| 68 | Q48 (p. 6) | Idioms & Phrases (draw the line) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'draw the line' meaning to set a strict limit on what one is willing to do or tolerate. |
| 69 | Q49 (p. 6) | Idioms & Phrases (a dime a dozen) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'a dime a dozen' meaning very common, plentiful, and of little unique value. |
| 70 | Q50 (p. 6) | Idioms & Phrases (snowball effect) | `english` | `english/vocabulary/idioms-and-phrases` | **retag** — Interprets idiom 'snowball effect' meaning a situation that gains rapidly in size, momentum, or severity. |
| 71 | Q6(h) (p. 3) | Reading Comprehension (Future Projection Inference) | `english` | `english/comprehension` | **retag** — Infers author's projection that innovative and inclusive planning is crucial for future sustainable cities. |
| 72 | Q6(g) (p. 3) | Reading Comprehension (Role of Green Roofs) | `town-planning` | `english/comprehension` | **retag** — Rectifies erroneous 'town-planning' misclassification: extracts passage analysis of how green roofs mitigate environmental degradation. |
| 73 | Q6(a) (p. 2) | Reading Comprehension (Primary Urbanization Challenge) | `english` | `english/comprehension` | **retag** — Extracts primary infrastructural challenge of rapid urbanization from informational text. |
| 74 | Q6(c) (p. 2) | Reading Comprehension (Impact on Green Spaces) | `english` | `english/comprehension` | **retag** — Extracts passage details regarding loss of green spaces and biodiversity due to new developments. |
| 75 | Q6(e) (p. 3) | Reading Comprehension (Quality of Life Inference) | `english` | `english/comprehension` | **retag** — Draws textual inference regarding how urbanization negatively impacts quality of life without proper management. |
| 76 | Q6(d) (p. 2) | Reading Comprehension (Environmental Mitigation Strategy) | `english` | `english/comprehension` | **retag** — Identifies sustainable mitigation strategy suggested in text for urban environmental protection. |
| 77 | Q6(b) (p. 2) | Reading Comprehension (Socio-Economic Disparity) | `english` | `english/comprehension` | **retag** — Identifies socio-economic disparity and income inequality highlighted in passage. |
| 78 | Q6(f) (p. 3) | Reading Comprehension (Purpose of Urban Planning) | `english` | `english/comprehension` | **retag** — Identifies author's conclusion on the essential purpose of urban planning to manage modern urban challenges. |

## Totals & Summary Breakdown

- **Total existing questions reviewed:** 78
- **Retag candidates proposed:** 78
- **Keep decisions:** 0
- **Holds:** 0
- **Unextracted written items preserved:** 10
- **Conventional marks preserved:** 190
- **Live database writes:** 0 (strictly read-only)

### Breakdown by Proposed Taxonomy Path

- `english/comprehension`: 8 questions
- `english/grammar/parts-of-speech`: 5 questions
- `english/grammar/prepositions`: 5 questions
- `english/grammar/reported-speech`: 5 questions
- `english/grammar/subject-verb-agreement`: 5 questions
- `english/grammar/tenses`: 10 questions
- `english/grammar/voice`: 5 questions
- `english/vocabulary/antonyms`: 5 questions
- `english/vocabulary/idioms-and-phrases`: 15 questions
- `english/vocabulary/one-word-substitution`: 10 questions
- `english/vocabulary/synonyms`: 5 questions

## Physical Element Inspection Evidence

Direct visual inspection of rendered PNG page images across all 4 papers (14 pages total):
- **Paper 1 (`doc_b5f51992824cdf78ca9eb105`, ACF 2023):** Inspected Pages 1 to 3. Preserved Essay Task 1 (25m) on page 1 and Reading Comprehension written questions Task 7 (15m) on page 3. Verified 10 MCQs on idioms & phrases on page 2.
- **Paper 2 (`doc_e46ac6fab7a2eb8bf138f169`, Informatics Officer 2024):** Inspected Pages 1 to 3 via tesseract OCR and PNG rendering. Preserved Essay Task 1 (25m) and Précis Task 2 (15m) on page 1, and Idea Expansion Task 5 (15m) on page 2. Verified 8 MCQs on Reading Comprehension (urbanization, green spaces, socio-economic disparity, quality of life, green roofs) on pages 2–3.
- **Paper 3 (`doc_210c8de409ca07cc3de1ad76`, MES Electrical Wing 2023):** Inspected Pages 1 to 2. Preserved Essay Task 1 (20m) on page 1 and Précis Task 3 (20m) on page 2. Verified 10 One-Word Substitution items on page 1.
- **Paper 4 (`doc_e13e10e93f23cf05cda8960a`, MLS English 2023):** Inspected Pages 1 to 6. Preserved Section A Conventional Tasks (50m: Essay 25m, Précis 15m, Idiom sentence composition 10m) on page 1. Verified 50 Section B MCQs across pages 2 to 6 (Synonyms 5, Antonyms 5, Prepositions 5, Conjunctions 5, Tenses 10, Subject-Verb Agreement 5, Reported Speech 5, Voice 5, Idioms 5).

## Documented Source, Extraction & Option Defects

1. **Rectification of 'town-planning' Subject Misclassification:** Rectified Informatics Officer reading comprehension item Q6(g) from `town-planning` to `english/comprehension`.
2. **Preservation of 190 Marks of Conventional Written Work:** Documented 10 descriptive tasks (Essays, Précis, Idea Expansion, and Idiom sentence writing) across all 4 booklets in `pending-written-intake.json`.
3. **Scanned PDF Optical Extraction Alignment:** Verified and numbered the 8 unnumbered comprehension items of Informatics Officer matching physical pages 2 and 3 of the examination booklet.
