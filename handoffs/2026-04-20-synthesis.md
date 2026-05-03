# Session Handoff: Shared Memory Layer Synthesis

## Session Date

2026-04-20

## Goal

Synthesize the 3 application overviews (written 2026-04-19) into the shared memory layer files: project-overview.md, system-landscape.md, glossary.md, and current-priorities.md. Establish what the knowledge layer now knows, what remains unknown, and what should be documented before creating custom agents.

## What Was Learned

- The project is a 3-application Czech healthcare ecosystem built by a single developer (Ivan Anikin), targeting diabetes patients (education) and doctors (dictation/reporting).
- **One confirmed cross-app runtime dependency:** App 3 (ANOTE Web) calls App 2's FastAPI backend for live demo report generation. App 1 (Medical Advisor) is fully self-contained.
- **All 3 apps share** the `anote-openai` Azure OpenAI resource (West Europe) and a single MSDN Azure subscription.
- **No database exists in any application.** All persistence is filesystem-based, localStorage, or in-memory.
- **No staging environments** exist for any application.
- **No centralized monitoring or observability** exists across the system.
- App 3 has zero automated tests (the weakest link in the test chain).
- A hardcoded bearer token in App 2's mobile source code is a known security gap.

## Files Reviewed

- `applications/app-1-overview.md`
- `applications/app-2-overview.md`
- `applications/app-3-overview.md`
- `project-overview.md` (was template)
- `system-landscape.md` (was populated from prior session)
- `glossary.md` (was populated from prior session)
- `current-priorities.md` (was template)
- `handoffs/handoff-template.md`

## Files Changed

- `project-overview.md`: Populated with mission, users, business purpose, scope, risks, compliance concerns, success criteria.
- `system-landscape.md`: Added "Confirmed vs Assumed" section with explicit separation of facts, cross-repo assumptions, and open questions.
- `current-priorities.md`: Populated with active goals, blockers, next actions, and recently completed items.
- `handoffs/2026-04-20-synthesis.md`: This file.

## Decisions Made

- Glossary was already complete — no new terms needed from synthesis (all terms were captured during per-app inspection).
- system-landscape.md structure was already good — added a "Confirmed vs Assumed" section rather than restructuring.
- Separated project risks into a table in project-overview.md to make them actionable.

## Assumptions

- The `anote-openai` resource referenced by all 3 apps is the same Azure resource (matched by name and region, not verified by resource ID). Needs verification: yes.
- The bearer token in App 3's env vars matches the one hardcoded in App 2's `constants.dart`. Needs verification: yes.
- App 3's West Europe SWA migration is complete (inferred from hostname). Needs verification: yes.

## Unresolved Questions

1. What are the actual Azure OpenAI TPM quotas and are they sufficient for concurrent 3-app usage?
2. Is there a second ANOTE backend in West Europe (`anote-web-api`), or is that CSP entry stale?
3. Actual test pass/fail counts for all 3 apps (conflicting documentation).
4. Is the `data/submissions.json` in App 3 persistent on Azure SWA?
5. Has the Azure OpenAI Modified Access form been submitted?
6. What is the production Whisper endpoint for App 3?

## Recommended Next Step

1. **Run all test suites** (`dotnet test` for App 1, `pytest` for App 2 backend, `flutter test` for App 2 mobile) and record results. This is the highest-value verification action.
2. **Document the shared `anote-openai` resource** as a standalone infrastructure page — deployments, quotas, SKUs, which apps use what.
3. **Verify production env vars** for App 3 via `az staticwebapp appsettings list`.
4. **Then create custom agents** — with verified test baselines and confirmed infrastructure, agents can be configured with accurate per-app context and cross-app awareness.
