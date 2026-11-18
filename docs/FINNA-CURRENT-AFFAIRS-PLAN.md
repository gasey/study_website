# Finna current-affairs automation — completion checklist

Scope: free-only sources and generation, YouTube evidence, private notes/quiz/card
candidates, source-bound daily/weekly briefs and owner review. Provider keys are
explicitly deferred by the owner. No subscription or paid fallback is authorized.

## Implemented

- [x] Selected YouTube channels, scheduled discovery and private evidence queue.
- [x] Existing downloaded captions retained with language, origin and cue hashes.
- [x] Supadata native-only adapter, Free-plan check, monthly reservation budget,
  no generated-transcription fallback and clear unavailable/quota states.
- [x] Gemini text and direct-video adapters with free-model/project guards.
  Model video analysis remains distinguishable from publisher captions.
- [x] Optional OpenCode free models without subscription dependence.
- [x] RBI RSS, PIB release pages and Mizoram DIPR page collectors; bounded fixed
  URLs, source structure/date checks, partial-failure audit and immutable revisions.
- [x] Daily and rolling seven-day packets using Asia/Kolkata publication windows,
  whole-source input limits, keyword relevance triage and visible coverage bounds.
- [x] Exact passage deduplication retaining all source references; AI semantic
  claim grouping/conflict warnings prepared for when generation is configured.
- [x] Source-cited brief notes plus quiz/card candidates with shared daily attempt
  budgets and fair daily/weekly scheduling; collection works without AI keys.
- [x] Owner website source/video/brief tabs; evidence inspection, retry, reject and
  private CMS handoff, with stale-source checks and idempotence.
- [x] Owner/MFA/CSRF, assessment reveal and mobile credential boundaries; immutable
  packet inputs and protected generated payloads. No automatic bank/scoring edits.
- [x] Synthetic integration tests, UI checks and local production build.
- [x] Final production migration/worker/browser verification for the brief release:
  40 retained releases, two packets, restricted grants, matched deployed hashes,
  96 backend checks, three UI checks and both-site health.

## Explicitly deferred external activation

- [ ] Configure a private Gemini key on a billing-disabled Free-tier project.
- [ ] Configure a private Supadata Free key if native-caption retrieval is wanted.
- [ ] Run live generation against the supplied saved transcript and source packets;
  inspect names, dates, figures, translation, semantic grouping and proposed answers.
- [x] Retest server-side YouTube RSS access: discovery succeeded on production
  runs 8 and 9 after earlier transient HTTP errors. Failures remain visible if they
  recur. Supadata/direct-video account access still needs the respective keys.

The code can be complete while these live account/quality checks remain pending.
No automated test substitutes for inspecting actual generated source claims.
Publication is a separate existing owner review action, never an automatic step.
Learner content uses the existing published material APIs on web/mobile; the new
automation workspace remains an owner website tool.

Optional future coverage includes GDELT/Akashvani, additional publishers and a
benchmarked local model. These are not prerequisites for this implementation and
are not claimed active or reliable.

[Private key setup and operations](FINNA-CURRENT-AFFAIRS-SETUP.md).
