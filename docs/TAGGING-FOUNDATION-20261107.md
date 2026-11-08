# How to tag once and reuse questions across exams

> Historical foundation and source findings. Current decisions and model work
> follow [Question tagging rules](QUESTION-TAGGING-RULES.md), which supersede the
> initial policy/work sequence below. Counts and source observations remain dated.

Reviewed 7 November 2026. This is the initial manual-review policy and a read-only findings report. No bank question or paper-scheme binding was changed for this review. The separate account-access release only changes the named owner's MFA requirement, account setup state, and an unverified scheme template.

## The answer

The existing architecture supports the intended organisation. Cross-exam learning filters and module-specific subject filters already work. It is not fully configured or fully classified. Agree the rules now and map representative papers before starting bulk manual cleanup. There is no need to rebuild the bank or create different copies of English questions for each exam.

## Five separate things to record

| Dimension | What it answers | Example |
|---|---|---|
| Original source appearance | Where exactly was this question printed? | Gazetted combined, year/booklet, General Studies I, Unit B, Q/page |
| Learning path | What knowledge or skill is actually tested? | GK/GS -> Current Affairs, or English -> Vocabulary |
| Context | What place, language and reference date apply? | Mizoram; English; dated event in 2025, or changing office-holder as of exam date |
| Applicable scheme | What structure/rules applied to this particular paper? | Gazetted 2025 revision; section marks, question type, timing and choice instructions |
| Module/collection membership | In which study area should this source/question be available? | UDC and Assistant together for a genuinely combined source; All English across all exams |

Do not derive the learning tag from the paper title alone. A General Studies paper can include history, current affairs, arithmetic and English vocabulary. A General English paper can include written and MCQ tasks. Language of printing is not an English subject tag. A geography question written in English stays Geography.

The app already combines General Knowledge and General Studies for discovery using approved display mappings, while retaining their stored IDs. Continue using the shared picker; avoid creating new duplicate GK/GS subjects. One primary learning path is the default. Add another approved path only when additional knowledge is genuinely tested. Source board, module names, year and region belong to their own dimensions.

## What the official sources show

| Source reviewed | Organisation consequence |
|---|---|
| Assistant/UDC combined syllabus linked for the 2026 recruitment | Paper I mixes GK and English MCQs with written Precis, Essay and Comprehension. Paper II contains Computer, Arithmetic and Reasoning. This is a recruitment-specific combined route, not the generic Non-Gazetted blueprint. |
| Generic Non-Gazetted, 9 July 2024 | General English and GK & Reasoning have their own allocations. The historical English outline differs from the later edition. Preserve this edition when applicable to a source. |
| Generic Non-Gazetted, 28 October 2026 | General route still has English plus GK & Reasoning, but English now explicitly includes Essay alongside Precis, Letter and Comprehension. The source has a separate technical route. The correct applicability is established by each recruitment notice/amendment. |
| Gazetted combined, 17 July 2025 | General English, General Essay and GS I/II/III are paper labels. GS I has Modern Indian History/Culture and Current Events. GS II has Polity, Economy and Geography. GS III has Science/Technology, Mizoram and Aptitude, including verbal/vocabulary work. |

Thus **Current Affairs within General Studies I is an exam section**. For reusable learning it uses the shared Current Affairs path. A static constitutional fact under a GS paper is Polity; do not call it Current Affairs just because the paper includes a current-events section elsewhere. A dated appointment question needs a reference period and must preserve its historical key. A grammar passage mentioning a political event tests grammar unless another task actually tests that event.

A vocabulary question printed in GS III can be classified English -> Vocabulary and remain discoverable from its original GS III/Aptitude source. Its source label and skill tag are intentionally different.

The 2026 combined Assistant/UDC source also distinguishes the standard of Assistant Grade when exams are held separately. Combining study coverage does not imply identical exam rules, level or applicability. Direct recruitment, LDE and Departmental sources must remain distinguishable.

## Is reuse working now? Fresh checks

Public paper-bank API, all-exam scope, all-question pool, 7 November:

| Filter | Published question count |
|---|---:|
| All exams -> English | 11,179 |
| UDC -> English | 1,245 |
| Assistant -> English | 265 |
| LDC -> English | 71 |
| Gazetted -> English | 158 |
| Gazetted -> GK/GS -> Current Affairs | 86 |

These are counts under current approved tags and current membership. They do not establish semantic completeness. Module totals overlap and must not be added. A read-only live query found **898 distinct canonical question IDs present in both UDC and Assistant browse membership**. This is real module reuse without needing duplicate copies.

An additional live primary-classification check found **4,557 live English questions with no topic label**. English Writing paths exist in the taxonomy, but that existence does not mean all written prompts were correctly assigned. Do not interpret this count as a complete writing-only backlog.

Fresh private read-only configuration counts:

- `bank_scheme_revisions`: **0**
- `bank_paper_profiles`: **0**
- `bank_question_contexts`: **0**

This is the main unresolved setup issue. The new versioned configuration tools/templates are deployed, but no saved revisions, exact paper bindings or new context records were populated at this check. Older module configuration, source roles and current-affairs systems are separate; these zeros do not mean those systems do not exist.

## Links that demonstrate the intended views

