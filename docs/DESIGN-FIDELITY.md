# Design fidelity — values extracted from the prototype

## Current visual reference — 14 November 2026

20 November locally staged privacy tools: existing semantic paper/night cards,
Figtree, labelled forms, min44px buttons and wrapped references/support address.
Age selection distinguishes a browser choice from signed-account confirmation;
under-18 enrollment is visibly unavailable. Account privacy forms and owner queue
show request receipts, withdrawal/review states and explicitly manual outcomes.
Final366-file build passes actual synthetic browser receipt/withdrawal, account
switch, owner queue review and terminal status at1280/320, light/night. Widths
1265/1265 and305/305 fit. About/refund previews are visibly drafts; Privacy text
and width are checked in AX/DOM (its saved transition image depicts About).
Final and intermediate screenshots are distinguished in the report; full-page
capture at overridden width failed, alternate viewport captures worked. No physical
Android/accessibility or publication certification. Preview resources removed,
light/viewport restored. reports/finna-privacy-implementation-20261120/.

19 November staged referrals: semantic Profile invitation card and optional Join
notice/removal, verified/launch explanations, seven-day/ten-answer/five-per-year
bounds and explicit withdrawal. Reuses current account and Google sign-in forms;
submission locks invitation removal and parallel sign-in. Three actual components
and364-file final build pass. Browser synthetic create/withdraw/reactivate/reload
and anonymous notice/removal pass at1280/320 in light/night, client/scroll1265/1265
and305/305. Long email/handle wrapping in Profile corrected. Captures precede only
nonvisual account-only guard/submission interlocks; final build includes both,
actual signup/Google component checks cover interlocks. Exact preview resources
and agent tab removed,Light/viewport restored. No production referral rollout.
Proof:../reports/finna-referrals-staged-20261119/.


19 November review digest: semantic card/buttons on Profile and Email preferences,
explicit Off default and verified-email explanation, evening window and empty-queue
copy. Signed-out unsubscribe needs no account and clears the fragment after a
successful explicit action; GET opening is inert. Two actual React components
cover response/account isolation and errors. Browser1280/320px light/night passes,
client/scroll305/305; exact preview resources removed and Light/viewport restored.
Live preference page verified read-only; owner subscription unchanged.
Reports:../reports/finna-review-digest-production-20261119/ and
../reports/finna-review-digest-staged-20261119/.

19 November staged Atlas district/context: semantic Studio source/reuse/district
forms and dated-entry search, learner source attribution/downloads and shared map
renderer. Saved-exam ordering uses current sections/live curated links and retains
the full list. Chronicle links roundtrip to the selected map event; source changes
hide stale links. Eleven starting proposals are private, dated illustrative data,
not current surveyed boundaries or complete reviewed district content. Seven actual
components and361-file build pass; disposable browser draft/attach/preview/publish,
synthetic binding, order toggle, map/Chronicle and source views pass.320px
light/night learner/source editor/Chronicle client/scroll305/305. Screenshots and
cleanup:../reports/finna-atlas-depth-staged-20261118/. No production rollout or
native/source/legal certification. User tab retained,Light/viewport restored.

18 November staged Atlas drills: explicit authoring controls reuse Studio forms;
learner activity uses a blank AtlasMap with no study overlays before answering.
Results state distance/tolerance and zero XP/points. Explored is display-only,
Today suggestions are optional, and warm-up completion from map activity cannot
claim a chest. Optional question context reuses AtlasMap and ordinary question
options/scoring. Synthetic browser author/publish/correct/wrong/explored/practice/
Today/context checks passed; phone light/night widths 305/305 at 320px. Six actual
components/screens and final 357-file build pass, including pending-request
chapter/account reset cases.
Captures: ../reports/finna-atlas-drills-staged-20261118/. Browser checks preceded
only the final request-reset fix, which changed no layout. Temporary previews,
exact database, tabs removed; user tab retained and Light/viewport restored.
No real content review, native certification or production release is claimed.

18 November staged Atlas Studio: chapter/fact/layer/event forms reuse semantic
cards, inputs and palette; pin/line/area drawing and draggable handles use the
same AtlasMap as learners. AtlasChapter is the one learner/draft render path;
Studio marks drafts visibly and omits the live question panel in private preview.
Facts/layers use accessible up/down controls; timelines support drag and up/down.
Autosave survives reopen, immutable source attribution and exact saved-preview
publication are explicit. Final355-file build,3actual components and final-build
1280/320px light/night QA fit1265/1265 and305/305 client/scroll. Actual browser pin
placement/drag, line/area finish, undo/redo, view capture, autosave/reopen, publish/
hold/restore, invalid GeoJSON rejection and selected-layer copy verified only in a
disposable fixture. Browser found undo selection drift; corrected and verified on
phone. Captures in ../reports/finna-atlas-studio-staged-20261118/. No new factual
source review, physical/native certification or production rollout. Preview exact
process groups/database/tabs removed; user tab retained,Light/viewport reset.

18 November staged Atlas bindings: existing map/layer/timeline renderer gains a
semantic asked-from-map panel using ordinary QuestionCard/provenance/answer flow,
chapter/layer and exam selection, real counts, pagination and honest empty states.
Question cards/details expose reverse deep links from the same binding store.
Owner binding form reuses semantic card/input colors and explicit preview/decision
controls. Final353-file build,3actual components and built-artifact browser QA:
synthetic save/preview8/publish/5+3pages/reverse/hold-empty/restore/inline answer,
1280/320px light/night, widths1265/1265 and305/305. Captures/cleanup are in
../reports/finna-atlas-bindings-staged-20261118/. No physical/native certification,
real topic curation, new source review or full chapter Studio claim. Agent tabs,
preview process groups/database removed; user tab retained, Light/viewport reset.

19 November actual Samsung native check: the installed development APK exposes
a Home percentage-height bug that component tests did not model. Intrinsic action
sizing fixes1285px blank blocks to135px normal/252px at200% font. Tab labels use
constrained single-line sizing with full accessibility names; large text now fits
without last-letter clipping. Normal/200% screenshots and guest navigation cover
Home,Exams,Library/questions/filters,mock builder,Desk andMe. Font restored; only
these observed views are certified for this test setup. Full native acceptance,
standalone hot-font/release behavior and iOS remain open. Receipt:
../reports/finna-desk-pdf-20261119/NATIVE.md. No production web deployment.

19 November saved Desk PDF check: unmodified authenticated export HTML from a
synthetic DB printed with Chromium156 into4actual PDFs/17A4 pages. Every page was
rendered/visually inspected; wrapping, long titles/references, Mizo glyphs, margins,
empty state and assessment/ownership privacy pass. No layout/runtime edit was
needed. Mobile print/other browsers/printers remain unverified. Evidence:
../reports/finna-desk-pdf-20261119/; synthetic saved PDFs in output/pdf/.

18 November staged question notes and room calendar: the existing Desk shell and
rail gain live note references and a shared-only central-calendar card. Central
editor retains its form and adds explicit per-entry room/private selection. Final
350-file build, actual components/screen and1280/320px light/night synthetic QA
verify share/save/view/withdraw/owner retention, canonical note links and print
pages. Client/scroll widths1265/1265and305/305; no native/physical-device or actual
saved-PDF pagination certification. All previews/agent tabs/exactDB cleaned, other
user tab retained, viewport/Light restored. Frozen captures live in
../reports/finna-desk-notes-staged-20261118/ and
../reports/finna-desk-calendar-staged-20261118/. Production healthy-week gate open.

18 November staged synchronized Desk practice: the existing Desk shell gains a
semantic card with an explicit shared-set confirmation, eligible count, active
reservation/resume links and waiting/full/started states. The common GameRoom
player supplies ready/start/round/review controls; Desk sessions show a return link
and member-only joining instructions instead of an external code. Independent
practice is labelled separately and assessment-locked emptiness is explicit.
Practice intro/sidebar and the game surface now use shared light/night colors.
Built-artifact QA at 1280 and 320 px fits (1265/1265 and 305/305 client/scroll):
create, synthetic peer join, Ready/start, server-clock progression, return/resume,
assessment lock and release/completion. Four actual component/screen checks and
349-file build pass. Final screenshots and pre-correction captures are retained in
../reports/finna-desk-practice-staged-20261118/. All data is synthetic; this is not
production, native or physical-device certification. Light/viewport restored and
preview/tab/exact database cleaned up.

18 November locally staged Desk v4: Finna Web prototype's existing Desk shell,
Figtree, semantic light/night colors,18px panels,16/20px padding and44px controls.
The room Progress tab adds a labelled numeric weekly target and accessible bar;
Shared Qs adds a labelled review-circle selector and flag/resolve/reopen buttons;
Focus adds the current opt-in board beside the existing timer. No new navigation,
Today/mastery panel or duplicate timer/summary. Version/conflict, private/empty,
reached, outage and stale-account states remain explicit. Shared question pages
stay at five items. Synthetic development-preview1280/320px light/night checks fit
(1265/1265and305/305client/scroll); nine screenshots and actual-component tests:
../reports/finna-desk-goals-staged-20261118/. The existing timer's night-color contrast
is outside the new board's visual certification. Preview interruptions and capture
timing are recorded. No production rollout, built-artifact browser or native/device
certification; preview/tab/database/marker cleanup, Light and viewport reset complete.

18 November build-tool continuation: source markup/design tokens untouched.
6887compiled CSS AST entries preserve declarations/rule/cascade order; only15media
whitespace differences. Actual built artifacts pass1280/320px paper/night QA for
Operations, phone account search/all5sections and learner Library; no overflow
(1265/1265and305/305). Six synthetic screenshots/components/navigation checks in
../reports/finnaplan-v12-build-dependencies-20261118/. No device certification.

18 November maintenance: existing Finna Admin prototype shell, semantic palettes,
18px cards/20px padding and44px controls. Owner site notice uses plain-text input,
explicit IST expiry, visible version/conflict/error/success states and clear/reload.
Global announcement sits above the app shell. Restore age distinguishes an actual
paired restore from checksum collection and warns at40days.1280/320px light/night
QA fits (phone305client/305scroll with scrollbar), including actual expiry save /
reload and site-wide clear/refresh. Five synthetic PNGs and component checks are
in ../reports/finnaplan-v12-maintenance-20261118/. Synthetic12-day preview is not
real restore evidence; live actual restore age is0. No device certification.

18 November account viewer: extracted Finna Admin prototype lines14–18,26–46,
51–69 supply the existing navy/sidebar, semantic light/night palette, Figtree,
18px cards,20px padding and12px nested receipts. Canonical /admin/users and phone
selector remain in the existing shell. Search controls stack at320px; five real
account sections, explicit missing/outage states and existing-tool links use44px
controls. Synthetic1280/320px light/night QA fits without horizontal overflow
(1280/1280and320/320); four final PNGs and real component/auth/navigation checks
are in ../reports/finnaplan-v12-users-20261118/. No device certification.

