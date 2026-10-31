# Exam journey, learning XP and reward points

Deployed 2026-10-21. Migration0034 is applied: never edit it. The bank remains the content authority; no questions/keys were changed in this packet.

## Learner journey

Exams → save exam → scoped practice/papers → timed mock → permanent result → progress/mistakes. ExamJourney shows any open mock (including another exam), recent original results and a Continue practice link. Filters/page live in URL; signed-in checkpoints also persist in exam_study_checkpoints. Guests retain device progress/URL state. Checkpoint paper/section IDs must belong to the public exam; client timestamps are ignored. Practice shows source instructions/emphasis/figures/PDF links without routing into the Bank.

Mock answer/mark/position persistence was already present and was exercised end-to-end. Two browser bugs fixed: overlapping initialization now rejoins the winner's saved mock; submission goes to /results/:id so refresh cannot silently launch another mock. If a submit response is lost, the runner can recover the existing saved result. Results include collection_id for return to the originating exam. Bookmarks expose save failures; collection loads guard stale responses.

## Distinct totals

| Total | Meaning | Spendable? |
| --- | --- | --- |
| Original/adjusted marks | Exam performance and correction history | No |
| Learning XP | Activity board (week/month/all time) and lifetime level | No |
| Reward points | Earned-benefit wallet | Yes, for enabled catalog offers |
| Contribution credit | Existing published-bank contribution reputation | No; new credit events also generate XP/reward entries |

Public board visibility defaults off. Opt-in publishes only handle/XP/rank, never email, wallet or progress details. Periods use Asia/Kolkata boundaries; equal XP shares a rank. This is an activity leaderboard, not a validated exam-rank/ability assessment. Lifetime level is max(1,floor(sqrt(max(0,XP)/40))); next level needs40*(level+1)^2. Spending points changes neither XP nor rank.

## Award policy v1

- New eligible first rewarded correct response to a unique canonical verified-key MCQ:10XP +1point. Shared study/game budget300XP/day, currently up to30 rewarded questions. Repeats across mocks/practice pay once. Claims are inserted atomically under a per-user reward transaction lock.
- Requires registered account, a server-scored correct answer, official/key proof and matching current strict eligibility. Mock reward requires submitted, non-late session and frozen source/key snapshot. Derived/inferred/guest/late rewards excluded. There is no browser API to set correctness or award arbitrary points.
- Awards start at migration launch; no historical bulk backfill or guest-history adoption grants. Previously correct questions can receive their first eligible post-launch reward. Existing attempts/scores remain saved.
- Newly appended contribution_credit events produce matching XP/points. Reversals append negative effects; they do not erase history. Already-spent contribution points can leave wallet debt; further redemption requires sufficient net balance. Ordinary later score reassessment does not rewrite past activity rewards. Abuse recovery is not an automatic claim of answer correctness.
- Votes, posting volume and self-reported completion do not earn points. Server scripts/DB roles remain trusted operators. The bank exposes answers for study: these caps do not prove cheating is impossible.

## Pro redemption

Default provisional offer:1000points →7daysPro, disabled pending owner launch review. Owner manages it in Admin → Rewards & points, with optimistic version checks and a reason/audit event. No customer funds, paid renewal or Razorpay action occurs for a reward redemption. There is one allowed redemption/account/30days. Users review cost before confirming. Per-user transaction locks plus idempotency receipts prevent concurrent double-spend; outdated price/version rejects. Existing receipt retries return the same receipt even if offer later closes.

Redemptions produce immutable dated entitlements, separate from users.plan_* and billing_subscriptions. account_has_pro centralizes practice/mock/mistake gates. Auth session/private profile/billing read effective Pro access; billing lists earned access separately. Starts after an existing trial/reward/access period. Active paid Razorpay subscriptions block redemption to avoid conflicting renewals. Expired rewards cease granting access by date without a cron rewrite. Future subscriptions could overlap a previously scheduled reward; a complete paid-renewal scheduling policy remains future work, not a promise to extend/refund billing automatically.

No live accounts were given artificial points, enrolled on the board or granted reward Pro in testing. Existing paid provider configuration was preserved.

## Games contract

The ledger reserves game source events; future game controllers must use server-owned question snapshots, server timing, replay-safe events and the same per-account daily budget/question claims. Do not expose an /award endpoint or trust game score from localStorage/client payload. Awarding a new game cannot bypass caps or reward the same canonical question twice. Games themselves, duels/cups, seasons, cosmetic inventory and game anti-abuse adjudication are not implemented by this packet. No wagering, point transfers, cash-outs or bought ranking boosts were added.

## Evidence and operations

52 isolated PostgreSQL tests pass (one upstream warning), including actual mpsc role execution, unique rewards, caps, provenance exclusions, guest exclusion, privacy, replay/concurrent redemption, expiry, owner/version guards, checkpoints and mock submission. Browser synthetic20-question flow: bookmark; start; selectB; mark; save/next; reload at question2 with1answer/1mark; submit1correct19skipped; reopen/refresh permanent result; wallet rose10→30XP across three distinct rewarded questions; account checkpoint Continue URL retained offset10. Native PDF rendering remains browser-dependent. Redemption success is integration-tested, not a real production user transaction.

Rehearsed0034 on production-data dump clone, then applied; frontend/API deployed and file SHA256s compared. Main bundle470.72kB after lazy exam split. Both shared sites healthy. Evidence: reports/learning-rewards. Server private copy: /home/ubuntu/ism-release-reports/2026-10-21-review/reports/learning-rewards. Keep catalog closed until business review; games/load/full privacy/abuse/backup/payment acceptance matrices remain incomplete.


## Creator publication extension — migration0035

Content Studio adds ledger kind content:20XP+5points on an independently owner-reviewed first publication, at most one/account/India day. No self-publication, demo, repeated publication or upvote awards. Persistent material claim plus shared reward lock; archiving reverses once, restore never re-awards. No retroactive bulk awards. Read CONTENT-STUDIO.md for contracts. Subscription redemption remains disabled pending launch rate decision.
