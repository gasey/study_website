# Finna Android beta

The regular Finna Android app runs on its own. You do not need to keep your phone connected to this computer, leave a terminal running, or use Metro. Development and repeatable checks use the dedicated QA emulator.

## Current download

[Download the verified regular Finna beta APK](https://expo.dev/artifacts/eas/2trlhsTa8dU3BwRwofLW8KCQsdgiJL-OqX3V0BTaFqg.apk) · [Local APK](../reports/finna-mobile-dependency-remediation-20261120/finna-beta-dependency-remediated.apk).

Build `6d2bc67d-bab7-4e3f-ae43-b1eb5f510d4a` is signed with the same certificate as the previous beta and installed in place on the owner's Samsung A55. The package is `in.hawayu.finna` version `0.1.0` / code `1`; on-device SHA-256 matches the downloaded APK: `9b44789a54fb3c1c24484cd9cc4d8d6c15dd64d8a730658a285f9571d472d399`. The prior build's bounded signed emulator checks still document long-list traversal/recovery, guest navigation and compact filters. This rebuild includes the remediated mobile dependency lockfile; installation and launch were verified, but the physical device was not used for TalkBack, answer-latency, or broader performance acceptance.

This update includes immediate answer-choice highlighting, practice feedback without the former extra GET, exam/module browsing, subject/topic/subtopic filters, scoped Papers, explicit pagination recovery and corrected question-position restoration.

## Install and use

1. Download the verified **regular beta** APK above. Open the file on your Android phone and follow Android's installation prompt.
2. Open **Finna**. The regular beta connects to the same production service as the website and uses your normal Finna account.
3. For exam study, open **Library → Study by exam**, choose an exam, and open its module. Use the subject, topic and subtopic filters to narrow the questions. Papers stay scoped to the selected exam.
4. An answer choice highlights immediately. A waiting or retry message means the server has not confirmed the answer yet. Keep the saved choice and use the explicit retry action when connected.
5. If a fast scroll reaches a page boundary without loading the next page, use **Load more questions**. The end notice identifies the end of the current selection.

The separate **Finna · Staging** app is only for synthetic QA data. Use the regular **Finna** app for your real account.

To reopen an existing practice set, use **Home → Saved questions → Collections →
Resume collection**. Home's **Continue** prepares a new set. If a cold launch fails
while offline, reconnect and reopen the app so the saved sign-in can be validated,
then resume the collection and explicitly retry its pending choice.

The current signed staging preview has passed that bounded account/recovery path
on the dedicated emulator. It is separate from the production-connected regular
beta linked above.
[Current recovery receipt](../reports/finna-current-signed-account-recovery-20261120/README.md).

## What to check

Try answer feedback, exam/module filters and reopening a long question list. Check readability and navigation with your usual text size and theme. A first physical Samsung scroll/frame sample is recorded in the [physical check receipt](../reports/finna-physical-android-check-20261120/README.md); answer-response timing still needs a safely signed-in synthetic staging session because staging practice redirects to sign-in. Full TalkBack traversal/speech and broader real-network/device acceptance remain open. iOS acceptance is deferred while no iOS device is available.

[Current build and QA evidence](../reports/finna-native-emulator-extended-20261119/README.md) · [Remaining plan](FINNA-REMAINING.md) · [Technical emulator runbook](FINNA-ANDROID-QA.md)
