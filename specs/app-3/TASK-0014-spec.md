# Technical Spec — TASK-0014
## ANOTE-web Demo Hardening Parent Spec

> **App:** app-3 (ANOTE-web)
> **Task:** TASK-0014
> **Created:** 2026-04-23
> **Status:** spec-complete — implementation-ready
> **Repo:** `/Users/ivananikin/Documents/ANOTE-web`

---

## 1. Summary

This parent spec defines the execution structure for the deferred ANOTE-web demo hardening work that followed `TASK-0013`. The scope stays strictly inside ANOTE-web code and ANOTE-web-owned Azure configuration. The purpose is to preserve `TASK-0014` as one umbrella task while splitting implementation into ordered child execution tracks that can ship independently.

---

## 2. Scope And Boundaries

### In Scope

- ANOTE-web repository changes only
- ANOTE-web-owned Azure configuration only:
- `anote-web-api` Container App env or scale settings
- ANOTE-web Static Web App app settings and `staticwebapp.config.json`
- Demo hardening for latency, cold-start behavior, streaming responsiveness, and transcription quality
- Ordered child-task breakdown for later execution

### Out Of Scope

- Any code, config, deployment, or path changes inside `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile`
- Reusing or switching to the mobile backend as the solution
- Changes to the mobile Container App (`anote-api`) or mobile OpenAI deployment selections
- Cross-app refactors or shared infrastructure redesign beyond ANOTE-web-owned settings
- Server-side ffmpeg silence trimming (`C-7`)
- Pure energy-gate VAD (`C-9`)

### Boundary Rule

`ANOTE_mobile` may be inspected as read-only architectural reference only. Any implementation pattern borrowed from it must be reimplemented independently inside ANOTE-web.

---

## 3. Current Behavior

1. `TASK-0013` already improved direct warm `/report` latency by changing the `anote-web-api` model deployment from `gpt-5-mini` to `gpt-4-1-mini` with `gpt-5-nano` fallback.
2. `src/app/api/demo/report/route.ts` currently proxies report generation as a single JSON response and does not expose SSE behavior.
3. `src/hooks/useDemoSession.ts` currently calls `streamReport()` but receives the full report at once, then appends it as one block.
4. Periodic report regeneration during recording currently has no transcript-growth debounce threshold and does not explicitly prefer the newest transcript over stale in-flight requests.
5. `src/hooks/useMediaRecorder.ts` currently rotates raw audio chunks without client-side VAD.
6. `src/app/api/demo/transcribe/route.ts` forwards audio to the configured Azure transcription endpoint with no initial-prompt anchor.
7. There is currently no `src/app/api/demo/health/route.ts` pre-warm proxy route.
8. `staticwebapp.config.json` currently allows only the ANOTE-web backend host and `anote-openai.openai.azure.com` in `connect-src`.

---

## 4. Proposed Behavior

After implementation:

1. `TASK-0014` remains the parent tracking task, but execution occurs through ordered child tasks.
2. `anote-web-api` runs with the faster verified chat deployment and `minReplicas = 1` to reduce cold-start latency and cold-start 500s.
3. The demo page pre-warms the report path via a lightweight health request and retries one report-generation failure on 5xx once before surfacing an error.
4. Client-side VAD reduces silent uploads; if VAD setup fails, the existing raw-upload behavior remains available.
5. The transcription proxy sends a Czech prompt anchor to improve medical transcription quality.
6. `/api/demo/report` can expose SSE when explicitly requested, and the client consumes incremental tokens rather than waiting for one final block.
7. Report regeneration is throttled by transcript-growth debounce and stale in-flight requests are canceled in favor of the newest transcript.
8. The transcription endpoint can later migrate to `gpt-4o-mini-transcribe` with the minimum required CSP expansion and a focused Czech smoke check.

---

## 5. Ordered Phases

Execution order is fixed and should be preserved when child tasks are created.

1. **A-1 / A-2 first**
Reason: config-only, highest immediate impact, minimal code risk.

2. **E-11 / E-12 second**
Reason: smallest ANOTE-web code changes, directly complements cold-start mitigation, low coordination cost.

3. **C-6 / C-8 third**
Reason: transcription quality and silence handling should improve before streaming work is layered on top.

4. **B-3 / B-4 / B-5 fourth**
Reason: streaming and request-control changes are the highest code-risk area and should build on already-stabilized config and transcription behavior.

5. **D-10 last**
Reason: endpoint migration and CSP expansion should happen after earlier latency and UX improvements are understood, and it requires focused validation against an independent Czech smoke sample.

---

## 6. Phase Definitions

### Phase 1 — Config Hardening (`A-1` / `A-2`)

