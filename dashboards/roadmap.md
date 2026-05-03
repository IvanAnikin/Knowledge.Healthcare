# Roadmap

> High-level view of planned work by application and time horizon.

## app-1: medical_advisor

| Now | Next | Later |
|-----|------|-------|
| | | |

## app-2: ANOTE_mobile

| Now | Next | Later |
|-----|------|-------|
| TASK-0036: Improve medical report quality (critical — allergy hallucination safety issue + 5 other report defects; needs spec) | TASK-0035: Fix app state reset on new recording | |

## app-3: ANOTE-web

| Now | Next | Later |
|-----|------|-------|
| | TASK-0019: branding rollout | TASK-0006: Demo page performance (deferred, backlog) |

**Completed (2026-04-20):** TASK-0001, TASK-0002, TASK-0003, TASK-0004, TASK-0005 — full content/copy/structural/animation batch. Build and type-check pass on all.

**Completed (2026-04-25):** TASK-0014 — demo hardening shipped to production with dedicated `anote-web-api` backend split, warm scale, pre-warm/retry, VAD silence filtering, SSE streaming, stale-cancel/debounce, and `gpt-4o-mini-transcribe` migration.

## app-4: Health-Analysis

| Now | Next | Later |
|-----|------|-------|
| | TASK-0030: Broz monthly comparison and post-meal reporting; TASK-0032: i18n + Czech language switch; TASK-0033: Broz CSV auto-mapping to Czech-localized field names | TASK-0031: Analysis window progressive load + foldable Episodes table; Phase 2 internal analytics sandbox; Phase 3 controlled agent mode |

## Cross-App

| Now | Next | Later |
|-----|------|-------|
| | | TASK-0006 deferred; may spawn cross-app task only if reactivated and backend cold start is confirmed as root cause |

## Risks and Dependencies

| Item | Type | Affects | Notes |
|------|------|---------|-------|
| TASK-0036 allergy hallucination — clinical safety defect | risk | app-2 | LLM misinterpreted "JAR" (dish soap brand) as "jara" (spring/pollen) and documented a false allergy. Incorrect allergy documentation is a patient safety risk. Must be resolved before broader rollout. |
| App-4 broader post-MVP direction still open | note | app-4 | The initial MVP path plus `TASK-0029` redesign are now reported tested. The main remaining near-term app-4 product choice is whether to prioritize `TASK-0030` or a new post-MVP extension task next. |
| TASK-0006 deferred to backlog | risk | app-3 | If reactivated and backend cold start found, new cross-app task needed. Do not expand scope of TASK-0006. |
| Temporary Azure hostname in use (from TASK-0004) | risk | app-3 | `https://yellow-forest-086a45303.7.azurestaticapps.net` used as placeholder in 9 locations. Must be replaced when production domain is confirmed. See follow-up items in task-board.md. |
| New App 3 backend split needs direct repo inspection | note | app-3 | Production notes now indicate `ANOTE-web/backend/` and `anote-web-api` are the active App 3 backend surfaces. Shared docs were updated from deployment evidence, but the new folder should still be reviewed directly in a future architecture pass. |
| impressum dict key still in cs.json / en.json | debt | app-3 | Impressum page now returns 404. Key can be removed once the page file is deleted. Low priority. |
| Testimonials section commented out | debt | app-3 | `src/app/[lang]/page.tsx`. Re-enable when doctor feedback is collected. No task needed until then. |
| BouncingChips animation not browser-tested | note | app-3 | Manual visual verification at multiple viewport widths is recommended before considering TASK-0003 fully signed off. |
| Old unused privacy/offline visuals in Features.tsx | debt | app-3 | Leftover after TASK-0003 visual replacement. Cosmetic cleanup only; no functional impact. |

---

## Usage

- **Now:** Actively in progress or about to start.
- **Next:** Committed for the near term, scoped and triaged.
- **Later:** Planned but not yet scoped in detail.
- Update this file when tasks are triaged or priorities shift.
