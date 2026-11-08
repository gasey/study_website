# Learning collections and Website bank

Implemented 3 November 2026. The earlier ShikshaCom comparison informed discovery,
review and learning workflows; its backend is not reused.

- `/bank`: MPSC source questions. `/website-bank`: reviewed Website questions;
  `/community/questions` remains supported. Original question IDs and provenance
  stay intact. Learner MCQs continue through the existing contribution queue and
  independent question review/publication safeguards.
- `/important-days`: reviewed recurring or explicitly dated observances, dated
  references, annual themes and linked question practice.
- `/practice-sets`: independently reviewed lists of existing eligible questions,
  with both-bank/MPSC/Website filtering and untimed revision quizzes.
- `/learning/manage`: authors search existing questions, propose links and save
  metadata; scoped reviewers publish, request changes, reject or withdraw. Every
  action has a version and immutable history. Draft edits retain the previous
  published version until independently approved. Collection approval never
  changes a canonical question or upgrades its answer provenance.
- Home adds actual last-seven-day activity, followed exams, upcoming Important
  Days and recent mocks. Mock topic breakdown uses the original saved snapshot;
  older records without topic snapshots are explicitly unclassified.

No synthetic events, themes, questions, accounts or reviews are seeded in
production. Real Important Days and practice sets need source-checked proposals
and an independent reviewer. A new-question suggestion records the collection
context in its rationale; after question publication a reviewed collection
revision must link its canonical ID.

Google sign-in is disabled until GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are
configured in the private API environment. Register the exact callback
`https://study.hawayu.in/api/auth/google/callback` with Google. Never put the secret
in source control or frontend variables. Existing users sign in normally and
explicitly link Google at Account security. Matching email does not merge accounts.
Existing authenticator checks remain required. Provider exchange is covered by
mocked tests; live provider configuration still needs verification after setup.

Release: rehearse migrations 0070/0071 on a disposable dump clone of **mpsc**, then
apply with `ISM_DB=mpsc bash scripts/migrate.sh`. `bench` is not the live study
DB. `bash scripts/deploy.sh learning-api` transfers only this feature's API files;
`bash scripts/deploy.sh web` builds locally and releases the frontend. The narrow
API mode does not replace publisher scripts. Check both study and family hosts.
