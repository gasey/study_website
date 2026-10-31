# Question discussions

Delivered scope: question-linked doubts, explanations and flat replies shared by the bank, exam browser, paper viewer, Arithmetic/Reasoning and subject practice. Each canonical question has one shared discussion timeline. Community-authored MCQs remain a separate published-question catalog.

## Learner workflow

Use **Discuss / Ask a doubt**, **Share question**, or **Suggest correction** beside a question. Discussion opens inline and loads only when requested. Sharing copies a direct question link with the paper/exam context when supplied; if clipboard access fails, a selectable URL appears. Publishing a top-level topic also makes it eligible for For you/Doubts; no duplicate feed post or separate copy of the question is created.

Checkable MCQs retain the existing answer-first gate. Questions without a uniquely checkable answer, and descriptive questions, support an explicit signed-in disclosure acknowledgement. Acknowledgements never create attempts, grades or rewards. Reading threads, replies, citations and feed content is blocked while the same user has that question in an active mock. The new session-based moderation queue also excludes the moderator's active mock questions.

Signed-in accounts can write plain text, attach up to five HTTPS references, reply, mark another person's post helpful, report conduct or withdraw their own post. A doubt's author can accept one other person's published reply. Acceptance and votes are community feedback; neither changes an answer or pays XP/points. Replies are one level deep and paginated, with an accepted reply first. Topic pages have 20 entries; direct links can focus a topic/reply beyond the current page. Shared option order is unchanged.

The first three approved posts require moderation; pending posts are visible only to their authors and the owner queue. Withdrawals hide a post, and withdrawing/hiding a root also removes access to its replies through learner routes. Post text, references and source context are immutable; withdraw and add a clarification to correct a discussion post. Historical anonymous-to-account authorship adoption remains compatible.

## Corrections and sources

**Use in correction draft** fetches a published post through the gated API, validates its canonical question against the selected question, and prefills the rationale plus retained reference citations. It carries supporting source links and the original appearance when known. Long posts are explicitly cited as excerpts with a link to the complete thread. Production citations use the same HTTPS origin; plain HTTP development retains the internal citation path in the note instead of creating a URL rejected by the evidence policy.

The proposed answer begins at the current bank baseline. Authors must select and justify any change. Saving creates an ordinary editable contribution draft; independent review, official-document mapping, MFA, publication and scoring rules still apply. Discussion approval is conduct review, not answer adjudication.

Source paper/question metadata is resolved from the database. Supplied paper context must contain the question; supplied exam context must contain that paper in its public live collection. Sharing a link does not create a thread, publish a question or reveal an answer.

## Moderation, safety and operations

Open `/admin/discussions` or **Question discussions** in the bank administration navigation. Owner grants are required; writes use existing staff session/MFA/CSRF enforcement. The shared moderation service handles first-post approval/rejection, conduct hide/dismiss and audit snapshots, retaining the existing bearer console for compatibility. A moderator cannot approve their own post. Queue pages are bounded to 40 items; process/refresh to advance the pending queue. Existing moderation action history and reversal remain in the original console.

Conduct reports retain reasons/notes and count one per account/post. Five ordinary independent reports trigger the existing automatic hide; dismissing the reports restores only an automatic hide. Incorrect keys and transcription errors go to the contribution workflow. Thread lock/unlock records a reason and append-only discussion event. Existing active mute/suspension sanctions prevent posting/voting/accepting; reporting and author withdrawal remain available.

Creator blocks now also hide both-direction question topics/replies, accepted reply excerpts, evidence reads and discussion feed entries while signed in. Blocked users cannot reply through a hidden parent. Public/signed-out access and historical bank attribution are not revoked; this remains distinct from a global account ban. Unblock in creator settings.

Replies notify the topic author only after publication, transactionally and idempotently. Accepted replies notify their author. Notifications contain a generic message and guarded question/post link, not an answer excerpt. No email provider, email delivery or following subscription is introduced.

Server guards: same-origin/CSRF account writes, existing atomic write budget (40 content changes/minute), 30 new posts/account/day, deterministic account/request idempotency, 64 KiB request cap, strict typed bodies/HTTPS reference validation, plain-text rendering, private/no-store reads, bounded pagination and indexed root/reply/feed access. Immutable `discussion_events` record creation/withdrawal/acceptance/locking; existing `mod_actions` retain moderation decisions. No endpoint directly changes bank content.

Migration **0039_question_discussions** adds request/context/source fields, disclosure acknowledgements, audit events, notification references and indexes. Applied migrations must never be edited. Backups must include these tables along with posts, votes, reports, moderation and notifications.

## Verification and limits

Evidence: `reports/question-discussions/`. Isolated integration coverage includes gates/CSRF, concurrent request replay, first-post visibility, exact paper validation, sources, replies/acceptance, votes, notifications, feed/block filtering, five-report auto-hide, mute/locks/withdrawal, active mocks, staff MFA/self-review, immutable data and correction-draft handoff without a bank edit.

Browser rehearsal uses disposable synthetic accounts/database only. It exercises accepted/helpful replies, a shared context URL, a saved unsubmitted correction draft retaining three evidence entries, new-post moderation, publication into the author's feed and 360px layout. No real user posts, votes, moderation decisions or answer corrections are seeded in production.

Attachments, rich-text post editing, standalone feed-only doubts, live push updates, follow subscriptions and email delivery are future additions. The broader P08 operational/security/accessibility/load gates and real independent bank-reviewer provisioning remain outstanding; this release does not claim the entire platform production readiness programme is complete.