- **Objective:** reduce direct backend latency and eliminate cold-start scale-to-zero failures on `anote-web-api`.
- **Likely files / config touched:** Azure Container App env or scale settings only; no ANOTE-web repo file is required unless deployment notes are updated.
- **Expected outcome:** faster or unchanged-worse chat-model selection for the current Czech report payload; `minReplicas = 1`; lower cold-start failure risk.
- **Dependencies:** Azure access; current `TASK-0013` deployment state; ability to compare `gpt-4o-mini` vs `gpt-4-1-mini` on comparable payloads.
- **Validation approach:** measure `/report` latency on a representative ~4k-char Czech transcript; compare p50 before/after; confirm cold path no longer returns SWA-visible 500 from scale-to-zero wake-up.
- **Rollback / safety:** revert env or scale settings to prior values if latency worsens, cost is unacceptable, or stability drops.

### Phase 2 — Cold-Start Mitigation (`E-11` / `E-12`)

- **Objective:** reduce perceived first-use latency and smooth transient 5xx behavior from the browser side.
- **Likely files / config touched:** `src/app/[lang]/demo/page.tsx`, `src/app/api/demo/health/route.ts` (new), `src/hooks/useDemoSession.ts`.
- **Expected outcome:** demo page mount triggers a non-blocking pre-warm request; one client retry occurs for report 5xx failures before user-facing error state.
- **Dependencies:** Phase 1 should land first; existence of a usable backend or proxy health path.
- **Validation approach:** open a cold demo page and confirm pre-warm fires without blocking UI; simulate or observe one transient 5xx and confirm exactly one retry occurs.
- **Rollback / safety:** remove the mount-triggered pre-warm and the retry wrapper if they create duplicate load, misleading UX, or extra backend churn.

### Phase 3 — Transcription Quality Hardening (`C-6` / `C-8`)

- **Objective:** reduce silence-induced hallucinations and improve Czech medical transcript quality before report generation.
- **Likely files / config touched:** `src/hooks/useMediaRecorder.ts`, `src/app/api/demo/transcribe/route.ts`, package/dependency files if VAD libraries are added.
- **Expected outcome:** chunks with detected speech are uploaded preferentially; VAD init failure falls back to current raw behavior; transcription requests include a short Czech medical prompt anchor.
- **Dependencies:** ANOTE-web-only implementation; browser compatibility for `@ricky0123/vad-web` and `onnxruntime-web`; no dependency on mobile code.
- **Validation approach:** test a 30-second silent-then-speech sample; confirm no silence-induced hallucination path; verify fallback still transcribes if VAD fails to initialize.
- **Rollback / safety:** disable or remove VAD integration while preserving current chunk upload behavior; remove the prompt field if it causes regression.

### Phase 4 — Streaming And Request Control (`B-3` / `B-4` / `B-5`)

- **Objective:** improve time-to-first-token and prevent wasteful or stale report generation requests.
- **Likely files / config touched:** `src/app/api/demo/report/route.ts`, `src/hooks/useDemoSession.ts`, and `anote-web-api` backend implementation for SSE support.
- **Expected outcome:** `/report` supports optional SSE streaming; the client renders incremental tokens; small transcript deltas do not trigger regeneration; stale in-flight requests are aborted in favor of the latest transcript.
- **Dependencies:** stable Phase 1-3 behavior; backend support for incremental generation hooks or equivalent streamable chunks.
- **Validation approach:** verify first visible token arrives within target on warm runs; confirm transcript growth under 30 chars does not trigger regeneration; confirm a new chunk cancels the older request path.
- **Rollback / safety:** keep non-streaming JSON path available; gate SSE by explicit query flag so the legacy response mode can remain as a fallback.

### Phase 5 — Endpoint Migration And Smoke Validation (`D-10`)

- **Objective:** migrate ANOTE-web transcription to `gpt-4o-mini-transcribe` on the intended host with the minimum required CSP change and focused validation.
- **Likely files / config touched:** ANOTE-web SWA app settings, `staticwebapp.config.json`, possibly deployment documentation.
- **Expected outcome:** `AZURE_WHISPER_ENDPOINT` points to the Sweden Central transcription deployment; CSP includes only the additional host actually used by ANOTE-web; Czech smoke sample quality is acceptable.
- **Dependencies:** identification of the current production endpoint; independent Czech smoke sample; final confirmation that the new host is required.
- **Validation approach:** verify live transcription works against the new endpoint; run a small independent Czech smoke sample that is not the mobile FLEURS set; confirm CSP allows only used hosts.
- **Rollback / safety:** revert endpoint and CSP host addition if transcription quality drops, latency is unacceptable, or CSP change is not needed.

---

## 7. Interface And Behavior Expectations

### `/report` SSE Behavior

- SSE must be opt-in, gated by an explicit query flag rather than replacing the current JSON mode outright.
- The response format should be `text/event-stream` with incremental text payloads suitable for token or chunk-level UI updates.
- The server should terminate the stream cleanly and preserve a non-streaming fallback path.

### Incremental Token Handling In `useDemoSession.ts`

- `streamReport()` should call `onToken` repeatedly as chunks arrive.
- The report state should be cleared only when a new generation actually begins.
- Incremental updates must append in order and avoid duplicating prior content.

### Cancellation And Stale Request Behavior

- The newest transcript always wins.
- Any in-flight report request for an older transcript should be aborted when a newer eligible chunk arrives.
- Aborted requests must not overwrite state or surface as user-visible errors.

