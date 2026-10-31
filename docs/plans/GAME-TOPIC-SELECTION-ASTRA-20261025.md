# Games students can choose without knowing the taxonomy

Planning recommendation · 25 October 2026 · no application, bank or server changes.

## Recommendation

Keep the existing games and scoring rules. Replace the required subject → topic → subtopic journey with three entry points: **For my exam**, **What I’ve practised**, and **Choose a subject**. Each proposes plainly named areas; the student chooses one and sees the actual scope before starting. A taxonomy remains an internal way to find questions. A student never needs to choose a stream, understand a tag, or prove mastery to play.

Ship one named area per game first. A Geography shelf may already represent multiple reviewed paths; that is one understandable area, not a custom mixture editor. Keep “Mixed subjects” as a separate, deliberate choice. Later, add private-room suggestions for areas both players are willing to play. Do not start with a mastery model, bespoke question sets for each opponent, or arbitrary weighted mixtures.

This refines the entry flow proposed in [GAMES-SPECIALIZATION-PLAN.md](../GAMES-SPECIALIZATION-PLAN.md). Its pool integrity, immutable context, readiness, exact matchmaking and reward contracts remain the foundation. This document proposes changes; it does not establish that those earlier contracts are implemented.

## What exists and what this needs

Source inspection: `web/src/screens/Games.tsx`, `web/src/lib/games.ts`, `api/app/routers/games.py`, `api/app/services/games.py`, [LIBRARY-TOPICS.md](../LIBRARY-TOPICS.md), [LEARNING-WORKFLOWS.md](../LEARNING-WORKFLOWS.md), [VOCABULARY-AUTOMATIC.md](../VOCABULARY-AUTOMATIC.md), and [LEARNING-REWARDS.md](../LEARNING-REWARDS.md). Repository guidance and decision records were read. No live pool census was made; counts below are examples or rule thresholds.

| Existing behavior | Smallest useful change |
| --- | --- |
| Games accepts one optional subject; empty means mixed. Featured Gauntlet can start before selection. | Route every start through one setup summary; require a deliberate area or mixed selection. |
| Games always uses the Mizoram recruitment source scope, even when global discovery says All exams. | Show “Games question sources: MPSC & Mizoram recruitment” persistently. Do not infer source scope from a header, question geography or academic stream. |
| Library has named shelves over approved paths; some combine multiple paths. | Reuse shelf IDs, labels and mappings. Geography need not be a top-level subject to be a good button. |
| Attempts, mock history, exam saves and study checkpoints exist. | Use them for suggestions with reasons, without creating a general mastery score. A checkpoint alone is not evidence of successful study. |
| Vocabulary has recognition scheduling for its own questions. | Keep its meaning local. Vocabulary recognition is not evidence of English subject mastery. |
| Subject catalog hides counts below ten and misses some final draw checks. | Share actual eligibility between availability and draws; show why an area is unavailable for a particular mode. |
| Private duel joins immediately start; random queue matches nullable subject. | Add rules preview/readiness and match frozen context before claiming the proposed fair topic experience. |

## Student journey and copy

An active game or unfinished mock remains the first card, with its existing resume action. Below it: **“What would you like to play?”** Show the three entry choices in the existing Games page, above every game start, including Gauntlet. Avoid a new onboarding questionnaire.

### For my exam

Offer saved/recent exams as shortcuts and a searchable exam picker. Do not automatically select the most recent exam if the student has several. Reuse public collection and section identities; do not match loose paper titles or turn an exam name into an inferred syllabus.

Selecting a known exam shows its existing named sections and eligible question counts. A section should say, for example, **“English · from your selected exam’s papers”**. Unknown or unsupported exam coverage gets an honest explanation, not a fabricated exam preset. An exam without a reviewed topic mapping can still offer an exact eligible paper/collection pool labelled **“Mixed subjects from these exam papers”**; that option requires a deliberate choice.

Where an exact exam pool is sparse, offer a second explicit action: **“Play this subject across Mizoram recruitment papers”**. Its preview must change the source label accordingly. An exam choice is a useful context, not a declaration that the student knows every syllabus subject. Do not label a random game an official exam simulation or balanced syllabus test.

### What I’ve practised

Show up to three named area suggestions with evidence such as **“Geography — you answered questions here recently”** or **“Continue English from your last study session”**. The latter is a continuation hint, not a competence claim. Use **“Choose an area”**, never “Your mastered topics.”

