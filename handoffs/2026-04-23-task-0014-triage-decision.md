# Session Handoff: TASK-0014 Triage Decision

## Session Date

2026-04-23

## Goal

Fully triage `TASK-0014`, decide whether it should stay as one implementation task or be split, and update shared tracking documents while preserving the strict ANOTE-web-only implementation boundary.

## What Was Learned

- `TASK-0014` is actionable inside `app-3` because the current ANOTE-web codebase already contains the primary touchpoints for report streaming, retry behavior, pre-warm routing, media recording, transcription proxying, and CSP updates.
- The task is too large for one implementation task because it mixes five distinct workstreams: Azure-only config changes, small client/proxy latency mitigations, transcription-quality hardening, report streaming/state-management changes, and endpoint/CSP migration validation.
- The cleanest structure is to keep `TASK-0014` as the parent umbrella task and split execution into ordered follow-up tasks that preserve the original sequencing.
- A lightweight spec is recommended before execution so the split, interfaces, and validation expectations are explicit, especially for SSE streaming and client-side VAD.
- The strict boundary is still appropriate: implementation only in ANOTE-web plus its own Azure Container App / SWA settings; `ANOTE_mobile` remains read-only reference only.

## Files Reviewed

- `/Users/ivananikin/Documents/Knowledge.Healthcare/AGENTS.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/current-priorities.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/workflows/session-start-checklist.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/workflows/triage-process.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/workflows/session-end-checklist.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/tasks/inbox/TASK-0014.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/tasks/templates/triage-template.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/dashboards/task-board.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/applications/app-3-overview.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/handoffs/2026-04-23-task-0014-triage.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/handoffs/2026-04-23-anote-web-demo-report-task-triage.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/tasks/triage/TASK-0012.md`
- `/Users/ivananikin/Documents/ANOTE-web/src/hooks/useDemoSession.ts`
- `/Users/ivananikin/Documents/ANOTE-web/src/hooks/useMediaRecorder.ts`
- `/Users/ivananikin/Documents/ANOTE-web/src/app/api/demo/report/route.ts`
- `/Users/ivananikin/Documents/ANOTE-web/src/app/api/demo/transcribe/route.ts`
- `/Users/ivananikin/Documents/ANOTE-web/src/app/[lang]/demo/page.tsx`
- `/Users/ivananikin/Documents/ANOTE-web/staticwebapp.config.json`

## Files Changed

- `tasks/triage/TASK-0014.md` — moved from inbox, marked as `triaged`, and expanded triage content with implementation boundary, dependencies, affected areas, split recommendation, and `needs-spec` recommendation
- `dashboards/task-board.md` — moved `TASK-0014` from `Inbox` to `Triaged` and recorded that it is a parent task requiring ordered split execution
- `current-priorities.md` — updated the recommended next action for `TASK-0014` from direct execution to lightweight spec plus ordered follow-up tasks
- `handoffs/2026-04-23-task-0014-triage-decision.md` — recorded this triage outcome

## Decisions Made

- `TASK-0014` should not be executed as one large implementation task.
- `TASK-0014` should remain the parent umbrella task so the original grouped intent and sequencing remain visible.
- Recommended execution split:
- A-1/A-2 config hardening
- E-11/E-12 cold-start mitigation
- C-6/C-8 transcription quality hardening
- B-3/B-4/B-5 report streaming and request control
- D-10 transcription endpoint/CSP migration and smoke validation
- Recommend `@spec-writer` for a lightweight spec before execution.

## Assumptions

- The current ANOTE-web backend and proxy shape is stable enough that a lightweight spec, not a deep investigation phase, is the right next control-layer step. (needs verification: yes)
- The requested ordering reflects both product preference and sensible engineering sequencing, so the split should preserve that order. (needs verification: no)

## Unresolved Questions

- What exact child task IDs should be allocated for the post-spec execution split?
- Should the lightweight spec include explicit SSE response format details and VAD asset-loading/runtime constraints, or only high-level execution boundaries?
- Is the missing `ANOTE-web/TASK-0013-IMPLEMENTATION.md` reference stale, or does it exist outside the currently inspected repo state?

## Recommended Next Step

- Send `TASK-0014` to `@spec-writer` for a lightweight implementation spec that defines the ordered child-task split, SSE/VAD interface expectations, and validation plan, then create the follow-up execution tasks starting with A-1/A-2.
