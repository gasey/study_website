# Design fidelity — values extracted from the prototype

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

User-approved functional extension of v3 question/feed cards. Keep existing cream panels, mono metadata, pill actions and44px targets. Open question is a secondary muted link instead of Details. Questions & Doubts uses the existing feed tab bar and a23px Newsreader subheading with wrapped pill filters. Reuses the existing inline discussion styling rather than introducing another page design.

## Exam calendar — 2026-10-23

Extracted v3 calendar1618–1675:1100px main,36px top/24px desktop side/96px bottom padding,Newsreader clamp34–50 heading,17px intro/720px max,20px flex gap,ink#1D1B18 countdown22px padding/10px radius/gold#D8A33A,26px title/64px days. Calendar uses7columns,Monday-first,1px ink outline/10px corners/24px month label; date event strips and selected-day details, month/list pill controls and12px official-source footnote. Mobile16px gutters allow44px day widths at360px. Existing Shikshacom grid navigation informed implementation; v3 governs product appearance. Replace prototype fake dates/72% syllabus claim with actual saved/followed event countdown and honest empty states. Exports, verification notes, owner editor and inbox preferences extend the reference controls using existing palette/44px actions. Official notices reuse the same underlying rows rather than duplicating editorial content.

## 2026-10-23 — Games and global search

Follow the v3 games hub cream/ink/gold palette, serif headings, featured Gauntlet scene, pastel mode cards and compact side panels. Render Gauntlet track in native SVG; use existing safe source-question renderer and shared two-column/list options. Actual account XP/history replace prototype samples. Global search groups results with category tabs and privacy labels. Backend room, reconnect, publication controls and unavailable marketplace checkout notes extend the reference honestly. Desktop evidence is in reports/games-search; attempted viewport override stayed at1280px, so mobile files are not mobile verification.

## 2026-10-23 — Direct subject Library and database map

Functional extension of v3's warm Library/cards and admin console: cream #FBF8F1 cards, hairline borders, Newsreader 25–54px titles, muted blue/green/gold shelf accents, rounded pill view controls and44px targets. Subjects opens first; tools remain in the adjacent view. Shelf tabs use four plainly named actions, additional filters fold under More filters, and original source context stays on existing question cards. The database map reuses the236px dark admin sidebar, cream workbench and blue selected cards, with selectable count/relationship views. No invented difficulty chips or activity counts. These new Library/map layouts extend v3 rather than claiming to be original prototype screens.

