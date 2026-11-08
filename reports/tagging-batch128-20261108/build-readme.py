"""Generate README.md for Batch 128."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 128: Jr. Accounts Officer (July 2026) — Paper-II (GK, Arithmetic & Reasoning) (Series A) [Part 1: Q1–Q50]

## Summary
- **Batch ID**: 128
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2025-2027/Jr. Accounts Officer Paper-II (GK, Arithmetic & Reasoning) -Series A..pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 200 Marks (100 Objective MCQs, 2 marks each across full paper)
- **Subject Coverage in Batch 128 (Q1–Q50)**: General Knowledge, Current Affairs, Indian History, Geography, Indian Polity, Indian Economy, Environment, and General Science (Biology, Physics, Chemistry)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **General Studies & Current Affairs (Q1–Q4, 4 MCQs)**:
   - **Q1–Q4**: National & international current affairs (INTERPOL Silver Notice, Project Waterworth, TALASH programme, Yala glacier) -> `general-studies/current-affairs` (4)
2. **Indian History (Q5–Q7, Q27–Q29, 6 MCQs)**:
   - **Q5–Q7, Q27–Q29**: Subsidiary Alliance, Gupta administration, Anglo-Maratha Wars, Ilbert Bill, Vernacular Press Act 1878, Cripps Mission -> `general-studies/indian-history` (6)
3. **Geography (Q8–Q10, Q30–Q32, 6 MCQs)**:
   - **Q8–Q10, Q30–Q32**: Convectional & orographic rainfall, heat budget, ITCZ, tropical cyclones, equator & tropics, Tibetan plateau -> `general-studies/geography` (6)
4. **Indian Polity (Q11–Q12, Q33–Q36, 6 MCQs)**:
   - **Q11–Q12, Q33–Q36**: Fundamental Duties, Drafting Committee, Money Bills, Judicial Review, Tenth Schedule anti-defection, non-constitutional bodies -> `general-studies/indian-polity` (6)
5. **Indian Economy (Q13–Q15, Q37–Q38, 5 MCQs)**:
   - **Q13–Q15, Q37–Q38**: GNP, HDI indicators, WTO Amber Box subsidies, Self Help Groups, dependency ratio -> `general-studies/indian-economy` (5)
6. **Environment & Ecology (Q16, Q39–Q41, Q43, 5 MCQs)**:
   - **Q16, Q39–Q41, Q43**: Red Data Book green pages, Brundtland Report, acid rain pollutants, biosphere reserves, wetlands & coral bleaching -> `general-studies/environment` (5)
7. **General Science (Q17–Q20, Q42, Q44–Q46, 8 MCQs)**:
   - **Q17, Q42**: Ecology (Amensalism, biomagnification) -> `science/biology/ecology` (2)
   - **Q18**: Physics (Work done pushing against a rigid wall) -> `science/physics/mechanics` (1)
   - **Q19**: Chemistry (Lithium-ion batteries vs lead-acid batteries) -> `science/chemistry` (1)
   - **Q20, Q44**: Human Physiology (Iodine-131, cerebellum balance) -> `science/biology/human-physiology` (2)
   - **Q45**: Physics (Rayleigh scattering of blue sky) -> `science/physics/light` (1)
   - **Q46**: Cell Biology & Genetics (Human chromosomes & RNA) -> `science/biology/cell-biology` (1)
8. **Mizoram State Studies (Q21–Q24, Q26, Q47–Q50, 9 MCQs)**:
   - **Q21–Q24, Q26, Q47–Q50**: Zupui Ni festival, Operation Jericho, folklore, Lushai Hills 1898 unification, Project Thaichhawninu, mythic world tree, Thingdim lam, Ram sem sap, 2nd Governor -> `general-studies/mizoram` (9)
9. **Sports (Q25, 1 MCQ)**:
   - **Q25**: Estadio Azteca hosting three FIFA World Cup opening matches -> `general-knowledge/sports` (1)

## Full Paper Integration Note
- **Batch 14** (`reports/tagging-batch14-20261107`) reviewed Questions 51 to 100 (50 MCQs covering Arithmetic, Mensuration, Data Interpretation, and Reasoning & Aptitude).
- **Batch 128** (`reports/tagging-batch128-20261108`) reviews Questions 1 to 50 (50 MCQs covering General Knowledge, General Studies, Science, and Current Affairs).
- Together, Batch 14 and Batch 128 provide complete 100% paper coverage (100/100 MCQs) for *Junior Accounts Officer 2026 Paper-II (Series A)* with 0 duplicated appearance reviews and 0 conflicts.
- `Jr. Accounts Officer Paper-II (GK, Arithmetic & Reasoning) -Series-B..pdf` (`doc_da3d581ae85f52a4bbe97c34`) is bypassed under single-booklet deduplication policy.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 50 candidate records staged under policy `study-tagging-v1`.
- Complete verification against rendered page images 1–6 from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
