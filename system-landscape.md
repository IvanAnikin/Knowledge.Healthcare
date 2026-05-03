# System Landscape

> Last updated: 2026-04-25. Based on inspection of the application repositories plus reported production deployment updates for App 3 `TASK-0014`.

## Overall System Summary

The healthcare project consists of 3 applications built by the same developer/team, all targeting Czech-speaking healthcare professionals and patients. The applications share Azure infrastructure (OpenAI resources, subscription). As of the reported `TASK-0014` deployment, App 3 (ANOTE Web) now runs its live demo against its own ANOTE-web-owned backend instead of App 2's backend.

## Applications

| Application | Purpose | Status | Repo Location |
|-------------|---------|--------|---------------|
| App 1 — Medical Advisor | Czech-language multi-advisor AI chatbot for diabetes patient education | Active (deployed to production) | `/Users/ivananikin/Documents/medical_advisor` |
| App 2 — ANOTE Mobile | Czech medical dictation: mobile voice recording → on-device transcription → LLM-generated structured medical reports | Active (pilot with doctor user) | `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile` |
| App 3 — ANOTE Web | Marketing website + live browser demo for the ANOTE dictation product | Active (deployed to production) | `/Users/ivananikin/Documents/ANOTE-web` |

See `applications/` for detailed overviews of each application.

## Integrations

| Source | Target | Mechanism | Description |
|--------|--------|-----------|-------------|
| Medical Advisor (App 1) | Azure OpenAI (`anote-openai`) | HTTPS REST API (via Semantic Kernel SDK) | Chat completion (gpt-5.4-mini) and text embeddings (text-embedding-3-small) |
| ANOTE Mobile backend (App 2) | Azure OpenAI (`anote-openai`) | HTTPS REST API (via `openai` Python SDK) | GPT-5-mini / GPT-4.1-mini for report generation |
| ANOTE Mobile app (App 2) | Azure OpenAI (`anote-openai-swe`) | HTTPS REST (optional) | Cloud transcription via gpt-4o-mini-transcribe (Sweden Central) |
| ANOTE Mobile app (App 2) | ANOTE Mobile backend (App 2) | HTTPS POST with Bearer token | `/report` endpoint for report generation; `/send-report-email` for email |
| **ANOTE Web (App 3)** | **ANOTE-web backend (`anote-web-api`)** | **HTTPS POST via `/api/demo/report` proxy** | **Live demo report generation via the ANOTE-web-owned backend. `TASK-0014` reported backend split to `ANOTE-web/backend/` and live image `anote-web-api:0.2.0`.** |
| ANOTE Web (App 3) | Azure OpenAI (`anote-openai-swe`) | HTTPS POST via `/api/demo/transcribe` proxy | Live demo transcription via `gpt-4o-mini-transcribe` |
| ANOTE Web (App 3) | Plausible Analytics | Client-side `<script>` | Cookie-free web analytics with custom events |

### Cross-Application Dependency

The earlier confirmed App 3 -> App 2 backend runtime dependency is now superseded by the reported App 3 backend split completed during `TASK-0014`.

- App 3 now calls its own `anote-web-api` backend for `/report` and `/report?stream=1`.
- App 2 mobile backend (`anote-api`) was explicitly reported as unchanged.
- The shared dependency that remains visible across apps is infrastructure, not direct report-generation runtime coupling: Azure subscription, OpenAI resources, and operational conventions.

App 1 (Medical Advisor) remains self-contained with no runtime dependencies on the other applications.

## Data Flows

- **Medical Advisor (App 1):** Loads verified medical documents from filesystem at startup, injects them into LLM prompts, returns AI-generated responses to anonymous browser clients via SignalR. Conversations are ephemeral (in-memory on server, localStorage on client). No patient data.
- **ANOTE Mobile (App 2):** Doctor records audio → on-device Whisper transcription (audio never leaves device) → transcript sent to FastAPI backend → backend calls Azure OpenAI for structured report → report returned to mobile app. Reports stored locally on device as JSON files.
- **ANOTE Web (App 3):** Visitor records audio or uploads file in browser → audio proxied through Next.js API to `anote-openai-swe` `gpt-4o-mini-transcribe` → transcript proxied to `anote-web-api` → structured report or streamed report deltas returned to browser. Nothing persisted server-side. Contact form submissions stored in file-based JSON.

## Environments

| Environment | Application | Purpose | Notes |
|-------------|-------------|---------|-------|
| Development (local) | App 1 | Local dev on macOS | `dotnet run` on localhost:5113; API key via .NET User Secrets |
| Production | App 1 | Live system for patients | Azure App Service `medical-advisor-cz`, B1 Basic, Linux, West Europe |
| Development (local) | App 2 (mobile) | Local dev | Flutter + local FastAPI backend |
| Production | App 2 (backend) | Live backend for mobile app | Azure Container Apps, Consumption tier, West US 2 (migration to West Europe planned) |
| Development (local) | App 3 | Local dev on macOS | `npm run dev` on localhost:3000 |
| Production | App 3 | Live marketing site + demo | Azure Static Web Apps, Free tier, West Europe, with `anote-web-api` Container App backend |

