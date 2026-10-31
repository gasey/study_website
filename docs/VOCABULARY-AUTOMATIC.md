# Automatic vocabulary review and smoother exam focus

24 October 2026. Implementation of the first recognition engine from Astra’s [design](VOCABULARY-AUTOMATIC-MASTERY-PLAN.md). Release evidence: `reports/vocabulary-automatic/`.

## Student workflow

- Sign in with a free account, open Vocabulary and answer a verified exam question. The server checks the answer and saves the next review in the same transaction. No confidence rating is requested.
- Correct: start at one day, then qualifying delayed reviews advance through 3, 7, 14, 30 and 60 days. Promotion requires being due, at least 24 hours since the latest recorded exposure and a different IST credit day. Recent checked Bank/review attempts also count as exposure.
- Wrong or “I don’t know”: review again in ten minutes. A revealed answer is learning, not a graded answer. Skip defers ten minutes without a wrong answer or stage reset.
- Due items come first. The server introduces at most ten new canonical items per IST day; the UI ends a ten-card sitting and offers an explicit continuation. Session count is UI convenience, not a security/reward quota, and resets after a page refresh. This differs from Astra’s suggested two-new-item mix during existing backlogs; bounded due-first selection is implemented, adaptive mixing is deferred.
- Account schedules are shared across devices and both question-focus modes. Refresh can restore the original saved feedback through an opaque authenticated receipt URL. Restored feedback is labelled as historical, not regraded using a later key.
- Source instructions, passages, underline/bold markup, figures, option layout, source PDFs and correction/discussion links use the shared question presentation. Original option order is preserved because options can refer to letters or “both above”.

## Server contract and integrity

Migration0048 adds scope-aware `v_vocabulary_eligible`, canonical account `vocabulary_state` and immutable `vocabulary_cards`. No canonical bank data or existing local ratings are rewritten. Eligibility requires strict scorable keys, approved English/vocabulary classification, 2–6 distinct nonempty options and a compatible source presentation. An equivalent Mizoram printing can be used even when the primary printing belongs to another exam system. Different source instructions are not silently substituted.

`GET /api/vocabulary/overview?exam_scope=…` gives eligible/started/due/accuracy/longer-interval counts. `POST /api/vocabulary/card` accepts an optional `resume_id`; unanswered cards expire after 30 minutes. `POST /api/vocabulary/cards/{id}/answer` accepts only action and displayed choice index. Correctness and schedule cannot be submitted by the client. Requests bind the expected signed-in account; writes retain origin, CSRF and rate checks. Responses are private/no-store.

A learning-session advisory lock, card/state row locks and version checks serialize competing tabs and scope cards. The attempt, state update and immutable response receipt commit together. Exact duplicate retries return the same receipt; conflicting retries, expired cards and changed source/key versions create no false grade. Active mock/competitive answer protections remain in force. Review attempts create no practice/game XP and do not refill free practice allowance.

Semantic learning hashes share progress across equivalent printings. Changed learning content resets the recognition stage on its next valid delivery, preserving historical checked answers; source revision metadata also invalidates stale tokens. Counters report original historical correctness, not current-key reassessment.

## Smooth focus switching

The shared focus store now updates through React Router rather than `window.location.assign`. The header/account session stays mounted; only scoped learner routes remount so old result state cannot be relabelled as the new pool. Scope-specific paper, collection, pagination and vocabulary receipt query parameters are cleared. A subtle 160ms entry transition respects reduced motion. Explicit URL changes synchronize the store; another tab’s preference cannot silently change the active document. Focus is disabled during a mock to preserve its immutable session.

This supersedes the full-page reload choice documented in ALL-EXAMS-AND-INBOX.md. Unscoped Inbox/desk/editor routes retain their form state. Games still uses the previously documented Mizoram verified pool.

## Acceptance and limits

- Full isolated suite: 150 passed, one upstream AnyIO deprecation warning, 30.65 seconds. Eight focused vocabulary cases plus two importer safety cases cover privacy, replay/concurrency, no answer leak, original choice order, recovery, spacing/recent exposure, reveal/defer, shared scope progress/equivalent printing, key changes, expiry, forged state, CSRF and active mock protection.
- Latest frontend production build passes. Migration0048 rehearses on a disposable production-data clone and the clone is removed without stopping production.
- Synthetic browser rehearsal: correct answer schedules one day automatically; refresh restores identical feedback; Next loads a different card; Skip records no wrong answer. Geography changes from two Mizoram items to three All items while preserving header input and authentication, demonstrating SPA switching.
- Recognition of an exam question is not independent word recall or a probability of mastery. No runtime AI, response-speed inference, mandatory confidence questionnaire or invented confidence percentage is used. Word-family/typed-recall tasks require separately reviewed content later.
- Earlier unscoped browser confidence maps are left untouched and are not imported as checked answers. First release requires an account; guest scheduler/adoption is deferred.
- Ten-minute repair requires a return visit; no email/push reminder service is enabled. Recorded answer attempts inform exposure, but this is not a claim to detect every answer seen elsewhere. Review receipt retention/archival and capacity testing remain future operational work; no physical-mobile or load certification is claimed.

Final deployment and live verification receipts are appended after release.

## Release receipt

0048checksum2ea2327e9e7912ff applied; no pending migration or checksum drift. API deployed before web.155eligible vocabulary items per focus, eligibility aggregate36ms in a single server SQL observation. Both currently equal because all1938papers are Mizoram. Health77751questions/12490strict. Guest API401and live guest page offers free sign-in; live filter switch preserves header input. No production vocabulary cards/states or synthetic learner attempts were created. Family site follows redirect to200.

Private pre0048backup27,024,146bytes/mode600. Operational check initially passed unsupported --status to the legacy sync script, which incorrectly fell through to a full same-bank sync. Bank content/keys, appearances, classifications, paper metadata, users and attempts were compared against a disposable restore of this backup. The only semantic difference was obsolete canonical difficulty imported from raw appearances:76724rows. Restored these to their previous NULL state, corrected primary propagation to keep canonical difficulty NULL and added unknown-mode fail-fast plus actual SQL regression tests. Final hashes match across all compared tables excluding update timestamps; local bank JSON and archive appearance metadata were never edited. Sync-log/timestamps record the operation. Evidence includes initial mismatch, column analysis, repair SQL and final equality. The restore clone is removed after comparison.

Final150tests pass; latest web build and deployed artifact manifest are recorded with screenshots in reports/vocabulary-automatic. No API errors in recent checked journal; no physical-mobile/load certification. Shared Caddy configuration untouched. Notes/reports/source handoff are mirrored privately beside the backup.
