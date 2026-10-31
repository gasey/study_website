# Avatar editor — v3 private-account cosmetics

## Delivered behavior

`/avatar` and `/profile/avatar` open the v3 Customize / Inventory workspace. The profile's Edit avatar link and the navigation menu lead there. Seven categories cover skin, hairstyle, hair colour, top, accessory, background and frame. The original v3 SVG geometry is reused with unique clipping IDs; rendering needs no image service, external media or question-bank request.

The current catalog has 19 free starter items and 7 level rewards. All skin tones, hairstyles and natural hair colours are free. Blue top, glasses and teal background unlock at level 5; saffron top and headphones at level 10; Committed frame at level 15; Gold frame at level 30. Eligibility uses actual lifetime XP from the existing reward ledger, with the same level formula used elsewhere. Saving a look claims all currently eligible level items. Claimed items remain available after an XP reversal; this is a cosmetic ownership rule and never restores reversed XP or points.

Preview choices do not change the saved avatar until Save look succeeds. Shuffle selects available items and keeps the chosen skin tone. Revert preview restores the saved choice. Use initials instead clears the active illustrated look but keeps claimed items and event history. Guests may preview the starter catalog; saving requires an account. Existing users keep their initials until they explicitly save an illustrated avatar.

Saved avatars appear in account navigation/profile, public creator cards/profiles, published question discussions/feed, material author bylines, learning/contribution leaderboards and private desk membership. The desk illustration uses the selected face, hair, shirt and skin; member chips/profile cards use the complete circular avatar. List queries carry the avatar alongside an already-visible identity, so there is no new user directory or per-avatar lookup loop. Existing public visibility and block checks remain in place. Blocked desk members' avatar values are withheld.

## API and storage contract

Migration `0041_account_avatars.sql` adds nullable `users.avatar`, nonnegative `avatar_version`, durable `user_avatar_items` and append-only `avatar_events`. Existing records are not force-customized. Bank data and reward balances are untouched.

- GET `/api/me/avatar`: private/no-store own identity, saved look/version, actual level, default and catalog/eligibility.
- POST `/api/me/avatar`: registered session, existing CSRF/rate/body limits, exact user binding, expected version and curated complete look (or null for initials).
- Only catalog values are accepted. Client-supplied prices, XP, ownership, arbitrary colours, URLs, markup and photo fields are rejected.
- User-row locking serializes conflicting saves. A retry with the already-current look returns the existing version; a different stale look returns 409 without replacing newer data.
- Save, unlock claims and event append are one database transaction. Reset keeps ownership. No avatar action writes XP, reward points, billing or leaderboard credit.

The single catalog authority is `api/app/data/avatar_catalog.json`. Keep existing values compatible when extending it. API helpers live in `services/avatars.py`, route in `routers/avatars.py`; the React renderer/editor and client types are separate. The editor is lazy loaded. Auth session responses are private/no-store; avatar-save events refresh the header and personal desk identity. In-flight editor/header reads are generation guarded across account changes.

## V3 fidelity and deliberate scope

Reference: saved `India Study Map v3.dc.html`, editor lines 1839–1917, renderer 2718–2743 and catalog 3071–3098. Layout uses 1240px maximum width, 32px/24px/96px page padding, 28px workspace gap, 280px preview basis/max 360px, 560px editor basis, 168px portrait, 70px banner, 14px preview corners, 132px item grid cells, 12px gaps, 10px item corners, and Newsreader/Public Sans/IBM Plex Mono. Selected items use a 2px ink border and an explicit Selected label; controls retain 44px targets. Inventory groups show actual starter/earned/eligible state rather than prototype samples.

The prototype's launch mode has Customize and Inventory only; this release follows that mode. Coin shop, paid cosmetics, badge-gated cosmetics, custom uploads, profile banners/name colours and avatar trading are not delivered. There is no invented coin balance, Pro coin allocation, paid-item purchase or score advantage. The existing reward-points/subscription system is unchanged.

## Verification and operation

See `reports/avatar-editor/` for tests, build, clone rehearsal, screenshots and deployment receipts. Synthetic accounts exercise save/reload, initial reset, inventory, locked-item choices, profile/header and desk display. Mobile check at 360px reported document width 345px with no horizontal page overflow. Automated coverage includes CSRF/session/account binding, curated payload validation, level guards, concurrent conflicting saves, idempotent retry, durable unlocks after XP reversal, immutable history, public projections and creator/desk block boundaries. Full suite: 109 passed, one upstream Starlette deprecation warning.

No production synthetic avatar saves or account impersonation are used. Release operations take a private database dump before migration, apply the additive migration, deploy compatible API before web artifacts, verify catalog/API/static hashes and check both study and family sites. Keep the additive schema if rolling back the frontend/API; never edit an applied migration. Backups and documentation/evidence mirror live under `/home/ubuntu/ism-release-reports/2026-10-23-avatar-editor`.

Limitations: unsaved previews are not an offline draft queue; Save look is explicit. Other already-open pages refresh their projections when reloaded/navigated rather than receiving a cross-device live push. No full account-erasure or avatar moderation service is introduced; user content remains limited to reviewed catalog choices.