Final collector-time reader correction (18 November): actual collection result
controls timer badges; checksum/peer-write latency is not a failed cycle. No
markup/static/token change after the five worker-release screenshots.11focused
backend regressions and real-role candidate/live reads verify the final state.

18 November worker/collector continuation: existing Finna Admin prototype semantic
palette,18px cards and16/20px padding stay. Probe cards now display measured GiB,
actual backup creation time and collector time separately, with explicit stale /
attention/unknown states. Successful checksum verification is visibly distinct
from a restore rehearsal.1280/320px light/night synthetic QA passes without
horizontal overflow (1265/1265,305/305); five PNGs and actual component/auth/error
checks live in `../reports/finnaplan-v12-workers-20261118/`. Phone Questions retains
its needs-review filter. No native/device or green-week certification is implied.

18 November ops slice: extracted `Finna Admin.dc.html` lines14–18,26–46,
51–69: navy sidebar, semantic light/dark palette, Figtree,18px card radius,
16/20px card padding and12px nested cells. `/admin/ops` reuses the existing admin
shell; the phone section selector reaches and leaves the canonical route.
State badges include words and unknown collection is visible. Refresh and
investigation controls have44px minimum height. Actual pool/economy/moderation/heartbeat queries replace prototype samples.
Synthetic1280/320px paper/night QA passes without horizontal overflow (1265/1265,
305/305px). Four PNGs, real component outage/auth-switch checks and navigation
proof: `../reports/finnaplan-v12-ops-20261118/`. No native/device certification;
collector readiness and a full healthy week are not implied by UI proof.

The owner supplied a new `India Study Map Redesign (1).zip` for study.hawayu.in.
Its Finna Web, Mobile and Admin markup supersedes the earlier visual values
below. The original files are preserved in `design/finna-20261114/`; implementation
mapping, live-data adaptations and verification are recorded in
`FINNA-REDESIGN-20261114.md` and `../reports/finna-redesign-20261114/README.md`.
Figtree, the exact navy/blue/yellow palette, light/dark semantic tokens, 1320px
content width and larger card/action radii replace the former warm-paper system.
Historical source, review, scoring and permission requirements still apply.

Existing-original link (4 November): the workbench uses the existing paper/card
tokens and44px controls to identify the exact registered PDF, show whether it is
empty, and explicitly link or refresh it before saving. Read-only reviewers see
the link and source-change warning; published drafts show completion instead of a
false warning merely because their questions now exist. Linking retains question
objects and adopts the original exam/year/subject metadata; it does not approve it.

Gazetted duplicate presentation (4 November): the original-paper workspace groups
only four source-audited written pairs, retaining the existing card styles. Its
header distinguishes printed questions from stored transcriptions. A 44px show-all
control, exact appearance links and flagged records preserve access to every record.
Grouping stops on current source/context/tag/hold differences. This is a reading
presentation change; archive/module inventory and scoring remain unchanged.

**The prototype markup is authoritative, not the handoff README.** The README
in `docs/design/README.md` gives a tidy summary of the tokens; where it
disagrees with `docs/design/India Study Map v3.dc.html`, the markup wins. It
disagrees in several places, listed below, and building from the README alone
produces something that looks close but reads wrong.

Extract values from the prototype with `grep`/`sed` before building a screen.
Do not eyeball them, and do not carry a value over from another screen
assuming it is shared.

## README vs. markup — known disagreements

| Thing | README | Markup (use this) |
|---|---|---|
| Card radius | 10px | **14px** (bank article) |
| Option button radius | 8px | **6px** |
| Correct state | `#2E7D46` / `#DCEFE1` | **`#3D7344`** border / **`#E3ECDD`** bg |
| Wrong state | `#C0392B` / `#F8DEDA` | **`#B0412A`** border / **`#F5E1D8`** bg |
| Option resting bg | `#FFFFFF` | **`#FBF8F1`**, border `#DCD3C2` |
| State indicator | symbols `✓ × !` | **words**: "Correct", "Answer", "Your pick" |

The README is still right about the six area colours, the three fonts, and
the "a colour names an area, never a state" rule.

## Bank question card (`v3.dc.html` line 407)

```
article  bg #FFFFFF · border 1px #E4DBC9 · radius 14px
         box-shadow 0 1px 2px rgba(29,27,24,.05) · padding 20px 22px
         margin-bottom 12px
```

Header row (`display:flex; flex-wrap; gap 6px 12px; align-items:center`):

1. **Topic chip** — mono 10px, uppercase, tracking .06em, padding 3px 9px,
   radius 999px, per-topic background and colour (see palette below).
2. **`Q{n} · {source}`** — mono 11px, `#6B6457`.
3. **Provenance pill** — mono 10px, uppercase, padding 2px 8px, radius 999px,
   **outlined**: `1px solid {provColor}`, text the same colour, no fill.
   `Official key` → `#3D7344`; anything else → `#2F5E8C`.
4. **Repeat badge**, only when `seen.length > 1` — mono 10px, uppercase,
   padding 3px 9px, radius 999px, **solid dark**: bg `#1D1B18`,
   text `#F4EFE4`. Copy: `Asked {n}× · {comma-separated years}`.
5. **`View original ↗`** — mono 11px, weight 500, `#33609E`,
   pushed right with `margin-left:auto`.

Question stem: Newsreader 21px, line-height 1.35, margin `10px 0 14px`,
`text-wrap: pretty`.

Options: `grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))`,
gap 8px. Each is a button — flex, gap 12px, padding 11px 14px, radius 6px,
font-size 15px, with the letter in mono 12px at a fixed 16px width.

**Options are answered inline on the bank list**, not only on a detail page.
The list header says "Tap an option to check it". After a pick the card
reveals an explanation underneath.

### Option states (from `opts()`, line 2603)

| State | bg | border | text | mark |
|---|---|---|---|---|
| resting | `#FBF8F1` | `#DCD3C2` | `#1D1B18` | — |
| revealed · correct | `#E3ECDD` | `#3D7344` | `#1D1B18` | `Correct` if you picked it, else `Answer` |
| revealed · your wrong pick | `#F5E1D8` | `#B0412A` | `#1D1B18` | `Your pick` |
| revealed · other | `#FBF8F1` | `#DCD3C2` | `#6B6457` | — |

Cursor is `pointer` before reveal, `default` after; options stop responding
once revealed.

## Topic palette (`const TOPIC`, line 2369)

`[colour, background]` pairs, keyed by topic name:

| Topic | colour | bg |
|---|---|---|
| Current affairs | saffron | — |
| Polity | blue | — |
| Science | green | — |
| English | plum | — |
| Mizoram | teal | — |

The literal hex values live in the `H` object in the prototype; read them
there rather than guessing. Note this palette is topic-specific and is **not**
the six area colours.

## Data-backed tags and discussion

The prototype's cards show a **topic chip** and a **discussion count**.
Taxonomy-v2 classifications now live in `question_classifications`, separate
from the legacy `subject`/`topic` values. Only `approved` claims appear in
bank filters and chips; pending proposals remain stored for review. Discussion
is milestone 4, so omit its count until that data exists. Never fall back to
the old `'gk'` placeholder.

### Bank and exam screens — live-data adaptations

- The Bank search currently searches question text only. Do not promise paper
  or topic search until the API indexes those fields.
- The answer-source filters apply to the selected pool. Scorable contains
  official and transcribed keys; All answered also contains derived and
  inferred answers. Unanswered questions are not in either pool, so “No
  published key” is not a selectable filter.
- The Bank's “Details” link opens question metadata and appearances. It is
  not a PDF viewer; page-image storage is still deferred.
- The launcher features a real public collection, currently ITI Instructor
  2026. LDE collections stay hidden until the user chooses to expand exam
  coverage. Never replace the live title or counts with sample values from the
  handoff.
- Section bars on an exam page show each section's share of that collection's
  scorable questions, not a percentage of the largest section.

## Naming — "module" is dead, and "exam" means two things

The prototype still uses the old vocabulary. The schema and UI moved on, and
the overlap is a real trap: the prototype's `exam` screen is **the timed
paper**, not an exam's landing page.

| Prototype screen | What it actually is | Schema | Our file |
|---|---|---|---|
| `modules` | the launcher, "Exams & tools" | `collections` | `screens/Exams.tsx` |
| `module` | one exam's landing page | one `collection` | `screens/ExamPage.tsx` |
| `exam` | **the timed paper itself** | `collection_papers.as_mock` | `screens/MockRunner.tsx` |

Schema v3 says it outright: *"Collections (UI: 'Exams & tools'; formerly
'modules')"*. Do not name anything new `module`, and do not assume a file
called `Exam*` is the timed paper — check which of the three it is.

Routes: `/exams` → launcher, `/exams/:id` → exam page, and the mock runner
is entered from there.

## Palette fidelity

Bank uses the Practice area palette (blue); Exams uses the Exams area palette
(ochre). Both follow the warm paper surfaces and ink primary actions in the
handoff. Vermilion is exactly `#C0462C` and reserved for the brand mark.
`placeholder #7A7366` remains as specified by the handoff.

## Public landing page (`is.landing`, prototype around line 77)

Use the V3 landing screen, not the signed-in feed: a full-width `#14130F`
hero/header with the six 7px area-mark squares, Newsreader wordmark and a
responsive two-column hero (copy left, answerable question card right).
Content is capped at 1240px with 24px gutters; hero copy uses a 38–64px
Newsreader heading, 18px/1.6 supporting copy, a Practice badge, blue primary
CTA, outlined bank CTA, and a plain “All exams” anchor. The example question
card is white with a pale Practice header, Newsreader 21px question, 8px
option corners, then source and provenance. Six area chips sit at the bottom
of the dark field. Below are three tinted steps, the live Exams grid, and the
Community introduction/cards. Finish with the near-black mono footer.

The app has no registration route or account authentication, so the prototype's
“Log in / Join free” is adapted to real destinations: “Study desk” and “Start
studying.” The hero question is selected daily from `v_scorable`, not inferred
answers; choosing an option calls the existing answer API, which records an
anonymous device attempt and reveals its provenance. Exam cards and totals are
read from the live database through `GET /api/home`. Only real public
collections are linked; community cards are visibly marked In progress or
Planned. Do not imply that feed, games, or accounts already work.

## Community feed (`is.feed`, prototype around line 169)

The V3 app home is the three-column Community feed: a 210–260px left rail for
exam, desk, partner, and exam links; a flexible central stream with the
Community heading, start-here exam banner, composer, five filter tabs, and
question/activity cards; and a 260–320px right rail for headlines, challenges,
weekly cup, standings, and help-the-bank links. Keep the main content within the
1240px shell, use 24px gaps, 14px white cards with `#E4DBC9` borders, warm
`#F4EFE4` page background, Newsreader headings, Public Sans body, and IBM Plex
Mono labels.

