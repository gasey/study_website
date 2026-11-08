# Topic Trail — a small exam game

2 November 2026 · Proposed design, not implemented or deployed.

## Product decision

Make a short solo expedition through one narrow topic, using existing exam questions. Start with one UDC or combined-prelims topic pack, not a whole syllabus or another general quiz lobby. Candidate packs are UDC articles/prepositions or Prelims Fundamental Rights. Final launch selection requires a live usable official-key pool census; these examples do not assert sufficient bank coverage.

Target: one enjoyable 4–6 minute session, readable on a phone, no AI calls during play. Reuse the site's source identity, strict scoring eligibility, authentication, session snapshots and reward protections. It is a new versioned mode rather than a silent change to Gauntlet.

## The theme and core loop

A small illustrated hill path has ten stepping stones, a bridge after stone three, a lookout after six, and a flag at ten. The player's existing avatar walks along it. Each stone represents one question; correct responses light the stone. Incorrect answers still move the player forward, leaving that stone marked for revision. Nobody is eliminated early from a learning session.

Choose a named pack → see exam/topic, ten questions and rules → start → answer → see brief answer feedback → continue → reach the flag → review mistakes.

The full question appears in a stable readable card; the scenery is a compact strip above it. No camera motion, character control, reflex requirement or animation blocking the options. The journey supplies momentum while the actual question remains the focus.

## Small but meaningful game mechanics

- Ten distinct scored questions from the same explicitly selected pack; no hidden broadening or repeats inside a run.
- Twenty seconds of server-timed answering per question for initial short-text packs. Between questions the clock pauses for feedback and Continue. Arithmetic/long passages need a separately defined rules version rather than the same timer.
- Correct answer earns 100 run points; incorrect/timeout earns zero. No speed bonus, so reading faster is not the objective.
- One optional **Double next** token, selected before seeing the next question. It makes that question worth 200 if correct and zero otherwise; used up on an incorrect answer or timeout. The token is a run mechanic, not currency.
- Three consecutive correct answers trigger a small visual celebration, with no hidden score multiplier.
- A bridge/lookout checkpoint shows progress and a short encouragement, then Continue; no extra menus or questions.
- Finish labels use actual outcomes: Finished (all ten attempted), Strong run (at least seven correct), Perfect trail (ten correct). These are run badges, never a claim of topic mastery.
- Result shows correct out of ten, run points, mistakes with evidence/explanations when available, and Try another run. Retrying mistakes is clearly separate untimed practice; no additional run score or repeated reward claims.

Maximum run score is 1,100. Accuracy remains out of ten regardless of Double next. Server validates token use before revealing the question and records an immutable action; refresh/retry cannot reuse it or reveal a replacement question. Interrupted sessions resume their original question/time state. Existing active-game answer restrictions apply.

## Three screens only for the first release

1. **Pack card:** title such as “Prelims · Fundamental Rights”, a one-line scope definition, actual usable count, ten-question rule, estimated session length and Start. If fewer than ten usable items remain, disable Start and offer explicit alternative packs or untimed study.
2. **Trail:** compact progress path/avatar, question number, answer timer, readable source question/options, remaining Double next token between questions, connection/submission status. Feedback exposes only the just-finished question. Quiet mode and reduced motion are supported.
3. **Finish:** flag scene, accuracy and run score, marked stones linking to review, source explanations where present and a replay button. Missing explanations are labelled; the game does not generate one.

Desktop centres the same narrow game panel. Mobile preserves at least 44px targets, visible focus, full diagrams and non-colour-only feedback. Animations are decorative SVG/CSS, avoid external image calls and respect reduced-motion preferences. Keep established site typography and option-state colours.

## Pack administration

A small owner tool chooses an existing exam collection and an approved taxonomy path or a reviewed explicit source list for that topic. It displays strict usable counts and previews source membership. A human confirms each candidate actually fits the narrow title; a broad GK classification does not establish Fundamental Rights membership.

Store pack ID/revision, displayed title, exact selection, source identities, eligible question IDs, rules version and publication state. Retain canonical IDs and original provenance rather than copying a second question bank. Initial suggested content target is thirty suitable questions to provide variety, with ten the hard run minimum; do not promise variety when the pool is smaller. Publish one pack first, then at most two additional packs after student feedback.

Only official/key answers that pass existing presentation/source checks enter scored runs. Preserve answer-access restrictions during active games. Recheck eligibility before start, snapshot the run, and handle subsequent key/source corrections with the existing exclusion policy; show adjusted eligible denominators rather than declaring an invalidated answer wrong. Never promote a friend’s checklist tick into official scoring status.

Run points and badges do not change account XP rules. Reuse exactly-once canonical reward claims and daily caps. No shop, paid boosts, leaderboards, leagues, chat, random multiplayer, AI opponents or seasonal content in the first release. A friend challenge can be considered later using the same frozen pack/rules and answer-release protections.

## Build and acceptance

1. Count and source-check real candidate pools; choose one pack with at least ten eligible questions. If none qualify, retain the design and prepare source/key review instead of filling it with inferred answers.
2. Build a clearly labelled synthetic visual prototype covering start, one question, feedback, Double next and finish. It must not write attempts/rewards or pretend to use real exam content.
3. Add versioned pack/run support and the narrow game UI using existing games infrastructure. Test exact scoring, one-use token, timeout, idempotent submit, reconnect, stale pack, insufficient pool, changed key and reward replay.
4. Exercise mobile/desktop with keyboard/reduced motion and two real test accounts; check that external source/review routes cannot expose an active answer.
5. Deploy one pack, measure completion/abandonment and invite feedback before adding packs or multiplayer.

No database migration, game implementation or production change was made to create this design.

## Sol 6.1 suitability

GPT-6.1 Sol is documented for complex coding and tool use: https://developers.openai.com/api/docs/models/gpt-6.1-sol . My engineering assessment is that this bounded feature is a suitable Sol implementation task, especially when delivered as pool audit, prototype, backend/rule tests and release checks. Model capability is not a correctness guarantee. Sol assists development; the deployed game runs on the existing website/API without a model call for each question.

## Temporal current-affairs prerequisite

Read `CURRENT-AFFAIRS-TIMELINE-DESIGN.md` when selecting time-sensitive questions. Freeze and display the original reference date, retain original options/keys, and withhold linked “Then and now” facts during active assessment. A current update does not make an old source eligible as a present-day question. Start with a stable topic pack while the temporal context path is being implemented.

## 3 November implementation status

Implemented and deployed at `/trail`, with owner pack administration at `/admin/topic-trail`. The initial pack is ten exact Prelims Constitution basics sources, each stem/option matched to the original PDF. Broad taxonomy did not suffice: booklet duplicates left only seven vocabulary questions, while physics included geography. Exact reviewed source lists are supported, and the pilot has limited variety. The original design's thirty-question variety target remains future content work. Source snapshots, active-assessment locks, one-use Double next, paused feedback and canonical reward claims are covered by tests and a full synthetic browser completion. No human sign-off was fabricated. Operational details and limitations are in `ORACLE-PAPER-WORKBENCH-RUNBOOK.md`.
