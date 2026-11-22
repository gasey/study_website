# Android QA without a connected phone

Normal installed Finna builds run independently of this computer. Source work, tests and repeatable Android checks can also use the dedicated local emulator. Reserve a physical phone for occasional hardware, TalkBack, real network and performance acceptance. iOS remains deferred while no iOS device is available.

From this repository:

```bash
python3 scripts/finna-android-emulator.py --start
python3 scripts/finna-android-emulator.py --check
# Stop only the dedicated emulator when finished; retain its data.
python3 scripts/finna-android-emulator.py --stop
```

Add `--visible` when starting to show its window. The launcher recognizes only `finna_qa_api36` on `emulator-5580`; it refuses a different AVD at that port and never selects a physical phone. The existing AVD uses the installed API36 Google APIs x86_64 image, KVM and its data directory on `/mnt/linux-storage/android/finna-qa-api36.avd`. Its registration lives under `~/.android/avd`. Keep both paths. The launcher skips stale SDK environment paths and falls back to `~/Android/Sdk`; set `ANDROID_HOME` if the SDK moves. A fresh host must install the official Android SDK emulator/platform-tools and matching API36 image, then create/register that dedicated AVD before using this launcher. It does not download SDKs or reset data.

Starting is nonblocking. During a cold boot, ADB can initially be offline and `--check` can report that the emulator is not running before its connection appears. Keep the existing emulator and repeat `--check` until it reports **ready**; do not start a second instance while port5580 is occupied. App commands issued before Android finishes booting can fail with “Too early to start/bind service.” This is boot readiness, not a Finna launch result.

Install a verified APK with the target explicitly selected:

```bash
adb -s emulator-5580 install -r /absolute/path/to/verified.apk
```

For account/recovery tests use the separate **Finna · Staging** package (`in.hawayu.finna.staging`), connected to https://finna-staging.hawayu.in. It uses synthetic data and supplied test accounts. Never enter a real account/password there. Private test credentials stay outside Git; the root-only Oracle copy is `/root/finna-native-staging/accounts.json`. Do not put credentials in shell command text, report screenshots or build environment variables. Chrome's initial Terms acceptance was explicitly approved by the owner for this QA emulator; no Google account was added.

The regular beta package (`in.hawayu.finna`) uses production. Restrict automated guest checks there to public reads; synthetic attempts belong in staging. Both installed packages are standalone signed builds, with no Metro or ADB tunnel needed. Preserve explicit account ownership and server feedback; never turn an unconfirmed answer into a successful result.

The capture helper in `reports/finna-native-release-readiness-20261119/capture-emulator.py` reuses the reviewed Finna focus/keyboard guard while targeting only `emulator-5580`. Use it for app-only evidence, and visually inspect captures. Guard each input against the expected foreground package. Do not capture browser passwords/codes or change phone settings. Emulator timing does not certify physical Samsung performance.

The persistent staging services and guarded retirement procedure are documented in `reports/finna-native-https-staging-20261119/README.md`. The latest reading-position correction, build IDs, source bindings and acceptance status are in `reports/finna-native-emulator-extended-20261119/`. Earlier account/recovery acceptance retains its original binary scope in `reports/finna-native-release-readiness-20261119/`. A queued/finished build alone is not a native acceptance pass. Owner installation notes are in `docs/FINNA-ANDROID-BETA.md`.


## Current signed account/recovery recheck — 20 November 2026

Preview01a448a3 now has its own real-browser synthetic account and offline-answer
acceptance receipt. Native sign-in/app return, authenticated cold restart, saved
pending choice, one explicit retry/one attempt, result restart, sign-out revocation
and guest restart pass. This uses only `finna_qa_api36`; no Samsung input or new
build. All 11 app captures are reviewed, original radio/shell settings are restored,
private test credentials removed and the emulator stopped with its data retained.
Staging ends with two synthetic accounts, six attempts, zero mail and zero active
QA auth sessions. [Current receipt](../reports/finna-current-signed-account-recovery-20261120/README.md).

A cold start without networking cannot validate the account/catalogue. Reconnect
and reopen the app for online validation; the saved credential and pending choice
survive this tested path. This is not full offline-study acceptance. For an existing
practice set use **Home → Saved questions → Collections → Resume collection**.
Home's **Continue** prepares a new practice set. The current signed test follows
the actual saved-collection controls and confirms no automatic answer submission
before the explicit Retry action. Physical network handover and TalkBack/performance
checks remain open; do not infer them from emulator radio toggling.
