# Study Desk and Study Partners — proposed plan

Status: the personal Study Desk and its safety-first partner UI preview are
implemented and deployed. The desk is device-local; partner connections, shared
desks, and discovery are **not connected to accounts or a backend**. Updated
19 October 2026. The user endorsed mutual study partners and shared activity
inside private desks. The later stages below are proposed future scope, with
separate release gates.

## Product direction

Study Desk is a learner's home for deciding what to study next, continuing
work, and studying with a small trusted group. It must be useful when the
learner has no partners. Partners are optional and discovery is opt-in.

The existing prototype proposes desks of up to six members. Keep that size
for shared desks. Defer class desks, paid desks, and public rooms until the
personal and small-group experience works.

The `/desk` UI has separate **My study** and **Study partners** tabs. It opens
on the Study partners screen to match the v3 shared-desk design; the personal
plan remains one tap away under **My study**. The partner screen is a clearly
labelled preview:
it explains exact-handle/expiring-link invitations and opt-in discovery, and
its buttons open explanatory dialogs only. Nothing is sent, published, or
saved from this preview. Existing account and operational-moderation gates
still apply before any real social action is wired.

## Personal desk

The **My study** tab:

- Today: one main goal, a short checklist, and a clear Continue studying action.
- Continue: unfinished mocks and recently opened practice sets.
- Revision: saved questions, mistakes, and subjects chosen for revision.
- This week: a modest weekly plan and personal completion summary.
- Partners: an optional area with Add study partner and pending invitations.

Use the bank's approved subject/topic taxonomy for goal selection. Descriptive
and unkeyed questions can be saved and discussed, but completion must not
imply a correct answer. Scored sessions continue to use the scorable pool.
Personal notes, individual answers, scores, mistakes, and activity stay private
unless the learner explicitly shares a specific item.

## Partners and shared desks

A partner connection is separate from desk membership: accepting a partner
does not automatically add them to a desk or reveal other desk members.

First release: Add study partner by exact handle or an expiring invitation
link. Show the inviter and intended action before acceptance. Links must be
revocable, single-use, and accepted by a signed-in user. Do not expose an
enumerable directory of account emails or phone numbers.

After acceptance, either learner may invite the other to a shared desk.
Shared desks hold two to six members and have a name, exam goal, weekly goal,
shared bank questions, a simple text discussion, and planned focus sessions.
Allow solo focus sessions too. Shared completion is voluntary; do not expose
private accuracy, missed sessions, or exact activity automatically.

Separate controls: leave desk, remove partner, mute, block, report. Owners
can manage membership, but cannot inspect personal study data. Transfer
ownership or close the desk if its owner leaves.

## Find a study partner — later release

Learners explicitly turn on discovery and choose the fields visible on their
discovery card: display name/avatar, target exams, subjects, preferred study
language, broad availability windows/time zone, and study style. Useful styles
include quiet focus, discussing questions, revision, and accountability.

Match on shared exam first, then subject interests, compatible times, language,
and preferred study style. Use simple explainable rules initially. Example:
“Both preparing for MPSC; shared interest in polity; evening study times.”
Do not infer sensitive identity, use precise location, or rank by popularity,
appearance, spending, marks, or inferred personality. Do not claim a match is
safe or compatible merely because the system recommended it.

Cards have Request to study, Dismiss, and Report. The request uses a short
structured reason, such as “Revise polity together.” Full conversation starts
only after acceptance. No swiping, public follower counts, automatic pairing,
unsolicited direct messages, or contact-detail exchange prompts.

Offer filters and an honest empty state when there are no matches. Do not
silently broaden into incompatible age groups or expose undiscoverable users.
Let learners pause discovery immediately and control outstanding requests.

## Safety requirements before any social release

- Real accounts and verified contact ownership before invitations or messages;
  verification does not establish identity or trustworthiness.
- Define the supported age policy before rollout. Recommended initial scope:
  adult partner discovery, with under-18 users excluded from adult matching.
  If minors are supported later, design separate protections and moderation
  before opening their social features. Avoid collecting identity documents
  merely to operate a study profile.
- Private profiles by default. No public phone/email, exact location, birth
  date, last-seen timestamp, live presence, or study timetable. Share broad
  availability only when the learner chooses it.
