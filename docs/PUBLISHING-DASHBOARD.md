# Publishing dashboard and material review

Implemented2026-10-22. Extends existing reviewed bank and CMS workflows; does not grant new permissions or automate approval.

## Owner workflow

`/admin/bank?tab=workflow` and owner Overview show a unified derived queue of submitted/in-review/accepted/publishing/failed corrections, submitted/changes-requested materials, open/confirmed question reports, open material reports and open creator reports. Author drafts, withdrawn/rejected corrections and resolved reports do not enter this pending queue.

Owner-only GET `/api/admin/bank/work` returns global type counts, filtered total/urgent/awaiting-author counts and paginated20-item rows (limit<=50). Filters: kind, stage, priority, search(title/author/ID), subject_id; ordering priority/oldest/newest. UI filter/search/page state persists in query parameters. Each item links to its exact material, correction, question report, material report or creator report. Existing subject-scoped reviewer queues remain separate; the combined queue requires an active all-subject owner grant. Private/no-store response caching; no lesson bodies or new copies of bank data selected.

Priority is explicit and deterministic: urgent=failed publication; high=wrong-key/outdated question reports, copyright material reports, harassment/impersonation creator reports; normal=remaining pending work. Priority does not prove allegations or change scoring, publication rights or rewards. Default priority order breaks ties using creation time and kind/ID. Materials use their first stored revision timestamp because materials has no native created_at column; migrated legacy records therefore reflect their first stored revision. Other types retain source creation times. Type counts are global; summary cards reflect current filters.

## Material inspector

`/admin/bank?tab=content&material=:id` selects the exact current draft even if it is outside the filtered queue. Queue supports title/author/ID search, workflow state, oldest/newest and pagination. Empty pages retain the correct total. Deep links can select a material report or creator report by ID, including older reports outside the default first page.

Inspector tabs: Publication preview (safe structured rendering and public excerpt), Compare revisions, Review history. Compare defaults to last published revision, or previous draft when no distinct published revision exists; first drafts compare against empty. Select any loaded historical revision or the current published pointer. Metadata changes, added/removed/edited/moved blocks and per-block before/after rendering are shown; structured equality sorts object keys and retains array ordering. Canonical-question blocks remain noninteractive in administrative previews. Comparison never selects the version to publish: decisions always send current expected_version and review the server-locked exact draft. Revisions remain immutable and only submitted work can publish. Previously approved readers stay on their existing pointer while drafts change.

Owner enters feedback in an inline form for publish/change-request/archive/restore; no native prompt dialogs in the material workflow. Action label names the target revision. Errors preserve the input; stale reviews offer a reload. No bulk approval, quorum bypass, auto-archive or reward changes. Existing MFA still protects staff mutations. Review history displays the latest30 material events and original timestamps/revision/reasons; older content revisions are immutable, with the latest30 revision choices plus published pointer available.

## Author feedback and inbox correction

Draft API includes the latest publish/change-request/archive/restore decision via a separate indexed lookup, so its feedback does not disappear behind later autosave events. Authors see its revision, date, reason and resubmission guidance above the editor. Decision notices link to `/studio/:id#review-feedback`; existing notifications remain account-owned. Publishing feedback is not email delivery.

Browser rehearsal found an existing route defect: /inbox redirected to /notifications, but only /contribute/notifications existed. This packet adds the missing /notifications alias, preserving the old route, and replaces the header's hard-coded0 with account-owned GET `/api/review/notifications/unread`. The count has private/no-store caching, reloads on navigation/auth changes and updates after marking a notice read; no polling or guest count fabrication. The previous CMS documentation's claim of a working /notifications page is corrected by this implementation.

## Storage and acceptance

Migration0037 adds material_events(material_id,id DESC) for bounded feedback/history lookup; no new workflow tables/states or bank data changes. Never edit after apply. GET work uses source tables directly. Existing CSRF, staff MFA, body limits, report resolution and publication/reward integrity rules remain.

Tests/evidence in reports/publishing-dashboard cover owner-only access, filters/ordering/empty-page totals, exact report targets, immutable revision sources, author/outsider access, latest feedback after35later draft events, notice ownership and unread decrement. Synthetic browser checked owner queue, exact material deep link, revision2 against published1 (2metadata/2block changes), inline change request, separate ordinary-author login, notification and feedback editor. Original live publication is unchanged by that request. Screenshots show disposable synthetic accounts/content, not production moderation decisions. Local fixture uses explicit ISM_CMS_DEMO=1 only to bypass staff MFA in the disposable database; real owner enrollment/session/security unchanged.

Remaining broader release gates: load/full accessibility/security/restore matrices, real independent bank review and adjudication, advanced module ingestion, deferred mail and future paid creator commerce. This packet does not claim those complete.
