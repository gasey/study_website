# Pilot source review and private draft page

The five original papers/pages were inspected after the SIWC pilot. Four records
are malformed MCQ representations: two original blanks without printed choices,
one five-part either/or question collapsed into four options, and one five-part
true/false question with placeholder choices. They are held from further local
solver selection. These records cannot form a five-MCQ accuracy evaluation.

The circuit source supplies the missing diagram: removing the load and shorting
the independent voltage source gives 4 Ω || 12 Ω = 3 Ω, printed option A. It is a
derived answer proposal, not an official key. The GFR paper explicitly names the
2005 edition; the original header resolves the pilot's edition uncertainty.
The object-head question prints Rule 74, while the supporting provision is Rule
73. The source text is retained and the discrepancy documented.

Detailed findings and source images are in the parent workspace artifacts:
`mcq-solver-source-review-20261106.md` and the standalone image-embedded HTML
with the same basename. Original local model drafts remain unchanged.

## Private website integration

Deployed route: https://study.hawayu.in/admin/mcq-solver

`GET /api/admin/mcq-solver/review` requires an owner/publisher account. It returns
the curated source findings without the original raw model draft. Source and
registered PDF hashes are compared with the authoritative Oracle database.

`POST /api/admin/mcq-solver/drafts/{appearance_id}` requires real recent MFA,
same-origin CSRF protection and a current source-version/hash. It only accepts
the five curated appearances and creates ordinary contribution drafts: four
defect proposals and one derived-answer proposal. Exact retries are idempotent.
It cannot infer, submit, approve or publish. Human approval remains null.
No production contribution was created by an operator script or forged session.

The focused deploy script `scripts/deploy-mcq-source-review.py` installs only
the new router, two services and curated data, and appends the router registration
to the existing remote main module. It keeps a root-only rollback backup and
restores files on import/health failure. No migrations or bank content writes.
The frontend was built locally and released using `scripts/deploy.sh web`.
API backup: `/srv/api/.release-backups/mcq-source-review-1793954946603675781`.

## Verification

- 43 worker tests pass, including holds blocking selection and inference.
- 10 backend tests pass against disposable PostgreSQL: real auth/role/MFA/CSRF
  gates, stale source/PDF rejection, strict body validation, answer/defect drafts,
  idempotency and no canonical/publication/decision/credit changes.
- TypeScript and Vite production build pass.
- Live private GET returns 401 without a session. The deployed browser route
  renders its sign-in requirement. An authenticated browser save was not performed.
- Both study and shared family website health checks pass after deployment.
- Recovery-bank SHA256 remains
  `99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0`.

No new hosted-model calls were made for source inspection or deployment. No paid
API configuration, published answer or published explanation was changed.
No unattended scheduler or larger inference batch has been enabled.

The updated standalone MIT review archive is
`artifacts/personal-mcq-solver-review-20261106-r3.zip` in the parent workspace,
SHA256 `76b8ff0b110ac1b2a80d8c8edbbbac70f81c620d1bf8f0938861e451516c87be`.
It contains the source hold support and 43 tests, without question-bank content,
source-review findings, website code or credentials. Earlier ZIPs are unchanged.