- Mutual acceptance, server-enforced membership checks, request limits,
  cooldowns after declines, and no repeated requests after blocking.
- Blocking ends direct contact, cancels requests, and removes both people
  from each other's recommendations. Explain that shared desks may still
  contain both members; hide their messages from each other and offer Leave
  desk or owner removal. Do not promise complete separation in a shared room.
- Report a profile, invitation, desk, or message in context. Retain the reported
  content and necessary context for authorized reviewers; do not grant general
  moderator access to private desks. Audit access and moderation actions.
- An operational report queue, accountable reviewer, escalation process,
  sanctions, and appeal path must exist at launch. Move this minimum moderation
  work ahead of social release rather than waiting for the current Phase 6.
- Start with text and bank links. Defer arbitrary uploads, voice/video, public
  room search, and external contact sharing features.
- Quiet hours cover all partner notifications. No bypass for desk invitations
  or duels. Provide mute and notification preferences.
- Define deletion and report-evidence retention before launch. Leaving a desk
  must revoke access immediately. Explain what happens to previously shared
  messages and content; preserve only justified report evidence after deletion.

## Implementation outline

Reuse existing accounts, questions, taxonomy, collections, attempts, and mocks.
Inspect existing invitation/report/moderation tables before adding equivalents.
Proposed additions: personal goals/tasks, saved study items, partner preferences,
partner requests/connections, blocks, desks, memberships/invitations, shared
items, messages, focus sessions, and reports where existing tables cannot serve.

Keep discovery visibility separate from account visibility. Store consent and
age eligibility separately from public card fields. Enforce invitation expiry,
capacity limits, acceptance state, blocks, and membership in database-backed
transactions. Use cursor pagination for messages; polling is sufficient for the
first release. Real-time presence and sockets are not prerequisites.

## Initial delivery order and completion criteria

1. Accounts and personal desk: save goals/questions, continue work, view personal
   progress across devices. No other user can retrieve private desk data.
2. Trusted partners: exact-handle/link invitations, mutual acceptance, shared
   desks, shared questions, text discussion, focus sessions, and the minimum
   moderation controls above. Exercise rejection, blocking, expired invites,
   removed membership, ownership transfer, and concurrent capacity limits.
3. Opt-in discovery: explainable suggestions, structured requests, filters,
   discovery pause, eligibility boundaries, and abuse controls. Start with a
   small rollout only when reports can be handled operationally.
4. Expand after observing usefulness and safety: group revision plans, shared
   mock scheduling, and eventually separately designed class desks.

Measure repeat study sessions and useful accepted connections alongside block
and report rates, repeat unwanted requests, and report response times. Do not
optimize for message volume or time spent browsing people.

## Social relationships and permissions

| Relationship | Consent | What it permits |
|---|---|---|
| Study partner | Both people accept | Partner-visible shared activity and invitations |
| Desk member | Invitation accepted, within capacity | That desk's shared items, discussion, and sessions |
| Follower, future | Follow a public publisher | Receive explicitly public study posts |
| Class member, future | Separate enrolment | Class assignments and explicitly defined class reporting |

Following must never create a partner connection, permit private messages,
reveal desk membership, or grant access to partner activity. Partner lists and
desk member lists are not public. A teacher badge must identify precisely what
was checked; contact verification alone cannot justify an expertise badge.

Request states: pending, accepted, declined, cancelled, expired. Partner
connections have active/removed states; blocking is a separate relationship
checked in both directions. Membership states are invited, active, left, and
removed. Rejoining requires a new invitation. Request acceptance must check
blocks, account eligibility, expiry, and any limits atomically. Duplicate and
crossed requests must resolve to one connection, not duplicate records.

Removing a partner revokes partner-audience access immediately, but leaves
explicit desk memberships unchanged. Explain that distinction in the action.
Removing a desk member revokes desk access immediately, including attachments
if introduced later. Previously seen content cannot be made unseen.

## Activity: useful updates with deliberate sharing

Start with chronological activity within a desk. Later offer a Partners tab
aggregating updates explicitly shared with partners. Keep the personal Today
screen as the default destination; do not replace it with an endless feed.

