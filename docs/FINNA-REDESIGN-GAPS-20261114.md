# Finna redesign coverage audit — 14 November 2026

This audit began after the first frontend deployment. The owner subsequently
requested the admin and mobile follow-up recorded in
`../reports/finna-admin-mobile-20261114/README.md`. Full fidelity to every possible
application state is not certified. Route availability and inherited fonts/colours do not count
as a completed screen redesign. This is a source-coverage audit, not a claim that
every state below has been visually exercised.

The preserved references contain 18 Web screen labels, 37 Mobile screen labels
and five Admin screen labels. Direction pickers and device frames are reference
presentation scaffolding; sample people, dates, scores and audit data are not
production content.

## Web reference coverage

| Reference label | Current implementation and remaining work |
| --- | --- |
| Navbar | New shared shell implemented; full signed-in account/notification states need comparison. |
| Home feed | Main three-column layout implemented with real data; full phone-specific composition still needs comparison. |
| Inbox | Existing notification/chat layout inherits theme; detailed reference layout not ported. |
| Creator profile | Existing layout inherits theme; detailed reference layout not ported. |
| Exams | Catalog cards, save/compare and real inventory implemented; all responsive states still need comparison. |
| Exam detail | Existing exam overview retained; not fully rebuilt against the reference. |
| Exam browse | Existing source-preserving browser retained; detailed visual matching incomplete. |
| Exam practice | Existing scoring/reveal implementation retained; detailed visual matching incomplete. |
| Exam progress | Existing progress views retained; detailed visual matching incomplete. |
| Library | New subject grid and guided-tool layout implemented; Reading/Saved/detail states need further comparison. |
| Question bank | Reference frame, header, three columns, pool/sort groups, selection bar, pagination range and a real Coverage-by-year rail implemented 15 November 2026. Two deliberate deviations: the row keeps `QuestionCard` inline answering by owner decision, so the reference's compact row and its Table view are not built; and "Saved filters" is omitted because no saved-views API exists. "Save to collection" is omitted for the same reason. |
| Question detail | Reference two-column frame, question card, option geometry, "Appeared in" and Topic rail cards implemented 15 November 2026. The inline discussion thread and reply composer are not built: no thread/composer API is wired to this screen, so the card shows its heading and locked state around the existing actions row. Answered states are not visually exercised. |
| Create hub | Framing and shared styling updated; every action/detail state not compared. |
| Profile and rewards | Existing layouts inherit theme; detailed reference layout not ported. |
| Games | Existing lobby/player layouts inherit theme; detailed reference layouts not ported. |
| Atlas | New chapter sidebar, subject controls and phone selection implemented over real maps; not full reference parity. |
| Study desk | Existing layout receives type/geometry overrides; reference composition/room states not fully ported. |
| Chronicle | New Canvas/Reading/source inspector implemented; reference era/track/heat-lens and cross-tool interactions are not fully matched. |

Past papers is an additional production adaptation at `/past-papers`; `/papers`
remains the original PDF asset namespace. Original booklet grouping and links
are retained.

## Mobile gaps

The requested follow-up implemented the reference bar **Home / Exams / Library /
Desk / Me**, phone headers and quick actions, narrow card/control geometry,
Inbox Notifications/Messages/Settings and conversation layouts, Me shortcuts,
Desk tabs, vertical Chronicle entries, source/question review tabs and responsive
module/exam/practice/mock/account presentation. Create and More remain accessible
through the phone header. Large unread counts use a 99+ badge with the actual
count retained in the accessible name.

Phone interaction checks now work through a temporary same-origin harness, using
actual app viewports at 390px and 320px. Live authenticated checks covered Inbox,
notification settings, profile editor, security, Desk notes, mock builder, and
admin review with the original PDF. Public/local checks covered the exam chooser,
exam study options, Library Modules, Atlas layers and light/dark appearance. The
harness was removed after verification. See the report for precise evidence and
limits; these checks do not certify every possible state in all 37 reference scenes.

## Admin gaps

| Reference label | Current implementation and remaining work |
| --- | --- |
| Admin sidebar | Grouped navy sidebar and gold active state implemented with existing grants. |
| Admin overview | Implemented attention rows, pipeline summary, totals and recent recorded activity; full coverage table and tools remain available. Verified signed in on the live site. |
| Admin question review | Implemented queue / original PDF / inspector panes with collapsible filters and phone tabs. Original PDF rendered live on desktop and phone; decision controls retained. |
| Admin paper pipeline | Implemented six real intake stages, independent per-stage previews, full stage lists and original guarded evidence editor. No simulated transitions or invented owners. |
| Admin audit history | Implemented timeline, loaded-event type/search filters, raw details and older-event loading. Live type filter checked; immutable event data retained. |

Authenticated learner and staff checks were performed through the owner’s existing
live browser session. New test attempts, messages, permissions and publications
were not created for visual QA. Complete layout work while preserving permissions, MFA, source booklet
identity, source labels, answer reveal restrictions and scoring rules. Do not
create synthetic attempts, messages, invitations or publication actions for QA.

## Completion criteria

- Match every reference scene to a real application route/state and record any
  deliberate live-data adaptation separately from unfinished implementation.
- Finish the individual layouts above; shared theme changes are insufficient.
- Compare desktop and actual phone interactions in both themes, including loading,
  empty, error, signed-in and permitted staff states where relevant.
- Retain existing source/permission/assessment checks, rebuild, and verify the
  deployed artifacts again after the remaining work is complete.