`/feed` implements that composition using live public exam collections and
actual device practice counts. The left rail follows the exam, progress, desk,
partner, and exam-list order; the center keeps the start-here banner, composer
card, five pill filters, and discussion stream; the right rail retains
headlines, challenges/cup, weekly stats, bank contribution, and exam discovery.
The composer and quick actions open a clear publishing-readiness dialog instead
of pretending to post. The discussion endpoint returns only published question
explanations/doubts after the current device has answered that exact question.
Following, community MCQs, materials, news, challenges, and public standings
remain unavailable until their account, moderation, and reliable-data
foundations exist; no prototype people, posts, or activity are shown as real.
`/` remains the public landing page; app-shell Home links to `/feed`.

## Moderation queue (`is.modq`, prototype around line 1483)

The owner moderation route uses the V3 Community · Moderator eyebrow and
Newsreader title, four live KPI tiles, pill queue tabs, a flexible stack of
white report cards, and a narrow right rail for the graduated response,
moderator limits, and separation of conduct from question review. Cards show
the live report reason, question context, author, report weight, body, optional
review note, and actions. Completed actions remain in the audit-history tab
with an Undo control where the database snapshot permits restoration.

The ShikshaCom admin question-review page informed the interaction pattern:
real queue counts, explicit filters, selected context, per-item action states,
required reviewer feedback, and errors that do not masquerade as empty queues.
Its Django API is not reused. India Study Map uses its own FastAPI and existing
`mod_actions`, `abuse_reports`, `appeals`, and `sanctions` schema. This first
console is site-owner-only through a separately provisioned bearer token;
anonymous device IDs never grant moderation access. It handles community
conduct and approval only and does not edit question keys or scores.

## Study Desk and partner preview

`docs/design/India Study Map v3.dc.html`, `is.partner` (around line 1115), is
the source of the shared-desk structure: Community mono eyebrow and large
Newsreader heading, partner/seat summary, visibility choices, right-aligned
desk actions, study/class mode pills, member chips, desk scene/status strip,
content tabs, and a wide main column with a narrow right rail. The source uses
`#86226F` Community ink, `#B23A9A` Community area, `#EEDDEC` Community soft,
`#F4EFE4` warm paper, `#FBF8F1` cards, `#E4DBC9` dividers, 10px scene radius,
Newsreader headings, Public Sans body, and IBM Plex Mono labels.

The `/desk` partner view follows that composition: desk header and actions,
visibility choices, study/class mode pills, member/invite chips, desk canvas
and status strip, seven content tabs, a broad content column, and a narrow
right rail for profile, partner invitation, sharing controls, and chat. It
replaces all sample people, activity, counts, Pro claims, and shared content
with an honest private empty state. Visibility and sharing controls are visual
previews only and reset when the view closes; the invitation, bank sharing,
duel, chat, open desks, and discovery are not wired to other people. Class
desks are shown as deferred. A real social release still requires accounts,
consent, blocking/reporting, and moderation. Following public study materials
stays separate from partner relationships and private desk access. See
[`STUDY-DESK-PLAN.md`](STUDY-DESK-PLAN.md) for the full product and safety
plan.

## Bank contribution administration — 2026-10-21

The admin workspace takes its layout from `docs/design/Admin Console.dc.html`: 236px dark #1D1B18 sidebar, #EFE9DD workspace, #F4EFE4 paper/#FBF8F1 cards, restrained dividers, Newsreader headings and monospace metadata. Tables scroll within their containers on narrow screens and the sidebar becomes a horizontal section selector. The question workshop pairs a real source PDF with proposed learner content, diff, evidence and versioned review actions. Prototype people, counts, activity and accepted decisions are replaced by live state or explicit empty states. Screenshots under reports/review-system use isolated synthetic data; production counts are not represented by those fixture screenshots.


## Account security — 2026-10-21

The v3 handoff has no dedicated authenticator screen. /account/security extends the current account/profile shell using the existing paper/card palette, Newsreader heading, mono section label, pill actions and minimum 48px inputs. Desktop and 360px browser evidence is in reports/review-system/security; document body width equals viewport width at 360px. Enrollment QR is generated locally, with a manual key alternative. Secrets and recovery codes remain transient component state and are not written to browser storage. No exact-prototype fidelity is claimed for this additional screen.


## Admin repair workspace — 2026-10-21

Read Admin Console.dc.html browserVals and browser markup: warm canvas #EFE9DD, dark sidebar #1D1B18, selected question #E3E9F8, card radius8px, control radius6px, control border#CFC5B2/background#FBF8F1, content max1400px, Newsreader36px page heading. Reused those values for the real repair queue/inspector and paper links. Instructions/options/source presentation use existing safe SourceQuestionText rendering. Paper preview is a real PDF iframe loaded on demand, not the prototype's synthetic PDF lines. Bounding-box highlighting is not implemented. Responsive inspection stacks at narrower widths; desktop/mobile evidence is under reports/review-system/repair-workspace.


## Learning board and rewards — 2026-10-21

Read v3 board/scoring/profile/rewards sections: warm canvas/card palette, Newsreader42px display, mono11px uppercase labels, rewards olive#8A8A12, gold#D8A33A and cream#FFF6DD,14px/12px cards and pill actions. Weekly/monthly/all-time tabs use real opted-in XP rather than synthetic rankings. Lifetime level uses40*n² thresholds with minimum level1. New subscription reward wallet extends the design; an exact prototype wallet match is not claimed. Desktop/mobile evidence in reports/learning-rewards;360px viewport showed no horizontal overflow. Exam journey extends existing exam hero while retaining paper/practice/progress workflows.


## Content Studio — 2026-10-21

