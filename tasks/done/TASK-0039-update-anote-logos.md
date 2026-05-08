# Task: Update ANOTE App Logos Across Web and Mobile

## Metadata

- **ID:** TASK-0039
- **Created:** 2026-05-06
- **Author:** User (via chat submission)
- **Status:** done
- **App(s):** cross-app (app-2, app-3)
- **Priority:** medium
- **Type:** feature

## Problem

A new ANOTE logo has been supplied as `logo.png` in the Knowledge.Healthcare control-layer root (`/Users/ivananikin/Documents/Knowledge.Healthcare/logo.png`). The current logo assets used by ANOTE-web (favicon, Open Graph icons, Apple touch icon, SVG icon) and ANOTE_mobile (Android launcher / adaptive icons, iOS `AppIcon.appiconset`) were last updated in TASK-0019 (2026-04-26/27) from a different source asset (`ANOTE_mobile/logo.PNG`). The new master supersedes that asset and must be propagated to both applications so that all surfaces reflect the current brand logo.

## Desired Outcome

When this task is complete:

1. **ANOTE-web (app-3)** — all Next.js icon routes (`favicon.ico`, `icon.png`, `apple-icon.png`, `icon.svg`) regenerated from `logo.png`. `npm run build` passes cleanly.
2. **ANOTE_mobile (app-2)** — Android launcher icon (flat and adaptive foreground at all 5 mipmap densities) and iOS `AppIcon.appiconset` (all required sizes, RGB-flattened) regenerated from `logo.png`. `flutter analyze` produces no new issues beyond the pre-existing 14-issue baseline.
3. Source asset path is documented in both task and implementation notes so future logo updates have a clear reference.
4. Real-device / browser validation is performed (or explicitly deferred with a follow-up ticket) for: ANOTE-web deployed favicon, Android launcher icon on at least one device or emulator, iOS Simulator after a clean build.

## Constraints

- **Source asset:** `/Users/ivananikin/Documents/Knowledge.Healthcare/logo.png` — this is the only confirmed new logo input.
- **Do not use** the old `ANOTE_mobile/logo.PNG` asset as the source for this task.
- Android adaptive icon: foreground PNG must keep the wordmark within the 66 dp safe zone; background color `#FFFFFF` via `values/ic_launcher_background.xml` (established in TASK-0019).
- iOS: opaque, no transparency (Apple HIG). System applies the superellipse mask.
- ANOTE-web rounded-corners convention (22.5%, transparent outside corners) established in TASK-0019 addendum should be preserved unless explicitly changed.
- Monochrome Android notification small icon is **out of scope** (deferred since TASK-0019; requires a separate brand-approved master — still tracked in `current-priorities.md`).
- No backend or logic changes. Asset-only update in both repos.

## Suspected Affected Areas

### app-3 — ANOTE-web (`/Users/ivananikin/Documents/ANOTE-web`)

| File | Change |
|------|--------|
| `public/favicon.ico` | Regenerate multi-size ICO from `logo.png` |
| `src/app/icon.png` | Regenerate 512×512 PNG |
| `src/app/apple-icon.png` | Regenerate 180×180 RGB PNG |
| `src/app/icon.svg` | Update SVG to mirror new logo |
| *(Likely)* `src/app/opengraph-image.png` | Inferred: may need update for OG consistency; confirm during implementation |

### app-2 — ANOTE_mobile (`/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile`)

| File | Change |
|------|--------|
| `mobile/android/app/src/main/res/mipmap-mdpi/ic_launcher.png` | Regenerate (48×48) |
| `mobile/android/app/src/main/res/mipmap-hdpi/ic_launcher.png` | Regenerate (72×72) |
| `mobile/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png` | Regenerate (96×96) |
| `mobile/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png` | Regenerate (144×144) |
| `mobile/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png` | Regenerate (192×192) |
| `mobile/android/app/src/main/res/mipmap-*/ic_launcher_foreground.png` | Regenerate adaptive foreground at 5 densities (108/162/216/324/432 px) |
| `mobile/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml` | Retain (references foreground + background — no change needed unless resource names change) |
| `mobile/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml` | Retain (same) |
| `mobile/android/app/src/main/res/values/ic_launcher_background.xml` | Retain `#FFFFFF` unless brand changes background color |
| `mobile/ios/Runner/Assets.xcassets/AppIcon.appiconset/` | Regenerate all required sizes (Contents.json references), RGB-flattened |

