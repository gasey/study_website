# Phase A and B validation record

6 November 2026. Implemented and tested locally; no live SIWC grant, inference or
Oracle deployment occurred. This report does not claim model accuracy or completed
production Phase B acceptance.

## Results

- `python -m unittest discover -s tests -v`: **39 tests passed**.
- `python -m compileall -q mcq_solver`: passed.
- `python -m pip check`: no broken requirements.
- `doctor` against the actual recovery bank: 81,627 questions, five eligible
  candidates, `auth_required`, eligibility `unconfirmed`, API-key adapter disabled,
  production writer not configured.
- `sync --dry-run --limit 5`: five candidates, zero writes, zero model requests.
- `sync --limit 5`: five local pending jobs, zero saved drafts.
- `export-packet --limit 5`: five blind source inputs exported with mode 0600 to
  `~/.local/share/mcq-solver/pilot-input-20261106.json`.
- Final local bank SHA256 matches discovery:
  `99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0`.

## What the five-question test establishes

The synthetic integration test enqueues five independent arithmetic fixtures,
uses a deterministic fake inference client, validates each output and commits
five separate review drafts. Repeating sync/run saves no duplicate drafts and
makes no additional inference calls. The source file remains byte-for-byte equal.
This tests orchestration and persistence, **not a hosted model's reasoning**.

Separate tests cover signed JWT verification (signature, issuer, audience, expiry,
nonce), PKCE/state checks, missing plan scope, revoked consent, refresh rotation,
distinct VM host identity, uncertain SSH transfer, and owner-only storage.
Streaming tests reject partial, failed, incomplete, malformed and wrong-model
responses. Queue tests cover stale hashes, duplicate IDs, lease fencing, bounded
backoff, Retry-After, usage pauses surviving restart, explicit resume and stop.
CLI tests cover no-write previews, API-key rejection, secret-safe diagnostics,
offline import idempotency, CSV formula escaping and overwrite prevention.

## Real queued identities

| Appearance ID | Version hash |
| --- | --- |
| `443a88ce9d7314ac8aa1` | `fd19b3fe0dfbd603b60d2527cc3b243a113acd6777be1f1d49d2e672dfa36708` |
| `3196372f962e3265b42d` | `23855f03da9abea0e821046c893b0f49d9520408ca6021952808a6ede9cee785` |
| `d9e29d48b9814985f74f` | `db3297460a6604dd0214fed97beb1133b7d3e37ecab08788b7e7c7ed9b232496` |
| `417ad12713a46c088ad5` | `18b560a1ed9fafa49209df437ab865f9c35ea5a03db4546935014cabfb2d3b82` |
| `b494509273a6c6ba1364` | `58ef460e2f88aef353dd0875552c444ecb5af724fda0cd23d19ef7bfad9dd82d` |

These are the first five eligible complete MCQs in snapshot order, not a
stratified evaluation set. No synthetic answer was attached to these real records.
The queue lives outside the repository at `~/.local/share/mcq-solver/jobs.sqlite`.

## Next acceptance gates

Confirm actual worker eligibility and obtain explicit owner browser consent.
Confirm this app cannot use additional ChatGPT credits, then discover the account
catalog and complete the streamed probe. Run the five-question local draft pilot
and inspect original sources. Before claiming a draft in the **existing live bank**,
implement/test its restricted authoritative-source reader and contribution writer.
The production website credential, deployment path and dedicated VM service user
have not been provisioned or borrowed. No scheduler, paid billing or account
rotation was enabled. See the README for commands and recovery limits.