### 2026-10-23 — Launch scope and Games recovery additions
These are functional additions requested by the user, not extracted v3 prototype elements. Header adds a compact warm focus line (11px, #F6F0E3, hairline border) for MPSC & Mizoram recruitment. Library shelf exam selector is always visible; optional advanced controls remain below. Games uses a cream/gold unfinished-mock banner with direct resume link above the featured game. Existing type, cards and source presentation retained.

### 2026-10-24 — v3 Inbox and source focus selector
Extracted Inbox1064–1114: main1240px,36px top/24px desktop side/96px bottom; Newsreader clamp36–52px/weight500/tracking-.02em; flexible340px notification and480px message bases,40px desktop gap; white cards,#E4DBC9hairlines,14px corners;14px notification text/11px Mono timestamps; cream thread list and magenta own-message/send. Real bounded notices and joined desk conversations replace prototype fixture threads. Category/read/retry/pagination and durable in-app preference controls extend v3; email/push/quiet-hour actions are not invented as working services. All exams header selector extends the requested launch focus, retaining the established cream strip. Physical mobile proof is not claimed.

## 24 October — Vocabulary automatic review and focus transition

Vocabulary Helper extends the v3 paper/card typography with a 900px reading column, purple vocabulary accent, four compact account counters, source instructions/markup, shared 2×2/list options and one primary Check/Next action. Manual Again/Hard/Good/Easy buttons are removed. Dates replace confidence input. Refresh shows “Saved feedback restored”. The recognition-only explanation avoids asserting word mastery. Smooth scope entries use160ms opacity.65→1 and2px vertical motion; prefers-reduced-motion disables animation. Header stays mounted, and private unscoped desk/inbox/editor state is preserved. Actual acceptance and limitations: VOCABULARY-AUTOMATIC.md.

##24October — English source context
Match prior UDC-LDC QuestionText/QuestionContext behavior for ruled blanks, nested **bold**, *italic*, __underline__ and default-open reading passages. Retain current v3 cream instruction panel (#F6F2E9), gold left border (#B9A579),13px context and source line breaks. Blank width follows underscore length capped2.4–12.6em; React text rendering keeps arbitrary HTML escaped. Apply the same shared source renderer to live practice, mocks and frozen result review. ENGLISH-SOURCE-FORMATTING.md records actual data scope.

##24October — Answer provenance help
Extend the existing v3 provenance pill with an information mark and44px summary target. Native hover text gives the short meaning; native details opens a cream320px/max-container note in normal flow for touch and keyboard, avoiding viewport-clipped tooltips. Keep green official/key and muted blue non-official styling, with separate reviewed wording. Help and question-specific evidence links disclose no answer.

Provenance-help layout follow-up: expanded help spans a full metadata row with a fluid680px maximum, superseding the initial320px note. This avoids vertically centering metadata beside a tall narrow text column. Closed pill/hover styling remains the same.

### 2026-10-24 — Community tab continuity

For you, Following, MCQs, Questions & Doubts and Materials now retain the v3 Community heading, tab bar and side rails. Previously Following/MCQs/Materials returned replacement whole-page layouts despite retaining `/feed`. Embedded views now use secondary headings and narrower content grids. Standalone readers remain available; Community lesson entry carries a return to the selected tab. No new top-level navigation is added.

### Admin exam inventory

Exams & coverage is a lazy-loaded workspace within the existing admin shell, with internal views and shared filters rather than new public navigation pages. Source and key previews load only on request. Four answer status totals drill into the existing repair workspace; details preserve source context and existing reviewed edits. Source context counts are not presented as proof that every instruction is required or restored.

## 2026-10-24 — Workflow extensions

These five workflows extend the existing v3 design rather than represent additional prototype screens. Reuse cream/card/ink surfaces, hairlines, Newsreader26–42px headings, mono metadata, 9–14px corners and44px controls. Intake and quality remain internal admin tabs with the existing236px sidebar. Continuation/daily revision enter through existing Library/Desk; question answers retain the shared source renderer and2×2/list choices. Resumed practice displays within its original module, with one clear return action. Correction updates use the existing Inbox and warm source-notice treatment. Synthetic screenshots are explicitly rehearsal evidence.


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
390px measured375px document/body width, without horizontal overflow. Desktop
and mobile screenshots live in reports/group-b-common-20261028.

### 28 October 2026 — Question source wording

Keep existing card typography and spacing. Topic badge uses approved learning topic; source row includes the full verified paper title, wrapping naturally. Detail appearances show this title in preference to the bare paper number.

### 28 October 2026 — Identity and learning tag admin screens

Reuse admin console typography, existing rounded-panel/card/hairline/paper tokens and min-h-11 controls. Learning tags has candidate selection and proposed path columns at xl, stacked on smaller screens, then per-question current/proposed preview cards. Every preview requires an individual checkbox. Batch status cards link immutable contribution history. Paper inventory embeds a two-column identity form/source preview at xl with optional600px PDF frame. Individual contributions show current/proposed tags and a shared GK/GS picker; exact stored IDs are under a disclosure. No new prototype or new visual theme.

### 28 October 2026 — Clerical exam routes and unlimited billing label

Reuse the existing exam card, hairline border, pill links and min-h-11 controls. Below the clerical hero add UDC/LDC/Assistant links with aria-current and own-exam English/GK shortcuts. Topic-map headings and broad question badges use General Knowledge in these exam contexts. Billing uses its existing paragraph style for “Unlimited Pro access · no expiry date”.

### 29 October 2026 — Exam-section polish

Retain the existing green exam hero, gold edge, Newsreader headings, cream/card surfaces, hairlines and44px controls. Focused study uses a28px exam title and fewer hero actions. Overview keeps Start practice / Subjects & topics / Past papers; answer guidance is a closed disclosure. Subject/topic/search form the main filter row, with secondary controls in a disclosure. Keep old results dimmed while replacement data arrives, with answers disabled. Match hero negative margins to actual shell padding:12px below768px and18px from768–1024px. Tab links scroll inside their own container. Result focus uses measured sticky-header clearance instead of a fixed mobile offset. Evidence: reports/exam-polish-20261028.

Final phone refinement: fold the subject/topic/search controls behind a44px toggle by default while retaining the current subject/topic beside the practice heading. This brings the first question into the initial study viewport.

### 29 October 2026 — Owner-requested less crowded paper lists and page gutters

Override the prototype's1240px outer shell with1440px for shared app navigation/workspaces; use16px desktop and12px phone outer gutters, retaining18px exam tablet padding and narrow prose/form limits. Exam1100px and Combined1160px wrappers use this shared width. Hero negative margins match actual gutters. Paper lists use a full-width row with Newsreader21px heading, cream card/hairline border,12px radius,16/20px inner padding and44px action/disclosure targets. Show only nonzero answer counts; keep unofficial wording visible. Native Paper details & tests holds full printed identity, explanation gaps and unchanged test settings/actions. This is an explicit user-directed functional/layout extension; not a newly discovered prototype value.

### 29 October 2026 — Explicit layout correction

Restore paper box cards with a responsive300px minimum width and stacked actions. Remove the shared1440px outer width cap, including Combined and Study Desk; retain16px desktop/12px phone edge gutters and existing tablet exam padding. The owner specifically rejected rows and remaining wide-screen outer margins. Earlier row/1440px notes are historical.

### 29 October 2026 — Fluid layout refinement

Paper boxes use340px minimum and16px gaps (12px phone). Shell remains uncapped with existing16/12px gutters. Exam question results use a left-aligned960px maximum; shared question headings75ch. This is the owner-authorized optimization of the corrected box layout.

### 29 October 2026 — Owner-requested card polish

Shared paper boxes now stretch to equal height per row with flex body/action alignment. Year badge and source link share the top line; official/unofficial statuses remain explicit with symbols and colour. Existing12px radius and16/20px padding retained. Details has a24px circular plus inside a44px summary target. Focus outline2px blue; shadows subtle; reduced motion disables transitions.

### 29 October 2026 — Interactive Atlas extension

Owner-authorized restoration uses existing cream/card/hairline tokens and Newsreader headings. Fluid16/12px shell gutters; desktop map plus300px layer rail, stacked phone layout. Map420px phone and clamp420px/64vh/720px desktop; Leaflet zoom44px. Native selects and44px checkbox/button targets; notes/features collapsed. Interactive Atlas belongs in Library tools and contextual subject navigation. This is a functional extension to the prototype, not a newly extracted prototype screen.

### 30 October 2026 — Simplified admin workflow

Retained prototype admin palette/sidebar: body#EFE9DD, sidebar#1D1B18/text#E9E1D2,236pxdesktop width,13.5pxnavigation,6pxnavigation radius; selected#3A3631 and#D8A33A marker. Adaptation requested by owner: five primary tasks and collapsed grouped specialist tools; phone section picker replaces21horizontal tabs. Main12pxphone/16pxdesktop gutters follow the owner's site spacing decision. Boxed task cards12pxradius; two columns on phones, four at xl. Queue summaries remain a three-column compact row on phones, avoiding the old three-card vertical stack before filters. System details and advanced filters use native disclosures.

### Paper workspace — 31 October 2026

Preserve boxed question cards with 12px phone / 16px desktop outer gutters. Bound reading width outside the two-column PDF comparison. Use the booklet filename as the compact heading, disclose full paper title/instructions/coverage, and keep mobile search full-width with type/status controls side by side. PDF stacks above the question on narrow screens and scrolls within its own container.