Read v3 materials/create sections (Newsreader35/46/27px, mono10px labels, warm14px cards, pill controls, callout#F6E7C6/#E5CF9C). Editor adds real reorder/duplicate/delete, metadata sidebar, safe reader preview and review states inspired by Shikshacom Admin-dashboard CMS. Admin retains existing dark sidebar/warm workspace. Synthetic desktop/editor/review/reader and360px paid-preview proofs are in reports/content-studio. No exact match is claimed for newly added workflow/reward controls.


## Material discovery — 2026-10-22

Read v3 feed material treatment around lines276–290: purple#EEE6F7/#5E2F98, Newsreader19px inner title,13px metadata,10px inner radius, and publishing/ranking around808–814. Discovery extends this treatment with warm14px shared cards, Newsreader27px section/25px card headings,10px monospace labels and purple-tinted grouping. Uses real titles/author/helpful/studied/access rather than a synthetic cover or payment listing. Existing material reader remains the destination.


## Public creator profiles — 2026-10-22

Read v3 profile header/stats/tabs around930–975: warm14px cards, border#E4DBC9, shadow0 1px 2px rgba(29,27,24,.05), Newsreader32px counts,13px labels, pill controls and round bordered avatar. Public creator screen reuses that language with42px heading and content/material cards; extends it with explicit consent settings and inline block confirmation. No private practice activity or fabricated role badges copied from the prototype.


## Publishing workflow — 2026-10-22

Read Admin Console prototype header and workbench: dark#1D1B18 sidebar236px, canvas#EFE9DD, paper#FBF8F1, Newsreader36px top heading,6px controls/border#CFC5B2, selected work#E3E9F8. New publishing queue reuses this shell, warm12px cards, mono10px priority labels and explicit statuses. Inspector stacks below queue on smaller layouts; before/after blocks use the existing safe material renderer. Author feedback uses existing cream/gold callout. Synthetic screenshots in reports/publishing-dashboard; added comparison/feedback forms extend the prototype.


## Module comparisons — 2026-10-23

Extends the previously extracted Admin Console workbench values: dark#1D1B18 sidebar236px, canvas#EFE9DD, paper#FBF8F1, Newsreader36px heading, controls6px/#CFC5B2, selected#E3E9F8. Bounded list/detail, neutral evidence status, cream provenance notice and source side-by-side use existing safe question rendering. Stacks on smaller screens. New comparison/citation/triage controls are workflow extensions, not an exact prototype screen claim. Synthetic viewport proof in reports/module-intake.


## Research assessment — 2026-10-23

Admin comparison extends existing cream/gold evidence notice (#FFF6DD/#E5CF9C),10px radius,Newsreader23px section title and13px source/rationale text. Scoped to selected appearance; clearly labels prepared evidence/independent review and separates proposed answers, retained bank answers, defects and unassessed cases. Sources are actual links; prepared payloads remain inspectable JSON, with no automatic vote/apply control. Synthetic browser proof reports/module-adjudication-20261023/synthetic-research-assessment.png.


## Difficulty retirement — 2026-10-23

User instruction supersedes prototype difficulty treatment. Remove taxonomy difficulty selector and rename actions Subject & topic tags. Existing subject/topic/subtopic controls retain shared warm6px inputs. Synthetic proof reports/retire-difficulty/synthetic-tags-only.png.


## Answer cards — 2026-10-23

User requested inspection of clerical/GroupB/Combined and separate PracticeHub2, and considered2×2 versus list. Source Combined uses2columns/8px gap/9px radii/green#156c54/gold#cf9b37; clerical uses green/gold and24px markers; PH2 uses blue#1f6feb, pale panels, list drill. Current cards keep warm neutral#FBF8F1/#DCD3C2,9px radius,10px gap,min48px options,25px letter chips, blue#2D5BD0/#E3E9F8 selected, green#2E7D46/#DCEFE1 correct, red#C0392B/#F8DEDA wrong. Preserve labels/symbols with colour. Shared2columns at640px+,1column narrower or explicit List, no option-order changes. Visible preference controls extend prototype; screenshots reports/research-drafts-answer-layout.


## Question discussion implementation — 2026-10-23

Inspected v3 lines467–510 and its discussion state/composer definitions. Reused the bank card's paper/card/hairline palette, mono metadata, Newsreader headings and pill actions. Discussion uses a 1px ink divider with14px top spacing,8px interior card radius,14.5px body/1.6line height, and prototype explanation green #E3EEE0 for an asker-accepted reply. Composer uses #FFFDF8 inputs, #DCD3C2 border and6px radius. Accepted replies explicitly say Accepted by asker; helpful votes do not imply a verified key. New source/share/correction actions use the same44px minimum target and wrapping mobile layout. No difficulty controls or invented activity counts.


## Study Desk v3 implementation — 2026-10-23

Inspected saved v3 Study Desk (`is.partner`, lines1115–1389) and actual Claude prototype Desk screen. Ported the original960×400 scene geometry (source2619–2733) to typed React: seat x150/280/410/550/680/810, pendant light/clock/books/cards/clipboard/mistakes board and seven labelled hot spots. Actual members and empty invite seats replace sample people. Illustrations do not represent inferred appearance or online status. Public/classes are disabled per user choice.

Use1240px max width,32px24px96px padding,10px scene corners,40px workspace gap,main flex999 1 560px and sidebar1 1 280px/max360px. Newsreader/Public Sans/IBM Plex Mono match product fonts. Visibility/mode selected fill#1F7F86 with#B23A9A outline. Seven tabs: Shared Qs, Desk set, Shared notes, Bookmarks, Progress, Mistakes wall, Focus session, retaining source red/blue/gold/teal/green/peach/purple accents. Below640px only the scene gets an internal640px canvas/scroll; equivalent44px controls and stacked workspace remain usable. Reduced motion disables scene animations. Screenshot reference and synthetic/mobile proof in reports/study-desk-v3.

## Avatar editor — 2026-10-23

Ported v3 avatarEl geometry (120×120 SVG, 55px circular clip, 58px background, 23px face, original hairstyle/accessory paths) with per-instance useId clipping. Editor source1839–1917 / catalog3071–3098:1240px main,32/24/96 padding,28px gap,preview280px basis/max360px,168px portrait,70px banner,14px card; editor560px basis;132px grid cells/12px gap/10px corners,2px selected ink border. Seven original categories and launch-mode Customize/Inventory tabs. Starter choices plus real ledger level5/10/15/30unlocks; no sample coins/badges or unimplemented shop actions.44px accessible controls, actual user handle/level, explicit preview/save/reset state. Hero and option cards use #FBF8F1. Original rendering reused at header/profile/post/board/member sizes and for the desk face/clothing, with existing privacy gates.

## Question entry and discovery refinement — 2026-10-23

User-approved functional extension of v3 question/feed cards. Keep existing cream panels, mono metadata, pill actions and 44px targets. Open question is a secondary muted link instead of Details. Questions & Doubts uses the existing feed tab bar and a23px Newsreader subheading with wrapped pill filters. Reuses the existing inline discussion styling rather than introducing another page design.

## Exam calendar — 2026-10-23

Extracted v3 calendar1618–1675:1100px main,36px top/24px desktop side/96px bottom padding,Newsreader clamp34–50 heading,17px intro/720px max,20px flex gap,ink#1D1B18 countdown22px padding/10px radius/gold#D8A33A,26px title/64px days. Calendar uses7columns,Monday-first,1px ink outline/10px corners/24px month label; date event strips and selected-day details, month/list pill controls and12px official-source footnote. Mobile16px gutters allow44px day widths at360px. Existing Shikshacom grid navigation informed implementation; v3 governs product appearance. Replace prototype fake dates/72% syllabus claim with actual saved/followed event countdown and honest empty states. Exports, verification notes, owner editor and inbox preferences extend the reference controls using existing palette/44px actions. Official notices reuse the same underlying rows rather than duplicating editorial content.

## 2026-10-23 — Games and global search

Follow the v3 games hub cream/ink/gold palette, serif headings, featured Gauntlet scene, pastel mode cards and compact side panels. Render Gauntlet track in native SVG; use existing safe source-question renderer and shared two-column/list options. Actual account XP/history replace prototype samples. Global search groups results with category tabs and privacy labels. Backend room, reconnect, publication controls and unavailable marketplace checkout notes extend the reference honestly. Desktop evidence is in reports/games-search; attempted viewport override stayed at1280px, so mobile files are not mobile verification.

## 2026-10-23 — Direct subject Library and database map

Functional extension of v3's warm Library/cards and admin console: cream #FBF8F1 cards, hairline borders, Newsreader 25–54px titles, muted blue/green/gold shelf accents, rounded pill view controls and 44px targets. Subjects opens first; tools remain in the adjacent view. Shelf tabs use four plainly named actions, additional filters fold under More filters, and original source context stays on existing question cards. The database map reuses the236px dark admin sidebar, cream workbench and blue selected cards, with selectable count/relationship views. No invented difficulty chips or activity counts. These new Library/map layouts extend v3 rather than claiming to be original prototype screens.

### 2026-10-23 — Launch scope and Games recovery additions
These are functional additions requested by the user, not extracted v3 prototype elements. Header adds a compact warm focus line (11px, #F6F0E3, hairline border) for MPSC & Mizoram recruitment. Library shelf exam selector is always visible; optional advanced controls remain below. Games uses a cream/gold unfinished-mock banner with direct resume link above the featured game. Existing type, cards and source presentation retained.

### 2026-10-24 — v3 Inbox and source focus selector
Extracted Inbox1064–1114: main1240px,36px top/24px desktop side/96px bottom; Newsreader clamp36–52px/weight500/tracking-.02em; flexible340px notification and480px message bases,40px desktop gap; white cards,#E4DBC9hairlines,14px corners;14px notification text/11px Mono timestamps; cream thread list and magenta own-message/send. Real bounded notices and joined desk conversations replace prototype fixture threads. Category/read/retry/pagination and durable in-app preference controls extend v3; email/push/quiet-hour actions are not invented as working services. All exams header selector extends the requested launch focus, retaining the established cream strip. Physical mobile proof is not claimed.

## 24 October — Vocabulary automatic review and focus transition

Vocabulary Helper extends the v3 paper/card typography with a 900px reading column, purple vocabulary accent, four compact account counters, source instructions/markup, shared 2×2/list options and one primary Check/Next action. Manual Again/Hard/Good/Easy buttons are removed. Dates replace confidence input. Refresh shows “Saved feedback restored”. The recognition-only explanation avoids asserting word mastery. Smooth scope entries use160ms opacity.65→1 and2px vertical motion; prefers-reduced-motion disables animation. Header stays mounted, and private unscoped desk/inbox/editor state is preserved. Actual acceptance and limitations: VOCABULARY-AUTOMATIC.md.

##24October — English source context
Match prior UDC-LDC QuestionText/QuestionContext behavior for ruled blanks, nested **bold**, *italic*, __underline__ and default-open reading passages. Retain current v3 cream instruction panel (#F6F2E9), gold left border (#B9A579),13px context and source line breaks. Blank width follows underscore length capped2.4–12.6em; React text rendering keeps arbitrary HTML escaped. Apply the same shared source renderer to live practice, mocks and frozen result review. ENGLISH-SOURCE-FORMATTING.md records actual data scope.

##24October — Answer provenance help
Extend the existing v3 provenance pill with an information mark and 44px summary target. Native hover text gives the short meaning; native details opens a cream320px/max-container note in normal flow for touch and keyboard, avoiding viewport-clipped tooltips. Keep green official/key and muted blue non-official styling, with separate reviewed wording. Help and question-specific evidence links disclose no answer.

Provenance-help layout follow-up: expanded help spans a full metadata row with a fluid680px maximum, superseding the initial320px note. This avoids vertically centering metadata beside a tall narrow text column. Closed pill/hover styling remains the same.

### 2026-10-24 — Community tab continuity

For you, Following, MCQs, Questions & Doubts and Materials now retain the v3 Community heading, tab bar and side rails. Previously Following/MCQs/Materials returned replacement whole-page layouts despite retaining `/feed`. Embedded views now use secondary headings and narrower content grids. Standalone readers remain available; Community lesson entry carries a return to the selected tab. No new top-level navigation is added.

### Admin exam inventory

Exams & coverage is a lazy-loaded workspace within the existing admin shell, with internal views and shared filters rather than new public navigation pages. Source and key previews load only on request. Four answer status totals drill into the existing repair workspace; details preserve source context and existing reviewed edits. Source context counts are not presented as proof that every instruction is required or restored.

## 2026-10-24 — Workflow extensions

These five workflows extend the existing v3 design rather than represent additional prototype screens. Reuse cream/card/ink surfaces, hairlines, Newsreader26–42px headings, mono metadata, 9–14px corners and 44px controls. Intake and quality remain internal admin tabs with the existing236px sidebar. Continuation/daily revision enter through existing Library/Desk; question answers retain the shared source renderer and2×2/list choices. Resumed practice displays within its original module, with one clear return action. Correction updates use the existing Inbox and warm source-notice treatment. Synthetic screenshots are explicitly rehearsal evidence.


## 2026-10-24 — Admin paper audit readability

Paper detail starts with What needs attention?, question count, missing numbers/images/answers, unconfirmed answers and a plain next action. Filter links open the repair workbench. Technical details, sources and change history are collapsed by default. Direct answer controls use readable status labels with evidence/reason fields, queued publication feedback and private immutable history. Verified does not mean official. Synthetic browser proof: reports/direct-admin-answers/admin-decision-synthetic.png and paper-summary-synthetic.png.


## 2026-10-24 — Restored first-paper student views

Paper view preserves source-specific text/context and uses the shared Official/Verified/Needs review help. Faulty source notes are visible before answer selection; those items cannot be checked/scored. A paper-specific Practice estimate link shows the real reviewed subset count and explicitly states that its score is unofficial. Mock question and result views now render the exact frozen original figure, including resume/history, instead of relying on a PDF link alone.


## 2026-10-25 — User-requested answer provenance contrast

Official key uses green plus the authority square; Verified solution · unofficial uses blue plus a tick; Needs review uses amber plus a question mark. The explicit unofficial wording is required even when reviewed working is eligible for a practice estimate. Labels and symbols accompany colour, with measured text contrast 8.35:1 / 7.32:1 / 6.74:1. Shared badges retain disclosure/evidence links; exam readiness includes the same legend. Correct/wrong option colours and grading eligibility are unchanged.


## 2026-10-25 — Admin review usability update

Retained Admin Console.dc.html values: 236px dark sidebar (#1D1B18), #EFE9DD workspace, 6px inputs, 8–9px panels, Public Sans body and existing display type. User-requested simplification adds review action cards with the established green official / blue unofficial / amber review semantics. Main review actions use native radio controls; extra year/topic/exact-paper filters collapse under More filters. Question focus respects reduced motion.

### 26 October 2026 — Shared question pagination

Pagination extends v3's Previous/Next study workflow using existing cream/card/ink/hairline/pill tokens. Desktop gets bounded direct page jumps; mobile gets a compact Previous/position/Next row, with 44px touch targets. Browse renders 25 questions, practice one, with existing answer-layout choices, original PDF context and provenance preserved. Module loading keeps the navigator position and uses a reserved question loading area; timed mocks keep their existing question order and timers. This is an intentional functional extension, not a claim that v3 specified these additional numbered controls. Live browser checks covered desktop direct page jumps, refresh/filter URLs and mobile practice controls; no signed-in practice answer was fabricated.

## 28 October 2026 — Exam subject/topic study extension

This owner-requested route extends the v3 exam landing page rather than claiming an additional prototype screen. It reuses the exam hero, warm card and hairline surfaces, Newsreader subject headings, mono counts and 44px controls. The topic map is paper-scoped and approved-tagged; the existing exam question cards and answer provenance remain the study surface. A live desktop-size LDC browser check covered the topic list and filtered questions. A mobile viewport override was unavailable during this check.

## 28 October — Group B common-subject entry

Owner-authorized functional extension of the existing exam cards and topic
view. Reuse shell width, warm exam tint, Newsreader headings, cream cards,
hairline borders and minimum44px pill controls. `/exams` and both Group B
archives link to English & GK/GS first and a separate Technical papers area.
Source-group and study-mode selectors wrap on small screens. Technical papers
use searchable two-column cards, eight per page. Original source names and
answer status remain on the shared question browser. Browser verification at
390px measured 375px document/body width, without horizontal overflow. Desktop
and mobile screenshots live in reports/group-b-common-20261028.

### 28 October 2026 — Question source wording

Keep existing card typography and spacing. Topic badge uses approved learning topic; source row includes the full verified paper title, wrapping naturally. Detail appearances show this title in preference to the bare paper number.

### 28 October 2026 — Identity and learning tag admin screens

Reuse admin console typography, existing rounded-panel/card/hairline/paper tokens and min-h-11 controls. Learning tags has candidate selection and proposed path columns at xl, stacked on smaller screens, then per-question current/proposed preview cards. Every preview requires an individual checkbox. Batch status cards link immutable contribution history. Paper inventory embeds a two-column identity form/source preview at xl with optional600px PDF frame. Individual contributions show current/proposed tags and a shared GK/GS picker; exact stored IDs are under a disclosure. No new prototype or new visual theme.

### 28 October 2026 — Clerical exam routes and unlimited billing label

Reuse the existing exam card, hairline border, pill links and min-h-11 controls. Below the clerical hero add UDC/LDC/Assistant links with aria-current and own-exam English/GK shortcuts. Topic-map headings and broad question badges use General Knowledge in these exam contexts. Billing uses its existing paragraph style for “Unlimited Pro access · no expiry date”.

### 29 October 2026 — Exam-section polish

Retain the existing green exam hero, gold edge, Newsreader headings, cream/card surfaces, hairlines and 44px controls. Focused study uses a28px exam title and fewer hero actions. Overview keeps Start practice / Subjects & topics / Past papers; answer guidance is a closed disclosure. Subject/topic/search form the main filter row, with secondary controls in a disclosure. Keep old results dimmed while replacement data arrives, with answers disabled. Match hero negative margins to actual shell padding:12px below768px and18px from768–1024px. Tab links scroll inside their own container. Result focus uses measured sticky-header clearance instead of a fixed mobile offset. Evidence: reports/exam-polish-20261028.

Final phone refinement: fold the subject/topic/search controls behind a44px toggle by default while retaining the current subject/topic beside the practice heading. This brings the first question into the initial study viewport.

### 29 October 2026 — Owner-requested less crowded paper lists and page gutters

Override the prototype's1240px outer shell with1440px for shared app navigation/workspaces; use16px desktop and12px phone outer gutters, retaining18px exam tablet padding and narrow prose/form limits. Exam1100px and Combined1160px wrappers use this shared width. Hero negative margins match actual gutters. Paper lists use a full-width row with Newsreader21px heading, cream card/hairline border,12px radius,16/20px inner padding and 44px action/disclosure targets. Show only nonzero answer counts; keep unofficial wording visible. Native Paper details & tests holds full printed identity, explanation gaps and unchanged test settings/actions. This is an explicit user-directed functional/layout extension; not a newly discovered prototype value.

### 29 October 2026 — Explicit layout correction

Restore paper box cards with a responsive300px minimum width and stacked actions. Remove the shared1440px outer width cap, including Combined and Study Desk; retain16px desktop/12px phone edge gutters and existing tablet exam padding. The owner specifically rejected rows and remaining wide-screen outer margins. Earlier row/1440px notes are historical.

### 29 October 2026 — Fluid layout refinement

Paper boxes use340px minimum and16px gaps (12px phone). Shell remains uncapped with existing16/12px gutters. Exam question results use a left-aligned960px maximum; shared question headings75ch. This is the owner-authorized optimization of the corrected box layout.

### 29 October 2026 — Owner-requested card polish

Shared paper boxes now stretch to equal height per row with flex body/action alignment. Year badge and source link share the top line; official/unofficial statuses remain explicit with symbols and colour. Existing12px radius and16/20px padding retained. Details has a24px circular plus inside a44px summary target. Focus outline2px blue; shadows subtle; reduced motion disables transitions.

### 29 October 2026 — Interactive Atlas extension

Owner-authorized restoration uses existing cream/card/hairline tokens and Newsreader headings. Fluid16/12px shell gutters; desktop map plus300px layer rail, stacked phone layout. Map420px phone and clamp420px/64vh/720px desktop; Leaflet zoom44px. Native selects and 44px checkbox/button targets; notes/features collapsed. Interactive Atlas belongs in Library tools and contextual subject navigation. This is a functional extension to the prototype, not a newly extracted prototype screen.

### 30 October 2026 — Simplified admin workflow

Retained prototype admin palette/sidebar: body#EFE9DD, sidebar#1D1B18/text#E9E1D2,236pxdesktop width,13.5pxnavigation,6pxnavigation radius; selected#3A3631 and#D8A33A marker. Adaptation requested by owner: five primary tasks and collapsed grouped specialist tools; phone section picker replaces21horizontal tabs. Main12pxphone/16pxdesktop gutters follow the owner's site spacing decision. Boxed task cards12pxradius; two columns on phones, four at xl. Queue summaries remain a three-column compact row on phones, avoiding the old three-card vertical stack before filters. System details and advanced filters use native disclosures.

### Paper workspace — 31 October 2026

Preserve boxed question cards with 12px phone / 16px desktop outer gutters. Bound reading width outside the two-column PDF comparison. Use the booklet filename as the compact heading, disclose full paper title/instructions/coverage, and keep mobile search full-width with type/status controls side by side. PDF stacks above the question on narrow screens and scrolls within its own container.

### 31 October 2026 — MCS Prelims paths

Retain existing Combined colours, boxed cards and outer gutter system. Present two clear source-paper paths above shared views, stack on phones and use two columns on wider screens. Keep selected-role links through topics, papers and practice. Disclose recovered-copy status directly on paper cards, with source details inside the existing disclosure. No Mains availability or complete-paper simulation claim in this release.

### 1 November 2026 — Reading continuity and revision actions

Owner accepted explicit Check answer / Show answer and requested the follow-up actions. Reuse existing cream paper, white card, hairline borders, 10px inner panel radius, 14px body and 12px notes. Continue studying is a wrapping row of existing pill controls with 44px minimum targets: Save for revision, Retry later, Next question. Reading mode shows remaining minutes and offers Retry now when its server window expires. Keep countdown changes outside live announcements to avoid repeated screen-reader interruptions. Preserve the existing source-paper identity and result layout.

### 1 November 2026 — Focused UDC overview

Owner-requested extension of the existing exam landing page. Retain the green/gold hero, Newsreader 25–44px headings, cream/card surfaces, hairline borders, 12–14px corners and 44px controls from v3 module1699–1791 and subsequent owner-approved fluid gutter/box-card changes. Place the five UDC views immediately below the hero, one journey action block next, then six own-exam subject shortcuts, disclosed answer/test guidance and three recent paper groups. Full paper search/pagination remains in Past papers. Broader Group B practice is a secondary bottom link. Remove the UDC cross-exam switcher, duplicate hero actions, single-section 100% bar and empty material panel. Existing Prelims booklet selector is reused without changing source records. Verified at360px and390px: document/body345px/375px with15px browser scrollbar; no horizontal page overflow. This release does not add bounded study sessions.

### 2 November 2026 — UDC short-set practice and saved finish screen

Functional extension of the approved UDC study flow. Reuse the existing green/gold exam identity, cream/card surfaces, Newsreader 24–30px headings, 13/14px text, 12–14px corners and 44px controls. Setup uses a subject select, 10/20 pill choices and a disclosure for source/topic/status filters. Active study has Question N of actual total, one compact Previous/Skip-or-Next row and an explicit finish action. The existing source/answer card is shared with unlimited browsing; session mode suppresses its duplicate Next button. Finish uses four wrapping Correct/Wrong/Viewed/Skipped counters, an original-feedback caveat, mistake practice and saved checked-question review. No timed score or fabricated mastery claim. Focus after the saved question list loads respects the real sticky header rather than clamping against the temporary loading page. Synthetic 390px verification measured 375px document width, 198.5px header bottom and 214.5px study-start position; expanded 360px filters measured 345px document width, with no horizontal overflow.


### 2 November 2026 — Disclosed booklet/source controls

Owner-requested refinement of existing UDC and MCS Prelims screens. Reuse current card surfaces, hairline borders, 12px corners, 12px secondary copy and 44px minimum summary/selector targets. The existing A–D pills sit inside a native closed details element labelled Booklet series & original sources. Grouped-card titles omit series; the full selected-source title and PDF remain inside Paper details. Shared study questions use a closed Source details element while retaining visible figures, passages, source-issue warnings and answer-provenance labels. No new layout or visual language. Production build passes; browser/mobile verification of this refinement remains pending because local server sockets are blocked in this session.


### 2 November 2026 — Admin readback and corrected saved-feedback notices

Refine existing controls rather than adding a new dashboard. Admin progress keeps the existing card, 13px body, 12px status/time detail and 44px minimum recheck/link targets. Distinguish applied-and-matched, unexplained mismatch, later publication and unavailable comparison in plain copy. Reuse the same progress card inside published contribution history. Student correction notices use existing canvas/hairline panels and secondary text with a current-question link; keep original finish counters unchanged. UDC syllabus/coverage guidance is a native disclosure with existing spacing and targets. Build passes; browser/mobile verification remains pending because this session cannot open local server sockets or reach the deployment host.

### 2 November — Verified current UDC syllabus guidance

Extend the existing native syllabus/coverage disclosure with the inspected 2026 blueprint and penalty rules. Retain 13px body text, existing canvas/card/hairline spacing and 44px source links. Mark the combined 2026 exam explicitly; historical paper cards and practice rules remain independent. Replace the redirect link with its verified direct official PDF. Production build and live browser display verified; source and screenshot in reports/udc-content-20261102.

### 2 November — Learner-first feed redesign

Owner-requested replacement of the three-column community landing. Retain prototype feed tokens: #14130F dark next-step panel, #D8A33A accent, #F4EFE4 paper, #E4DBC9 hairlines, 14px cards, Newsreader headings and Public Sans body. New hierarchy: 36/44px study-feed title, 28/32px next-step heading, two revision/help cards, then existing community tabs. Desktop uses minmax(0,1fr) plus a 280px resource rail; mobile places learning actions and feed before the rail. Actual all-time activity replaces the misleading Your week heading and unsupported progress bars. Native disclosures contain secondary contribution actions and publication updates. Browser checks at 1280px and 390px show no horizontal overflow (document widths 1265/375px respectively).

### 2 November — Group B Non-Gazetted study choices

Extend the existing Group B exam-soft hero and 14px source/topic card language. New three-choice section uses Newsreader28px heading/24px card titles,13–14px secondary copy,44px links, three columns on medium screens and one on mobile. Use a native disclosure for module relationships and syllabus references; technical entry is separate. Retain original archive/source titles while displaying General Knowledge in the NG topic map and subject selector. Build passed; this slice has not been deployed or visually verified because current SSH access is sandbox-blocked.

### 2 November — Group B navigation finalization

Separate Study home from Choose a topic / Read questions / Practise answers. Active study uses compact28px title/p4 hero; home retains32–48px/p6–8. Recruitment source selector and original-paper archives are native disclosures. Home scroll resets to the beginning. Reuse44px controls and existing exam/card colors. Local browser with real API data confirms390px viewport/375px document without overflow. Production deployment remains blocked by SSH restrictions.


### 2 November — Group B dated syllabus guidance

Reuse the existing collapsed module-relationship disclosure,13px body, bold inline labels and source-link styles. Add inspected May2025 general/technical schemes with July interview amendment; no additional home cards or scoring controls. Live360px expanded overview has345px document width and no horizontal overflow. Evidence:reports/group-b-release-20261102/syllabus-mobile.jpg.


### 2 November — Visible exam names on paper resources

Retain21px Newsreader paper headings and existing cream card/12px radius. Prefer printed paper labels when available, then display the existing exam identity in a wrapping 13px secondary paragraph below; viewer uses 14px and max-w-5xl. Source filename remains in disclosed details. This resolves generic filename ambiguity without new cards or navigation.390px card list has 375px document width.


### 2 November — Exam and year list

Owner-requested archive extension uses existing cream/card surfaces, hairlines,12pxradius and44pxcontrols. Desktop columns:72pxyear, flexible examination and paper,180pxactions. Mobile stacks each source row; exam names wrap at14px and source headings13px. Search/year/order/display controls wrap. Group B Past papers defaults to list; card mode remains available. Live390pxviewport/375pxdocument has no horizontal overflow. Evidence:reports/bank-human-handoff-20261102/archive-desktop.jpg and archive-mobile.jpg.


### 2 November — Assigned paper review workspace

Functional extension of existing source comparison/contribution UI: reuse cream/card/hairline surfaces,12pxpanels,13–14pxbody,24/32pxNewsreader headings and44pxcontrols. Assignment choices and paper select precede a360pxquestion rail plus flexible source inspector on desktop, stacked on phones. Checklist outcomes explicitly distinguish human inspection from answer provenance/publication. Owner assignment controls stay in a native disclosure. Synthetic1280/390rehearsal measured1265/375document widths without overflow; live signed-out entry verified separately. Screenshots:reports/udc-prelims-human-review-20261102/synthetic-desktop.jpg and synthetic-mobile.jpg.

### 2 November — Current affairs connections

Reuse the established paper/card/hairline/ink/link tokens, 44px controls and 6–14px corner radii. The learner's Then and now panel sits after permitted answer/explanation reveal, with source context, dated fact cards and related-paper rows. Unknown dates and Recheck due are text, not colour-only badges. The manual editor uses labelled form fields, a permission-scoped source search, source preview, separate proposal/history cards and a rationale form before a publication decision. Mobile form columns stack. Synthetic rehearsal measured document widths1265/375against viewports1280/390with no horizontal overflow. Screenshots and replay fixture are in reports/current-affairs-connections-20261102 and api/tests/run_current_affairs_preview.py; synthetic fact values are not production assertions.

### 3 November — question discovery and dated Hot topic administration

Owner-requested extension, using existing paper/card/hairline tokens, Newsreader
headings, 12px cards and 44px controls. Home retains resume/study actions first,
then exam-specific Popular/Recommended/Hot sections before community. Three cards
per Home section and six inside UDC/Prelims; source exam/year/question and exact
paper link remain visible. Sparse activity, absent inspected recommendations and
unpublished topics have honest empty states. Hot picks show why-now text, primary
source/date and expiry. Owner administration uses existing session/CSRF/MFA and
audited draft/publish/retire actions. Production browser measurements: 1265px document
at 1280px viewport; 375px document at 390px viewport. Screenshots are retained in
reports/ai-discovery-20261103. No new exact-prototype claim or fabricated activity.

### 3 November — Learning collections and Website bank

Extend the existing paper/card/hairline palette, Newsreader headings, pill actions
and44px controls. Important Days uses wrapping search/month/bank filters and
responsive cards; the author/reviewer editor stacks its list and form on phones.
Question selection searches both banks and reuses the established QuestionCard
for answer reveal and provenance. Live390px inspection measured375px document
width without overflow. No prototype or synthetic entries were published.

### 3 November — Navigation and page hierarchy refresh

User-authorized restructuring uses five shared destinations: Home, Exams, Library,
Create and More. Desktop uses one header row; phones use the matching five-item
bottom navigation. Warm paper, white cards, Newsreader, source labels and existing
area colours remain. Search is always available outside focused test/game sessions;
secondary tools and role-aware staff links live in More. Visible focus outlines
and skip links support keyboard navigation.

Home (/feed) now contains the next study action, revision/subject shortcuts,
compact discovery and a weekly overview. The full community feed is /community;
legacy community query links redirect with filters preserved. Library groups
Subjects, Practice, Reading, Saved and Tools, with explicit MPSC/Website bank
choices. Create groups current question, material, practice-set and Important Day
workflows, with submission status links. The landing page has shorter navigation,
six featured exams and accurate links to available community features.

Live desktop Home/Create screenshots and Library/More/legacy-route checks passed.
The local preview was denied by browser approval; public production verification
was read-only. The browser viewport override did not change the 1280px viewport,
so mobile visual QA is not claimed for this release. Responsive styles compile;
temporary viewport settings were reset. Screenshot: screenshots/study-home-2026-11-03.jpg.


## 4 November 2026 — simplified editorial workspace

Reused workspace tokens/cards for My work / Needs attention / Completed. Inline
corrections preserve context; searchable paged pickers replace long lists. One
batch preview precedes Apply. Submitted/queued/applied/failed labels reflect actual
status. Sticky question actions sit above mobile navigation with safe-area spacing.
Tag cleanup preserves the current paper through its independent paper filter.

Live signed-out entry inspected at 390x844 and 768x1024 with document width equal
to viewport width and no horizontal overflow. Viewport reset afterwards.
Authenticated layouts were component-tested but not visually exercised in a
signed-in browser; no physical-device visual QA is claimed.


### 4 November — visible review/admin entry points

Keep five learner destinations. A wrapping44px workspace strip below the header
appears for staff/assigned reviewers; it scrolls away to preserve existing sticky
editor offsets. More places role-aware workspace cards before learning/community
links. Admin sidebar uses existing dark panels and44px links; admin home leads with
module review, followed by Across the bank. Editorial adds an admin return action
and a module-scoped tag shortcut, retaining current source position.

Role variants, account transitions and link destinations passed component checks.
Live signed-out More has no overflow at390px/document375px and768px/document768px.
Tablet screenshot visually inspected; viewport reset. Signed-in visual QA remains
pending, so no claim of a complete authenticated device audit is made.


### 4 November — separate Group B learner homes

Use existing warm paper/card surfaces, Newsreader headings, hairlines and 44px
controls. Non-Gazetted retains the exam colour; Gazetted uses a sage header with
its own explicit title. Shared study is secondary. Four/five equal mobile tabs
fit one row; the unrelated global study-focus selector is omitted on this hub.
Non-Gazetted leads with common subjects; Gazetted leads with actual source papers
and collapses sparse common-subject availability. Availability determines practice
controls. A paper library replaces long paper dropdowns with search, year, content,
sort and ten rows per page. No false scores or syllabus-completion claims.

First deployed design visually inspected. Final live DOM checks: phone390/document375,
tablet768/document753, no overflow on checked home/archive routes; primary phone
subject action bottom710 within844px height. Final screenshots failed in the
browser capture service, so final visual/physical-device QA remains qualified.
Viewport reset. Details: [Group B design record](GROUP-B-STUDY-DESIGN.md).


### 4 November — reusable module review

Reuses paper overview, inline editor and source context. A searchable paged module
chooser and compact source-coverage counts replace nested dropdowns. Source rules
remain secondary/read-only. All / Remaining / Needs attention queues support
full-paper search and25-row pages. Original source and prior reviewer attribution
remain visible. A source leaving the queue gets explicit Show all / Continue actions.

The question list collapses on phones/tablets and becomes a side panel at xl.
Controls retain44px minimum height and existing safe-area-aware editor actions.
Live signed-out entry measured390/390 and768/768 document/viewport widths without
overflow; viewport reset. Component tests cover source binding, drafts, retry and
capability. Authenticated visual/physical-device QA remains pending. Browser
screenshot capture timed out; no screenshot claim is made.


### 4 November — module setup panel

A secondary owner-only panel sits under the review module chooser. Uses existing
warm paper/card surfaces, Newsreader headings, hairlines and44px controls. Search
and20-paper pages replace long dropdowns. Existing sources, imported libraries,
exclusions and publication history use collapsed disclosures. Preview gives two
compact Current/Proposed columns and scrollable paper changes; publication requires
a reason and an unchanged saved preview. New-module fields are hidden until needed.
Component checks cover owner/account visibility, saved preview, reason/MFA gating
and retained retry identity. Real-session phone/iPad inspection is in progress;
no authenticated visual certification is claimed by this implementation record.

### 4 November — source references and written context

Extend the existing shared correction card with Source reference and Text / context
choices. Physical PDF page / printed number controls stack on phones and use two
columns at sm; instructions/passages retain full-width16px textareas,44px targets,
existing paper/card surfaces and hairlines. No new visual theme. Zero-extraction
paper cards disclose actual PDF availability. Authenticated visual QA remains
unverified; component checks and production build cover this functional extension.

## Editorial list and quick revision — 4 November 2026

Opening a source paper now defaults to a full-width question list, with25 entries
per page and existing search/status filters. Explicit question deep links retain
the detailed view. Reviewers can switch between Question list and Detailed review.
Rows use the prototype's warm paper,14px container,6px option corners,44px controls
and word labels. Each row retains its exact appearance and canonical identity.

Options / self-check loads that source on demand. Tapping an option compares it
with the recorded answer immediately, without a second Check answer action.
Show answer and Show answers on this page are read-only; Hide answer / try again
resets the local pick. Page-wide reads run through at most three request lanes.
Missing answers and written prompts have explicit empty states. Key references,
provenance, source PDF, tags and expandable explanation remain available.

Neither a reveal nor a local pick records a learner attempt or an editorial check.
Review / edit source opens the existing detailed workflow, where permissions,
source-version checks, issue resolution and explicit inspection recording remain.
The existing learner Check answer control still confirms a scored attempt.

### One-tap practice and larger editorial pages — 4 November follow-up

The owner requested removing the extra Check answer step. Bank cards, question
detail, module practice, original-paper practice, saved UDC sets and vocabulary
now submit the tapped option immediately. Existing attempt/reveal rules and
source-option mapping remain authoritative. Pending requests block repeated taps;
request errors allow retry. Show answer continues to mean reading without an
attempt. Editorial local self-check remains read-only and never records approval.
Editorial lists now offer25,50 or100 rows; both shared and assignment endpoints
accept a bounded limit, and continuation/previous/next use the selected size.

## Public language polish — 4 November 2026

Learner copy uses answer source, official key, worked solution and answer awaiting
review. Implementation terms such as canonical, provenance, inferred/derived,
publication checks and server configuration belong in staff tools, not public
help. Answer badges retain official/unofficial, disputed, unverified and provisional
key distinctions; simpler wording must never imply stronger verification.
Answer help is a short description, scoring consequence and correction link.
Explanation review remains separate from answer-key status. Account unavailable
states describe what the learner can do, without payment/configuration internals.
Scoring counts now have an explicit loading state and retryable error state.
Source question text, source documents, stored answers and scoring rules are not
rewritten as part of presentation cleanup.

## Compact answer panel — 4 November

Following the owner’s phone screenshot, retain the answer, source badge and real explanation upfront. Missing explanations use one muted line. Save and next are the main actions; a native, initially closed More options disclosure contains contributions, dated connections, reward details and answer comparison. Reset that disclosure for each source question. Preserve 44px controls and visible date-sensitive/source warnings.

### 4 November — list navigation follow-up

Removed per-question Next and Save and continue from bank/library cards, module lists and original-paper list mode. Single-question detail and paper focus retain navigation. List pagination remains available. Answer-panel checks cover both navigation variants; one-tap regression passed.

## Public answer comparison and private reports — 5 November 2026

Owner-requested reduction of learner-card copy. Keep the existing paper surfaces,
option layout and44px controls. Reveal shows a compact Official key / Our answer
comparison, merging agreement into one line. Map letters to visible options by text;
missing keys/solutions stay explicit. Detailed evidence and long explanations are
closed initially. Short explanations remain readable without repeated disclaimer
paragraphs. Staff review/edit replaces public correction prompts; the public gets
one subdued Report an issue action beside Discussion and Share. Reports enter the
existing private review queue. Source/review details stay available through
expandable help; this presentation change does not certify or rewrite content.

### 5 November — Further density reduction

Owner requested a smaller card. This supersedes the prior short-explanation
upfront rule: all explanation/evidence is now inside one closed Explanation &
sources disclosure, while answer and official-key comparison stay visible.
Use a wrapping comparison line, shared save/tools row and source disclosure in
the module card footer. Preserve44px targets, readable text and material source
warnings. Live first UDC revealed card is40.6% shorter at390px viewport, with
unchanged content available on expansion. See public-cards/compact-mobile.jpg.

### 5 November — Practice discovery and stable mixed browsing

Use two compact visible selectors for My questions and Question order above the
subject filters. Never attempted counts recorded attempts only; Previously wrong
includes corrected mistakes, with a brief hint; Last answer wrong keeps the
latest-attempt meaning. Mixed order is default for module browse/practice, with
explicit Shuffle again and an alternative Most repeated first. Preserve a seed
through pagination, reload and saved set/checkpoint resume; answering/revealing
must not reshuffle the current page. Original-paper views remain unchanged.

## PDF Library — 5 November

Staff bank console gains Library / Needs attention / Activity views in its
existing paper/card palette. Search and paginated rows replace a grid of large
source cards; each row has one primary continuation. Source filenames distinguish
otherwise identical exam titles. File copies, hashes and history stay under
details; answer coverage and module membership are explicit in the selected-paper
view. Inputs/actions retain44px minimum height. URL state preserves filters/page
through detail and workbench return. Global archive gap totals remain separate
from filtered result totals. Permission/navigation components and build passed;
live signed-out entry verified. Full signed-in phone/tablet visual QA is pending.

## Everyday navigation and compact study entry — 5 November

Keep the prototype's warm paper, Newsreader headings, 14px panels, 6–8px controls
and 44px touch targets. The exam catalog now leads with search and compact exam
cards; direct Questions / Subjects / Original papers links replace duplicate
entry actions. The oversized featured route and three statistic panels are removed.
Group B cross-exam links remain in a compact footer panel. Existing bookmark,
progress, search-alias, URL and pagination behavior remains.

Home prioritizes a real active test or saved continuation. When neither exists,
Quick start is the primary entry, with a live exam catalog and Mixed practice /
Never attempted / Previously wrong / Original papers choices. Question choices
open the existing mixed browse queue; they do not start or submit a timed test.
Previously wrong retains the ever-wrong meaning. Topic discovery is a closed,
on-demand disclosure. Personal study history is not copied to browser storage.

Find opens a native modal with an explicit close button, focus containment,
Escape, arrow-key navigation and Ctrl/Cmd+K. Student destinations are shared;
staff destinations use current existing permissions, and assignment-only users
see only their review workspace. Search all hands typed text to existing search.
Focused tests/games do not mount this launcher. The admin sidebar has the same
launcher. Searchable navigation is not an authorization mechanism.

PDF Library keeps search/module visible, secondary filters collapsed, active
filter summaries, module shortcuts and Clear filters. Previous/next source stays
within the current results page and retains the page/filter return. Source actions
are cleared when a new detail loads or fails. Page offsets are bounded and adjust
after a result set shrinks. No import, approval or publication policy changes.


## Exam browsing refresh — 5 November 2026

The owner explicitly requested a modern, more appealing module layout and expanded
colour palette. For the exam catalog and module navigation/headers, this refinement
supersedes the earlier green/gold legacy wrappers and prototype surface tokens.
`web/src/styles/exam-experience.css` is scoped to these surfaces: cool slate/off-white
canvas, white cards, restrained teal (UDC), blue (LDC), violet (Assistant/Gazetted),
indigo (Prelims) and amber (ITI) accents. Existing Newsreader typography is retained.
Answer correctness, provenance and question-option styles keep their existing rules.

Catalog Cards/List and one expanded exam are URL-backed. Expanded options preserve
questions, subjects, papers and practice routes. Module views use one consistent
navigation below the header; redundant hero shortcuts are limited to Overview.
Subject headings are full-width disclosure buttons with independent expansion,
Expand/Collapse all, valid controlled panels and search results that can still be
collapsed. Controls retain keyboard focus and phone touch targets. Header copy is
shorter on phones; subject search/topic surfaces use the same cool palette.

## Bank working overview — 7 November 2026

The global-staff admin landing page uses warm paper, white 14px cards, Newsreader
headings, mono eyebrows and 44px controls. Lead with live coverage and actionable
field gaps, then the exam table and historical work. Keep the table inside its own
keyboard-focusable horizontal scroll region on phones; the document must not
scroll horizontally. Show snapshot time and honest overlap/configuration/history
labels. Search, attention filter and CSV export operate on the visible exam rows.
Subject-scoped reviewers keep the existing permitted work queue.

The question inspector now leads with wrapping44px task pills and scoped counts.
Each list row retains its learning tag and answer/workflow label, shows a specific
review reason, and truncates its long paper title to one line with a full title
attribute. Workflow lanes group work; they never imply an answer is verified.

## Compact practice cards — 7 November 2026

Owner requested minimal expanding question cards, comparing the map.hawayu.in
MCQ practice hub. This overrides earlier spacing/disclosure stacking for public
bank and module question cards. Use compact padding, 44px controls, a small answer
divider, visible provenance/key comparison and a one-line historical exam-date
note. Save, More and Explanation & details share a wrapping footer. More contains
source, discussion, sharing, private reporting and permitted staff editing;
Explanation & details contains the complete explanation, source evidence, dated
revision context and secondary study tools. Preserve reveal gates, assessment
restrictions and visible material source/scoring warnings. Do not hide uncertainty
or turn historical answers into current claims. Local before/after evidence and
limitations: `reports/compact-cards-20261107/README.md`; deployment remains pending.

### 12 November — Clearer Home quick start

Functional refinement of the compact study entry above: retain warm paper,
Newsreader headings, 14px cards and 44px controls. Quick start now has a small
cream-tinted heading, four exam shortcuts, two labelled selects, a contextual
instruction and one explicit action. Phone layouts use a two-by-two shortcut grid,
stacked selects and a full-width action. MES uses its own branch/syllabus/paper
choices; it is not advertised as a cross-paper mixed queue. No invented activity
or progress is introduced. Resume cards and real weekly activity remain ahead of
optional discovery, with retry states that distinguish failures from empty data.

##17November2026 — V.5 weekly boards and Monday recap (local only)

Followed the actual `docs/design/finna-20261114/Finna Web.dc.html` board row and
Today-card markup: existing18px card surfaces, typography, hairlines and44px
controls. Replaced the monthly/paged board and subject/stream board widgets with
weekly top10and nearby ranks. On desktop these share two columns; on phones the
nearby ranks lead. Public rows show handle/score/rank only. The private placement
is labelled explicitly, with no avatar, streak, academic result or wallet badge.
Error/loading/empty standings are distinct. Game tabs remount the read widget
on selection to prevent old-mode results remaining visible.

Monday recap sits inside the existing Today card and keeps first milestones in
a closed disclosure. Its focus line says sessions ended last week; no estimated
focus time or historical tier changes are presented as observations. Local normal
sign-in against a disposable fixture verified the populated/private XP board,
empty and populated game modes, and source-derived recap. Desktop and320px layouts
were inspected; phone document305px within viewport320px, no inspected horizontal
overflow. Screenshots: `reports/finnaplan-v5-boards-20261117/`. Viewport reset and
owned tab/server/fixture cleaned up. This is local QA, not a production/native/
physical-device visual certification; calendar/profile/cosmetics remain pending.

##17November2026 — V.5 helper calendar (local only)

Kept the current Finna card/type/control system and the existing calendar's month/
list grid, official notices and follows. The actual20261114web prototype has no
complete private-calendar editor, so this extends the existing surface using its
card/hairline/type rules. The helper heading leads; one layer card controls official,
review, habit, private notes, progress slots and exam targets. Account-only plain-text
editor fields stack on phones; date/title/note/select controls remain44px minimum.
Private occurrence details and target countdowns appear below the same grid.
The subscription disclosure explains bearer-link access, revocation, retained copies
and calendar-app refresh; the secret is shown once in memory, not a browser link.

Normal disposable-fixture sign-in verified create/edit, fortnightly slot selection/
save, month/list, a seven-day target countdown and feed create/revoke. Screenshots
and limitations: reports/finnaplan-v5-calendar-20261117/. Inspected320px (document305)
and1265px (document1250), no horizontal overflow. Viewport captures used when full-
page capture under the viewport override failed. Restored viewport, closed owned
browser tab, stopped local servers and removed fixture DB. This is local UI QA;
week navigation and existing Cup/Desk schedule composition remain follow-ups.

##17November2026 — V.5 identity and points cosmetics (local only)

Extended the actual20261114Profile/Rewards identity-card controls and existing
v3 avatar editor, keeping the current Finna card/type/hairline system. Profile's
registered Edit profile now opens one versioned display-name/handle/bio editor.
Cooldown date and pending/hidden bio state are explicit; fields stack at320px and
avoid the old fixed260px identity minimum. Profile clears private state on account
changes. Creator settings retain separate public consent and moderation status.

Added Shop beside Customize/Inventory, with three curated previews (Plum25,
Twilight50, Orbit125), one explicit review/confirm flow, live wallet balance,
permanent Owned state and a Rewards meter link. New Orbit geometry is repo-native
SVG; no raster asset, paid-status decoration or earned-frame lookalike. Existing
starters/level items are intact. Buying doesn't auto-equip; saved looks use the
same editor. Owner Creator reports now include versioned bio review controls;
Rewards diagnostics adds3read-only cosmetic counters.

Disposable normal sign-in verified saved name/handle/pending bio, disabled cooldown
handle field, purchase200→175points, Owned, then wear/save in Customize. Inspected
desktop shop at1265px and phone editor/shop at320px (document305px). Retained final
screenshots are phone captures, explicitly named as such; full-page capture has
fixed-navigation artifacts, with viewport captures for normal reading context.
reports/finnaplan-v5-profile-20261117/. Viewport reset, owned tab closed, servers
stopped and fixture DB removed. No native/physical-device or admin-console browser
certification claimed. Catalog/renderer compatibility and full self-service
consolidation remain release/follow-up work.


##17November2026 — V.5 calendar integration and client transport (local only)

Used the existing calendar grid and actual20261114web prototype card/type/token
rules. Month/week/list share one grid and selected-day detail region. The week
heading wraps at320px; seven small date columns retain complete accessible labels
and full details below. Community & play is an account-only layer using actual
Sunday Cup times. Desk's compact date list reads the same source and links into
the selected day, keeping calendar editing in one surface. Today keeps full due
reviews first, followed by a private countdown/taper card and optional normal mock.
The current prototype has no complete owned calendar; no prototype fake dates,
activity, marks or progress were introduced.

Normal disposable-fixture sign-in verified desktop/320px calendar, previous/next
week, the2026→2027 boundary/month switch, target deep links from Desk, final-week
Today and the versioned web shop catalog. Phone document305px within320px viewport.
Screenshots: reports/finnaplan-v5-integration-20261117/. Viewport reset and owned
browser tab/servers/fixture removed. API tests cover legacy native catalog safety;
no physical-native-device visual certification is claimed. Actual Desk scheduling
awaits its later upgrade; existing Desk audit events are not calendar appointments.


##17November2026 — V.5 account tools (local only)

Read the actual20261114Profile/rewards markup (identity header, card groups,
visibility controls and reward shortcut) and extended its card/type/token rules.
Profile gathers Identity, Study setup, Privacy & security and Wallet with direct
links to existing controls. Desktop uses two columns with a wide privacy panel;
320px stacks cards and44px controls without horizontal scroll. Password editing
moves to Account security. The optional deletion disclosure opens a centred,
scrollable dialog explaining retention/access, exact typed confirmation and a
prominent Keep my account action; its final button stays disabled until matched.
No new prototype sample progress, activity or counts were introduced.

Normal disposable-fixture sign-in verified primary exam save, parsed owned JSON
download, password-settings destination and deletion-dialog gating/cancellation.
No browser account deletion or password change was submitted; isolated backend
tests verify destructive behavior. Phone document305px within320px viewport;
desktop inspected. Screenshots: reports/finnaplan-v5-account-20261117/. Viewport
reset, owned tab closed, local servers/fixture removed. Mail/MFA configuration
availability remains honest in the local fixture; production/native parity is
not certified by these browser checks.

V.5 release (17November2026): the previously inspected boards, calendar,
Profile/account tools and shop screens are now deployed in the frozen337-artifact
web build, alongside28API artifacts and0097.1081backend tests and229-table
preservation pass;36private read-only release checks and both-site health pass.
Recovery uses prior static with the current privacy-safe API and paused new V.5
writes; error responses use existing form error states. No additional screen or
prototype sample activity was introduced in the recovery batch. Native physical
visual certification remains open. Receipt:
reports/finnaplan-v5-recovery-20261117/README.md.

## 17 November 2026 — V.9 surface consolidation

Read the current Finna Web reference markup's brand/search row: 1320px content,
50px search housing, 16px radius, max720px width and semantic light/dark tokens.
The housing now opens the one Quick find dialog. The same dialog owns phone,
Ctrl/Cmd-K, slash and search-result editing; screen-local filters stay local.
Revise groups the existing review/queue/mistake/vocabulary renderers; Chronicle
groups the existing timeline/date/source views. The Play cards use existing
card/action tokens in one grid. No stock activity or unavailable modes were added.

Personal Desk removes its duplicate plan/progress/review panels and illustration
hotspots, leaving saved questions, notes and focus. Shared-room illustration,
member controls and disclosure rules remain. The five phone destinations remain
Home/Exams/Library/Desk/Me. All renamed or retired destinations keep compatible
redirects with source, saved-session, query and fragment state.

Actual disposable-fixture browser checks cover 1440px desktop/dark and 320px
phone/light/dark, Quick find focus and results, empty review/vocab/mistake states,
private note save, date calendar bookmark and Play/Gauntlet setup. Phone document
305px≤320px; search dialog286px with17px left margin. Screenshots and explicit
limits: reports/finnaplan-v9-20261117/. Viewport/theme restored and preview stopped.
Static release hashes and both-site health pass. Actual printing/PDF output,
filled production activity and native physical-device parity are not certified.

### 17 November 2026 — V.10 Following and duplicate-doubt deflection

Read the actual Community composer/filter markup around lines215–223 in Finna
Web.dc.html and the existing question discussion implementation. Retain the
Community heading/pill tabs, paper/card surfaces, hairline borders, Newsreader
23px subsection heading and 44px controls. Following's new chronological
question cards reuse the existing discussion card; followed materials stay in a
secondary disclosure. Deflection adds an inline community-tinted aside within the
existing question composer, plain-text excerpts and wrapping join/continue
controls. Joining focuses the existing reply textarea while preserving the draft;
no new top-level surface or fabricated engagement was added. Synthetic desktop
1440/phone320 screenshots and measurements are in
reports/finnaplan-v10-following-20261117/. Document widths1425/305; no horizontal
overflow. Final renderer checks additionally cover account and block refreshes.

### 17 November 2026 — V.10 study-note composer and reader

Consulted actual Finna Web Community composer/filter markup around215–223 and the
existing question-discussion card. Notes reuse paper/card and community-tinted
surfaces, hairlines, Newsreader27px heading,13–15px form/body text,6/8px interior
corners and44px pill actions. Create adds one explicit Study note card; Community
keeps its tabs and opens composer/reader inline. Optional subject and Finna-link
fields keep uploads/URLs out of the note body. Pending visibility is explicit;
feedback never implies a verified answer or points award. New content remains
text rather than raw HTML. Synthetic desktop1440/phone320 and new note-panel night
checks show1425/305px document width without overflow; saved pending note, source
link, withdrawal and chronological Following were exercised. Screenshots:
reports/finnaplan-v10-study-20261117/. Broader existing discovery-panel night
contrast is not certified by this check. Preview/theme/viewport were cleaned up.


###18November2026 — Reviewed word practice and mixed Smart Review

Extended the existing20261114Revise/Content Studio paper/card tokens, semantic
light/night palette, heading hierarchy and44px actions. Curated words use an
explicit editorial card with authored choices, usage/gloss/source and reviewed
deck links. Mixed sets retain the existing saved player and use Item labels;
checked summaries distinguish editorial content from canonical source labels.
Today and the existing deck selector lead into the same practice, with honest
zero retained words and an unavailable/empty selected deck.

Disposable normal sign-in inspected all4modes, actual reverse-language check /
reload,4canonical+3word checks,7correct/noaward finish, checked summary, Today
0due/4new and empty deck start disabled.1440/320document widths fit their actual
viewports in light/night. Screenshots and explicit limitations are in
reports/finnaplan-v10-curated-vocabulary-20261118/. Full-page fixed-navigation
artifacts and two later failed full-page captures are documented; no invented
production content/progress or physical-native certification. Preview cleaned up.
The bounded342-artifact web +16API/data +0106 release passed both-site health.

### 18 November 2026 — Public question/test sharing

Question More reuses the existing44px inline action row and semantic link token
for WhatsApp. Test sharing retains its existing card/actions. No new global
navigation. Standalone public previews derive navy#0E1330, blue#1F4BE0,
yellow#FFC83D, paper/card/hairline and OS-night semantic colors from the actual
20261114Finna Web markup. Responsive24px card/14px action radii and explicit Open
links fit320px. Shared1200×630brand PNG has editable SVG; local Noto Sans raster
and standalone system-UI fallbacks are deliberate dependency-free adaptations,
not exact Figtree raster parity. Question/exam/year is escaped OG text, not image
raster content. No fake learner progress, awards or inferred provenance labels.
Synthetic1280/320px/light/night control QA and clean light standalone previews pass;
OS-dark standalone/actual WhatsApp rendering remains uncertified. Clipboard UI
success is separate from the empty browser-session readback; exact payload/failure
verified in actual-component checks. Full-page app fixed-nav capture artifacts are
documented. Receipt: reports/finnaplan-v11-sharing-20261118/README.md. Preview and
agent tab cleaned; viewport reset and Light restored.

## 18 November — Optional primary-exam check-in

The `/onboarding` screen extends the current Finna focused practice layout with
existing Figtree, navy/blue/yellow semantic tokens, panel radii and 44px controls.
Today/account entry is optional and uses the actual primary-exam title. The shared
question player retains source badges, stored-feedback notices and normal answer
states; finished summary separates correct/wrong/viewed/skipped, shows checked
subject evidence and offers explicit focus checkboxes/Save. No forecast accuracy,
readiness score, celebratory bonus or invented content is added. Suggestions keep
existing selections and carry the small-sample qualification. Synthetic local
browser QA covers1280/320px, light/night, resume and explicit focus save/reload;
phone scrollWidth and clientWidth both305px. Eight screenshot receipts and capture
limitations are in `reports/finnaplan-v11-onboarding-20261118/browser-proof.json`.
`checkin-summary-desktop.png` is the clean viewport proof; full-page fixed headers
appear at their viewport capture position. Preview tab/API/web/database cleaned,
viewport and Light restored, original user tab retained. New endpoint/device-native
capability is not certified; web-only guards remain explicit.

## 18 November — Bulk group prices and claim receipts

Rewards & accounts keeps its existing owner route and adds one semantic-token
panel for100-email preview/apply batches, pending/applied state, explicit removal
from future matching, and bounded group codes. Actual stored code usage/expiry /
revocation and searchable retained entries replace invented member counts. The
billing page gets an explicit claim form; opening a link does not redeem it.
Buttons name future ₹50/month pricing, not Pro access. Existing mandates and
access are described separately. The new receipt reader is on-demand, paginated,
owner-only and omits private study/payment details; account changes clear it.
Prototype Finna Figtree/navy/blue/panel tokens and44px controls are reused. Preview
and search wrap at320px with305pxclient/scroll widths. Light/night desktop/phone
synthetic screenshots and capture limitations live in
`reports/finnaplan-v11-bulk-20261118/browser-proof.json`; source authority remains
`Finna Admin.dc.html`/`Finna Web.dc.html`. This does not certify native/device use.