## Unknowns

1. **Open Graph image** — It is unconfirmed whether `opengraph-image.png` in ANOTE-web currently uses the old logo or a separate marketing asset. Confirm during implementation before regenerating.
2. **Brand background color** — The `#FFFFFF` Android adaptive icon background was established for the previous logo. Confirm it still applies to the new logo artwork.
3. **Real-device validation** — No Android hardware or iOS device is confirmed available in the build agent environment. Validation may need to be performed manually by the user.

## Notes

- **Prior art:** TASK-0019 (completed 2026-04-26, addendum 2026-04-27) performed an identical cross-app logo propagation. Its implementation notes in `handoffs/2026-04-26-task-0019-done.md` and `handoffs/2026-04-27-task-0019-rounded-corners-addendum.md` provide a detailed, proven execution guide. Reuse that pattern directly.
- **Pending TASK-0019 follow-up:** `current-priorities.md` still lists real-device validation of the TASK-0019 logo rollout as an open item. This task supersedes that follow-up — validating TASK-0039 output on real devices closes both.
- **Monochrome notification icon** (Android foreground service small icon) remains deferred from TASK-0019 and is not in scope here. Track separately.
- Source asset location for implementation: `/Users/ivananikin/Documents/Knowledge.Healthcare/logo.png`

## Implementation Update

### 2026-05-07 — app-3 / ANOTE-web completed

- Source asset inspected before generation: `logo.png` is `1254x1254`, `RGBA`, with alpha extrema `(0, 255)`.
- Regenerated ANOTE-web assets from that master:
  - `public/favicon.ico`
  - `src/app/favicon.ico`
  - `src/app/icon.png`
  - `src/app/apple-icon.png`
  - `src/app/icon.svg`
- `src/app/opengraph-image.png` does not exist in ANOTE-web, so no Open Graph image regeneration was needed.
- Validation completed: `npm run build` passed cleanly with no new warnings.
- Visual comparison completed against `logo.png`.
- Deviation from the TASK-0019 rounded-corner convention: the previous 22.5% rounded-square mask was not re-applied for ANOTE-web because the supplied master is already a circular RGBA logo with transparent outer area. Preserving the provided geometry was treated as the correct brand-faithful behavior.
- Remaining scope: app-2 / ANOTE_mobile is still pending.

### 2026-05-08 — app-3 / ANOTE-web manually validated

- User manually reviewed the local ANOTE-web result and confirmed the regenerated logo assets look correct.
- This satisfies the web/browser validation portion for app-3.
- TASK-0039 remains `active` overall because app-2 / ANOTE_mobile has not yet been updated or validated.

### 2026-05-08 — app-2 / ANOTE_mobile completed

- Source asset confirmed again before generation: `/Users/ivananikin/Documents/Knowledge.Healthcare/logo.png` is `1254x1254`, `RGBA`, with transparency present.
- Regenerated Android launcher assets in `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/`:
  - legacy `ic_launcher.png` at `mipmap-mdpi`, `mipmap-hdpi`, `mipmap-xhdpi`, `mipmap-xxhdpi`, `mipmap-xxxhdpi`
  - adaptive `ic_launcher_foreground.png` at the same 5 densities, with the supplied logo centered inside the established `66/108` safe-zone ratio on a transparent canvas
- Intentionally retained existing Android adaptive-icon wiring:
  - `mipmap-anydpi-v26/ic_launcher.xml`
  - `mipmap-anydpi-v26/ic_launcher_round.xml`
  - `values/ic_launcher_background.xml` with `#FFFFFF`
