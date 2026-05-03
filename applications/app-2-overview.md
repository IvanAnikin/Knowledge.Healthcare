# Application 2 Overview — ANOTE Mobile (Medical Dictation)

> Last updated: 2026-04-19. Based on direct inspection of the `ANOTE_mobile` repository.

## Repository Name

`ANOTE_mobile` — local path: `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile`

## Purpose

Czech-language mobile application for medical dictation: a doctor speaks during a patient visit, the app transcribes speech to text on-device (Whisper + Silero VAD), then sends the transcript to a Python/FastAPI backend that generates a structured Czech medical report via Azure OpenAI LLM. The system supports 6 visit types (general, initial exam, follow-up, gastroscopy, colonoscopy, ultrasound), each with a specialized 10-20 section report template.

**Production backend URL:** `https://anote-api.gentleriver-a61d304a.westus2.azurecontainerapps.io`

Source: `README.md:1-3`, `APP_ARCHITECTURE.md:1-3`, `backend/main.py:1,68`

## Users

- **Primary:** Czech-speaking doctors (internists, diabetologists, gastroenterologists) dictating during or after patient visits
- **Known test user:** Dr. Jan Brož (internist/diabetologist) — 6 feedback sessions documented in `feedback_janbroz/`
- **Target device:** Samsung Galaxy S8 (Android 9, API 28) — matches the first customer's phone; iOS also supported
- **Language:** Czech only (transcription, report generation, UI labels)

Source: `PRODUCTION_CHECKLIST.md:1-4`, `README.md:299`, `feedback_janbroz/FEEDBACK_ANALYSIS.md:1-3`

## Responsibilities

Within the broader healthcare ecosystem, this application is responsible for:

1. **Voice-to-report pipeline** — end-to-end flow from microphone audio to structured Czech medical report
2. **On-device speech-to-text** — privacy-preserving transcription using Whisper Small/Turbo INT8 models with Silero VAD; no audio leaves the device
3. **Cloud transcription fallback** — optional Azure OpenAI Whisper API mode for higher accuracy (audio sent to Azure Sweden Central)
4. **LLM-based report structuring** — backend sends transcript to Azure OpenAI (GPT-5-mini primary, GPT-4.1-mini fallback) to produce visit-type-specific structured medical reports
5. **Report email delivery** — optional SMTP-based email sending of generated reports
6. **Recording history** — local JSON-based persistence of past transcripts and reports on the device
7. **Demo/testing mode** — pre-recorded Czech medical scenarios for demonstration without a microphone

This application does **not** handle: patient records/EHR, authentication beyond a static bearer token, database storage, patient-facing features, or insulin pump/diabetes education (that is App 1 — Medical Advisor).

Source: `README.md:37-48`, `backend/main.py:560-735`, `APP_ARCHITECTURE.md:280-318`

## Tech Stack

| Layer | Technology | Version/Details | Notes |
|-------|-----------|-----------------|-------|
| Mobile framework | Flutter / Dart | Flutter 3.27+, Dart SDK >=3.2.0 <4.0.0 | `pubspec.yaml`, `flutter_ci.yml` |
| State management | Riverpod | flutter_riverpod ^2.4.0 | StateNotifier pattern |
| On-device STT | sherpa_onnx | ^1.12.26 | Whisper Small/Turbo INT8 + Silero VAD |
| Audio capture | audio_streamer | ^4.0.0 | 16 kHz mono PCM |
| HTTP client | dio | ^5.4.0 | Report generation, email sending |
| Secure storage | flutter_secure_storage | ^9.0.0 | API tokens, backend URL |
| Background tasks | flutter_foreground_task + wakelock_plus | ^8.17.0 / ^1.4.0 | Keep recording alive |
| Backend framework | FastAPI (Python) | fastapi 0.115.0, Python 3.12 | `backend/requirements.txt`, `Dockerfile` |
| Backend ASGI server | uvicorn | 0.30.0 | |
| LLM SDK | openai (Python) | 1.50.0 | AzureOpenAI + OpenAI clients |
| LLM (primary) | Azure OpenAI GPT-5-mini | GlobalStandard, version 2025-08-07 | `README.md:145` |
| LLM (fallback) | Azure OpenAI GPT-4.1-mini | Standard SKU, 30K TPM | `backend/main.py:59` |
| Cloud STT (optional) | Azure OpenAI gpt-4o-mini-transcribe | Sweden Central | `mobile/lib/config/constants.dart:23-24` |
| Container runtime | Docker | Python 3.12-slim base | `backend/Dockerfile` |
| Hosting | Azure Container Apps | 0.5 CPU / 1 GB RAM, Consumption tier | West US 2 |
| CI | GitHub Actions | Flutter CI on push/PR to main | `.github/workflows/flutter_ci.yml` |
| Testing (backend) | pytest + pytest-asyncio | 8.3.0 / 0.24.0 | |
| Testing (mobile) | flutter_test + mockito | mockito ^5.4.0 | |