Initial deterministic proposal: rank areas using unique canonical questions attempted in the last 90 days, capped at the latest 100 distinct questions; three distinct attempted questions in an area suffice for a recent-practice suggestion. This is a proposed discovery threshold, not a validated mastery threshold. Repeated answers to one question count once. An area supported by fewer attempts can appear only as a recent-session shortcut, with that weaker reason. Use current approved paths for mapping, not free-text notes or material tags. Prefer specific areas only when supported by their own reviewed paths; broad General Studies activity cannot imply Geography activity.

Include wrong answers: the student has encountered that area and may want another try. An attempted question with an unofficial solution can support the neutral claim “practised”; it cannot enter the scored game unless it independently meets strict game eligibility. Answer validity, confidence and topic familiarity are different facts. Missing mappings produce fewer suggestions, not guessed classifications. No exact private history or accuracy is shared with opponents.

Choosing a suggestion opens **“Geography · questions from MPSC & Mizoram recruitment · some questions may be new to you.”** This selects the area, not merely the exact previously answered IDs. Offer **“Review my answered questions”** as an ordinary study link if the student wants only familiar items. Do not present a game over known answers as an ability assessment.

### Choose a subject

Offer ordinary labels backed by current Library mappings: English, Arithmetic & Reasoning where supported, Geography, History, Polity, Science, Mizoram GK and the remaining available subjects. These are examples, not permission to invent a mapping. Display unavailable areas with a short reason. Put optional narrower choices behind **“Choose a smaller topic”**; do not require them.

Provide **“Mixed subjects”** separately. Its summary lists the actual included areas or an expandable complete list and says **“A mix from the available question bank; subjects may appear unevenly.”** A mixed pool with incomplete classification cannot promise exclusions it cannot enforce. For personal scoped games, omit unclassified questions when a positive selection or exclusion requires classification.

### Confirm once, then play

Example summary:

> **Geography**  
> MPSC & Mizoram recruitment papers  
> Speed round · up to 10 questions · 60 seconds total  
> Scored using official answer keys. Some questions may repeat.  
> **Play** · Change area · Practise without a timer

The current Speed game has ten selected questions, up to 15 seconds each within its absolute 60-second run. Explain that in expanded rules; do not promise time for all ten. Other modes retain their exact existing counts, timers and scoring. Remember the last confirmed choice per account and show it on return, with **“Play again: Geography”** and **“Change”**. A saved setting may prefill the visible summary; it must not launch a game or silently accept a changed scope.

## Preferences and adaptive suggestions

“I haven’t studied this yet” hides an area from personal recommendations and can add it to **“Leave out of my games”** only through an explicit action. These are preferences, not tests of ability. “Include again” is always available; one wrong answer never removes an area or demotes a student.

Exclusions are hard constraints on personal game construction. Resolve them through approved paths; if a canonical question matches any excluded area through an approved primary or related path, remove it even if it also matches an included area. Explain overlap when it noticeably reduces availability. Unknown classification cannot establish that an excluded subject is absent, so omit that question from an exclusion-constrained pool. Never apply exam-source inclusion from a different printed appearance than the displayed scoped source.

New activity may change future suggestion order, but cannot add an area to the confirmed choice, remove an exclusion, change a queue, or change a running game. Present **“You’ve also practised Polity. Add it to your choices?”** as an optional future-session action. No silent expansion after wins, errors, inactivity or a long matchmaking wait. Stale history means less confidence in the suggestion reason, not loss of permission to play.

During setup, refreshed counts may disable Play with an explanation. A changed shelf/path mapping or source membership requires a refreshed preview and explicit confirmation before a new start. Preference edits during a room affect the next game. Running contexts and displays remain frozen; actual loss of question eligibility follows the shared exclusion policy in the specialization plan. Pure label changes do not rewrite historical context.

## Cold starts and small pools

| Situation | Behavior and copy |
| --- | --- |
| No history or saved exam | “Start with an exam or a subject you know.” Show the exam picker and broad subjects immediately. No stream choice or diagnostic is required. |
| Only a few attempts | “We’re still learning what you practise. Choose any subject to play.” Keep manual selection available; no “low mastery” state. |
| Student studied offline | Accept their subject choice immediately; account evidence is unnecessary. |
| Exact exam/area has eight usable questions | “8 questions with official keys are ready; this game needs 10.” Offer Choose another area, explicitly broaden the source/parent, or ordinary practice. |
| Area has 10–19 usable questions | Enable Speed/Duel/private multiplayer as appropriate; Gauntlet explains that it needs 20. Cup needs 25. |
| Enough questions but frequent repeats | “This is a small question set; some questions may repeat.” Prefer less recently served IDs when possible, then fill from the same eligible pool; never claim unseen questions without evidence. |
| All selected questions excluded or unavailable | “There aren’t enough questions for these choices yet.” Keep choices intact and expose Change area / Manage left-out subjects / Practise. |
| No exact exam coverage | “We don’t have a game set for this exam yet.” Offer named broad subjects, not an automatically widened exam game. |