- [All English](https://study.hawayu.in/bank?subject_id=english&exam_scope=all)
- [LDC English](https://study.hawayu.in/bank?collection_id=ldc&subject_id=english&exam_scope=all)
- [UDC English](https://study.hawayu.in/bank?collection_id=udc&subject_id=english&exam_scope=all)
- [Assistant English](https://study.hawayu.in/bank?collection_id=assistant&subject_id=english&exam_scope=all)
- [Gazetted English](https://study.hawayu.in/bank?collection_id=group-b-gazetted&subject_id=english&exam_scope=all)
- [Gazetted Current Affairs](https://study.hawayu.in/bank?collection_id=group-b-gazetted&subject_id=gk-gs&topic_id=gk-gs%3Acurrent-affairs&exam_scope=all)
- [Learning tags](https://study.hawayu.in/admin/bank?tab=retag)
- [Modules & schemes](https://study.hawayu.in/admin/bank?tab=organization)
- [Paper readiness](https://study.hawayu.in/admin/bank?tab=organization&organization_view=paper)

For a new combined UDC/Assistant collection, reuse the existing module composer to select reviewed source membership. It must be the union of the intended sources, with distinct-question learning counts. Do not merge entire UDC and Assistant histories merely because some sittings were combined. Preserve each original paper and its exact scheme.

## The initial manual work sequence

1. **Agree this small tagging policy.** Use the existing approved taxonomy. Keep source labels, learning paths, context, scheme and module membership separate.
2. **Choose four representative sources:** one genuinely combined Assistant/UDC paper, one separate/legacy clerical paper, one Gazetted GS paper and one English/written paper. Check their precise recruitment notices and amendments.
3. **Save the applicable scheme editions as drafts** in Modules & schemes. The new Assistant/UDC combined template keeps mixed Paper I, its written tasks and separate Paper II; it is not automatically verified or bound to any source. Historical dates and printed written-question counts stay unknown until sourced.
4. **Complete exact paper profiles** in Paper readiness: provider/corpus, era, scheme revision, paper key, every printed appearance in order and section mapping. A current template must not retroactively overwrite a legacy paper.
5. **Tag a small representative batch manually**, for example 20-50 questions from each selected source. Record one primary path, useful related paths, written/MCQ format, source locator, figures/passages and changing-date context. Use intentional subject-only resolution only for genuinely broad questions with evidence.
6. **Check the learning views after publication/readback.** Every selected English item should appear in All English and its eligible exam/module English view. A GS Current Affairs question should remain in its original paper and also appear in its shared learning topic. Inspect a GS III vocabulary example explicitly.
7. **Correct the pilot rules and then scale** bounded batches, saved by source/module/issue. Keep original-paper coverage, general practice readiness and scored full-simulation readiness separate.

Manual checking is the final content authority for your workflow. The foundation makes each correction reusable, so the same question does not need independent retagging for every module. Never create inspection or approval records to represent work that was not done.

## Manual review checklist

- Exact PDF, source year, booklet, printed page/question and section confirmed.
- Question wording, options, passages and diagrams match the original.
- Primary subject/topic describes the task, not the paper title or passage decoration.
- Additional paths are justified; provider/year/region are not duplicate subject tags.
- Format is preserved: MCQ, written comprehension, essay, precis or letter.
- Historical/current reference date is explicit where the answer can change.
- Scheme revision is applicable to that exact recruitment; unknown rules remain unset.
- Existing module source membership is correct; combined-source reuse is deliberate.
- Save/publish status and bank readback verified; unresolved issues remain labelled.

## Evidence and limits

Downloaded fresh from the official MPSC site and visually inspected the relevant pages:

- [Assistant/UDC combined](https://mpsc.mizoram.gov.in/uploads/attachments/2026/05/f74b4d6652a90a741cd5907be6fad00d/syllabus-for-assistant-udc-combined.pdf). SHA256 `1387109c60b985bbcf3a4e2215b04bb3939c2652bd55942c119edce47af87a23`; table and learning areas visually checked on page 1. The prior 2 November source receipt records the amendment/penalty inspection. New download matches that exact file.
- [Gazetted 2025](https://mpsc.mizoram.gov.in/uploads/attachments/2026/04/ee26522353e4d860ba5b28834fb35af9/scheme-of-examination-for-mizoram-group-b-gazetted-general-services-combined-competitive-examinations-2025.pdf), relevant learning sections visually inspected on pages 5-8.
- [Non-Gazetted October 2026](https://mpsc.mizoram.gov.in/uploads/attachments/2026/11/32bc3ed03f920c30e06edaccfa44e6fe/syllabus-for-non-gazetted-posts-28102026.pdf), page 1 visually inspected.
- [Non-Gazetted July 2024](https://mpsc.mizoram.gov.in/uploads/attachments/2024/07/63f9bc05c3b756aaa90fbf045d0ae494/syllabuses-for-group-b-non-gazetted-posts.pdf), page 1.

Code reviewed: `services/learning_taxonomy.py`, `learning-topic-aliases.json`, question and collection filters, `bank_organization.py`, module composition, scheme templates and current implementation records. Counts from direct public API calls and a read-only production SQL transaction. This is a source/configuration review with selected examples, not a semantic inspection of all 82k records. No bulk retagging, canonical merges, source publication or human approval was performed.