Source: `pubspec.yaml`, `backend/requirements.txt`, `backend/Dockerfile`, `README.md:127-153`, `mobile/lib/config/constants.dart`

## Key Directories and Files

```
ANOTE_mobile/
├── README.md                           # Comprehensive documentation (436 lines)
├── APP_ARCHITECTURE.md                 # Mermaid-based architecture diagrams
├── PRODUCTION_CHECKLIST.md             # 6-phase deployment guide
├── MODEL_COMPARISON_TEST.md            # GPT-4.1-mini vs GPT-5-mini benchmark
├── LLM_JUDGE_SPEC.md                   # Report quality evaluation spec
├── FEEDBACK_FIXES_SPEC.md              # Fixes derived from doctor feedback
├── TRANSCRIPTION_IMPROVEMENTS_SPEC.md  # Whisper quality improvement plans
├── .github/workflows/flutter_ci.yml    # CI pipeline (Flutter test + analyze)
│
├── backend/
│   ├── main.py                         # FastAPI app — /health, /report, /scenarios, /send-report-email
│   ├── Dockerfile                      # Python 3.12-slim, uvicorn on port 8000
│   ├── requirements.txt                # 8 Python dependencies
│   ├── .env.example                    # Azure OpenAI credentials template
│   ├── evaluate_reports.py             # LLM-as-Judge report quality evaluation
│   ├── evaluate_transcription.py       # Whisper+VAD transcription quality evaluation
│   ├── tests/
│   │   ├── test_report_endpoint.py     # 7 core endpoint unit tests
│   │   ├── test_prompt_builder.py      # 25 system prompt construction tests
│   │   ├── test_endpoints_comprehensive.py  # 20 edge case / GDPR / auth tests
│   │   ├── test_transcription_quality.py    # 24 scenario integrity / CER/WER tests
│   │   ├── test_report_quality.py      # 20 live report quality tests
│   │   └── test_email_endpoint.py      # Email endpoint tests
│   └── eval_dataset/                   # Evaluation WAV files (gitignored)
│
├── mobile/
│   ├── pubspec.yaml                    # Flutter package manifest, v0.3.0+1
│   ├── lib/
│   │   ├── main.dart                   # App entry point
│   │   ├── config/constants.dart       # Backend URL, tokens, timing config
│   │   ├── config/secrets.dart         # Gitignored secrets file
│   │   ├── models/session_state.dart   # Recording status, session data
│   │   ├── providers/session_provider.dart  # Riverpod state management
│   │   ├── screens/home_screen.dart    # Main UI with collapsible panels
│   │   ├── screens/settings_screen.dart # Backend URL, token, visit type config
│   │   ├── services/
│   │   │   ├── audio_service.dart      # Microphone capture (16 kHz PCM)
│   │   │   ├── whisper_service.dart    # On-device Whisper + Silero VAD
│   │   │   ├── report_service.dart     # HTTP client for backend API
│   │   │   ├── cloud_transcription_service.dart  # Azure Whisper API
│   │   │   └── recording_storage_service.dart    # JSON file persistence
│   │   ├── utils/wav_encoder.dart      # PCM -> WAV encoding
│   │   └── widgets/                    # UI components (recording, report, transcript, demo, history)
│   ├── assets/demo_scenarios/          # Pre-recorded Czech medical scenarios (.txt)
│   ├── assets/models/                  # On-device ML models (auto-downloaded, ~250 MB)
│   ├── test/                           # Unit tests (11 files across services/, models/, widgets/, providers/)
│   └── integration_test/               # E2E tests (app_e2e_test.dart, recording_history_test.dart)
│
├── feedback_janbroz/                   # 6 doctor feedback sessions + analysis
├── testing_hurvinek/                   # Czech audio + reference transcripts for Whisper eval
└── test_scenarios/                     # Additional test scenario files
```

