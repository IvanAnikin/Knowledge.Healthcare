# Session Handoff: ANOTE Mobile (App 2) Initial Inspection

## Session Date

2026-04-19

## Goal

Inspect the `ANOTE_mobile` repository and produce a grounded application summary as `app-2-overview.md` in the shared knowledge folder, following the same structure established for App 1 (Medical Advisor).

## What Was Learned

- ANOTE Mobile is a Czech medical dictation app: doctor speaks, on-device Whisper transcribes, FastAPI backend + Azure OpenAI LLM generates structured Czech medical reports.
- Two-component architecture: Flutter mobile app (v0.3.0+1) + Python/FastAPI backend on Azure Container Apps.
- Shares the `anote-openai` Azure OpenAI resource (West Europe) with Medical Advisor (App 1). Also uses a separate `anote-openai-swe` resource (Sweden Central) for optional cloud transcription.
- 6 visit types supported with distinct report templates: default, initial, followup, gastroscopy, colonoscopy, ultrasound.
- Real doctor (Dr. Jan Brož, diabetologist) has tested 6 sessions — transcription quality is the main bottleneck, but LLM report generation is good.
- GitHub Actions CI exists for Flutter (analyze + test) but not for backend.
- App is pre-production / early pilot stage (v0.3.0, sideloaded APK, single test user).
- A bearer token is hardcoded in committed source (`constants.dart`) — security concern for broader distribution.

## Files Reviewed

- `README.md` (436 lines — comprehensive, most informative single file)
- `APP_ARCHITECTURE.md` (364 lines — Mermaid diagrams of full pipeline)
- `PRODUCTION_CHECKLIST.md` (337 lines — 6-phase deployment guide)
- `backend/main.py` (735 lines — full backend source)
- `backend/Dockerfile`, `backend/requirements.txt`, `backend/.env.example`
- `mobile/pubspec.yaml` (package manifest)
- `mobile/lib/config/constants.dart` (backend URL, tokens, Azure Whisper config)
- `mobile/lib/services/report_service.dart` (HTTP client)
- `.github/workflows/flutter_ci.yml` (CI pipeline)
- `.gitignore` (secrets handling)
- `feedback_janbroz/FEEDBACK_ANALYSIS.md` (doctor feedback analysis)
- `backend/tests/` (directory listing)
- `mobile/test/` (directory listing, 11 test files)
- `mobile/integration_test/` (2 E2E test files)

## Files Changed

- `/Users/ivananikin/Documents/Knowledge.Healthcare/applications/app-2-overview.md`: Replaced template with comprehensive application summary
- `/Users/ivananikin/Documents/Knowledge.Healthcare/glossary.md`: Added 9 terms (anote-openai-swe, sherpa_onnx, Silero VAD, Whisper on-device, Visit type, Riverpod, az containerapp up, APK sideloading, EU data residency); updated `anote-openai` definition to reference both apps
- `/Users/ivananikin/Documents/Knowledge.Healthcare/handoffs/2026-04-19-app2-initial-inspection.md`: Created this handoff

## Decisions Made

- Wrote to `app-2-overview.md` (not `app-1-overview.md`) because App 1 was already documented as the Medical Advisor, and this ANOTE_mobile repository is clearly the second application.

## Assumptions

- The app is pre-production based on version number, distribution method, and single test user (needs verification: yes)
- GPT-5-mini was chosen over GPT-4.1-mini for production despite the README recommending the latter — likely a quality-driven decision after doctor feedback (needs verification: yes)
- No runtime integration exists between App 1 and App 2 — only shared Azure OpenAI infrastructure (needs verification: no — high confidence)

## Unresolved Questions

- What is Application 3 in the healthcare ecosystem?
- Is the hardcoded bearer token in `constants.dart` acceptable for the current deployment scope?
- What is the current transcription model in production use (Small, Turbo, or Cloud)?
- Has the Azure Modified Access form been submitted for zero data retention?
- What is the patient data retention policy for locally stored recordings?

## Recommended Next Step

- Inspect Application 3 and write `app-3-overview.md` to complete the three-application ecosystem picture.
- Update `system-landscape.md` with the confirmed Azure infrastructure topology spanning both apps.
