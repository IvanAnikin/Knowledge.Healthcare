# Session End Checklist

Use this checklist at the end of every meaningful work session to preserve context for future work.

## Checklist

- [ ] **Update relevant documentation** -- If any files in this knowledge layer are now stale or incomplete because of work performed, update them.
- [ ] **Add a handoff note if needed** -- If the session produced meaningful context, create a new handoff in `handoffs/` using the template.
- [ ] **Update `current-priorities.md`** -- Reflect any changes to goals, blockers, in-progress items, or completed items.
- [ ] **Capture decisions** -- If any decisions were made, create an ADR in `decisions/` or note the decision in the handoff.
- [ ] **List the recommended next step** -- State clearly what the next session should focus on, either in the handoff or in `current-priorities.md`.

## App-Specific Gates

### app-4 (Health-Analysis) — frontend / visual / i18n changes

Before marking any app-4 frontend task `done`, the following gates MUST be run from `/Users/ivananikin/Documents/Health-Analysis/web/`:

- [ ] `npm run lint` — clean
- [ ] `npm run typecheck` — clean
- [ ] `npm test` (vitest) — all green
- [ ] `npm run build` — clean
- [ ] **`npm run test:e2e` (Playwright) — all green.** If a visual snapshot diff is expected (intentional UI change), run `npm run test:e2e:update` to refresh `web/e2e/analysis.spec.ts-snapshots/`, then re-run `npm run test:e2e` clean before marking done.

Rationale: TASK-0029 and TASK-0030 were marked `done` without running the e2e suite, leaving two stale assertions in `web/e2e/analysis.spec.ts` (`cgm v1.0.0`→`v1.1.0` and the heuristic-badge locator) that surfaced only during the TASK-0031 validation gate on 2026-04-29. Running e2e at done-time prevents this drift.

## Notes

- Not every session requires a handoff. If the session was trivial or exploratory with no meaningful output, a handoff may not be needed.
- When in doubt, leave a handoff. A short note costs little but can save significant time for the next contributor.
