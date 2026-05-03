# Task: ANOTE-web demo streaming hardening: SSE, debounce, and stale request cancellation

## Metadata

- **ID:** TASK-0014-D
- **Parent:** TASK-0014
- **Created:** 2026-04-25
- **Updated:** 2026-04-25
- **Author:** Implementation agent (per TASK-0014 spec)
- **Status:** deployed
- **App(s):** app-3
- **Priority:** high
- **Type:** infra

## Problem

`/report` returns one JSON blob; `streamReport` calls `onToken` once. Periodic regeneration runs even on tiny transcript deltas, and stale in-flight requests can overwrite newer state.

## Desired Outcome

- `anote-web-api` exposes opt-in SSE for `/report`.
- `/api/demo/report/route.ts` pipes SSE through.
- `streamReport` consumes incremental tokens.
- Periodic regeneration skipped when transcript grew `< 30` chars.
- Newer transcript aborts older in-flight `/report`.

## Scope

- `B-3` SSE streaming.
- `B-4` Debounce.
- `B-5` Cancel stale `/report`.

## Affected Areas

- `anote-web-api` backend (SSE support).
- `src/app/api/demo/report/route.ts`.
- `src/hooks/useDemoSession.ts`.

## Constraints

- SSE gated by explicit query flag; non-streaming JSON path preserved.
- Aborts must not surface as user-visible errors.

## Validation

- TTFT `<= 1.5 s` on warm runs.
- Sub-30-char transcript growth does not trigger regeneration.
- Newer chunk aborts older request cleanly.

## Implementation Result (2026-04-25)

### Files changed

- `src/app/api/demo/report/route.ts` — added opt-in `?stream=1` SSE pass-through. Forwards the same flag upstream with `Accept: text/event-stream`, returns the response body as `text/event-stream` (with `Cache-Control: no-cache, no-transform`, `Connection: keep-alive`, `X-Accel-Buffering: no`). JSON path retained as default.
- `src/hooks/useDemoSession.ts`
  - `streamReport` now accepts `useStream` flag. When `true`, opens SSE, parses `data:` events line-by-line, supports raw text payloads or `{"text"|"token"|"delta"}` JSON, and calls `onToken` incrementally. When `false`, legacy JSON behavior is unchanged. The 5xx single-retry from Phase 2 is preserved.
  - Added `ENABLE_SSE_REPORT` constant (default `false`). Single flip to enable end-to-end once `anote-web-api` exposes `?stream=1`.
  - Added `REPORT_MIN_DELTA_CHARS = 30` debounce (`B-4`). Periodic `handleChunk` skips `/report` when transcript growth since last issued report is `< 30` chars. Final stop and upload paths bypass the debounce.
  - Added dedicated `reportAbortRef` controller (`B-5`). New chunk aborts any in-flight `/report` immediately so the newest transcript wins. Transcribe queueing is preserved so already-uploaded audio bytes are not wasted.
  - `reset` and `startRecording` clear the report controller and reset the debounce baseline. `useEffect` unmount cleanup aborts both controllers.
  - `AbortError` continues to be swallowed; aborted reports do not surface as user errors and do not overwrite report state (the next request issues a fresh `SET_REPORT`/incremental tokens).

### Behavior

- SSE is opt-in. Default behavior is byte-for-byte unchanged from Phase 2 because `ENABLE_SSE_REPORT === false` and the proxy does not forward `?stream=1` until requested.
- When SSE is enabled and the upstream supports it, `onToken` fires incrementally per event — incremental UI updates work without further client changes.
- If SSE is enabled but upstream returns JSON (no `text/event-stream` content-type), client falls back to JSON parsing automatically.
- Periodic regeneration of `/report` skips updates when growth is `< 30` chars.
- A newer chunk aborts the prior `/report` (visible as silent abort, not as error).

### Validation

- Local: `npx tsc --noEmit` clean.
- Local: `npm run build` succeeds; routes intact.
- Production deployment later confirmed as part of the full `TASK-0014` rollout on 2026-04-25.
- Diff boundary check: no `ANOTE_mobile` paths in any changed file.

### Deployment confirmation

- The backend dependency was resolved in the deployed `anote-web-api:0.2.0` release.
- User-reported production validation confirmed live SSE on `GET/POST /report?stream=1` with incremental deltas, canonical final payload, and `[DONE]` terminator.
- Reported production timing: TTFT `0.38 s`, total `3.13 s`, `263` deltas.

### Rollback

- `src/app/api/demo/report/route.ts`: remove the `wantsStream` branch and pass-through `Response`.
- `src/hooks/useDemoSession.ts`: remove `useStream` parameter handling, `ENABLE_SSE_REPORT`, debounce constant + `lastReportTranscriptLenRef` + skip block, `reportAbortRef` and its plumbing. Restore the previous single-controller flow.

## Notes

- Parent: TASK-0014. Phase 4.
