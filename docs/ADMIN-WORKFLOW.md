# Everyday admin workflow

Updated30October2026. Entry: `/admin/bank`.

## Start with a task

The owner's primary menu has five destinations:

1. **Home** — task cards, actionable counts and quick links. Bank totals/worker details stay in the collapsed system-status section.
2. **Review answers** — find a question, inspect its printed source, record the appropriate reviewed decision and continue to the next question.
3. **Learning tags** — find/select questions, preview subject/topic changes and submit through the existing review workflow.
4. **Review queue** — inspect submitted corrections, materials and reports together. Search, work type and stage are visible; priority/order are under More filters. Reset restores the default queue.
5. **Papers & exams** — manage coverage and printed paper identity. Use Add a source paper from Home or More tools for intake.

Subject-scoped reviewers get Home, Review answers and Community corrections as their primary destinations. Global inventory roles retain existing paper/tag access. Permissions continue to be enforced by the API. A bookmarked section outside the current role shows a clear return-to-home message and does not launch its data request.

Desktop **More tools** groups paper coverage, review/publication, community/content, accounts/settings and references. It opens when the current advanced section needs it. Mobile uses a labelled section picker with Daily work first, rather than a horizontal strip of21tabs. Old tab IDs and direct bookmarks remain supported, including `papers`, `quality`, `review`, `workflow`, `publications` and `rewards`.

## Resolve a question report

Open the report from the Review queue or More tools → Question reports.

- **Open question review** goes directly to the question inspector. Use the source and existing decision/review controls; use **Back to report** in the inspector to return to that exact report.
- **Resolve with publication** opens an inline form with publication ID and reason. The server still requires an applied publication for that exact canonical question.
- **Dismiss report** opens the reason form. Both outcomes record the existing audited resolution; cancelling records nothing.

Errors stay beside the form, preserve input and allow correction/retry. Reasons retain the server's20–2000character requirement; publication IDs retain its100character maximum. No new approval/publication shortcut or automatic bank edit was introduced.

## Release details

Frontend presentation and navigation only. Existing backend endpoints, MFA/roles, independent review, publication guards, source identity and bank authority are unchanged. No schema migration or API restart is required. The home page no longer mounts a second full publishing queue; open Review queue when needed. Reviewer subject/state filters and combined-queue filters stay in the URL for refresh/bookmarks.

Owner task cards remain boxed. Main admin gutters follow the shared12pxphone/16pxdesktop preference; sidebar236px,13.5pxnavigation,6pxnavigation radius and existing cream/ink palette come from the admin prototype. Phone task cards use two columns and queue counts use a compact row so controls appear sooner.

Evidence: reports/admin-workflow-20261030/STATUS.md. All write acceptance uses a disposable local database; no synthetic production reports, decisions or grants. Static backup on server: /tmp/admin-workflow-web-before-20261030.tgz.

## Usability and loading follow-up

Review answers uses one Review list selector (including written questions), one exam selector, search and subject. More filters retains every issue type, year, topic and exact paper; Clear filters stays outside it. Common UDC/LDC/Assistant choices survive a full-inventory error. Subject/topic choices wait for taxonomy; saved filter values remain visible while it loads. Changing a subject clears an incompatible topic.

Next and Save & next continue across 20-question page boundaries, selecting the next page’s first question only after its matching response arrives. Recent saved receipts remain visible. A pending search/year/filter change prevents selecting old rows or navigating using stale counts. Valid four-digit years and search drafts debounce; status/exam/page changes apply immediately. No navigation action modifies review or scoring state.

Home, combined queue, reports and inventory no longer wait for taxonomy. Subject/tag/grant tasks load it separately, with retry; permission forms never render incomplete subject choices. Identical concurrent admin reads share only their pending request, bounded to32entries; completed reads are removed. Writes, content changes and account changes invalidate pending reuse. Account generation checks reject old account responses. GETs have a15second header timeout; writes retain existing idempotency and are never automatically retried. The combined queue no longer delays initial/filter/page requests by200ms; only text entry is debounced.

Validation and current release: reports/admin-usability-20261030/STATUS.md.
