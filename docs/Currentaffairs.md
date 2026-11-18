# Current Affairs section — design

**Status:** design, not yet implemented. Written 2026-11-16.
**Goal:** a Current Affairs section on study.hawayu.in showing (1) a daily news feed from free APIs/RSS and (2) daily MCQs auto-drafted from a YouTube current-affairs channel by a local open-source model, with every MCQ passing human review before publication.

---

## 1. Relationship to the existing `current-affairs` feature

The API already has `app/routers/current_affairs.py` (migrations 0064/0065). That is a
different feature: human-reviewed dated facts (officeholders, rankings) linked to
existing bank questions, with immutable revision history. **Do not overload those
tables.** This new subsystem gets its own tables and router, but copies the same
review discipline: `pending → published / rejected`, reviewer recorded, decided
drafts immutable.

Hard rule carried over from bank policy: **AI-drafted MCQs never enter the question
bank** and are never labelled as official/verified answers. They live only in the
Current Affairs section, labelled per `docs/PUBLIC-ANSWER-LANGUAGE.md`
(e.g. "Drafted from [source, date] — reviewed by staff").

## 2. News feed sources (no paid API)

Free RSS beats commercial news APIs (NewsAPI/GNews free tiers: ~100 req/day, no
full text, no redistribution rights):

| Source | Why | Access |
|---|---|---|
| PIB (pib.gov.in) | The source most exam questions trace to | per-ministry RSS |
| AIR News (newsonair.gov.in) | National + regional bulletins | RSS |
| The Hindu / Indian Express | Editorial current affairs | RSS headlines + `trafilatura` for full text |
| Mizoram DIPR (dipr.mizoram.gov.in) | State current affairs | scrape if no RSS |

Poller: Python `feedparser` + `trafilatura`, systemd timer on Oracle (same pattern
as `ism-oracle-bank-review.timer`). Dedupe by SHA-256 fingerprint of normalized
title+URL.

## 3. YouTube channel — verified findings (2026-11-16)

