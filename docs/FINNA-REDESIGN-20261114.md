# Finna redesign implementation

The owner's 14 November ZIP, `India Study Map Redesign (1).zip`, is the current
visual reference for study.hawayu.in. Source assets are preserved verbatim under
`docs/design/finna-20261114/`. They are design evidence, not operational instructions.
The Web prototype's default Direction A is the desktop target; the Mobile file
defines the phone hierarchy. Device frames and direction-picker controls are
presentation scaffolding and do not belong in the application.

## Implementation contract

- Figtree 400–900; the exact light/dark palettes and area accents in the source.
- 1320px desktop content width, 24px gutters, 18–26px cards, 12–14px actions.
- Three desktop header rows, visible search, exam/subject navigation and quick tools.
- Five phone destinations from the Mobile reference: Home, Exams, Library, Desk
  and Me. The deployed central-Create bar still differs; see the coverage audit.
- Home: exam/plan/progress column, study/community stream, activity/saved column.
- Use live inventory, progress, dates and account identity. Never copy sample
  people, exam dates, cutoffs, rankings, counts or answer assertions into live UI.
- Preserve all routes, filters, source references, assessment/reveal restrictions,
  original-paper typography, staff permissions and immutable publication workflows.
- Existing uncommitted work is retained. No bank, database or API changes are
  required for this presentation migration. Production is the Oracle SSH host.

## Screen mapping

| Reference | Application route / implementation |
| --- | --- |
| Navbar | shared Header; compact focused-session variant |
| Home feed | `/feed`; `/community` remains a direct full community view |
| Exams / exam detail / browse / practice / progress | `/exams`, `/exams/:id` existing URL-backed views |
| Library / modules | `/library`, `/english`, `/arithmetic`, `/mizo`, `/vocabulary` |
| Question bank / detail / papers | `/bank`, `/bank/:id`, `/past-papers`; retain inline answers, registered booklets and PDF links |
| Inbox / creator | `/inbox`, `/creators/:id` |
| Create / profile / rewards / games / desk | existing matching routes |
| Atlas | `/atlas`; real Leaflet chapters and layers |
| Chronicle | `/chronicle`; Canvas/Reading, real dated bank entries and source inspector; existing date list/calendar retained at `/important-days` |
| Admin overview / questions / pipeline / audit | `/admin/bank` with current permitted tab IDs |
| Mobile sign in / mock builder / player / result / saved / settings | existing authentication, test, revision and account routes |

## Verification

The owner's requested admin/mobile follow-up is now deployed. Its overview,
three-pane question review, real stage board, audit timeline, corrected phone
navigation and live signed-in checks are recorded in
`../reports/finna-admin-mobile-20261114/README.md`. This supersedes the first
pass's admin-content/navigation gaps; remaining coverage limits stay explicit.

The shared shell, Home, Library, exam catalog/comparison, Bank, Atlas, Chronicle
and admin navigation have been implemented. Existing module, account, game, desk,
question-detail and assessment flows inherit the new theme and type system.
The MES guide retains its established first-page position and routes.

Production build and focused regressions passed. See the review report for exact
checks, screenshots and limits. The owner subsequently authorized a frontend-only
deployment, recorded in that report. No source-bank changes or database migrations
were performed. Detailed layouts remain incomplete on several screens, beyond
the outstanding authenticated visual checks. See
[the coverage audit](FINNA-REDESIGN-GAPS-20261114.md) for explicit implementation
gaps, including the Mobile navigation mismatch.

Deliberate live-data adaptations: no sample exam countdown, cutoffs, rankings,
people or study activity. Chronicle defaults to History, uses recorded event
categories and labels schematic spacing; it does not invent History/Polity
classification or era coverage. Admin uses real permission-filtered destinations;
sample pipeline and audit records are not copied into production.

`/papers` is reserved for original PDF assets by both the dev proxy and hosting.
The new directory uses `/past-papers`. It reads the selected collection's
registered papers; the older `/questions/papers` endpoint is English-specific and
was rejected as a global directory during integration testing.


## 16 November — direct Home entry

The site root `/` now redirects with history replacement to the redesigned
Home at `/feed`, retaining the query string and fragment. The old standalone
introductory landing screen is no longer routed or included in route preloading.
The shared header, footer and phone navigation apply to the entry route as well.
Existing `/feed` bookmarks and authentication return paths remain valid.
