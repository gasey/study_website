# Pending source-reviewed tagging — Batch 43: Final 2024–2025 Direct English Booklets (81 items)

Policy: `study-tagging-v1`. **81 existing questions reviewed: 79 retag proposals, 2 keep decisions, 0 tag holds. All 81 remain pending. Zero live changes, submissions or publications.**

## Target Papers & 100% Paper Completion Milestone

This batch completes 100% source review across the remaining four 2024–2025 Direct English examination booklets in the corpus:
1. *Competitive Examination for the Post of Sericulture Extension Officer (2025) — General English* (`Old_Questions/Direct_2025-2027/General English..pdf`, `doc_3e7d37598a061cd1d52da2ad`, 20 MCQs, 100% paper completion).
2. *Technical Competitive Examination for Junior Grade of Mizoram Engineering Service (Combined) (2025) — General English* (`Old_Questions/Direct_2025-2027/Jr. Grade of MES (Combined)-2025 - General English..pdf`, `doc_682ab0cad0fd9c4e525e91a9`, 21 MCQs, 100% paper completion).
3. *General Competitive Examination for Recruitment to the Post of Junior Grade of Mizoram Planning, Economic & Statistical Service (2025) — General English* (`Old_Questions/Direct_2025-2027/Jr. Grade of MPE & SS, General English..pdf`, `doc_895b0f62c2314d435e125458`, 30 MCQs, 100% paper completion).
4. *Group B(NG) (Technical) Paper-I (General English)-2024* (`Old_Questions/Direct_NG_2024-2027/Group B(NG) (Technical)Paper-I (General English)-2024..pdf`, `doc_d50623457f36f5aeab231741`, 10 composite items, 100% paper completion).

- **Untagged & Misclassified Baseline Rectification:** All 81 items suffered from unclassified or coarse tag baselines (`subject=english, topic=null` or `topic_id: english/grammar`). Most notably, in Sericulture Extension Officer, question Q3(ii) was misclassified in production as `subject_id: sociology`, which has been cleanly rectified to `english/comprehension`. Across all 4 papers, rectified 100% of targets to active English subtopics: Reading Comprehension (7 items), One-Word Substitution (6 items), Synonyms (6 items), Antonyms (11 items), General Grammar & Clause Analysis (10 items), Tenses & Verb Forms (15 items), Prepositions (16 items), Subject-Verb Agreement (1 item), Parts of Speech (5 items), Précis Writing (1 item), Letter Writing (1 item), Voice (1 item), and Reported Speech (1 item).
- **Preserved Conventional Intake:** Preserved 5 conventional written tasks totaling 80 marks across the papers in `pending-written-intake.json` (Sericulture: Précis 10m, Complaint Letter 15m; MES: Essay 20m; MPE & SS: Essay 20m, Précis 15m).
- **Fresh Oracle read-only export:** `2026-11-07T20:31:37.517552+00:00`. Readback validation (`2026-11-07T20:33:30.474315+00:00`) confirmed 100% source fingerprint consistency, zero live mutations, and 100% compliance with active taxonomy nodes.

## Before / after table

| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | Q3(ii) (p. 2) | Reading Comprehension (Inference) | `sociology` | `english/comprehension` | **retag** — Rectifies sociology misclassification: evaluates passage illustration of class factor in political aspirations. |
| 2 | Q9(ii) (p. 4) | One-Word Substitution | `english` | `english/vocabulary/one-word-substitution` | **retag** — Tests noun 'cynic' denoting one who sneers at the aims and beliefs of fellow human beings. |
| 3 | Q9(v) (p. 4) | One-Word Substitution | `english` | `english/vocabulary/one-word-substitution` | **retag** — Tests linguistic term 'phonetics' for the scientific study of speech sounds. |
| 4 | Q7(i) (p. 3) | Synonyms | `english` | `english/vocabulary/synonyms` | **retag** — Tests synonym of 'persuasions' ('beliefs / convictions') in sociopolitical context. |
| 5 | Q8(iv) (p. 3) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'deft' ('clumsy / awkward'). |
| 6 | Q3(i) (p. 2) | Reading Comprehension (Detail) | `english` | `english/comprehension` | **retag** — Analyzes phrase meaning 'Fusion of political and communal aspirations' within passage context. |
| 7 | Q3(v) (p. 2) | Reading Comprehension (Detail) | `english` | `english/comprehension` | **retag** — Identifies author's proposed solution for tackling communal politics in the passage. |
| 8 | Q8(ii) (p. 3) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'dejected' ('cheerful / elated'). |
| 9 | Q8(i) (p. 3) | Antonyms | `english/vocabulary/antonyms` | `english/vocabulary/antonyms` | **keep** — Confirms exact active subtopic for antonym of 'delayed' ('expedited / hastened'). |
| 10 | Q7(v) (p. 3) | Synonyms | `english` | `english/vocabulary/synonyms` | **retag** — Tests synonym of 'pernicious' ('harmful / destructive'). |
| 11 | Q8(v) (p. 4) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'urbane' ('uncouth / rude'). |
| 12 | Q9(i) (p. 4) | One-Word Substitution | `english` | `english/vocabulary/one-word-substitution` | **retag** — Tests noun 'aesthete' for a person with highly developed sensitivity to beauty and art. |
| 13 | Q8(iii) (p. 3) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'literal' ('figurative / metaphorical'). |
| 14 | Q3(iii) (p. 2) | Reading Comprehension (Detail) | `english` | `english/comprehension` | **retag** — Analyzes political exploitation of religion based on passage arguments. |
| 15 | Q7(ii) (p. 3) | Synonyms | `english` | `english/vocabulary/synonyms` | **retag** — Tests synonym of 'rescind' ('revoke / repeal / annul'). |
| 16 | Q9(iv) (p. 4) | One-Word Substitution | `english` | `english/vocabulary/one-word-substitution` | **retag** — Tests adjective 'gregarious' / 'sociable' for one who enjoys spending time with others. |
| 17 | Q9(iii) (p. 4) | One-Word Substitution | `english` | `english/vocabulary/one-word-substitution` | **retag** — Tests noun 'xenophobia' denoting prejudice or hatred against people from other countries. |
| 18 | Q7(iii) (p. 3) | Synonyms | `english` | `english/vocabulary/synonyms` | **retag** — Tests synonym of 'frailties' ('weaknesses / foibles'). |
| 19 | Q3(iv) (p. 2) | Reading Comprehension (Inference) | `english` | `english/comprehension` | **retag** — Analyzes passage rationale for raising communal feelings to frenzy. |
| 20 | Q7(iv) (p. 3) | Synonyms | `english` | `english/vocabulary/synonyms` | **retag** — Tests synonym of 'insatiable' ('unquenchable / voracious'). |
| 21 | Q9(i) (p. 4) | Clause Analysis (Noun Clause) | `english` | `english/grammar` | **retag** — Identifies dependent noun clause functioning as direct object of reporting verb. |
| 22 | Q7(v) (p. 3) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests present continuous tense aspect ('Listen! John is singing...'). |
| 23 | Q9(iii) (p. 4) | Clause Analysis (Adverb Clause) | `english/grammar` | `english/grammar` | **keep** — Confirms exact active topic for subordinating adverbial clause of reason / cause. |
| 24 | Q2(d) (p. 2) | Contextual Vocabulary | `english` | `english/comprehension` | **retag** — Analyzes contextual vocabulary meaning of 'solemn' ('grave / serious') within passage. |
| 25 | Q5(d) (p. 2) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'Friction' ('harmony / agreement'). |
| 26 | Q5(a) (p. 2) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'Strident' ('soft / subdued / soothing'). |
| 27 | Q7(iii) (p. 3) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests subjunctive / modal verb complementation ('It is strange that he should say so'). |
| 28 | Q8(iii) (p. 3) | Prepositions | `english` | `english/grammar/prepositions` | **retag** — Tests fixed adjective-preposition collocation 'well-known for'. |
| 29 | Q9(iv) (p. 4) | Clause Analysis (Adverb Clause) | `english` | `english/grammar` | **retag** — Identifies subordinating adverbial clause of condition ('If you work hard...'). |
| 30 | Q5(e) (p. 2) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'Conceptual' ('concrete / physical'). |
| 31 | Q9(ii) (p. 4) | Clause Analysis (Adjective Clause) | `english` | `english/grammar` | **retag** — Identifies relative adjective clause modifying antecedent noun ('who won the prize'). |
| 32 | Q8(ii) (p. 3) | Prepositions | `english` | `english/grammar/prepositions` | **retag** — Tests phrasal verb preposition 'looks after' denoting caretaking. |
| 33 | Q7(ii) (p. 3) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests past continuous / past habit aspect ('Ram lived / was living in Mumbai for five years'). |
| 34 | Q5(b) (p. 2) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'Dank' ('dry / arid'). |
| 35 | Q8(iv) (p. 3) | Prepositions | `english` | `english/grammar/prepositions` | **retag** — Tests spatial preposition 'through' indicating traversal of examination or passage. |
| 36 | Q9(v) (p. 4) | Clause Analysis (Adverb Clause) | `english` | `english/grammar` | **retag** — Identifies subordinating adverbial clause of time ('When the bell rang...'). |
| 37 | Q8(v) (p. 3) | Prepositions | `english` | `english/grammar/prepositions` | **retag** — Tests fixed verb-preposition collocation 'cautioned against' governing noun complement. |
| 38 | Q5(c) (p. 2) | Antonyms | `english` | `english/vocabulary/antonyms` | **retag** — Tests antonym of 'Component' ('whole / entirety'). |
| 39 | Q8(i) (p. 3) | Prepositions | `english` | `english/grammar/prepositions` | **retag** — Tests fixed adjective-preposition collocation 'proud of'. |
| 40 | Q7(iv) (p. 3) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests past continuous aspect ('One clown was balancing a ball while another was juggling'). |
| 41 | Q7(i) (p. 3) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests present continuous aspect ('Be quiet! The baby is sleeping'). |
| 42 | Q1 (p. 2) | Clause Analysis (Adjective Clause) | `english` | `english/grammar` | **retag** — Identifies defining relative clause 'who topped the examination'. |
| 43 | Q2 (p. 2) | Clause Analysis (Adverb Clause) | `english` | `english/grammar` | **retag** — Identifies adverbial clause of purpose 'so that no one could notice her absence'. |
| 44 | Q3 (p. 2) | Clause Analysis (Noun Clause) | `english` | `english/grammar` | **retag** — Identifies interrogative noun clause 'where the treasure had been hidden'. |
| 45 | Q4 (p. 2) | Clause Analysis (Adverb / Noun Clause) | `english` | `english/grammar` | **retag** — Identifies clause of reason 'why I refused the offer'. |
| 46 | Q5 (p. 2) | Clause Analysis (Adverb Clause of Manner) | `english` | `english/grammar` | **retag** — Identifies modal adverbial clause of manner 'as if he owned the entire company'. |
| 47 | Q6 (p. 2) | Subject-Verb Agreement | `english` | `english/grammar/subject-verb-agreement` | **retag** — Tests agreement: parenthetical 'along with his friends' does not change singular subject 'He' -> 'is going'. |
| 48 | Q7 (p. 2) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests future perfect aspect ('will have already left') with temporal anchor 'By the time we reach'. |
| 49 | Q8 (p. 2) | Tenses & Verb Forms (Subjunctive) | `english` | `english/grammar/tenses` | **retag** — Tests subjunctive past tense complement ('I'd rather you did not discuss...') following preference idiom. |
| 50 | Q9 (p. 2) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests present perfect / duration aspect ('has worked / has been working') following concessive clause. |
| 51 | Q10 (p. 2) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests passive future perfect aspect ('will have been completed') before new director takes office. |
| 52 | Q11 (p. 3) | Parts of Speech (Pronoun) | `english` | `english/grammar/parts-of-speech` | **retag** — Classifies indefinite pronoun 'One' serving as subject of modal statement. |
| 53 | Q12 (p. 3) | Parts of Speech (Adjective) | `english` | `english/grammar/parts-of-speech` | **retag** — Classifies qualitative adjective 'wise' modifying subject noun 'king'. |
| 54 | Q13 (p. 3) | Parts of Speech (Conjunction) | `english` | `english/grammar/parts-of-speech` | **retag** — Classifies conjunctive adverb / adversative connective 'however' joining contrasting clauses. |
| 55 | Q14 (p. 3) | Parts of Speech (Interjection) | `english` | `english/grammar/parts-of-speech` | **retag** — Classifies emotional interjection 'Hurrah!' expressing exultant triumph. |
| 56 | Q15 (p. 3) | Parts of Speech (Verb) | `english` | `english/grammar/parts-of-speech` | **retag** — Classifies past participle verb form 'borne' (from bear) in past perfect construction. |
| 57 | Q16 (p. 3) | Prepositions of Place | `english` | `english/grammar/prepositions` | **retag** — Tests spatial prepositions for city and nation: 'in Aizawl, in India' (or 'at Aizawl in India'). |
| 58 | Q17 (p. 3) | Prepositions of Direction / Motion | `english` | `english/grammar/prepositions` | **retag** — Tests dynamic motion preposition 'into' indicating transfer inside a vessel ('into the cup'). |
| 59 | Q18 (p. 3) | Prepositions of Time | `english` | `english/grammar/prepositions` | **retag** — Tests temporal preposition 'since' governing definite past starting point ('since last week'). |
| 60 | Q19 (p. 3) | Prepositions of Time | `english` | `english/grammar/prepositions` | **retag** — Tests terminal temporal preposition 'until' / 'till' ('stay at the hotel until Sunday'). |
| 61 | Q20 (p. 3) | Prepositions of Place | `english` | `english/grammar/prepositions` | **retag** — Tests spatial preposition 'in' / 'on' ('sitting in an armchair / on a chair'). |
| 62 | Q21 (p. 3) | Prepositions of Instrument | `english` | `english/grammar/prepositions` | **retag** — Tests instrumental preposition 'with' used with inanimate tools ('beaten with a ruler'). |
| 63 | Q22 (p. 3) | Prepositions of Place | `english` | `english/grammar/prepositions` | **retag** — Tests surface contact preposition 'on' ('put the files on the table'). |
| 64 | Q23 (p. 3) | Prepositions of Duration | `english` | `english/grammar/prepositions` | **retag** — Tests temporal preposition 'for' indicating duration of time span ('for more than four hours'). |
| 65 | Q24 (p. 3) | Prepositions of Time | `english` | `english/grammar/prepositions` | **retag** — Tests deadline preposition 'by' indicating no later than ('finish my work by evening'). |
| 66 | Q25 (p. 3) | Prepositions of Relative Position | `english` | `english/grammar/prepositions` | **retag** — Tests vertical level preposition 'above' / 'below' ('tenants living above our floor'). |
| 67 | Q26 (p. 4) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests simple present habitual aspect ('teaches') matching singular subject 'Miss Sarah'. |
| 68 | Q27 (p. 4) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests past continuous aspect ('was crossing') interrupted by simple past shout. |
| 69 | Q28 (p. 4) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests past perfect continuous / past perfect aspect ('had studied / studied') prior to examination. |
| 70 | Q29 (p. 4) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests simple past sequence of completed actions in narrative ('arrived, we found'). |
| 71 | Q30 (p. 4) | Tenses & Verb Forms | `english` | `english/grammar/tenses` | **retag** — Tests future perfect aspect ('will have finished') anchored by deadline 'by the end of the month'. |
| 72 | QW5 (p. 2) | Prepositions (Multi-part) | `english` | `english/grammar/prepositions` | **retag** — Evaluates multi-sentence blanks testing appropriate prepositions of place, time, and agency. |
| 73 | QW1 (p. 1) | Précis Writing | `english` | `english/writing/precis` | **retag** — Conventional task: Summarize reading passage in approximately one-third length with title. |
| 74 | QW6 (p. 2) | Tenses & Verb Forms (Multi-part) | `english` | `english/grammar/tenses` | **retag** — Evaluates multi-sentence blanks testing correct verb inflections and tense sequences. |
| 75 | QW2 (p. 1) | Reading Comprehension | `english` | `english/comprehension` | **retag** — Descriptive task: Reading comprehension passage analysis and short-answer prompts. |
| 76 | QW4 (p. 2) | Letter Writing | `english` | `english/writing/letter` | **retag** — Conventional formal letter drafting to public authorities regarding civic/community issues. |
| 77 | QW10 (p. 4) | Synonyms (Multi-part) | `english` | `english/vocabulary/synonyms` | **retag** — Evaluates multiple lexical items for exact or closest synonyms. |
| 78 | QW7 (p. 3) | Voice Transformation (Multi-part) | `english` | `english/grammar/voice` | **retag** — Evaluates active-to-passive and passive-to-active sentence transformations. |
| 79 | QW11 (p. 4) | Antonyms (Multi-part) | `english` | `english/vocabulary/antonyms` | **retag** — Evaluates multiple lexical items for exact opposite antonyms. |
| 80 | QW9 (p. 3) | One-Word Substitution & Usage | `english` | `english/vocabulary/one-word-substitution` | **retag** — Evaluates one-word substitution selection and sentence contextual usage. |
| 81 | QW8 (p. 3) | Reported Speech (Multi-part) | `english` | `english/grammar/reported-speech` | **retag** — Evaluates direct-to-indirect and indirect-to-direct narration transformations. |

## Totals & Summary Breakdown

- **Total existing questions reviewed:** 81
- **Retag candidates proposed:** 79
- **Keep decisions:** 2
- **Holds:** 0
- **Unextracted written items preserved:** 5
- **Live database writes:** 0 (strictly read-only)

### Breakdown by Proposed Taxonomy Path

- `english/comprehension`: 7 questions
- `english/grammar`: 10 questions
- `english/grammar/parts-of-speech`: 5 questions
- `english/grammar/prepositions`: 16 questions
- `english/grammar/reported-speech`: 1 questions
- `english/grammar/subject-verb-agreement`: 1 questions
- `english/grammar/tenses`: 15 questions
- `english/grammar/voice`: 1 questions
- `english/vocabulary/antonyms`: 11 questions
- `english/vocabulary/one-word-substitution`: 6 questions
- `english/vocabulary/synonyms`: 6 questions
- `english/writing/letter`: 1 questions
- `english/writing/precis`: 1 questions

## Physical Element Inspection Evidence

Direct visual inspection of all 16 rendered PNG page images across 4 papers:
- **Paper 1 (`doc_3e7d37598a061cd1d52da2ad`):** Inspected Pages 1 to 4: Q1 (Précis on sericulture), Q2 (Complaint letter on defective silkworms), Q3(i)–Q3(v) (Comprehension passage on communal politics and social class factors), Q7(i)–Q7(v) (Synonyms: persuasions, rescind, frailties, insatiable, pernicious), Q8(i)–Q8(v) (Antonyms: delayed, dejected, literal, deft, urbane), Q9(i)–Q9(v) (One-word substitution: aesthete, cynic, xenophobia, gregarious, phonetics).
- **Paper 2 (`doc_682ab0cad0fd9c4e525e91a9`):** Inspected Pages 1 to 4: Q1 (Essay), Q2(d) (Contextual meaning of 'solemn'), Q5(a)–Q5(e) (Antonyms: Strident, Dank, Component, Friction, Conceptual), Q7(i)–Q7(v) (Tenses/Verbs: Be quiet!, Ram lived, It is strange, One clown, Listen John), Q8(i)–Q8(v) (Prepositions: proud of, looks after, well-known for, through, cautioned against), Q9(i)–Q9(v) (Clauses: noun, adjective, adverb clauses).
- **Paper 3 (`doc_895b0f62c2314d435e125458`):** Inspected Pages 1 to 4: Q1 (Essay), Q2 (Précis), Q1–Q5 (Clause analysis: relative, purpose, noun, reason, manner), Q6–Q10 (Tenses: along with, by the time, I'd rather, though he worked, takes office), Q11–Q15 (Parts of speech: One [pronoun], wise [adj], however [conj], Hurrah! [interj], borne [verb]), Q16–Q25 (Prepositions: in/at, into, since, until, in/on, with, on, for, by, above), Q26–Q30 (Verb forms: teaches, was crossing, had studied, found, will have finished).
- **Paper 4 (`doc_d50623457f36f5aeab231741`):** Inspected Pages 1 to 4: QW1 (Précis), QW2 (Comprehension), QW4 (Letter), QW5 (Prepositions multi-part), QW6 (Verb forms multi-part), QW7 (Voice multi-part), QW8 (Reported speech multi-part), QW9 (One-word substitution multi-part), QW10 (Synonyms multi-part), QW11 (Antonyms multi-part).

## Documented Source, Extraction & Option Defects

1. **Rectification of Erroneous 'sociology' Subject Misclassification:** In Sericulture Extension Officer, question Q3(ii) was mistakenly ingested with `subject_id: sociology` due to the passage topic ('class factor in communal politics'). Rectified to `english/comprehension`.
2. **Unextracted Conventional Descriptive Tasks:** Preserved 5 conventional written prompts totaling 80 marks in `pending-written-intake.json` across Sericulture, MES Combined, and MPE & SS.
