# Free-only current-affairs sources and generation — 16 November 2026

Implementation update: RBI collection and Gemini/Supadata adapters were deployed;
PIB/DIPR public-page collection and daily/weekly brief implementation now extend
that release. Gemini/Supadata remain paused
pending private keys, per the owner's instruction. This document preserves the
research findings below; current setup and verified limitations are in
[the operations guide](FINNA-CURRENT-AFFAIRS-SETUP.md) and
[release receipt](../reports/current-affairs-free-release-20261116/README.md).
Use [the completion checklist](FINNA-CURRENT-AFFAIRS-PLAN.md) for current status;
the proposed order below preserves the earlier research, not the live checklist.

Owner requirement: no OpenCode subscription now or in future. Consider only
zero-paid-API operation for this pipeline unless the owner explicitly changes the
budget. Never silently upgrade, buy credits, enable auto-recharge or fall back to a
paid model. When a free allowance disappears, pause that provider and show why.
The deployed OpenCode adapter already accepts only two explicit free model IDs.
This research did not create accounts, add credentials, change providers, publish
content or install another service.

## Recommended starting configuration

Test **Gemini 3.8 Flash on a billing-disabled Free-tier project** as the first
alternative. Its current pricing table lists free standard input/output. The
existing text-transcript adapter is already available, but has no configured key.
A separate YouTube URL adapter is proposed, not implemented or proven working.

Google documents direct public YouTube video input. The URL feature is currently
a no-charge preview with a free-tier ceiling of eight video-hours/day, alongside
model/project token and request limits. It is limited to public videos. This is
an official input path that could avoid needing Oracle to fetch captions. It must
be tested against the supplied video with the selected free model; do not promise
that the daily video ceiling is the actual account quota or guaranteed capacity.
The documentation's example model may be paid: keep the actual request explicitly
pinned to a currently free model and do not copy example model IDs indiscriminately.
Free-tier source inputs/outputs may be used to improve Google's products; send
public source content only, never private learner records or credentials.

For retained timestamped caption evidence, test **Supadata Free, native mode**.
Its recurring free allocation is 100 credits/month without a card. Existing native
transcripts cost one credit; generated transcription costs two credits per video
minute. Therefore use `mode=native`, `text=false`, bounded requests and a monthly
ledger. Do not use default `auto` mode, which can consume the allowance by generating
missing transcripts. An unavailable transcript can still cost one credit. At
roughly one or two videos/day, native-only collection may fit the allowance; this
is a capacity estimate, not a success guarantee. No Supadata key was configured
or authenticated transcript request executed in this research.

Keep OpenCode free as an optional existing provider, without depending on a future
subscription. Keep manual caption upload as a recovery option. A model's direct
video interpretation must be attributed as model video analysis, not falsely
recorded as a publisher caption download or an exact immutable transcript.

## AI alternatives

