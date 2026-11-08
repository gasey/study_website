# Local SIWC five-question pilot

6 November 2026, Asia/Kolkata. This is a local draft-only smoke test, not a
production publication or a measured accuracy evaluation.

## Authorization and usage

The worker completed its own OAuth registration and signed identity checks, with
the granted `chatgpt.tokens.use.direct` scope. The account-specific catalog
includes `gpt-6.1-sol`; the configured reasoning effort remains `high`.
The owner confirmed that additional credit spending is disabled for the app.
That confirmation is recorded in private runtime configuration; no paid billing
setting was enabled or changed by this task.

This route counts against the signed-in account's existing Codex / ChatGPT Work
plan usage. It does not provide a second allowance. See the
[official SIWC user documentation](https://learn.chatgpt.com/docs/sign-in-with-chatgpt).
The worker does not read API-key environment variables or pool credentials.

## Stream compatibility correction

The first probe reached the provider but failed local validation. A second,
diagnostic probe recorded only sanitized event structure: completed message items
are streamed individually, while `response.completed.response.output` can be
empty. No raw tokens or response text were logged. The parser now retains only
`response.output_item.done` snapshots and releases them after a matching successful
`response.completed`. It still rejects partial streams, incomplete responses,
failed responses, unexpected models and conflicting item snapshots.

The third probe completed through the corrected normal client and returned the
expected sentinel. The three probes consumed plan usage; none created a draft.
All **42 worker tests passed**, including regressions for the observed stream
shape and the credit-confirmation inference gate. The existing five backend
integration tests passed previously against a disposable database.

## Scope and interpretation

The five inputs are the exact recovery-snapshot appearances listed in
`tools/mcq-solver/docs/phase-ab-validation.md`. They include dated regulations,
question-format defects and an unsupplied circuit diagram. Such cases must remain
uncertain/review-required; the pilot does not infer source correctness from a
successful JSON response. Every output is stored separately in the private local
ledger and requires human source/reasoning inspection. No source-bank answer,
published explanation, human sign-off or live contribution is changed.

The private authoritative draft service is implemented and tested, but has no
exposed route or unattended worker credential. Oracle deployment and live
contribution readback remain later acceptance work. No scheduler or larger batch
was started.

## Pilot outcome

The real `run --limit 5` finished with **five valid drafts, five flagged for
review, zero failures and zero pauses**. Two drafts select an option (one
uncertain and one self-reported confident); three explicitly cannot determine
an answer. All five retain `human_approval: null`. This is not two verified
correct answers: original-source and factual review still remain.

The unresolved cases concern slash-separated/ambiguous choices, a true/false
question with duplicate placeholder options, and an unsupplied circuit diagram.
The uncertain selection flags a version-dependent regulation. These model
diagnoses are review leads, not certified source or legal findings.

Results are retained privately in `~/.local/share/mcq-solver/jobs.sqlite` and
`~/.local/share/mcq-solver/review-20261106.csv` (five rows, no publication enabled).
The run used five question requests after three small probe requests, including
the two diagnostic/validation attempts described above. Exact provider token or
usage-percentage measurements were not retained and are not claimed.

The bank's SHA256 remains
`99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0`.
No real contribution or publication was created in the production website.
The revised MIT review ZIP includes the stream fix and 42-test suite:
`artifacts/personal-mcq-solver-review-20261106-r2.zip` relative to the parent
personal workspace, SHA256
`e51f6a86783c204a0a4c53509de98332140456e26e208bac8a3a2ab7fed8637a`.

## Source-inspection follow-up

The source review and private website draft page are now complete. See
[the release notes](solver-source-review-20261106.md). Four records need format
repair; the circuit supports a derived 3 Ω answer. Historical pilot outcomes above
are retained; this is not a five-MCQ accuracy score.