### Debounce Behavior

- Periodic regeneration should be skipped when transcript growth since the last report request is fewer than 30 characters.
- Final post-recording generation should still run even if the final delta is small.

### VAD Fallback Behavior

- If VAD initializes successfully, only speech-positive chunks should be uploaded.
- If VAD initialization fails or required assets cannot load, recording must fall back to the current raw-upload behavior without blocking demo usage.
- Fallback must not require any mobile code or shared runtime.

### Health Pre-Warm Route Behavior

- The demo page should issue a non-blocking `GET /api/demo/health` on mount.
- The route should be minimal and safe to call repeatedly.
- Pre-warm must not block rendering, display user-facing loading state, or fail the page if the ping errors.

### CSP Update Constraints

- `staticwebapp.config.json` must be expanded only for hosts ANOTE-web actually uses.
- No speculative host additions.
- Existing security headers should remain otherwise unchanged.

### Endpoint Migration Constraints

- D-10 must change only ANOTE-web-owned transcription endpoint configuration.
- It must not modify mobile transcription configuration or route traffic through the mobile backend.
- Validation should be done with an independent Czech sample, not by reusing the mobile FLEURS set.

---

## 8. Validation Expectations

### Core Targets

- `/report` p50 end-to-end through SWA: `<= 6 s` warm
- `/report` p50 end-to-end through SWA: `<= 10 s` cold
- perceived time-to-first-token on `/report`: `<= 1.5 s`

### Practical Validation

| Check | Method |
|------|--------|
| Warm latency | Measure repeated warm `/report` runs through the ANOTE-web path on a representative Czech transcript |
| Cold behavior | Measure first request after cold idle or after scale-down conditions; confirm no cold-start 500 path after Phase 1 |
| Time to first token | Observe streamed response timing in browser network/devtools during Phase 4 |
| Silent-then-speech behavior | Use a 30 s silence-then-speech sample and confirm no silence-induced hallucinated transcript/report content |
| D-10 smoke sample | Use a small independent Czech audio sample not sourced from the mobile FLEURS set |
| No mobile changes | Confirm no files under `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile` were modified and no mobile paths appear in implementation diffs |
| CSP correctness | Confirm only actively used ANOTE-web hosts are present in `connect-src` |

### Minimum Engineering Validation Per Child Task

- Relevant ANOTE-web local checks still pass after code changes
- Any Azure config change is recorded with the exact value changed and rollback value
- Validation notes capture whether results were warm, cold, local, or deployed

---

## 9. Recommended Child-Task Breakdown

Keep `TASK-0014` as the parent and create the following child execution tasks.

1. **TASK-0014-A** — Config hardening (`A-1` / `A-2`)
2. **TASK-0014-B** — Cold-start mitigation (`E-11` / `E-12`)
3. **TASK-0014-C** — Transcription quality hardening (`C-6` / `C-8`)
4. **TASK-0014-D** — Streaming and request control (`B-3` / `B-4` / `B-5`)
5. **TASK-0014-E** — Endpoint migration and smoke validation (`D-10`)

Child tasks should inherit the same strict boundary: ANOTE-web implementation only, `ANOTE_mobile` read-only reference only.

---

## 10. Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Azure config changes improve one metric while harming another | Medium | Compare before/after values on the same report payload and keep rollback values ready |
| Pre-warm and retry introduce unnecessary extra load | Medium | Keep both minimal, non-blocking, and limited to one retry |
| VAD bundle/runtime integration is unstable in the browser | Medium | Preserve raw-upload fallback and keep the integration isolated to ANOTE-web |
| SSE support in `anote-web-api` is more complex than expected | Medium | Keep streaming behind an opt-in query flag and retain JSON fallback |
| Stale request handling causes duplicate or overwritten report state | Medium | Treat aborts as non-errors and ensure only the latest request can update report state |
| CSP broadening becomes overly permissive | Low | Add only the exact host required for ANOTE-web |
| Mobile boundary accidentally leaks into implementation notes or diffs | Low | Explicitly check for mobile path references before finalizing each child task |

---

## 11. Open Questions

1. Does `anote-web-api` already expose a small `/health` endpoint, or should one be added there as part of Phase 2 support?
2. Does the current backend generation stack already expose incremental generation hooks sufficient for SSE, or is additional backend work needed first?
3. Are `@ricky0123/vad-web` and `onnxruntime-web` acceptable in the current ANOTE-web runtime and deployment constraints?
4. What exact independent Czech smoke sample should be used for D-10 validation?
5. Is the `ANOTE-web/TASK-0013-IMPLEMENTATION.md` reference stale, or does it exist outside the currently inspected repo state?

---

## 12. Rollout Notes

- Each child task should be independently shippable.
- Earlier phases should land before later phases are started unless a blocking discovery forces resequencing.
- Phase 4 should preserve legacy non-streaming behavior until streamed behavior is validated.
- Phase 5 should be held until the endpoint and CSP need are confirmed and the smoke sample is prepared.
