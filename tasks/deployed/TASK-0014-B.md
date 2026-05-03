# Task: ANOTE-web demo cold-start mitigation: pre-warm and single retry

## Metadata

- **ID:** TASK-0014-B
- **Parent:** TASK-0014
- **Created:** 2026-04-25
- **Updated:** 2026-04-25
- **Author:** Implementation agent (per TASK-0014 spec)
- **Status:** deployed
- **App(s):** app-3
- **Priority:** high
- **Type:** infra

## Problem

Demo first-use latency includes Container App cold start. No browser-side pre-warm exists and a transient 5xx surfaces directly to the user.

## Desired Outcome

- `GET /api/demo/health` proxy route exists and is non-blocking.
- Demo page mount fires a non-blocking pre-warm.
- `streamReport` retries once on 5xx before surfacing an error.

## Scope

- `E-11` Pre-warm ping.
- `E-12` Client retry.

## Affected Areas

- `src/app/[lang]/demo/page.tsx`
- `src/app/api/demo/health/route.ts` (new)
- `src/hooks/useDemoSession.ts`

## Constraints

- ANOTE-web repo only. No mobile imports or paths.
- Pre-warm must not block rendering or surface errors.

## Validation

- Cold demo page: pre-warm fires without blocking UI.
- One simulated/observed 5xx triggers exactly one retry.

## Implementation Result (2026-04-25)

### Files changed

- `src/app/api/demo/health/route.ts` (new) — minimal `GET` proxy to `${ANOTE_BACKEND_URL}/health`. 8 s timeout, `cache: "no-store"`. Always returns `{ ok, ... }` JSON with HTTP 200; never surfaces backend failure to caller.
- `src/components/demo/DemoUI.tsx` — `useEffect` on mount fires `fetch('/api/demo/health')` non-blocking. `.catch(() => {})` swallows errors. `AbortController` cleans up on unmount.
- `src/hooks/useDemoSession.ts` — `streamReport` retries exactly once on a 5xx response (`status >= 500 && status < 600`). Skips retry if signal is already aborted. 4xx and network errors are not retried.

### Behavior notes

- Pre-warm placed in `DemoUI.tsx` (the demo page's client mount) rather than `page.tsx`, since `page.tsx` is a Server Component. Effect runs only when the demo UI is rendered for the user, matching spec intent.
- Pre-warm is non-blocking: rendering does not wait for the fetch and pre-warm errors are swallowed.
- Retry is limited to one extra attempt and only for 5xx (transient cold-start / upstream blips).

### Validation

- Local: `npx tsc --noEmit` clean.
- Local: `npm run build` succeeds. New route `ƒ /api/demo/health` appears in route manifest.
- Production deployment later confirmed as part of the full `TASK-0014` rollout on 2026-04-25.

### Deployment confirmation

- The demo pre-warm route and one-time 5xx retry logic are reported live on the production SWA host.
- Parent validation captured successful `/health` and `/report` production runs after deployment.

### Mobile boundary check

- No `ANOTE_mobile` files modified or imported.
- `git diff` scope: `src/app/api/demo/health/route.ts`, `src/components/demo/DemoUI.tsx`, `src/hooks/useDemoSession.ts` only.

### Rollback

- Delete `src/app/api/demo/health/route.ts`.
- Revert pre-warm `useEffect` block in `src/components/demo/DemoUI.tsx`.
- Revert `streamReport` in `src/hooks/useDemoSession.ts` to single-fetch form.

## Notes

- Parent: TASK-0014. Phase 2.
