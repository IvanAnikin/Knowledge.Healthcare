# Implementation Plan — TASK-0014
## ANOTE-web Demo Hardening Parent Plan

> **Spec:** `specs/app-3/TASK-0014-spec.md`
> **App:** app-3 (ANOTE-web)
> **Repo:** `/Users/ivananikin/Documents/ANOTE-web`
> **Created:** 2026-04-23

---

## Sequencing

`TASK-0014` stays as the umbrella task, but implementation should proceed through five ordered child tasks:

1. Phase 1: `A-1` / `A-2` config hardening
2. Phase 2: `E-11` / `E-12` cold-start mitigation
3. Phase 3: `C-6` / `C-8` transcription quality hardening
4. Phase 4: `B-3` / `B-4` / `B-5` streaming and request control
5. Phase 5: `D-10` endpoint migration and smoke validation

This order should be preserved unless a later phase is explicitly re-triaged because of a blocker.

---

## Steps

### Step 1: Create Child Task For Config Hardening

- **What:** Materialize the first execution task covering `A-1` and `A-2`, then evaluate the best chat model and set `minReplicas = 1` on `anote-web-api`.
- **Where:** Child task file in the control layer; Azure Container App env and scale settings.
- **Validation:** Record before/after latency on a representative Czech report payload; confirm cold-start 500 path is no longer observed.
- **Rollback:** Restore previous model env values and scale settings.

### Step 2: Create Child Task For Cold-Start Mitigation

- **What:** Add a lightweight demo pre-warm route and a single client retry on report 5xx.
- **Where:** `src/app/[lang]/demo/page.tsx`, `src/app/api/demo/health/route.ts`, `src/hooks/useDemoSession.ts`.
- **Validation:** Confirm page mount fires a non-blocking pre-warm request; confirm exactly one retry occurs on transient 5xx.
- **Rollback:** Remove the pre-warm call, route, and retry wrapper.

### Step 3: Create Child Task For Transcription Quality Hardening

- **What:** Add client-side VAD with safe fallback and add a Czech prompt anchor to transcription requests.
- **Where:** `src/hooks/useMediaRecorder.ts`, `src/app/api/demo/transcribe/route.ts`, dependency manifests as needed.
- **Validation:** Run silent-then-speech check; verify fallback path still works when VAD initialization is forced to fail.
- **Rollback:** Remove VAD integration and revert to current raw-upload-only behavior; remove prompt field if needed.

### Step 4: Create Child Task For Streaming And Request Control

- **What:** Add opt-in SSE for `/report`, incremental token handling, debounce, and stale request cancellation.
- **Where:** `anote-web-api` backend implementation, `src/app/api/demo/report/route.ts`, `src/hooks/useDemoSession.ts`.
- **Validation:** Confirm streamed first-token timing, confirm sub-30-character transcript growth does not regenerate, confirm newer transcript cancels older requests cleanly.
- **Rollback:** Disable SSE path and return to JSON-only response mode while preserving debounce/cancellation rollback separately if needed.

### Step 5: Create Child Task For Endpoint Migration And Smoke Validation

- **What:** Move ANOTE-web transcription to `gpt-4o-mini-transcribe`, update CSP only for the required host, and run the Czech smoke sample.
- **Where:** SWA app settings, `staticwebapp.config.json`, validation notes.
- **Validation:** Confirm live transcription works against the migrated endpoint and the independent Czech smoke sample is acceptable.
- **Rollback:** Restore previous endpoint and remove the added CSP host if no longer needed.

---

## Checkpoints

| After Step | Check | Pass Criteria |
|-----------|-------|---------------|
| 1 | Config hardening applied | Faster or equal-best report model selected; `minReplicas = 1`; no regressions recorded |
| 2 | Cold-start mitigation works | Pre-warm is non-blocking; retry behavior is limited and correct |
| 3 | Transcription hardening works | Silence handling improves; fallback remains usable |
| 4 | Streaming path works | Incremental UI updates arrive early; stale requests no longer win |
| 5 | Endpoint migration validated | New endpoint works; CSP is minimal; Czech smoke sample passes |

---

## Final Validation

Before closing the parent task as implemented, confirm:

- Warm `/report` p50 through SWA is `<= 6 s`
- Cold `/report` p50 through SWA is `<= 10 s`
- Time to first token is `<= 1.5 s`
- No silence-induced hallucinations occur on the silent-then-speech sample
- `staticwebapp.config.json` includes only hosts ANOTE-web actually uses
- No files in `ANOTE_mobile` were modified
- No mobile paths or implementation imports appear in the ANOTE-web diff

---

## Recommended Child Task Titles

1. `TASK-0014-A` — ANOTE-web demo config hardening: model selection and min replicas
2. `TASK-0014-B` — ANOTE-web demo cold-start mitigation: pre-warm and single retry
3. `TASK-0014-C` — ANOTE-web demo transcription hardening: VAD fallback and Czech prompt anchor
4. `TASK-0014-D` — ANOTE-web demo streaming hardening: SSE, debounce, and stale request cancellation
5. `TASK-0014-E` — ANOTE-web demo transcription endpoint migration and Czech smoke validation

---

## Rollback Plan

If the full hardening effort needs to be partially or fully reverted, roll back in reverse phase order:

1. Revert D-10 endpoint and CSP changes
2. Disable SSE path and request-control changes if Phase 4 is unstable
3. Remove VAD integration while preserving current recording/transcription path
4. Remove pre-warm and retry logic
5. Restore previous `anote-web-api` env and scale settings

This order removes the most behaviorally coupled changes first while keeping the earlier low-level config baseline available for comparison.
