# Session Handoff: ANOTE Web (App 3) Initial Inspection

## Session Date

2026-04-19

## Goal

Inspect the `ANOTE-web` repository and write a grounded application summary into the shared knowledge layer as `app-3-overview.md`. Update cross-project documentation (system landscape, glossary) with newly discovered facts.

## What Was Learned

- ANOTE Web is a Next.js 16.2.2 marketing website + live browser demo for the ANOTE medical dictation product, deployed to Azure Static Web Apps (Free tier, West Europe).
- **First confirmed cross-app runtime dependency:** The web demo's `/api/demo/report` route calls the same ANOTE FastAPI backend that powers App 2 (ANOTE Mobile). This is the first inter-application integration discovered in the 3-app ecosystem.
- The site supports Czech (default) and English locales via `[lang]` dynamic segments with JSON dictionary files.
- All API keys are server-side only (proxied through Next.js API routes). No secrets are exposed to the browser.
- **No automated tests exist.** This is the only application in the ecosystem with zero test coverage. The only CI validation is TypeScript type checking and a production build.
- A detailed West Europe migration plan exists, and evidence suggests the migration has been partially or fully completed.
- The `TRANSCRIPTION_IMPROVEMENTS.md` file contains cross-app findings from the mobile team (Whisper → gpt-4o-mini-transcribe migration, hallucination filter) that are pending implementation in the web app.
- Contact form submissions are stored in `data/submissions.json` — a file-based approach that may not be reliable on Azure SWA's ephemeral serverless environment.
- Two GitHub Actions workflows exist for the same branch, which may cause duplicate builds.

## Files Reviewed

- `ANOTE-web/README.md` — primary documentation (183 lines)
- `ANOTE-web/package.json` — dependencies and scripts
- `ANOTE-web/.env.example`, `.env.local.example` — environment variable templates
- `ANOTE-web/next.config.ts`, `tsconfig.json` — build and TS configuration
- `ANOTE-web/staticwebapp.config.json` — security headers, CSP
- `ANOTE-web/.github/workflows/azure-static-web-apps.yml` — CI/CD pipeline
- `ANOTE-web/.github/workflows/azure-static-web-apps-yellow-forest-086a45303.yml` — auto-generated SWA workflow
- `ANOTE-web/IMPLEMENTATION_PLAN.md` — 4-phase build plan (434 lines)
- `ANOTE-web/WEST_EUROPE_MIGRATION_PLAN.md` — region migration plan (241 lines)
- `ANOTE-web/TRANSCRIPTION_IMPROVEMENTS.md` — cross-app transcription findings (230 lines)
- `ANOTE-web/AGENTS.md`, `CLAUDE.md` — AI agent rules
- `ANOTE-web/src/proxy.ts` — locale routing logic
- `ANOTE-web/src/app/api/demo/transcribe/route.ts` — Whisper transcription proxy
- `ANOTE-web/src/app/api/demo/report/route.ts` — ANOTE backend report proxy
- `ANOTE-web/src/app/api/contact/route.ts` — contact form endpoint
- `ANOTE-web/src/app/api/admin/submissions/route.ts` — admin submissions viewer
- `ANOTE-web/src/lib/demo-rate-limit.ts` — rate limiting implementation
- `ANOTE-web/src/lib/submissions.ts` — file-based submission store
- `ANOTE-web/src/lib/email.ts` — nodemailer email sender
- `ANOTE-web/src/hooks/useDemoSession.ts` — demo state machine
- `ANOTE-web/src/app/layout.tsx`, `src/app/[lang]/layout.tsx` — root and locale layouts
- `ANOTE-web/src/app/[lang]/demo/page.tsx` — demo page
- All directory listings for `src/`, `src/app/`, `src/components/`, `src/lib/`, `data/`, `public/`

## Files Changed

- `Knowledge.Healthcare/applications/app-3-overview.md` — populated with full application overview (replaced empty template)
- `Knowledge.Healthcare/system-landscape.md` — updated with all 3 applications, cross-app integrations, complete environments table, expanded external services and shared dependencies
- `Knowledge.Healthcare/glossary.md` — added 5 new terms (Azure SWA, proxy.ts, Plausible Analytics, hallucination filter, Azure SWA deploy); updated `anote-openai` entry to include App 3
- `Knowledge.Healthcare/handoffs/2026-04-19-app3-initial-inspection.md` — this file

## Decisions Made

- Classified this repository as App 3 based on the existing numbering in the Knowledge.Healthcare directory (App 1 = Medical Advisor, App 2 = ANOTE Mobile, App 3 = empty template).
- Updated the system landscape to replace "unknown" entries for App 2 and App 3 with confirmed details from all three inspections.

## Assumptions

- The West Europe migration for the SWA resource has been completed (based on hostname `.7` suffix differing from the East US 2 `.1` suffix). Needs verification: yes.
- The `data/submissions.json` file-based storage is unreliable on Azure SWA. Needs verification: yes.
- The two GitHub Actions workflows both trigger on push to `main` and may cause duplicate deployments. Needs verification: yes.
- The IMPLEMENTATION_PLAN.md Phase 4 checkboxes are stale — the demo is fully implemented. Needs verification: no (confirmed by code inspection).

## Unresolved Questions

- Is `data/submissions.json` persistent across Azure SWA function invocations?
- Which Azure Whisper deployment is the production `AZURE_WHISPER_ENDPOINT` pointing to?
- Which backend URL is used in production — West Europe or West US 2?
- Are both GitHub Actions workflows active simultaneously?
- Is the custom domain `anote.cz` configured on the new SWA resource?
- What is the actual Lighthouse performance score for the production site?

## Recommended Next Step

1. Verify the Azure SWA region and active workflows by running `az staticwebapp show` and checking GitHub Actions run history.
2. Investigate the `data/submissions.json` persistence issue — this is the most operationally risky finding.
3. Document the shared ANOTE FastAPI backend as a cross-cutting infrastructure concern, since both App 2 and App 3 depend on it and it uses a single static Bearer token.
4. Consider adding at minimum API route tests for the web app's proxy endpoints.