| Service | Current free option | Fit and limitations | Checked source |
| --- | --- | --- | --- |
| Gemini API | Selected models include free input/output; Gemini 3.8 Flash currently qualifies | First candidate for public Hindi recap analysis and structured English drafts; actual account limits and quality need testing | [Pricing](https://ai.google.dev/gemini-api/docs/pricing), [video input](https://ai.google.dev/gemini-api/docs/video-understanding), [limits](https://ai.google.dev/gemini-api/docs/rate-limits) |
| Groq | Free plan with per-model requests/tokens limits; free-plan excess returns 429 rather than a charge | Text-draft alternative. Several listed free text models have an 8K-token/minute cap, so long Hindi transcripts need source-preserving chunks. Uploaded authorized audio can use Whisper; this does not obtain a blocked YouTube video | [Limits](https://console.groq.com/docs/rate-limits), [free-plan FAQ](https://community.groq.com/t/do-i-get-charged-for-anything-on-the-groq-free-plan/832) |
| OpenRouter | `:free` models: 50 requests/day without purchasing credits, 20/minute; failures count | Useful optional free provider. Pin an eligible model or `openrouter/free`; exclude paid fallbacks and `openrouter/auto`. This free limit is distinct from the higher allowance that requires buying credits | [Free models](https://openrouter.ai/collections/free-models), [limits](https://openrouter.ai/docs/api/reference/limits) |
| Cloudflare Workers AI | 10,000 neurons/day on Workers Free | Alternative for small jobs; neurons measure compute, not a fixed number of articles. Some models require a paid billing method even though the platform has a free allowance: select only a Free-plan-compatible model | [Pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) |
| Local model through Ollama | Local inference endpoint, without a hosted API key | Removes reliance on hosted free-model quota. Hardware, power, latency and model licensing still matter; benchmark before sharing CPU/RAM with production. No local model installed or quality-tested here | [Local API](https://docs.ollama.com/api/introduction) |

These are free plans available at the research date, not promises of permanent
free availability. Provider access is not evidence of accurate exam questions.

## Current-affairs content sources

RSS is a machine-readable feed and is sufficient for unattended discovery; a
paid JSON API is not necessary for every source. Keep collection, factual evidence
and model generation as separate steps. A search API result is a discovery lead,
not a checked source statement.

| Source | Interface and intended coverage | Actual read-only check |
| --- | --- | --- |
| RBI | Official press-release and notification RSS, no API key; economy, banking, policy and regulations | Both local and Oracle returned valid feeds with ten entries each. Press-feed first timestamp was 16 November; notifications 11 November. Publication timestamps lack an explicit timezone, which a connector must record/normalize explicitly rather than guess silently |
| PIB | Official advertised RSS; central government schemes, appointments, science, ministries | RSS index accessible, but its release link redirected and returned a valid empty feed in both environments. A PIB collector is not ready merely because HTTP status is 200; use a reviewed source-page connector or resolve the official feed before enabling it |
| Mizoram DIPR | Official public press-release website; state/local current affairs | Homepage accessible from both environments. No RSS/Atom link advertised in the inspected HTML; no documented public API identified. Needs a bounded public-page collector, with source dates/URLs and source-structure checks |
| GDELT DOC API | Keyless JSON article discovery for India/world coverage | Official API documented. One bounded article-list test timed out locally and on Oracle. Keep optional until operational reliability is established; results contain links/metadata, not a primary-source fact guarantee or blanket article reuse license |
| Akashvani / News on AIR | Potential national/regional source | Homepage timed out from both environments. No feed endpoint enabled or claimed working |
| World Bank and other report publishers | Structured statistical updates and report editions | Reuse Finna's existing Stats work; these series have reference periods and publication lags and should not be labelled daily news |

Exact URLs, response formats, sizes, publication dates and retrieval timestamps
are saved in `reports/current-affairs-api-research-20261116/local-probes.json` and
`oracle-probes.json`. These probes made public GET requests only and changed no
production application, scheduler, database or bank content.

## News APIs excluded from a free production recommendation

- **NewsAPI.org Developer:** its terms limit free use to development/testing and
  expressly exclude staging/production, including internal deployments.
- **Guardian Developer:** free access is non-commercial; a monetized Finna product
  cannot assume it qualifies for that plan.
- **NewsData.io:** current free pricing advertises 200 credits/day, twelve-hour
  delay and testing/personal projects. Some provider blog posts make broader
  commercial-use claims, while the terms describe a personal/internal-business
  license. Treat public-app use as unresolved until the provider clarifies it;
  do not recommend it as an established free public-production license.

[NewsAPI terms](https://newsapi.org/terms),
[Guardian access](https://open-platform.theguardian.com/access/),
[NewsData pricing](https://newsdata.io/pricing),
[NewsData terms](https://newsdata.io/terms).

Do not copy full publisher articles, answers or images simply because a feed/API
can return them. Keep source links and appropriately sourced original study notes.
No public-ready exam quiz API with sufficient verified free-production terms and
source accuracy was established by this research.

## Proposed Finna implementation order

1. Retain the deployed private queue, global attempt limit, source identity,
   validation, audit and review boundaries. Add a provider policy with explicit
   free model IDs, quota visibility and no paid fallback. Keep new keys server-side.
2. Test Gemini text generation against the saved supplied transcript, then direct
   YouTube URL input separately. Compare numbers, names, reporting dates, timestamp
   references and MCQ answers against the actual source. Record output quality;
   existing synthetic schema tests do not establish model accuracy.
3. Test Supadata's native-only timestamped output as another collection provider,
   storing its actual language, retrieval method and immutable cue hash. Add a
   monthly credit budget and stop before an upgrade/recharge would be required.
4. Add generic RSS/source-item staging with a new immutable migration rather than
   inventing YouTube IDs for RBI releases. Start with RBI; separately finish the
   PIB and DIPR collectors. Retain source publication, effective/reporting and
   retrieval dates, language, source URL, content identity and citation spans.
5. Deduplicate the same event across a video and official release. Filter for exam
   relevance, prepare a bounded daily/weekly brief and supported quiz/card drafts,
   and send them through existing private review/publication flows. Fewer supported
   questions are preferable to a forced daily quota. Headline-only inputs are not
   enough to certify detailed claims.

Primary transcript references:
[Supadata plans](https://supadata.ai/pricing),
[transcript modes and credit costs](https://docs.supadata.ai/get-transcript),
[YouTube caption-download permissions](https://developers.google.com/youtube/v3/docs/captions/download).

Primary source-feed references:
[PIB feed index](https://www.pib.gov.in/ViewRss.aspx?lang=1&reg=1),
[RBI RSS index](https://rbi.org.in/Scripts/rss.aspx),
[GDELT API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/amp/),
[Mizoram DIPR](https://dipr.mizoram.gov.in/).
