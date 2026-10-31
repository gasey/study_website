# Games and global search — 23 October 2026

## Delivered contracts

`/games` offers Gauntlet, speed, private/random duels, private 2–4 player rooms and weekly cups. Registered accounts play; guests can preview. All modes draw strict `v_scorable` questions, reject Community origins, duplicate/empty options and missing figures, and require a matching source appearance. Instructions, option emphasis, figures and source links travel with the snapshot. Subject filters use approved classifications.

| Mode | Rules |
| --- | --- |
| Gauntlet | Up to 20 gates, 25 seconds each, three lives; correct streaks add distance |
| Speed | Ten questions, 15 seconds each, absolute 60-second limit |
| Duel | Two players, ten shared questions, 20 seconds each; code or same-subject queue |
| Multiplayer | Two to four private players, host starts, ten questions, 25 seconds each |
| Weekly cup | Sunday 19:00–20:00 Asia/Kolkata, 25 questions, 30 seconds each, one entry per account; last start 19:47:30 |

Room clocks, choices, scoring, membership and immutable question snapshots live in PostgreSQL. A supervised two-second worker advances expired rounds with row locks/SKIP LOCKED. Visible clients poll every two seconds, back off on errors, and stop on terminal rooms. Reconnect restores the server state. Waiting rooms expire after ten minutes. Leaving forfeits rewards and immediately frees the user's active-game slot. Mock/game starts share an advisory lock. Replay receipts, immutable choices and unique active membership protect retries and races.

Normal scores award 100 plus up to 50 server-timed bonus per correct answer; Gauntlet ranks distance. Finalization locks canonical records and excludes questions whose answer, text, source context or appearance changed. Exclusions do not count as wrong. Only actual choices become practice attempts. Correct verified questions earn the existing 10 XP/1 point once per canonical question under the shared 300 XP daily budget; repeats across practice/games do not earn again. Forfeited players receive no rewards. Game scores do not create spendable coins or prize payments.

Correct answers stay hidden until a shared game ends; cup review waits until close. Existing direct answer and discussion/feed gates also suppress active game/cup questions. Public creator blocks apply to matching, membership views, search and cup standings. Only room members see participant handles/avatars; no public room directory or chat. Cup publication is opt-in and reversible; own private result remains visible. No emails or wallet balances in room DTOs.

## Global search

Header and `/search` search questions, public creator profiles, published material metadata, the user's own notes, joined private desks, published paid previews and public exam collections. All shows four results per category; category pages show twenty. Queries are parameterized, 2–120 characters, with bounded pagination. Question matches include approved subject/topic keywords. Search never returns answer fields, private notes belonging to someone else, unpublished material blocks, account emails or unjoined desks. Private/no-store responses and account-generation guards prevent stale private results after account switches.

Listings currently means published paid-content previews. It is not a new seller marketplace or checkout. Public desk discovery/classes remain off.

## Verification and operational limits

123 integration tests pass (one upstream AnyIO deprecation warning), including eight new games/search tests for server authority, reward replay, races, capacity, blocks, key changes, weekly clock windows and audience filtering. Production migration is rehearsed on a disposable clone before application. Browser checks use disposable synthetic accounts: Gauntlet refresh/lives, speed completion/reload, private room join/host start and own-note search. Screenshots prefixed synthetic are not real user activity.

The browser viewport capability did not change the actual 1280px viewport during the mobile attempt; those screenshots do not establish 360px coverage. Responsive CSS exists, but physical mobile verification remains outstanding. No public load/capacity or prize anti-cheat certification is claimed. Polling is intentional; WebSockets/Redis are not required for durable shared database state and may follow measured load. External sources/prior knowledge cannot be prevented. Final original game results are immutable; later bank corrections do not automatically rerank completed game standings. Cup timing is integration-tested with a controlled clock; the next real Sunday event has not yet occurred.

Future: Locate-on-map, run upgrades/cosmetics, sponsored prizes, full marketplace, capacity testing and real Sunday observation. Automatic MPSC notice collection with human approval remains in PLAN; no scheduler was created.