| Event | Personal record | Optional shared version |
|---|---|---|
| Goal completed | Task detail | “Finished today's goal” |
| Practice completed | Questions, answers, accuracy | “Completed a polity practice session” |
| Mock completed | Result and detailed review | Completion only; score requires an extra explicit choice |
| Question saved | Private bookmark | A separately shared question link and study prompt |
| Session planned | Private schedule | Invitation with the selected session time |
| Weekly goal completed | Personal summary | A short completion card |

Provide “Share an update” after a meaningful action. Preview the exact text,
audience, and any score before posting. Default audience is Only me; choices
are Only me, Partners, or one named desk. Public is introduced only with the
future publishing feature. A private desk post cannot be forwarded publicly
with one click. Do not auto-post failures, missed days, weak topics, or raw
answers. Avoid revealing answer keys in previews of active scored sessions.

Keep study records and shared posts separate: deleting a post does not erase
an attempt, and completing a task does not publish it. Audience authorization
is evaluated on every read. Partner-audience posts should be limited to the
partners eligible when published who are still connected; accepting a new
partner must not reveal old activity silently. Likewise, newly joined desk
members start with current pinned resources and messages from joining onward;
make any alternative history policy explicit before membership acceptance.

Initial interaction: a small encouragement reaction and a study reply in the
desk thread. No public reaction totals, repost mechanics, trending topics,
engagement ranking, or automated streak pressure. Editing/deleting shared
posts is supported. Reported versions may be retained under the report policy.

## Screens and core journeys

- `/desk`: Today, revision, weekly plan, and links to shared desks.
- `/desk/partners`: accepted partners, invitations, Add study partner; later
  a separate Find partners action and discovery settings.
- `/desk/:deskId`: Overview, Questions, Discussion, Sessions, and Members.
- `/desk/activity`: optional combined partner updates, after desk activity works.
- `/settings/privacy`: discovery, sharing defaults, blocked accounts, account
  deletion/export, and notification preferences.
- `/inbox`: actionable notifications with read/dismiss controls. It must not
  quietly become an open direct-message inbox.

A learner without partners can use the full personal desk. A learner invited
by a friend sees the inviter and scope, signs in, accepts, and chooses whether
to join a desk. A learner joining discovery previews their card before enabling
it, reviews matching reasons, sends a structured request, and waits for consent.
All core flows must work on mobile, with keyboard navigation and clear loading,
empty, error, and expired-link states. Never show sample people as real users.

## Notifications

Notify for invitations, accepted requests, direct replies, desk mentions, and
opted-in session reminders. Ordinary completion updates stay in the feed or an
optional digest. Deduplicate notifications and cap reminders per event. Quiet
hours use the learner's time zone. Notification previews must omit scores and
private question content by default; opening one rechecks current permission.
Do not notify a blocked account that it was blocked. Start with in-app delivery;
email/push are separate opt-ins with unsubscribe controls.

## Technical growth plan

Keep the existing FastAPI/PostgreSQL application and React interface. Add
numbered migrations and narrowly scoped API modules. Do not split services for
this feature. Start with indexed reads, cursor pagination, and bounded polling.

Suggested records beyond the initial outline: shared activity posts with
explicit audiences, audience recipients, reactions, notification preferences,
notifications, and an outbox for reliable asynchronous delivery. A domain event
is not permission to publish: private completion events only generate a share
prompt until consent is recorded. Use idempotency keys for invitations, posts,
and reminders, and a unique pair constraint for partner connections.

Likely API groups: personal desk tasks/saves; partner requests and connections;
desk memberships and items; posts/replies; sessions; blocks/reports; privacy
settings; and, later, discovery and public follows. Every object endpoint must
check ownership or current membership, including counts, search, previews,
exports, and notification targets. Never rely on hiding controls in the UI.

Index memberships by user/desk, posts by audience and creation cursor, requests
by recipient/state, and notifications by recipient/read state. Start partner
feeds with reads over the small relationship graph. Introduce background fanout
only when measurements justify it. Cache only with audience-aware keys and
invalidate on membership, audience, and block changes. Add WebSockets/Redis
when measured polling or multiple workers require them; authorization must also
be rechecked on reconnect and membership revocation.

Store short invitation tokens as hashes, expire them, and never log raw tokens
or private message bodies. Back up data and rehearse restoration. Define
retention windows for messages, expired requests, security logs, and reported
evidence before storing production social content. Measure request latency,
database load, storage growth, failed jobs, and moderation backlog before
choosing infrastructure upgrades. No fixed capacity claim is justified yet.

