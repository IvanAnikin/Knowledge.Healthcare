# Session Handoff: TASK-0019 Addendum — Rounded Corners + Android Adaptive Icon

## Session Date

2026-04-27

## Goal

Apply rounded corners to the ANOTE app icons that the user perceives, and upgrade the Android launcher icon to a proper adaptive icon so it renders correctly under the per-device launcher mask on Android 8+.

## What Was Learned

- Pre-rounding iOS icons is an anti-pattern: iOS applies its own superellipse mask at runtime on the home screen, and the App Store rejects icons with any alpha (especially the 1024x1024 marketing icon). The right answer for iOS is to leave icons square and opaque.
- Android 8+ launchers mask any non-adaptive icon to the device's chosen shape. If you bake rounded corners into a flat `ic_launcher.png`, modern launchers will mask the result *again*, producing a visible double-rounding or shape conflict. The correct fix is a real adaptive icon with a separate foreground PNG and background.
- The Android adaptive icon canvas is 108dp; only the central 66dp safe zone (~61.1% of the side, centered) is guaranteed to remain visible after the launcher's mask. The foreground PNGs were generated to that spec at 108/162/216/324/432 px for mdpi → xxxhdpi.
- The current `AndroidManifest.xml` only references `@mipmap/ic_launcher` (no `roundIcon`), but providing `ic_launcher_round.xml` in `mipmap-anydpi-v26/` is harmless and helps launchers that probe for the round variant.
- The ANOTE_mobile project had no prior `values/colors.xml`, so introducing `values/ic_launcher_background.xml` does not collide with any existing color resources.
- Pillow + a clipPath-wrapped SVG are sufficient to bake 22.5% rounded corners with transparent corners across `favicon.ico` (multi-size 16/32/48/64), `icon.png`, `apple-icon.png`, and `icon.svg` for ANOTE-web.

## Files Reviewed

- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/logo.svg`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/logo.PNG`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/AndroidManifest.xml`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/values/` (directory listing)
- `/Users/ivananikin/Documents/Knowledge.Healthcare/tasks/done/TASK-0019.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/dashboards/task-board.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/current-priorities.md`

## Files Changed

ANOTE-web (regenerated with 22.5% rounded corners, transparent outside):

- `/Users/ivananikin/Documents/ANOTE-web/src/app/favicon.ico` — multi-size ICO (16/32/48/64).
- `/Users/ivananikin/Documents/ANOTE-web/src/app/icon.png` — 512x512 RGBA.
- `/Users/ivananikin/Documents/ANOTE-web/src/app/apple-icon.png` — 180x180 RGBA.
- `/Users/ivananikin/Documents/ANOTE-web/src/app/icon.svg` — wordmark paths wrapped in a `<clipPath>` rounded rectangle, 424x424 viewBox.

ANOTE_mobile Android — new adaptive icon files:

- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/values/ic_launcher_background.xml` — `#FFFFFF`.
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-mdpi/ic_launcher_foreground.png` — 108 px.
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-hdpi/ic_launcher_foreground.png` — 162 px.
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-xhdpi/ic_launcher_foreground.png` — 216 px.
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-xxhdpi/ic_launcher_foreground.png` — 324 px.
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_foreground.png` — 432 px.

ANOTE_mobile Android — modified legacy fallback (rounded, transparent outside):

- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-mdpi/ic_launcher.png`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-hdpi/ic_launcher.png`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png`
- `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png`

ANOTE_mobile iOS:

- No changes (deliberate; see Decisions).

Knowledge layer:

- `/Users/ivananikin/Documents/Knowledge.Healthcare/tasks/done/TASK-0019.md` — appended “Addendum (2026-04-27): Rounded Corners + Android Adaptive Icon” with decisions, files changed, and follow-ups; bumped `Updated` date.
- `/Users/ivananikin/Documents/Knowledge.Healthcare/dashboards/task-board.md` — extended TASK-0019 Done-row note with the addendum summary.
- `/Users/ivananikin/Documents/Knowledge.Healthcare/current-priorities.md` — added a Recently Completed entry for 2026-04-27, updated the App-3 Follow-Ups TASK-0019 entry, broadened the related Active Goal to mention adaptive-icon shape verification, refreshed the “Last updated” marker.

Tooling (ephemeral, useful for re-runs / monochrome follow-up):

- `/tmp/iconenv/gen_rounded.py` — full generation script for the addendum (web rounded set + Android adaptive + legacy rounded fallback). Reuses the existing `/tmp/iconenv` Pillow venv.

## Decisions Made

- **iOS skipped.** Apple disallows alpha and applies its own superellipse mask. Pre-rounding causes a visible double-rounding inside Settings/Spotlight at best, and an App Store review rejection for the marketing icon at worst. Leaving iOS square is the platform-correct answer.
- **Android: full adaptive icon, with rounded legacy fallbacks.** Adaptive is the only way to render correctly under modern launcher masks; legacy rounded PNGs cover Android <8 only.
- **Adaptive background color:** `#FFFFFF` to match the existing wordmark plate. Can be revisited when a brand-approved colored plate exists.
- **Corner radius:** 22.5% of side (iOS-like superellipse approximation) for both ANOTE-web icons and the legacy Android `ic_launcher.png` fallback.
- **Outside the rounded shape (web):** transparent. App-icon convention; respected by browsers and PWA install surfaces.

## Assumptions

- The Android adaptive icon's white background is acceptable as a brand decision (matches the existing logo plate). _Needs verification: low risk; revisit if brand wants colored plate._
- Providing `mipmap-anydpi-v26/ic_launcher_round.xml` while the manifest only declares `android:icon=@mipmap/ic_launcher` is harmless. _Needs verification: no — well-established Android behavior; launchers fall back gracefully._
- The wordmark, when scaled into the 66dp safe zone of a 108dp adaptive canvas, remains legible after a circular launcher mask. _Needs verification: yes — confirm visually on at least one stock-Android (e.g. Pixel) and one OEM (e.g. Samsung) device or emulator._

## Unresolved Questions

- Should the adaptive icon background eventually be a colored plate (e.g. ANOTE blue) instead of white? Brand decision.
- Should we add `flutter_launcher_icons` as a configured tool now, so the next logo or color iteration is a single command? Punted; not in scope of this addendum.

## Recommended Next Step

- Real-device validation:
  - ANOTE-web: hard-reload `https://localhost:3000/` and a deployed environment; verify favicon and `apple-icon.png` show rounded corners.
  - Android: `cd /Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile/mobile && flutter clean && flutter run` on at least one stock-Android emulator (Pixel system image, Android 14+) and ideally one OEM device (Samsung One UI). Confirm the launcher mask cooperates with the new adaptive icon and the wordmark stays legible inside circle/squircle/rounded-square shapes.
  - iOS: `flutter run` on the iOS Simulator; confirm the home-screen icon still looks correct (it should, since iOS icons are unchanged).
- After the above passes, the still-open follow-up is the Android monochrome notification small icon, which still requires a brand-approved silhouette master.
