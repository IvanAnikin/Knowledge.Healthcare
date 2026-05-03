# Session Handoff: TASK-0009 and TASK-0016 Duplicate Review

## Session Date

2026-04-24

## Goal

Determine whether TASK-0009 and TASK-0016 are separate ANOTE-web tasks or the same homepage defect reported twice.

## What Was Learned

- `TASK-0009` describes the first homepage Features visual as unreadable placeholder bars.
- `TASK-0016` describes the same visual as blank next to `Dva režimy přepisu`.
- Code-level mapping confirms both reports point to the same implementation location: `src/components/sections/Features.tsx`, first feature slot, `featurePlaceholders[0] = "transcript"`.
- This is one underlying task with two symptom descriptions, not two separate implementation tasks.

## Files Reviewed

- `tasks/triage/TASK-0009.md`
- `dashboards/task-board.md`
- `current-priorities.md`
- `ANOTE-web/src/components/sections/Features.tsx`
- `ANOTE-web/src/dictionaries/cs.json`

## Files Changed

- `tasks/triage/TASK-0009.md` — marked as the canonical task for the homepage visual bug
- `tasks/triage/TASK-0016.md` — removed as a duplicate after folding relevant symptom detail into TASK-0009
- `dashboards/task-board.md` — clarified canonical vs duplicate handling
- `current-priorities.md` — removed TASK-0016 as a separate execution action and recorded the duplicate conclusion
- `handoffs/2026-04-24-task-0009-0016-duplicate-review.md` — this handoff note

## Decisions Made

- Treat `TASK-0009` as the canonical implementation task.
- Remove `TASK-0016` entirely after transferring the relevant symptom detail into `TASK-0009`.

## Assumptions

- None. The repo state is sufficient to conclude both tasks target the same implementation location.

## Unresolved Questions

- None for the duplication review itself.

## Recommended Next Step

- Implement the homepage visual fix under `TASK-0009` only.