## Comprehensive release sequence

| Stage | Deliverable | Release gate | Relative scope |
|---|---|---|---|
| A | Accounts and personal desk | Private-data authorization, device-history migration, restore/delete paths | Medium |
| B | Mutual partners, private desks, questions, text discussion, deliberate activity sharing | Requests/membership/blocks work; staffed reports and appeals; age policy operational | Medium–large |
| C | Focus sessions, weekly desk plans, optional partner activity aggregation | Reminder controls, time zones, audience revocation and score privacy verified | Medium |
| D | Opt-in partner discovery | Eligible opt-in candidates only; explained matches; abuse limits; moderated pilot | Medium–large |
| E | Follow teachers/publishers and public study posts | Public-content moderation, publisher controls, spam/copyright processes, separate public audiences | Large |
| F | Class desks and teacher assignments | Teacher roles, enrolment, defined student-data visibility, age protections, capacity controls | Large |
| G | Optional richer collaboration | Demonstrated demand and funded operational support | Variable |

Stage B should first roll out to a small invited group. Each stage needs a
feature flag and a rollback path; turning off discovery stops new suggestions
and requests while preserving personal study work and access to safety tools.
Disabling posting must not disable leaving, blocking, reporting, or deletion.

Stage E follows public educational content only. Private learner profiles stay
private; following does not expose their personal study activity. Defer public
comments until their moderation can be supported. Do not monetize safety or
charge users to block, report, leave, export, or delete their data.

Stage F is a separate product extension, not a larger private desk. Teachers
may see only the assignment results and attendance explicitly covered by class
participation, not a learner's full personal history. Paid enrolment and the
prototype's class billing require separate decisions.

Stage G candidates: collaborative revision sets, scheduled group mocks,
moderated exam communities, accessible attachments, and integrations with
calendars. Voice/video, open public rooms, unrestricted direct messaging, and
automated matching are deferred until their specific demand and safety costs
are understood. No automatic upgrade from a private desk to a public group.

## Acceptance checks and operational readiness

Before social rollout, exercise unauthorized cross-user reads, forwarded and
expired invites, concurrent last-seat acceptance, duplicate requests, removal
during an open session, blocking across shared desks, deleted/edited posts,
new-partner history visibility, and notifications after access revocation.
Check reports against edits/deletions and verify reviewer access is scoped and
audited. Test mobile/keyboard flows and account recovery. These are meaningful
permission and lifecycle checks, beyond visual confirmation of a happy path.

Track personal-desk reuse, accepted invitations that lead to voluntary shared
study, completed shared sessions, and opt-in learner feedback. Review alongside
unwanted requests, blocks/reports, repeated offenders, response time, and appeals.
Set pilot targets after measuring the baseline; low report volume alone does
not establish safety. Stop expanding when moderation cannot meet its published
response expectations or permission boundaries fail.

## Decisions to settle before each affected build

Accounts: authentication/recovery provider and guest-history migration.
Social launch: supported ages, moderation owner/coverage, retention schedule,
configurable invitation limits, and initial desk/partner limits per account.
Discovery: public card fields, eligibility process, pilot size, and matching
weights. Publishing/classes: publisher verification meaning, comment policy,
teacher permissions, enrolment, and any billing model. These decisions do not
block planning or the personal desk, but must precede their respective releases.


## Implemented private v3 release — 23 October 2026

This section supersedes the opening historical preview status and the proposed first-release sequence. The desk now has account-saved planning/private notes and a six-seat, member-only collaboration backend with real invitations, resources, chat, deliberate progress/mistake visibility and server-time focus sessions. The seven v3 tabs and copied scene geometry are implemented with actual members/empty seats. See STUDY-DESK.md for the delivered contract, evidence, operations and limitations.

The user explicitly chose **private invitations; discovery/classes off**, while email verification remains deferred. That approval supersedes the verified-contact prerequisite for this private release only. Direct room membership by exact-handle invitation is the delivered workflow; a separate mutual partner graph and expiring-link invitations remain future scope. Do not treat the future discovery/teacher/game requirements elsewhere in this planning document as delivered. No automatic sharing, inferred online status, fabricated partners or focus rewards.