Source: direct directory listing

## Integrations

| Integration | Direction | Mechanism | Description |
|-------------|-----------|-----------|-------------|
| Azure OpenAI (`anote-openai`, West Europe, RG `ANOTE`) | Outbound (backend) | HTTPS API via `openai` Python SDK | GPT-5-mini / GPT-4.1-mini for report generation |
| Azure OpenAI (`anote-openai-swe`, Sweden Central) | Outbound (mobile) | HTTPS REST | Optional cloud transcription via gpt-4o-mini-transcribe Whisper API |
| SMTP server | Outbound (backend) | SMTP/TLS | Optional email delivery of generated reports; disabled if `SMTP_HOST` unset |
| Mobile app -> Backend | Outbound (mobile) | HTTP POST with Bearer token | `/report` endpoint for report generation; `/send-report-email` for email |

**Cross-application integration:** The Azure OpenAI resource `anote-openai` (West Europe, RG `ANOTE`) is shared with the Medical Advisor app (App 1). Both apps use the same Azure OpenAI account but different model deployments. No direct runtime communication between applications.

Source: `backend/main.py:36-60,79-90`, `mobile/lib/config/constants.dart:5-6,23-24`, `README.md:139-153`

## Data Handled

| Data Type | Sensitivity | Storage | Notes |
|-----------|-------------|---------|-------|
| Live audio (16 kHz PCM) | High (patient voice) | In-memory only, never persisted or transmitted | GDPR-by-design: audio stays on device |
| Transcript text | High (patient clinical data in Czech) | Device local storage (JSON files); transmitted to backend via HTTPS | Auto-saved every 10s; backend deliberately does not log transcript content |
| Structured medical report | High (clinical data) | Device local storage; optionally emailed via SMTP | 10-20 section Czech medical report |
| Recording history index | Low (metadata only) | Device local storage (`recordings/_index.json`) | ID, date, visit type, preview text |
| API bearer token | Secret | Mobile: `flutter_secure_storage`; Backend: Azure Container Apps secrets | Static token, not user-specific |
| Azure OpenAI API key | Secret | Backend: Azure Container Apps secrets (`azure-openai-key`) | Never in source code |
| Azure Whisper API key | Secret | Mobile: gitignored `secrets.dart` | Referenced in `constants.dart` |
| On-device ML models | Internal | Auto-downloaded to device (~250 MB) | Whisper Small INT8, Whisper Turbo INT8, Silero VAD |

**GDPR considerations:** Audio never leaves the device. Transcript text is sent to Azure OpenAI in West Europe (Standard SKU) for report generation. The backend explicitly does not log transcript or report content (`main.py:680-681`). Azure OpenAI in West Europe = EU data residency. The optional cloud transcription uses a separate Azure OpenAI resource in Sweden Central.

Source: `README.md:39,43`, `backend/main.py:680-681`, `APP_ARCHITECTURE.md:312-318`, `mobile/lib/config/constants.dart`

## Deployment and Runtime