Keep the existing full-length mode requirements initially: 20 Gauntlet, 10 Speed/Duel/private multiplayer, 25 cup. Do not duplicate canonical IDs, shorten a ranked game without a new rules version, or fill with inferred, reviewed-unofficial or unkeyed answers. Practice may offer a different answer pool only through its existing clear provenance labels and assessment rules; it must not become a new official-score game by relabelling it.

## Duels that both students can understand

For the first release, the host chooses one named area and shares a code. The other student sees **“Geography · 10 questions · 20 seconds each · same questions for both players”**, can accept or decline, and both explicitly ready before start. Private party rooms use the same consent for all 2–4 participants. A code does not grant access to another student’s study history.

Later, add **“Find an area we can both play”** to private rooms. Each player privately selects acceptable named areas; their suggestions can seed this picker, but are not accepted automatically. Compute the overlap of those accepted areas, accounting for shelf aliases and ancestor/descendant relations, then apply both players’ exclusions and the one shared strict pool. Overlapping shelf counts must deduplicate canonical questions. If one accepts all History and the other only Indian History, propose Indian History when a reviewed mapping exists; do not fabricate a new common topic from unrelated tags.

Show common named candidates and counts, not “your opponent is weak at…” or private attempt totals. Choose one common candidate; both accept its exact preview. The intersection is of **areas each agrees to play**, not of previously answered question IDs. The latter would favor memorised questions and unnecessarily empty the pool.

If no candidate has ten questions, say **“No shared game set is ready for these choices.”** Offer each player the option to choose another area. No automatic mixed fallback or pressure to disclose studies. A broadened choice requires both players’ consent. For related-path questions, every applicable selected predicate and exclusion is evaluated consistently against the resolved shared selection; never construct a false same-path subject/topic combination.

Both receive the same immutable canonical IDs, order, options, timing and scoring policy. Apply one exclusion set to both at finalization. Personal adaptation can suggest the next room; it cannot change one player’s paper or points inside a duel. Changing setup creates a new context and clears readiness. Keep bilateral blocks, sanctions, active-session locks, cancellation, expiry and retry behavior.

Random matchmaking remains simpler: match exactly on the confirmed normalized context, including actual source scope, area and exclusions, counts/timers/scoring rules and context revision. Personal suggestion history does not enter the queue key. Different contexts wait separately. Show **“Waiting for someone playing Geography”** and Cancel / Play solo / Choose another area; never claim an invented opponent count, widen automatically, or add bots. Existing ten-minute expiry remains.

## Scores, points and cups

Preserve current server scoring: normal games award 100 plus up to 50 timing bonus for a correct answer; Gauntlet uses distance/streak/lives. Topic choice introduces no bonus multiplier. Do not infer ability from response speed, game wins or easier remembered questions. Normal tie rules remain disclosed and exact ties share rank; network timing is not a latency-neutral assessment.

Compare private duel players only within their common room. Solo results show the selected area and personal history, without combining different question draws into a claimed fair academic rank. Even identical topic filters do not make two random papers equivalent. Learning XP’s existing public board remains an opt-in activity board, separate from game scores and spendable reward points.

Retain first rewarded correct canonical answer = 10 XP + 1 point, once across study and games, under the shared 300 XP daily budget. Changing area, related path, mode, exam, opponent or retry cannot reset the claim. Forfeits get no game rewards; queueing, readiness, self-declared knowledge and wins alone earn none. Server snapshots, canonical claims, immutable receipt/reward locking and existing correction policy stay authoritative. Do not promise a fixed point payout for a game containing previously rewarded questions.

Keep the current weekly cup as **“Mixed subjects cup — same set for everyone”**. Personal topic adaptation and exclusions cannot customize a ranked cup. If saved exclusions conflict, show this before entry and require a deliberate **“Play the fixed mixed cup”** action for this event; preserve the preference for personal games. Declining leaves the student free to play solo or a private subject game. Do not say the cup honors their exclusions.

Subject cup tracks remain later work under the earlier plan: identical published track set, separate track standings, one entry across the event, and a shared correction/validity ledger before claiming final comparable rankings. Current room-by-room correction checks do not yet ensure identical exclusions for staggered cup entries. No cross-subject overall skill rank, wagering, prizes, bought boosts or new point economy is part of this change.

## Minimal delivery sequence

