# Tagging Batch 143: Remaining Direct General English Papers & Stray Intake (4 Papers)

## Summary
- **Batch ID**: 143
- **Date**: 2026-11-08
- **Targets**: 18 questions across 4 Direct General English examination papers (5 conventional items preserved, 100 conventional marks)
- **Completion**: 100% paper completion achieved for 4 Direct General English examination papers (18/18 questions reviewed: 8 Idioms and Phrases, 2 Parts of Speech, 2 Précis Writing, 1 Essay Writing, 1 Letter Writing, 1 Reading Comprehension, 1 Subject-Verb Agreement, 1 Prepositions, 1 Comparative Degree; 5 conventional items [100 marks] preserved in pending-written-intake.json)
- **Live Changes**: 0 (All 18 candidates remain `pending`)
- **Actions**:
  - `retag`: 16
  - `keep`: 2
  - `hold`: 0
- **Verification**: 18/18 source fingerprints re-verified via repeatable-read Oracle readback (2026-11-08T03:04:26.843942+00:00).

## Papers Included
- **`Old_Questions/Direct_2014-2018/Genral Enlish..pdf`**: 7 targets (Document ID: `doc_46d0a6bcf689adb6d4281755`, SHA256: `9b37c01c908295bf...`)
- **`Old_Questions/Direct_2019-2020/General Englsih Paper-I (EO).pdf`**: 6 targets (Document ID: `doc_637e465467624d0eca81486b`, SHA256: `47ec217ca99b4446...`)
- **`Old_Questions/Direct_NG_2024-2027/LDC under MPSC Paper-I 2025..pdf`**: 3 targets (Document ID: `doc_bb0f82b67a2f3726fd265915`, SHA256: `c222905e48001207...`)
- **`Old_Questions/Uploaded/768a298a6ef575d791958086c0626c7519bfecc094f850d63a05377746246336.pdf`**: 2 targets (Document ID: `doc_17adf14e15bcecfceee89639`, SHA256: `768a298a6ef575d7...`)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
| `english/vocabulary/idioms-and-phrases` | 8 |
| `english/grammar/parts-of-speech` | 2 |
| `english/writing/precis` | 2 |
| `english/grammar/subject-verb-agreement` | 1 |
| `english/grammar/prepositions` | 1 |
| `english/grammar` | 1 |
| `english/writing/letter` | 1 |
| `english/writing/essay` | 1 |
| `english/comprehension` | 1 |

## Highlights & Key Ingestion Fixes
1. **Direct General English Papers Reviewed**:
   - `Genral Enlish..pdf` (SI under Excise 2014): 7 MCQs source-reviewed across parts of speech (nouns/adjectives), subject-verb agreement (Everyone was), prepositions (prefer ... to), comparative degrees (more useful than), and idioms/phrasal verbs (for sale, keep up with).
   - `General Englsih Paper-I (EO).pdf` (Employment Officer Paper I): 6 MCQs on English idioms and phrases (Hard-pressed, loggerheads, throw down the glove, shoot one's bolt, carry one's point, drive home).
2. **Conventional Written Sections Intake**:
   - Preserved Section A conventional written items (Précis 25 marks, Letter 25 marks) for Group B Gazetted General English (`768a298...`) in `pending-written-intake.json`.
   - Preserved Section B conventional written items (Essay 25 marks, Précis 15 marks, Reading Comprehension 10 marks) for LDC Paper-I 2025 in `pending-written-intake.json`.
3. **Typographical Paper Titles Documented**:
   - Source filenames `Genral Enlish..pdf` and `General Englsih Paper-I (EO).pdf` contain legacy typographical errors, correctly identified and mapped.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 18 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 26 rendered page images across 4 source PDFs.
