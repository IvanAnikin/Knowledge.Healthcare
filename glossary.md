# Glossary

> Add terms as they are encountered and confirmed. Organize by category. Keep definitions concise and unambiguous.

## Business Terms

| Term | Definition | Notes |
|------|-----------|-------|
| Advisor | A topic-specific AI chatbot mode within the Medical Advisor app, each with its own knowledge base, system prompt, and URL route | Source: `medical_advisor/appsettings.json`. Currently 5 advisors configured. |
| Context stuffing | Grounding technique where all source documents are injected into the LLM system prompt on every request | Used by 3 of 5 advisors. Alternative to RAG. |
| RAG (Retrieval-Augmented Generation) | Grounding technique where relevant document chunks are retrieved via vector search and injected per-query | Used by the 2 pump advisors due to large manual sizes (~114K tokens). |
| Grounding | The practice of constraining AI responses to information present in verified source documents | Core design principle of the Medical Advisor app. |

## Technical Terms

| Term | Definition | Notes |
|------|-----------|-------|
| Semantic Kernel | Microsoft's .NET-native AI orchestration SDK for chat completion, embeddings, and prompt management | Version 1.74.0 in `medical_advisor`. |
| Blazor Server | ASP.NET web framework using server-side rendering with real-time UI updates via SignalR WebSocket connections | The app's rendering model; requires WebSockets enabled on host. |
| SignalR | ASP.NET library for real-time server-to-client push communication over WebSockets | Powers token-by-token streaming of AI responses to the browser. |
| MudBlazor | MIT-licensed Material Design component library for Blazor | Version 9.2.0 in `medical_advisor`. |
| Circuit | A Blazor Server connection between a browser tab and the server; scoped services live per-circuit | ConversationState, MedicalAdvisorService, ThemeService are scoped per circuit. |
| Embeddings cache | A JSON file containing pre-computed vector embeddings for document chunks, avoiding re-embedding on restart | Located at `docs/pump/embeddings_cache.json` and `docs/pump2/embeddings_cache.json`. |
| `anote-openai` | Shared Azure OpenAI resource in West Europe, resource group `ANOTE` | Hosts gpt-5-4-mini, text-embedding-3-small, gpt-5-mini, gpt-5-chat, whisper. Used by all 3 apps: Medical Advisor (App 1), ANOTE Mobile (App 2), and ANOTE Web (App 3). |
| `anote-openai-swe` | Azure OpenAI resource in Sweden Central | Hosts gpt-4o-mini-transcribe (Whisper API). Used by ANOTE Mobile for optional cloud transcription. Source: `ANOTE_mobile/mobile/lib/config/constants.dart:23`. |
| sherpa_onnx | Cross-platform speech recognition library that runs ONNX models on-device (no server needed) | Used in ANOTE Mobile for on-device Whisper transcription. Flutter package version ^1.12.26. |
| Silero VAD | Lightweight Voice Activity Detection model (~640 KB ONNX) that filters silence from audio streams | Used in ANOTE Mobile before Whisper to prevent hallucinations on silent audio segments. |
| Whisper (on-device) | OpenAI's Whisper speech-to-text model, quantized to INT8 ONNX format for mobile deployment | ANOTE Mobile uses Whisper Small (~240 MB) and Whisper Turbo (~1 GB) variants via sherpa_onnx. |
| Visit type | A classification of a medical encounter that determines the report template used by the LLM | ANOTE Mobile supports 6 types: default, initial, followup, gastroscopy, colonoscopy, ultrasound. Source: `backend/main.py:68`. |
| Riverpod | Dart/Flutter state management library using providers and notifiers | Used in ANOTE Mobile for session state management. |
| Azure Static Web Apps (SWA) | Azure hosting service for static sites with built-in serverless API functions, CI/CD, SSL, and global distribution | Used by ANOTE Web (App 3). Free tier, West Europe. Serverless functions run Next.js API routes. |
| `proxy.ts` | Next.js 16 replacement for `middleware.ts` for edge-level request rewriting and locale routing | Used in ANOTE Web for Czech/English locale detection and URL rewriting. Source: `ANOTE-web/src/proxy.ts`. |
| Plausible Analytics | Privacy-friendly, cookie-free web analytics service (no cookie banner needed) | Used by ANOTE Web (App 3). GDPR-compliant by design. Source: `ANOTE-web/.env.example:23`. |
| Hallucination filter | Post-processing step applied to transcription output to remove known Whisper hallucination artifacts (fake subtitles, URLs, emoji) | Documented in `ANOTE-web/TRANSCRIPTION_IMPROVEMENTS.md`. Shared finding from ANOTE Mobile (App 2) team. |

## Clinical Terms

| Term | Definition | Notes |
|------|-----------|-------|
| CGM (Continuous Glucose Monitoring) | Technology for real-time tracking of blood glucose levels via a subcutaneous sensor | One of 4 knowledge base documents in the diabetes advisor. |
| TIR (Time in Range) | Percentage of time a patient's glucose stays within a target range; key CGM metric | Referenced in CGM document. |
| Gestational diabetes | Diabetes that develops during pregnancy | Dedicated advisor with its own knowledge base (`docs/gestational/`). |
| Hybrid closed-loop | Insulin pump system that automatically adjusts basal insulin delivery based on CGM readings | Topic of the Tandem Control IQ pump advisor. |
| Ketoacidosis | Dangerous condition where the body produces excess ketones; requires emergency medical attention | Mentioned in system prompts as an emergency referral trigger. |
| Hypoglycemia | Abnormally low blood glucose level | System prompts instruct emergency referral for severe cases. |

## Operational Terms

| Term | Definition | Notes |
|------|-----------|-------|
| ZIP deploy | Deployment method where the published app is zipped and uploaded to Azure App Service via `az webapp deploy` | Used by Medical Advisor (App 1); no CI/CD. |
| `az containerapp up` | Azure CLI command that builds a Docker image, pushes to ACR, and deploys to Azure Container Apps in one step | Used by ANOTE Mobile backend (App 2) for deployment. Source: `ANOTE_mobile/README.md:167`. |
| Cold start | The delay when an Azure App Service instance starts from an idle state | 60-90 seconds for Medical Advisor due to document loading. |
| User Secrets | .NET's built-in mechanism for storing secrets during local development, outside the source tree | Used for the Azure OpenAI API key in dev. |
| APK sideloading | Installing an Android app by directly transferring the .apk file (USB, email, download link) without the Google Play Store | Current distribution method for ANOTE Mobile. |
| Azure SWA deploy | GitHub Actions-based CI/CD where `Azure/static-web-apps-deploy@v1` uploads the built app to Azure Static Web Apps | Used by ANOTE Web (App 3). Triggered on push to `main`. Source: `.github/workflows/azure-static-web-apps.yml`. |

## Compliance and Regulatory Terms

| Term | Definition | Notes |
|------|-----------|-------|
| Educational tool disclaimer | Warning text ("This is an educational tool and not a certified medical tool") shown when the diabetes-2 advisor provides insulin dose guidance | Source: `DIABETES2_TECH_SPEC.md:136`. No formal regulatory status documented. |
| EU data residency | Requirement that personal data of EU residents is processed and stored within the EU/EEA | ANOTE Mobile uses Azure OpenAI in West Europe (Standard SKU) for GDPR compliance. Source: `ANOTE_mobile/README.md:43`. |

---

**Guidelines for adding terms:**
- Use plain language. Avoid circular definitions.
- If a term has different meanings in different contexts, note the context.
- Link to authoritative sources when available.
- Flag terms whose definitions are provisional or unconfirmed.