- **Backend deployment:** Azure Container Apps via `az containerapp up --source ./backend`. Manual process, no CD pipeline. Docker image built from `backend/Dockerfile` (Python 3.12-slim).
- **Backend runtime:** Azure Container Apps, Consumption tier, 0.5 CPU / 1 GB RAM, West US 2 region. Container App name: `anote-api`, resource group: `anote-rg`.
- **Backend environment variables:** `AZURE_OPENAI_KEY` (secret), `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `APP_API_TOKEN` (secret), `MOCK_MODE`, optional SMTP vars.
- **Mobile deployment:** Manual APK build (`flutter build apk --release`) and sideloading via USB, Firebase App Distribution, or direct sharing. No Google Play Store listing.
- **Mobile CI:** GitHub Actions workflow (`flutter_ci.yml`) runs `flutter pub get`, `build_runner`, `flutter analyze`, and `flutter test` on push to `main` and PRs.
- **iOS deployment:** Supported via Xcode archive + `devicectl` install. No TestFlight or App Store listing documented.
- **Model distribution:** Whisper + VAD models (~250 MB) are auto-downloaded on first app launch. Not bundled in APK.
- **Azure subscription:** Visual Studio Ultimate with MSDN (subscription ID: `8a3849cc-c762-4a9c-8874-6487046bc245`)

Source: `README.md:127-208`, `PRODUCTION_CHECKLIST.md:65-98`, `backend/Dockerfile`, `.github/workflows/flutter_ci.yml`

## Tests and Validation

### Backend Tests (Python/pytest)

| File | Count | Type | Description |
|------|-------|------|-------------|
| `test_report_endpoint.py` | 7 | Unit (mocked) | Core /report endpoint behavior |
| `test_prompt_builder.py` | 25 | Unit | System prompt construction for all visit types |
| `test_endpoints_comprehensive.py` | 20 | Unit | Edge cases, GDPR, auth, Unicode, visit routing |
| `test_transcription_quality.py` | 24 | Unit/Integration | Scenario file integrity, CER/WER metrics, eval infra |
| `test_report_quality.py` | 20 | Live integration | Live Azure OpenAI report quality (structure, accuracy); ~3 min, skippable via `SKIP_LIVE_TESTS=1` |
| `test_email_endpoint.py` | TBD | Unit | Email endpoint tests |

### Mobile Tests (Flutter/Dart)

**Unit tests** (11 files in `mobile/test/`):
- `services/`: report_service_test, whisper_service_test, wav_encoder_test, cloud_transcription_service_test, recording_storage_service_test, whisper_model_config_test
- `providers/`: session_provider_test
- `models/`: transcription_model_test
- `widgets/`: report_panel_test, recording_history_list_test
- `widget_test.dart`

**Integration tests** (2 files in `mobile/integration_test/`):
- `app_e2e_test.dart` — 15 tests: app launch, recording flow, clear, settings, performance, error handling, theme toggle
- `recording_history_test.dart` — 2 tests: empty state, record-save-load-edit flow

**E2E results (26 March 2026, Samsung Galaxy S8 emulator):** 17/17 passed.

### Evaluation tools (non-test scripts):
- `backend/evaluate_reports.py` — LLM-as-Judge report quality scoring
- `backend/evaluate_transcription.py` — Whisper+VAD pipeline benchmarking (WER/CER)

### CI pipeline:
- GitHub Actions: Flutter analyze + test on push to `main` and `copilot/*` branches, PRs to `main`
- Backend: No CI. Tests run manually via `python -m pytest tests/ -v`.

Source: `README.md:369-435`, `.github/workflows/flutter_ci.yml`, `mobile/test/`, `backend/tests/`

## Confirmed Facts

These are established with high confidence from direct file inspection:

1. The application is a Flutter mobile app (v0.3.0+1) with a Python/FastAPI backend, purpose-built for Czech medical dictation and structured report generation.
2. On-device transcription uses sherpa_onnx with Whisper Small/Turbo INT8 models and Silero VAD. No audio leaves the device in the default (on-device) mode.
3. The backend is a stateless FastAPI service with 4 endpoints: `/health`, `/report`, `/scenarios`, `/send-report-email`. It is deployed as an Azure Container App.
4. Report generation uses Azure OpenAI GPT-5-mini (primary) with GPT-4.1-mini as fallback. Both models are on the shared `anote-openai` resource.
5. The system supports 6 visit types: default (auto-detect), initial, follow-up, gastroscopy, colonoscopy, ultrasound — each with a distinct multi-section Czech report template.
6. A real doctor (Dr. Jan Brož, internist/diabetologist) has tested 6 sessions. Main finding: transcription quality is the critical bottleneck; report quality from LLM is good even with noisy input.
7. There is a GitHub Actions CI pipeline for the Flutter mobile app (analyze + test). No CI for the backend.
8. The backend has ~96+ unit tests plus 20 live integration tests. The mobile app has unit tests across 11 files plus 17 integration/E2E tests.
9. The shared Azure OpenAI resource `anote-openai` (West Europe, RG `ANOTE`) is used by both this app and the Medical Advisor app (App 1).
10. Authentication is a single static Bearer token — no user accounts or login system.
11. CORS is set to `allow_origins=["*"]` in the backend (noted as needing tightening for production in `PRODUCTION_CHECKLIST.md:97`).
12. A secondary Azure OpenAI resource `anote-openai-swe` (Sweden Central) hosts cloud transcription (gpt-4o-mini-transcribe).
13. The `mobile/lib/config/secrets.dart` file is gitignored and contains the Azure Whisper API key.
14. An optional email feature exists (`/send-report-email`) using SMTP, but is disabled by default (requires `SMTP_HOST` env var).

## Assumptions

These are reasonable inferences that should be verified:

1. **The app is pre-production / early pilot.** Evidence: version 0.3.0+1 in `pubspec.yaml`, APK sideloading distribution model, single test user, CORS set to `*`, `PRODUCTION_CHECKLIST.md` written in first-person checklist form. But the backend IS deployed to Azure and a doctor HAS tested it.
2. **The `defaultToken` hardcoded in `constants.dart` is the actual production bearer token.** This is a security concern — the token `_lZNhJDgaoneVaztSf2tJnf-rZMEQV5ZCLBPRAyC38I` is committed to source. It may be acceptable for a pre-production pilot but is not suitable for broader distribution.
3. **The GPT-5-mini model was selected over GPT-4.1-mini for quality reasons despite being slower and more expensive.** The `README.md` model comparison table recommends GPT-4.1-mini for production, but the current deployment uses GPT-5-mini as primary. This may reflect a change in priorities toward quality after doctor feedback.
4. **No inter-application runtime integration exists** between ANOTE Mobile and the Medical Advisor (App 1). They share Azure OpenAI infrastructure only.
5. **The app is Android-first** despite Flutter's cross-platform nature. Evidence: Android emulator tests, Samsung Galaxy S8 target device, detailed Android setup in `PRODUCTION_CHECKLIST.md`. iOS is supported but secondary (no TestFlight, limited iOS-specific docs).

## Open Questions

1. **What is the current transcription model in production use — Small, Turbo, or Cloud?** `constants.dart` references all three modes; the README primarily documents Small, but `APP_ARCHITECTURE.md` shows Turbo as an option.
2. **Is the SMTP email feature actively used?** The endpoint exists but `SMTP_HOST` is documented as optional and disabled by default.
3. **What is Application 3 in the ecosystem?** No cross-references found in this repository.
4. **What is the actual test pass/fail status?** The E2E results from 26 March 2026 show all passing, but the backend tests and current mobile unit test status are not documented.
5. **Is the `anote-openai-swe` (Sweden Central) resource shared with other apps?** It appears only in the mobile constants for cloud transcription. Its relationship to the broader infrastructure is unclear.
6. **What is the plan for app distribution beyond APK sideloading?** The `PRODUCTION_CHECKLIST.md` mentions Firebase App Distribution and GitHub Releases but does not confirm which was used.
7. **Is the CORS `allow_origins=["*"]` still in place on the production backend?** It was flagged as needing restriction in the checklist.
8. **What is the patient data retention policy?** Reports are stored locally on the doctor's device as JSON files. No documented retention limits or deletion policy.
9. **Has the Modified Access form for Azure OpenAI been submitted** (to opt out of abuse monitoring for zero data retention)? Listed as optional/unchecked in `PRODUCTION_CHECKLIST.md:31`.

## Recommended Next Documentation Step

1. **Inspect Application 3** and write `app-3-overview.md` to complete the ecosystem picture.
2. **Update `system-landscape.md`** with the confirmed Azure infrastructure: `anote-openai` (West Europe), `anote-openai-swe` (Sweden Central), `anote-api` Container App (West US 2), shared subscription.
3. **Run the backend and mobile test suites** to establish current pass/fail status and resolve test count uncertainties.
4. **Document the shared `anote-openai` resource** as a cross-cutting infrastructure concern — which apps use which deployments, quotas, and SKUs.
5. **Assess the hardcoded token in `constants.dart`** — determine if this is acceptable for the current pilot scope or needs remediation.