- Regenerated all 15 required iOS `AppIcon.appiconset` PNGs from `Contents.json`, flattened onto white and converted to opaque RGB per Apple requirements.
- Validation completed:
  - `flutter analyze` in `mobile/` remained at the pre-existing 14-issue baseline with no new issues introduced
  - `flutter clean && flutter build apk --debug` succeeded and produced `mobile/build/app/outputs/flutter-apk/app-debug.apk`
  - `adb install -r build/app/outputs/flutter-apk/app-debug.apk` succeeded on emulator `emulator-5554`
  - `adb shell am start -n com.ivananikin.anote_mobile/.MainActivity` succeeded, confirming the updated package installs and launches cleanly on Android
  - User manually reviewed the Android emulator launcher result on 2026-05-08 and confirmed the refreshed icon looks correct
- Validation limits / deferrals:
  - iOS Simulator visual verification remained blocked by the host simulator environment (`launchd` / boot error 60)
  - Follow-up validation ticket created: `TASK-0041` for the remaining unverified surfaces (deployed ANOTE-web favicon and iOS icon rendering)

### 2026-05-08 — task closeout decision

- Implementation scope for both repos is complete.
- Remaining validation is environment/surface-specific rather than an implementation blocker.
- TASK-0039 therefore moves to `done`, with explicit follow-up tracking in `TASK-0041` instead of keeping the asset-refresh task open indefinitely.

---

## Triage Assessment

| Field | Value |
|-------|-------|
| **Task ID** | TASK-0039 |
| **App(s) Impacted** | cross-app — app-2 (ANOTE_mobile), app-3 (ANOTE-web) |
| **Task Type** | feature |
| **Priority** | medium |
| **Urgency** | soon |
| **Impact** | medium |
| **Confidence** | high — identical pattern executed successfully in TASK-0019; implementation steps are well-understood |
| **Dependencies** | Source asset `logo.png` confirmed present at KH root. No blocking tasks. Monochrome notification icon is a known out-of-scope defer. |
| **Recommended Status** | done |
| **Suggested Next Action** | Execute `TASK-0041` to validate the refreshed logo assets on stable real/deployed surfaces: deployed ANOTE-web favicon, Android launcher icon on a stable launcher surface, and iOS Simulator/device icon after a clean build |

### Reasoning

- **Impact is medium**: this is a visual branding update with no functional changes. Both apps remain operational with the current logo; the update improves brand consistency but is not blocking any feature or fixing a defect.
- **Urgency is soon**: a new logo has been explicitly supplied and should be applied in a timely manner to keep both applications on-brand, but there is no production incident or compliance deadline driving immediate action.
- **Medium + Soon → Medium** per the priority matrix in `workflows/triage-process.md`.
- **Confidence is high**: TASK-0019 produced a complete, validated execution record for exactly this operation. All affected files are known, tooling is confirmed working, and the only open questions are low-risk implementation details (image dimensions, OG image scope) that can be resolved at execution time without a separate investigation phase.
- **Recommended status is `done`**: implementation is complete in both repos. Remaining work is validation-only and has been split into follow-up `TASK-0041` so the asset-refresh task can close cleanly.

### Cross-App Considerations

This task touches two separate repositories:

| App | Repo | What changes |
|-----|------|-------------|
| app-3 (ANOTE-web) | `/Users/ivananikin/Documents/ANOTE-web` | Next.js icon route assets (`favicon.ico`, `icon.png`, `apple-icon.png`, `icon.svg`) |
| app-2 (ANOTE_mobile) | `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile` | Android mipmap PNGs (flat + adaptive foreground), iOS `AppIcon.appiconset` |

Coordination notes:
- Changes in each repo are **independent** — neither repo imports assets from the other. Both can be updated in the same session without ordering constraints.
- The source asset (`logo.png`) lives in the Knowledge.Healthcare control layer and must be copied/referenced by the build agent when working in each repo.
- Validation gates are independent: `npm run build` for app-3; `flutter analyze` for app-2.
- Real-device validation covers both apps and can be sequenced: web favicon (deployed browser) → Android launcher (device/emulator) → iOS Simulator.
- Reference: `workflows/cross-app-change-process.md` for full coordination checklist.
