# Task: ANOTE-web demo transcription hardening: VAD fallback and Czech prompt anchor

## Metadata

- **ID:** TASK-0014-C
- **Parent:** TASK-0014
- **Created:** 2026-04-25
- **Updated:** 2026-04-25
- **Author:** Implementation agent (per TASK-0014 spec)
- **Status:** deployed
- **App(s):** app-3
- **Priority:** high
- **Type:** infra

## Problem

Recorder rotates raw chunks without client VAD; Whisper proxy has no Czech medical prompt anchor. Silent input can produce hallucinated transcripts.

## Desired Outcome

- Client-side VAD via `@ricky0123/vad-web` + `onnxruntime-web` uploads only speech-positive chunks.
- VAD init failure cleanly falls back to current raw-upload behavior.
- Whisper request includes a short Czech medical prompt anchor.

## Scope

- `C-6` Client-side VAD.
- `C-8` Whisper initial-prompt anchor.

## Affected Areas

- `src/hooks/useMediaRecorder.ts`
- `src/app/api/demo/transcribe/route.ts`
- `package.json`

## Constraints

- ANOTE-web only. Pattern reimplemented from scratch; no `ANOTE_mobile` imports.
- Fallback path must remain functional.

## Validation

- 30 s silent-then-speech sample produces no silence-induced hallucination.
- Forced VAD-init failure still transcribes via raw-upload path.

## Implementation Result (2026-04-25)

### Files changed

- `package.json` — added `@ricky0123/vad-web@^0.0.30` and `onnxruntime-web@^1.24.3`.
- `src/lib/speech-vad.ts` (new) — dynamic-import wrapper around `MicVAD.new`. Returns `{ disabled, hasSpeech, consume, destroy }`. On any failure (CSP block, asset 404, runtime error) returns `disabled: true` and the caller skips filtering. Assets pinned to versioned jsDelivr URLs (`@ricky0123/vad-web@0.0.30`, `onnxruntime-web@1.24.3`).
- `src/hooks/useMediaRecorder.ts` — calls `createSpeechVad(stream)` after acquiring the mic; tracks speech across each segment via `onSpeechStart` + `onFrameProcessed` callbacks; on segment rotation drops the segment when VAD is enabled and no speech frame was observed; final stop always delivers the segment regardless. `cleanup()` destroys VAD.
- `src/app/api/demo/transcribe/route.ts` — appends Whisper `prompt` field with a short Czech medical anchor (`Lékařská zpráva. Pacient udává obíže, anamnéza, vyšetření, diagnóza, doporučení.`).
- `staticwebapp.config.json` — minimum CSP additions required for VAD via jsDelivr:
  - `script-src` += `'wasm-unsafe-eval' https://cdn.jsdelivr.net` (ORT wasm + worklet script load).
  - `connect-src` += `https://cdn.jsdelivr.net` (asset fetch).
  - new `worker-src 'self' blob:` (AudioWorklet / ort worker).

### Behavior

- VAD initializes asynchronously alongside MediaRecorder. While initializing, all segments are uploaded normally.
- Once ready, only segments containing at least one speech frame (`isSpeech > 0.6`) are uploaded. Silent segments are dropped.
- Final segment on user stop always uploads (avoids losing trailing speech).
- VAD failure (`disabled: true`) makes the filter a no-op — identical to pre-change behavior.

### Validation

- Local: `npx tsc --noEmit` clean.
- Local: `npm run build` succeeds; routes intact.
- Production deployment later confirmed as part of the full `TASK-0014` rollout on 2026-04-25.

### Deployment confirmation

- VAD filtering, jsDelivr-backed runtime support, and the Czech prompt anchor are reported live on production.
- The parent deployment summary states no silence-induced demo regressions were observed in the shipped hardening pass.

### Mobile boundary check

- No `ANOTE_mobile` files modified or imported.
- Implementation is independent (the wrapper is a thin lib-direct call, not a port of any mobile module).

### Rollback

- Remove `vadRef` lines + the `speechSeen` block in `src/hooks/useMediaRecorder.ts`.
- Delete `src/lib/speech-vad.ts`.
- Remove `prompt` field append in `src/app/api/demo/transcribe/route.ts`.
- Revert CSP in `staticwebapp.config.json` to remove `'wasm-unsafe-eval'`, `https://cdn.jsdelivr.net` in script-src/connect-src, and the new `worker-src` directive.
- `npm uninstall @ricky0123/vad-web onnxruntime-web`.

## Notes

- Parent: TASK-0014. Phase 3.
