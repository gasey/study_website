# Navigation and loading — 24 October 2026

## Navigation rule

Community's For you, Following, MCQs, Questions & Doubts and Materials are filters within one `/feed` workspace. All five tabs, the Community heading and side rails remain visible. Query parameters make the current filter shareable; switching tabs replaces filter history rather than creating many Back steps. Arrow keys, Home/End and a labelled panel support keyboard navigation. Material filters preserve the selected Community tab. Full lessons, discussions and question details remain destinations; material cards opened from Community carry a validated local return location. Standalone materials and MCQ pages still serve existing bookmarks.

## Delivered

- Lazy load the screens; keep header/footer navigation present while code loads. Pointer and keyboard intent warm same-origin route code, respecting Save-Data/2G. This does not prefetch personal API data.
- Load legacy exam CSS with the exam module. Retain its styling and the current 2×2/list answer controls.
- Back/Forward restore the former scroll position after asynchronous content expands. New routes start at the top; same-route filters preserve position. Hash anchors wait for their targets. User scroll cancels deferred restoration.
- Chunk/render failures show a manual reload action; no automatic reload loop. Standard GET requests have a 15-second retryable timeout. Writes are not automatically timed out/retried.
- Header uses the small aggregate progress response, refreshed by answer/mock/game completion, account changes and focus. Account/session and Inbox checks no longer repeat solely because the route changes. Inbox retains its visibility-aware poll.
- Public catalog reads coalesce and cache for 30 seconds per scoped URL in the current document. No browser storage. Only taxonomy, collection list and subject-shelf metadata qualify; question records, answers, histories, mocks and Inbox data do not.
- Backend caches public collection counts, taxonomy and shelves for 10 seconds, with per-key concurrent request coalescing, scoped/pool-separated keys, failure eviction and bounded entries. Successful admin/collection writes invalidate it. Answers and scoring eligibility still query current data.
- Deploy default order corrected to API before web. No schema migration, bank/answer changes, production synthetic records or Caddy changes.

## Measurements and verification

See `reports/navigation-performance` for exact byte counts, HTTP samples, logs and deployment manifest.

- Root JS before: 496,360 bytes / 144,449 gzip. After: about 229 KB / 74.5 KB gzip (54% fewer raw bytes, 48% fewer gzip bytes).
- Root CSS before: 114,958 bytes / 21,003 gzip. After: about 69.6 KB / 13.0 KB gzip. Exam-specific CSS arrives when needed.
- Collection HTTP samples before: 1.93–1.96 seconds. After: 2.02 seconds cold, 0.22–0.24 seconds warm.
- Taxonomy: 1.06–1.07 seconds before; 1.07 cold, 0.29–0.32 warm after.
- Shelves: 1.37–1.39 before; 1.41 cold, 0.22–0.32 warm after.
- 159 isolated backend/offline tests; five Node navigation/cache tests. Production frontend build passes. One existing upstream deprecation warning remains.
- Local browser: exam browse, source styling, new-route top, Back restoration, focus switching, account sign-in, Desk, all Community tab destinations and keyboard Home. Live: Materials/Following in-place tabs, lesson return to selected tab, no console errors. No production answer or proposal submitted.
- API/static SHA256 manifest confirms local and server artifacts. Health remains 77,751 questions / 12,490 strict-scorable. Bank remains IN SYNC. Family site final 200 after redirects.

## Limits

Cold catalog SQL remains roughly 1–2 seconds; warm cache improvements are not cold-query improvements. Timings are a few serial network samples, not a capacity benchmark or every-page certification. Browser verification used the current desktop viewport, not a physical mobile device. Catalog counts may lag external bank changes by up to approximately 40 seconds across both cache layers; scoring/questions remain fresh. Deploying new chunks can require a manual reload for an already-open old document if its former chunk was removed.

## 25 October 2026 — Read materials without leaving the learning context

Material cards and public material search hits use `read_material` in the current route. A native modal dialog keeps the background list mounted, traps focus and supports Escape/Close/history, with an explicit full-page option. Reader access still comes exclusively from the existing materials API. Private-note search results retain their Study Desk destination. Related materials expand and paginate in their current exam/subject/feed context; saved materials live within Library. Notes are a kind of shared Material; private work and publication editing have distinct purposes.

Collection detail responses group readiness/section counts, reuse scoped question IDs rather than repeatedly scanning launch views, use transaction-local `jit=off`, and share the short public catalog cache. Learner data is never placed in that cache. See the UDC release report for measured samples and limits.

## LDC paper drill-downs

Paper cards now link directly to their current exam's answer-state list and study pool, using `#exam-question-browser` to focus the learning area while preserving browser-back restoration. Reviewed paper subsets are discoverable without first opening every paper. Paper readiness fields come from one grouped query, not a separate request for each card. An unavailable paper gets a recovery link; pagination shows loading and supports retry without retaining the prior page's questions under a new page number.

## 26 October 2026 — Question pagination

Bank and subject browsing request 25 questions per page; exam study practice requests one. The shared pager keeps Previous, a bounded set of page numbers and Next on one desktop row. Small screens show Previous, position/total and Next. Controls have 44px minimum targets, keyboard focus and current-page labels. Exam catalog cards remain eight per page, past-paper cards nine; those metadata grids do not download the question bank.

Search, source/year/subject/topic/paper/pool filters and positions survive refresh in URL parameters. Filter edits replace the current history entry and reset position; page jumps add history entries. Existing route restoration handles Back/Forward scroll. Out-of-range pages clamp to the matching result count. Current questions disappear during a replacement fetch so an old answer cannot be clicked under a new position. Practice preserves its in-memory picks while changing position and keeps the existing account checkpoint and answer-save endpoints. A successful answer in an unseen/wrong personal queue refreshes the current position before advancing, avoiding skipping the next remaining item.

Question-list metadata uses a separate twelve-entry memory cache with a 15-second lifetime and request coalescing. Scope is part of its key. Mutations, authentication/content changes and progress events invalidate it; private study-status queues bypass it. It never stores question pages in local/session storage or caches answer-result requests. Each screen may request only its next page, without recursion; hidden documents, data-saving connections and 2G connections skip speculation. Prefetch failures cannot replace the visible request's error. This does not claim zero latency or an account/device performance benchmark.

Local TypeScript/Vite build and live guest browser checks recorded in `reports/source-pagination-review-20261026`. No synthetic account, answer submission or mock attempt was created for these checks. Signed-in checkpoint persistence and the changing unseen/wrong queue branch retain existing APIs but were not exercised with a manufactured user session.
