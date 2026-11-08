# Completed saved tagging publication — 8 November 2026

The owner instructed “merge it and publish it” for 78,049 reconciled unique candidates
at commit `75eea6a532d4a68d801a54e16e134906c1f44040`, already on origin/main.
**Publication and verification are complete. Do not replay the frozen runs.**

## Current bank outcomes

| Outcome | Unique questions |
| --- | ---: |
| Published tagging corrections | 58,197 |
| Confirmed unchanged | 19,594 |
| Blocked with recorded reasons | 258 |
| No saved review in this pass | 4,334 |
| Total bank | 82,383 |

77,791 accepted tagging outcomes cover 94.4% of the bank, with zero stale outcomes.
This is owner-delegated acceptance of saved AI classification work, not independent
human inspection or answer verification. No new answer certification is implied.

The 258 blockers comprise 186 missing physical-page references, 25 invalid taxonomy
paths and 47 context/routing cases. The separate 4,334 includes alternate booklets;
absence from this pass does not establish absence of every earlier kind of review.

## Exact publication scopes

9,925 intended paths already matched source-bound live completions and were skipped.
The main immutable scope covered the other 68,124 targets. Four disjoint supplements
recovered original source bindings and supported context without expanding target IDs.

| Scope | Targets | Frozen SHA256 |
| --- | ---: | --- |
| [Main](publication/frozen.json.gz) | 68,124 | `2d9737104889f1f512412463ef403cb7abf0f130bc0ec507b438f855c40f5855` |
| [Document binding](publication/supplemental/frozen.json.gz) | 46 | `94ed9a37e7b9327cb03c4d4c162714dea27f18338fa9c1911387eafde9e7576f` |
| [Shared packet evidence](publication/supplemental-shared/frozen.json.gz) | 171 | `755c0b730c2c5caaa8f2f8c4f433321b4dba346607c8e5ad0c2f72ee4d76b382` |
| [Printed-year context](publication/supplemental-context/frozen.json.gz) | 45 | `3c25bcf73fef1da239b37db491a99a13ed74219acf8a9eaf9f7077162d9e5069` |
| [Existing LDC document registration](publication/supplemental-registered/frozen.json.gz) | 100 | `4bc77e000220a57eb847a031e869f74ef60f3a8fe0d8c49dcbe0fb0cf598700e` |
| [Final policy/context reconciliation](policy-final/frozen.json.gz) | 24 | `d04c5c84d806f20e98451d72dedfacda418bfa0f816725744f731f25f764db04` |

Hashes identify decompressed exact JSON bytes. Main plus four supplements finished
with 51,543 publications, 16,312 unchanged confirmations and 269 blocked targets.
The final 24-target reconciliation produced 14 publications and ten confirmations:
13 corrected already accepted classification policies and eleven unblocked supported
source-context cases. Publication instances therefore overlap; use the unique current
outcomes above, not the sum of historical publication instances, as coverage.

One existing LDC Paper-II PDF was registered only after its exact source hash matched
saved evidence. Its cover identity was inspected; the Tourism Paper-II cover supplied
an explicit June 2018 exam period for eleven supported contexts. These cover checks
do not claim new question or answer inspections. See [registration](publication/document-registration.json)
and [cover evidence](source-evidence/udc-tourism-cover.png).

## Verification and safeguards

Both [main proof](publication/verification.json) and
[final policy proof](policy-final/verification.json) passed. Every publication manifest
digest and live receipt was checked. All 82,383 question IDs, text, options, answers,
provenance and paper identities were preserved; only admitted taxonomy fields changed.
No question was added, removed or merged, no peer vote or answer decision was created,
and no export remained unapplied. Existing review/source holds were preserved.
The 78-paper / 6,931-question protection baseline passed every sync without reset.

Bank SHA256 proof chain:

- Before: `867a2d47ab70882516891c3c5c2b7f34db8990631d00e17b6cb2702328c3e44f`
- After main: `1c63502b38a3c6d2f2ee0fa8a106dc25546ea36d4801abdaa08b94009356a225`
- Final: `352908ec4e94b7cb3d63738700374b0a1e12d62c87082e80513863824b24da9c`

The [final unique outcomes](final-outcomes.json.gz) retain all 78,049 target dispositions.
Oracle runtime evidence remains in `/var/lib/ism-taxonomy-final-20261108` and
`/var/lib/ism-taxonomy-policy-final-20261108`. Preparatory drafts outside these listed
scopes were not executed and must not be replayed.

The serial guarded writer retains source checks, 100-decision admission groups,
bounded atomic synchronization, immutable manifests/receipts and privilege isolation.
Performance changes cache immutable parsed scopes and exact history keys while still
rehashing files and querying fresh source signatures. Ordinary API budgets remain
unchanged. Validation: 127 backend tests, 14 queue tests and two preparation tests.

The shared queue retains submitted evidence, marks current accepted outcomes complete,
and sends later publication blockers back to follow-up without reclaiming active work
or repeatedly invalidating newer submissions. All API/paper/document/review services
are active. Live health reports 82,383 questions and 13,898 scorable; Study responds 200.

Final [queue snapshot](queue-final.json): 258 follow-up ready, 1,366 new ready,
2,968 alternate-booklet targets, no active claims. A fresh remote bank/taxonomy
`--check` reports IN SYNC at the final hash, with the protection baseline intact.
