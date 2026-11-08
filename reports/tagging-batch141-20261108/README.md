# Tagging Batch 141: LDE & Departmental General English Collection (11 Papers)

## Summary
- **Batch ID**: 141
- **Date**: 2026-11-08
- **Targets**: 91 questions across 11 examination papers (3 conventional items preserved, 50 conventional marks)
- **Completion**: 100% paper completion achieved for 11 LDE & Departmental General English examination papers (91/91 questions reviewed: 17 Grammar & Transformations, 17 Comprehension, 12 Vocabulary, 10 Phrasal Verbs & Idioms, 10 Parts of Speech, 9 Essays, 8 Letters & Memorandums, 4 Précis, 3 Reported Speech, 2 Synonyms, 1 Voice, 1 Antonyms, 1 Paraphrasing; 3 conventional items [50 marks] preserved in pending-written-intake.json)
- **Live Changes**: 0 (All 91 candidates remain `pending`)
- **Actions**:
  - `retag`: 88
  - `keep`: 3
  - `hold`: 0
- **Verification**: 91/91 source fingerprints re-verified via repeatable-read Oracle readback (2026-11-08T02:52:21.065959+00:00).

## Papers Included
- **`Old_Questions/Departmental_2015-2018/General English Common..pdf`**: 4 targets (Document ID: `doc_51aa01aa947a84598a1f12b9`, SHA256: `fef497509020d207...`)
- **`Old_Questions/Departmental_2015-2018/Paper I General English..pdf`**: 7 targets (Document ID: `doc_b2575a6392f3c342386ad464`, SHA256: `f84327257a70ecdc...`)
- **`Old_Questions/Departmental_2015-2018/aper-I General English..pdf`**: 4 targets (Document ID: `doc_b2fe8488b543e9e3c0b6e800`, SHA256: `9d45f5498997aaea...`)
- **`Old_Questions/LDE_2014-2018/1.Functional Manager (LDE) 2016 General English.pdf`**: 10 targets (Document ID: `doc_98f878d275ca87fda8d96a35`, SHA256: `eb634637f200a506...`)
- **`Old_Questions/LDE_2019-2020/Asst. Jailor Paper-I.pdf`**: 3 targets (Document ID: `doc_3fdcfae8f35982d53695b72b`, SHA256: `2d8cd0a812079650...`)
- **`Old_Questions/LDE_2019-2020/General English (ASI-UB).pdf`**: 3 targets (Document ID: `doc_977cc358a9c0eb35da3053f0`, SHA256: `981474cb6e8d080d...`)
- **`Old_Questions/LDE_2019-2020/MSS Paper-I.pdf`**: 2 targets (Document ID: `doc_400f9cc4172aaba44334b939`, SHA256: `04535dce3352e6f5...`)
- **`Old_Questions/LDE_2019-2020/Paper-I (UDC-Various Deptt.).pdf`**: 2 targets (Document ID: `doc_e9f2993a3aca5c46b2bc8e3d`, SHA256: `bc311785cae48425...`)
- **`Old_Questions/LDE_2021-2022/LDE Inspector of Police (MUC) under Home Deptt. Paper-I..pdf`**: 13 targets (Document ID: `doc_9c89b24d2fe1f5b373f333ec`, SHA256: `2ef4715e03f5df98...`)
- **`Old_Questions/LDE_2024-2026/Headmaster (High School)LDE Paper-I-2024..pdf`**: 10 targets (Document ID: `doc_75ab5e5aeef21070b1694dc3`, SHA256: `e5611151f50592a9...`)
- **`Old_Questions/LDE_2024-2026/LDE, Principal HSS Paper-I..pdf`**: 33 targets (Document ID: `doc_f4091465f2148568fefcff91`, SHA256: `3c15b24c2deb4c5f...`)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
| `english/grammar` | 17 |
| `english/comprehension` | 16 |
| `english/vocabulary` | 12 |
| `english/grammar/parts-of-speech` | 10 |
| `english/vocabulary/idioms-and-phrases` | 10 |
| `english/writing/essay` | 8 |
| `english/writing/letter` | 6 |
| `english/writing/precis` | 4 |
| `english/grammar/reported-speech` | 3 |
| `english/vocabulary/synonyms` | 2 |
| `english/writing` | 1 |
| `english/grammar/voice` | 1 |
| `english/vocabulary/antonyms` | 1 |

## Highlights & Key Ingestion Fixes
1. **Cross-Domain Corrections**:
   - Multiple essays originally misclassified under `general-studies` or `education` (in Asst. Jailor, ASI-UB, MSS, UDC, and Principal HSS papers) were properly unified into `english/writing/essay`.
   - Official memorandum and formal letter drafting items originally misclassified under `service-rules-and-office-procedure` were properly unified into `english/writing/letter`.
2. **Grammar & Vocabulary Refinements**:
   - Reclassified 10 phrasal verbs into `english/vocabulary/idioms-and-phrases`.
   - Refined 17 reading comprehension questions into `english/comprehension`.
   - Categorized reported speech, active/passive voice, and abstract nouns into their specific grammatical subtopics.
3. **Conventional Preservation**:
   - Preserved Section A conventional written sections (Essay 25 marks, Précis 15 marks, Letter 10 marks) for Functional Manager LDE in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 91 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 32 rendered page images across 11 source PDFs.
