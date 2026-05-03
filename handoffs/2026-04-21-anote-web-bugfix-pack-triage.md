# Session Handoff: ANOTE-web Bugfix Pack Triage

## Session Date

2026-04-21

## Goal

Convert a new ANOTE-web bugfix / cleanup requirement pack into structured, tracked tasks.

## What Was Learned

- The Bezpečnost issue already overlaps with existing TASK-0012, but that task was framed incorrectly as a new feature.
- The current repo confirms that security content is embedded inside `src/app/[lang]/typy-zprav/page.tsx` via the `Privacy` component under `id="security"`.
- The homepage `Více o bezpečnosti` link in `TrustStrip.tsx` currently routes users to `/typy-zprav#security` (or the English equivalent), which matches the reported bug.
- The reported unreadable features visual exactly matches the current `transcript` placeholder in `src/components/sections/Features.tsx`.
- TASK-0009 had been advanced to `tested`, but the new requirement pack shows the bug is still reproducible and the task needed to be reopened.

## Files Reviewed

- `/Users/ivananikin/Documents/Knowledge.Healthcare/AGENTS.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/current-priorities.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/applications/app-3-overview.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/workflows/session-start-checklist.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/workflows/triage-process.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/workflows/session-end-checklist.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/tasks/triage/TASK-0012.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/tasks/tested/TASK-0009.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/dashboards/task-board.md`
- `/Users/ivananikin/Documents/ANOTE-web/src/app/[lang]/typy-zprav/page.tsx`
- `/Users/ivananikin/Documents/ANOTE-web/src/components/sections/Features.tsx`
- `/Users/ivananikin/Documents/ANOTE-web/src/components/sections/TrustStrip.tsx`
- `/Users/ivananikin/Documents/ANOTE-web/src/components/layout/Navbar.tsx`
- `/Users/ivananikin/Documents/ANOTE-web/src/components/layout/Footer.tsx`
- `/Users/ivananikin/Documents/ANOTE-web/src/dictionaries/cs.json`
- `/Users/ivananikin/Documents/ANOTE-web/src/dictionaries/en.json`

## Files Changed

- `tasks/triage/TASK-0009.md` — reopened from `tested`, retitled, and rewritten around the still-unreadable `transcript` visual
- `tasks/triage/TASK-0012.md` — reframed from feature work to a direct bugfix/content-architecture correction
- `dashboards/task-board.md` — moved TASK-0009 back into triage and updated TASK-0012 title/type/notes
- `current-priorities.md` — reflected the two newly triaged app-3 bugfixes
- `dashboards/task-dashboard.html` — should be regenerated after this tracker update

## Decisions Made

- Reuse TASK-0012 instead of creating a duplicate Bezpečnost task; the correct fix is to rewrite its scope and classification.
- Reopen TASK-0009 instead of creating a duplicate features-visual task, because the new requirement is the same unresolved homepage UI bug.
- Treat the Bezpečnost issue as a bugfix / information-architecture correction, not a new feature.

## Assumptions

- The requirement pack reflects the current desired scope for ANOTE-web and supersedes the older feature framing of TASK-0012. (Needs verification: no)
- The quoted HTML snippet for the features issue is taken from the current running UI and accurately reflects the unresolved bug. (Needs verification: no)

## Unresolved Questions

- Should the dedicated Bezpečnost route be exposed in navbar/footer as part of this correction, or is fixing the current page separation and CTA target sufficient?
- For TASK-0009, should the replacement visual contain literal readable text, or is a clearer illustrative mock enough?

## Recommended Next Step

- Execute TASK-0012 first, then rework TASK-0009 and verify both changes in the browser before advancing them again.