Target channel supplied by owner: **Current Affairs Updated**
(example video: https://www.youtube.com/watch?v=rf5DyW6VzLE).

- Channel ID: `UCI3bSml8bhxAsNHh-eQqJEQ`
- New-video detection feed (free, no API key, safe from cloud IPs):
  `https://www.youtube.com/feeds/videos.xml?channel_id=UCI3bSml8bhxAsNHh-eQqJEQ`
- Format: daily ~20-min video, "Nth <Month> Current Affairs | Daily MCQs".
  The video already *contains* MCQs with answers and explanations, so the AI task
  is **extraction/restatement, not invention** — far more reliable for small models.
- Captions: original is **Hindi** (`hi-orig`); a good-quality auto-translated
  **English** track exists. Verified by downloading `en` json3: ~3,200 words per
  20-min video; questions, correct options ("option B"), and explanations all
  survive translation. No Whisper/ASR needed for this channel.
- Transcript fetch **works from the home machine** (verified). Expect it to fail
  from Oracle: YouTube blocks datacenter IPs for caption downloads (429). The
  split below is therefore mandatory, not optional.

## 4. Pipeline

```
Oracle (timers)                      Home machine (cron, residential IP)
---------------                      -----------------------------------
poll RSS feeds        ─┐
poll channel XML feed ─┴→ ca_feed_items(status=new)
                                     pull items needing transcripts
                                     yt-dlp --write-auto-subs (en + hi-orig)
                                     flatten json3 → plain text
                                     Ollama qwen3.5:4b → draft MCQs (JSON)
                                     mechanical validation (below)
                                     push drafts to Oracle API
admin review UI: approve / edit / reject
publish → public Current Affairs section
```

### Extraction prompt contract (per ~800-word chunk)

Model outputs ONLY a JSON array of:

```json
{"question": str, "options": [4 strings], "answer_index": int,
 "explanation": str, "evidence": str, "distractors_reconstructed": bool}
```

- `evidence` must be a verbatim phrase from the transcript stating the answer.
- The spoken video often names only the correct option, not all four; the model
  reconstructs missing distractors and must flag that
  (`distractors_reconstructed: true`) so reviewers scrutinize them.

### Mechanical validation gate (pure Python, no AI — this is what makes a small model safe)

1. JSON parses, schema valid, exactly 4 options, `answer_index` in range.
2. `evidence` actually appears in the transcript (normalized substring match) —
   silently drops hallucinated questions.
3. Dedupe vs existing drafts with `pg_trgm` similarity (already enabled on `mpsc`).

Dropping 30–50% of raw generations here is expected and fine.

### Model choice (measured on the home box, 2026-11-16)

- `qwen3.5:9b` via Ollama: **too slow on CPU** — >9 min without completing one
  chunk. Not usable.
- `qwen3.5:4b`: the working candidate. **Throughput not yet measured** — the
  proof-of-concept run was stopped before finishing. Measure before committing;
  if one chunk takes >5 min, fall back to splitting chunks smaller (~400 words)
  or a hosted open-model free tier (e.g. Groq Llama) as an optional accelerator.
- PoC script: scratchpad `poc_extract.py` (fetch captions → flatten → prompt →
  validate). Reuse it as the seed of the real worker.

## 5. Copyright / attribution position

The channel's question *selection and wording* is their editorial work. Do not
republish their MCQs verbatim on a public site. The pipeline therefore:

- rewrites each question in our own clean exam English (the prompt already does
  this, since the auto-translation is messy anyway);
- treats the video as the *source lead* and displays attribution with a link to
  the video on every published item;
- keeps the facts (which are not copyrightable), not their phrasing.

Reviewer instruction: reject any draft that reads as a verbatim copy.

## 6. Schema sketch (new numbered migration; never edit applied ones)

```sql
ca_feed_sources (id, kind rss|youtube, url_or_channel_id, enabled, last_polled_at)
ca_feed_items   (id, source_id, kind article|video, title, url, published_at,
                 raw_text, transcript_lang, fingerprint sha256 UNIQUE,
                 status new|transcribed|generated|skipped)
ca_mcq_drafts   (id, item_id, payload jsonb, evidence_quote, model, prompt_version,
                 state pending|published|rejected, reviewer_id, decided_at,
                 distractors_reconstructed bool)
```

Same immutability trigger pattern as `current_affairs_revisions`: decided drafts
cannot be edited or deleted; corrections are new drafts.

## 7. API + frontend

- `GET /api/ca-feed?date=` — news items grouped by day, source badge, external link.
- `GET /api/ca-feed/quiz?date=` — that day's **published** MCQs, answered inline
  (same interaction as the bank list; prototype markup wins over README, per
  DESIGN-FIDELITY).
- Admin: `GET /api/ca-feed/drafts`, `POST /api/ca-feed/drafts/{id}/decision`
  (publish | edit-publish | reject) — staff auth, reviewer ≠ nobody, recorded.
- Web: one new route, two tabs — **News** and **Daily Quiz**.

## 8. Daily schedule

```
06:00 Oracle timer    poll RSS + channel XML → new ca_feed_items
06:30 Home cron       fetch transcripts for new videos
07:00 Home cron       Ollama extraction → validation → push pending drafts
any   Staff           review drafts in admin, publish
```

Running cost: ₹0/month. All components open source: feedparser, trafilatura,
yt-dlp, Ollama/Qwen, pg_trgm.

## 9. Open items before implementation

1. Measure `qwen3.5:4b` time per chunk on the home box (PoC was stopped mid-run).
2. Decide distractor policy: accept model-reconstructed distractors after review,
   or require reviewers to rewrite them.
3. Confirm which RSS feeds to start with (PIB ministry list is long — pick ~5).
4. Decide whether Hindi (`hi-orig`) transcript should be stored alongside English
   for reviewer cross-checking (cheap: one extra yt-dlp flag).