1. **Honest choices:** shared mode-specific pool eligibility, approved shelf/section resolution, one visible confirmed selection, explicit mixed choice, truthful sparse states and an immutable room context. Support exact collection/section source constraints through registered IDs. Retain the launch scope and current transport. This is useful without any personalization.
2. **Convenient suggestions:** saved exam shortcuts, recent area suggestions and account-owned include/exclude preferences. Reuse attempts and checkpoints; store no speculative mastery percentage. Clear personal state and stale responses on account changes. Do not make recommendations a dependency of starting a manual game.
3. **Shared consent:** private preview/readiness and exact-context random queues. Then add the optional private common-area picker when selection intersection and privacy contracts are verified. Keep ordinary host-selected private games available.
4. **Later only if needed:** deliberate custom mixtures with quotas, shorter separately named practice games, subject cup tracks, broader source scopes and richer learning models. Each needs its own contract; none blocks the first useful release.

New schema work would use new numbered migrations; existing applied files stay immutable. A room snapshot should include source/collection constraints, resolved selection and excluded paths, policy/mapping versions, rule/timer values, safe display labels and a normalized hash. Recommendation origin/reason may be stored privately for explainability, but must not affect a fair matching key or expose history. Preview and start share the same eligibility logic; creation rechecks transactionally and returns a refreshed conflict without allocating orphan membership or rewards. No tag reclassification, bank import, guessed difficulty, new transport or source adjudication belongs in these packets.

## Acceptance criteria for the future implementation

- **A1 — No taxonomy knowledge needed:** a new student can choose an exam section or a named subject and start an eligible solo game without selecting a stream, tag or subtopic. Featured Gauntlet follows the same flow. No first-visit empty selection becomes mixed.
- **A2 — Manual choice is authoritative:** a student with no attempts can play Geography; one incorrect result does not remove it. A stale or failed suggestion service leaves manual setup usable.
- **A3 — Evidence is honest:** one repeated canonical question cannot create three-item practice evidence; a checkpoint is labelled continuation; broad-only paths do not generate narrow suggestions; vocabulary recognition never becomes whole-subject mastery.
- **A4 — Sources stay explicit:** choosing a particular exam uses registered collection/section/paper membership. Broadening to other Mizoram recruitment papers requires a new visible choice. Global All exams cannot silently widen Games.
- **A5 — Exclusions hold:** any approved excluded path removes the question, including overlapping related paths; unclassified questions do not bypass an exclusion. Empty results show recovery actions without removing the preference.
- **A6 — Counts are usable counts:** fixtures at 9/10 and 19/20 gate the proper modes; missing required figures, invalid options, changed keys, duplicate canonical IDs and unsupported sources affect preview and draw identically. Ten selected IDs remain required even though Speed may time out earlier.
- **A7 — No surprise adaptation:** new study history, a mapping change, a parent change, account switch or a long queue cannot silently change the confirmed selection. Changed setup invalidates old readiness; reconnect restores the frozen context.
- **A8 — Shared duels:** History versus Indian History can produce a mutually confirmed Indian History game when supported. Disjoint choices or an underfilled intersection do not match. A shared area need not contain jointly attempted IDs. Players receive identical questions/rules and final exclusions.
- **A9 — Privacy and consent:** code preview reveals no private progress, keys or answer-bearing question preview. Both duel players accept before start; all current party members ready before host start. Blocks and Leave remain effective through preview, join, waiting and reconnect.
- **A10 — Queue isolation:** equivalent normalized choices match; different source scopes, exclusions or rules do not. Equivalent recommendation origins can match. Cancel/expiry release the active slot and no fallback occurs without consent.
- **A11 — Rewards remain once-only:** retries, rematches and selecting an alternate related path never re-award a canonical claim. Daily cap, no forfeit awards and public-board opt-in remain effective. Score, XP and wallet points remain clearly distinguished.
- **A12 — Cup boundaries are visible:** personalized preferences cannot alter an event set. A student sees a conflict with left-out subjects before entry and may decline. No personalized cup rank or fair cross-track winner is implied.
- **A13 — Recovery and access:** selection survives a stale-count failure; unfinished mocks resume in their runner; unauthorised/private history never crosses account changes. Keyboard controls, readable focus/error states, 44px targets, real 360px layout and reduced motion work. The timer is not announced every second.
- **A14 — Results tell the truth:** show area/source/rules and excluded-question denominators; distinguish repeat questions from new reward opportunities; offer Review answers, Practise this area and Play again. Cup review stays gated until close. Existing legacy rooms resume with only their actually stored context.

These are future acceptance checks, not test results. This planning session did not run tests, build, sync, deploy, inspect production accounts, change the bank or measure current game pool sizes.