No staging or pre-production environment has been identified for any application.

## External Services

| Service | Purpose | Used By | Notes |
|---------|---------|---------|-------|
| Azure OpenAI (`anote-openai`) | LLM inference (chat, embeddings, legacy whisper) | App 1, App 2 | West Europe; resource group `ANOTE`. Deployments include gpt-5-4-mini, text-embedding-3-small, gpt-5-mini, gpt-5-chat, whisper. |
| Azure OpenAI (`anote-openai-swe`) | Cloud transcription | App 2 (optional), App 3 | Sweden Central; hosts `gpt-4o-mini-transcribe`. Reported live for App 3 as of `TASK-0014-E`. |
| Azure App Service (`medical-advisor-cz`) | Web hosting | App 1 | B1 Basic, Linux, West Europe; resource group `medical-advisor-rg`; ~$13/month |
| Azure Container Apps (`anote-api`) | Backend API hosting | App 2 | Consumption tier, 0.5 CPU / 1 GB, resource group `anote-rg`. Currently West US 2. |
| Azure Container Apps (`anote-web-api`) | Backend API hosting | App 3 | Resource group `anote-rg`, image repo `ca859739e5daacr.azurecr.io/anote-web-api`; reported live on tag `0.2.0` with SSE support and `minReplicas=1`. |
| Azure Static Web Apps | Static site + serverless functions | App 3 | Free tier, West Europe; resource name `yellow-forest-086a45303` |
| Plausible Analytics | Web analytics | App 3 | Cookie-free, GDPR-friendly. Domain: `anote.cz` |
| Gmail SMTP | Contact form email | App 3 | Optional; nodemailer-based |
| Azure subscription | Infrastructure billing | All | Visual Studio Ultimate with MSDN (`8a3849cc-...`); single subscription |

## Shared Dependencies

- **Azure OpenAI resource `anote-openai`** (West Europe, RG `ANOTE`) — shared by all 3 applications. Model deployments: gpt-5-4-mini, text-embedding-3-small, gpt-5-mini, gpt-5-chat, whisper.
- **Azure OpenAI resource `anote-openai-swe`** (Sweden Central) — used by App 2 for optional cloud transcription and reported live for App 3 demo transcription.
- **Azure Container Apps resource group / operational surface (`anote-rg`)** — now hosts separate App 2 (`anote-api`) and App 3 (`anote-web-api`) backends.
- **Azure subscription (MSDN)** — single subscription hosts all Azure resources.
- **Bearer API token pattern** — App backends use bearer-token authentication. Whether App 2 and App 3 still share the same secret after the backend split is not confirmed here.

## Unresolved Architecture Questions

- Does the `anote-openai` resource have rate-limiting concerns if all 3 applications are active simultaneously?
- Is there a shared deployment or CI/CD strategy planned across the 3 applications?
- Are there data-sharing needs between applications (e.g., shared patient context, unified analytics)?
- What monitoring/observability strategy covers the system as a whole? None of the 3 apps have Application Insights or centralized logging.
- What observability and alerting now cover `anote-web-api` after the App 3 backend split?
- Is the bearer-token setup between App 3 SWA and `anote-web-api` distinct from App 2 now, or still operationally shared?
- What is the longer-term hosting and ownership plan for the new `ANOTE-web/backend/` codebase?

## Confirmed vs Assumed

### Confirmed (from source code inspection)

- All 3 apps use the same Azure subscription (MSDN) and the same `anote-openai` resource.
- App 3 is reported to use its own `anote-web-api` backend in production after `TASK-0014`.
- App 1 has no runtime dependency on Apps 2 or 3.
- No database exists in any application — all persistence is filesystem, localStorage, or in-memory.
- No staging or pre-production environment exists for any application.
- Single developer/operator (Ivan Anikin) across all repos.

### Cross-Repo Assumptions (need verification)

- The `anote-openai` resource group `ANOTE` is the same resource referenced by all 3 apps (matched by name and region, not by resource ID).
- The West Europe migration of App 3's SWA is complete (inferred from hostname suffix `.7` vs `.1`).
- The reported App 3 backend split corresponds to a durable repo-level ownership boundary, not just a deployment packaging split.

### Open Questions

See also per-app open questions in `applications/app-*-overview.md`.

1. What are the actual Azure OpenAI TPM quotas on `anote-openai`, and are they sufficient for concurrent usage by all 3 apps?
2. What is the exact long-term architecture of `anote-web-api` and its relation to App 2's backend code after the split?
3. Are App 2 and App 3 still sharing any authentication secrets or report-generation code paths operationally?
4. Has the Modified Access form for Azure OpenAI been submitted (zero data retention)?
5. What is the plan for app distribution (App 2) beyond APK sideloading?
6. Is the `data/submissions.json` in App 3 actually persistent on Azure SWA, or is it lost on cold starts?
