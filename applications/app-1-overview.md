# Application 1 Overview — Medical Advisor (Diabetologický poradce)

> Last updated: 2026-04-19. Based on direct inspection of the `medical_advisor` repository.

## Repository Name

`medical_advisor` — local path: `/Users/ivananikin/Documents/medical_advisor`

## Purpose

Czech-language AI chatbot web application that provides diabetes education and guidance to patients. The AI is strictly grounded in verified Czech medical documents — it cannot hallucinate or invent medical advice. The app operates as a multi-advisor platform where each advisor (topic area) has its own knowledge base, system prompt, and URL route.

**Production URL:** https://medical-advisor-cz.azurewebsites.net

Source: `README.md:1-3`, `appsettings.json:14-80`

## Users

- **Primary:** Czech-speaking diabetes patients (including gestational diabetes and insulin pump users)
- **Tone target:** Older adults, not necessarily tech-savvy; design emphasizes simplicity, comfort, and guided interaction
- **Access model:** Anonymous — no login required, no user accounts
- **Language:** Czech only for the primary advisors; "Diabeticky poradce 2" supports multilingual switching (user language auto-detection)

Source: `README.md:50-51`, `UI_ENHANCEMENT_SPEC.md:30-38`, `DIABETES2_TECH_SPEC.md:103-113`

## Responsibilities

Within the broader healthcare ecosystem, this application is responsible for:

1. **Patient-facing diabetes education** — conversational AI chat grounded in doctor-verified documents
2. **Multi-topic advisory** — currently 5 configured advisors covering different diabetes topics and insulin pump systems
3. **Document-grounded Q&A** — AI answers exclusively from provided medical texts (with one advisor variant that also allows high-confidence general medical knowledge)
4. **Session management** — browser-side localStorage persistence of up to 5 conversation sessions (no server-side persistence)

This application does **not** handle: clinical data, EHR integration, patient authentication, prescriptions, or medical device control.

## Tech Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Runtime | .NET | 8.0 (LTS) | `MedicalAdvisor.Web.csproj` TargetFramework |
| Web framework | ASP.NET Blazor Server | 8.0 | Real-time streaming via SignalR |
| AI orchestration | Microsoft Semantic Kernel | 1.74.0 | Chat completion + embedding generation |
| UI components | MudBlazor | 9.2.0 | Material Design for Blazor |
| LLM (chat) | Azure OpenAI | gpt-5.4-mini (GlobalStandard, 100K TPM) | Deployment name: `gpt-5-4-mini` |
| LLM (embeddings) | Azure OpenAI | text-embedding-3-small (GlobalStandard, 120K TPM) | Used for RAG in pump advisors |
| DOCX support | DocumentFormat.OpenXml | 3.2.0 | Runtime text extraction from `.docx` files |
| Testing | xUnit + Moq + coverlet | 2.5.3 / 4.20.72 / 6.0.0 | Unit tests only |
| Hosting | Azure App Service | B1 Basic, Linux | West Europe region |

Source: `MedicalAdvisor.Web.csproj`, `Program.cs`, `appsettings.json`, `README.md:130-139`

## Key Directories and Files

```
medical_advisor/
├── MedicalAdvisor.sln                  # Solution file (2 projects)
├── README.md                           # Comprehensive documentation (799 lines)
├── TECH_SPEC.md                        # Original technical specification
├── MULTI_ADVISOR_SPEC.md               # Multi-advisor architecture design
├── PUMP_ADVISOR_SPEC.md                # RAG-based pump advisor design
├── DIABETES2_TECH_SPEC.md              # "Confident advisor" variant spec
├── DIABETES2_IMPLEMENTATION_PLAN.md    # Phased plan for diabetes-2 advisor
├── UI_ENHANCEMENT_SPEC.md              # Modern chat UX design spec
├── IMPLEMENTATION_STATUS.md            # Deployment tracking log
├── .gitignore                          # .NET + macOS + secrets + Azure
│
├── src/MedicalAdvisor.Web/             # Main Blazor Server application
│   ├── Program.cs                      # Entry point, DI, middleware, RAG init
│   ├── appsettings.json                # 5 advisors configured, Azure OpenAI settings
│   ├── Models/                         # AdvisorConfig, ChatMessage, EmbeddingChunk, etc.
│   ├── Services/                       # 6 services (AdvisorRegistry, DocumentService,
│   │                                   #   MedicalAdvisorService, ConversationState,
│   │                                   #   ThemeService, PumpRagService)
│   ├── Prompts/                        # 5 system prompt .txt files (one per advisor)
│   ├── Components/                     # Blazor components (Pages, Layout, Shared)
│   │   └── Shared/                     # 8 shared components including AdvisorSelector,
│   │                                   #   QuickReplyButtons, WelcomeCards, etc.
│   ├── docs/                           # Knowledge base documents per advisor
│   │   ├── *.txt                       # 4 diabetes docs (261K chars)
│   │   ├── diabetes2/                  # 1 normalized guide for confident advisor
│   │   ├── gestational/                # 1 .docx for gestational diabetes
│   │   ├── pump/                       # Tandem CIQ summary + manual + embeddings cache
│   │   └── pump2/                      # MiniMed 780G summary + manual + embeddings cache
│   └── wwwroot/                        # Static assets (CSS, favicon)
│
├── tests/MedicalAdvisor.Tests/         # Unit test project
│   ├── Services/                       # 6 test classes
│   └── Models/                         # 2 test classes
│
├── advisor1.2/                         # Source material for diabetes-2 advisor
├── advisor2/                           # Source material for gestational advisor
├── advisor3/                           # Source material for pump advisor (Tandem)
├── advisor3.2/                         # Source material for pump-2 advisor (MiniMed)
└── docs/                               # Reference copies of diabetes docs
```

Source: direct directory listing and file inspection

## Integrations

| Integration | Direction | Mechanism | Description |
|-------------|-----------|-----------|-------------|
| Azure OpenAI Service (`anote-openai`) | Outbound | HTTPS API (Semantic Kernel SDK) | Chat completion (gpt-5.4-mini) and text embeddings (text-embedding-3-small) |
| Browser localStorage | Bidirectional | JavaScript interop | Session history persistence (up to 5 sessions), client-side only |
| Browser cookies | Bidirectional | HTTP cookies | Theme preferences (Clinical/Friendly + Light/Dark), 1-year expiry |

**No database.** No inter-application integrations detected. No message queues, event buses, or shared data stores with other applications.

The Azure OpenAI resource `anote-openai` (West Europe, resource group `ANOTE`) is shared with other projects — the README notes other deployments on the same resource: `gpt-5-mini`, `gpt-5-chat`, `whisper`.

Source: `Program.cs:16-30`, `appsettings.json:9-13`, `README.md:570-584`, `PUMP_ADVISOR_SPEC.md:76-86`

## Data Handled

| Data Type | Sensitivity | Storage | Notes |
|-----------|-------------|---------|-------|
| Medical knowledge documents (Czech) | Internal / Public (published medical literature) | Bundled as `.txt`/`.docx` files in `docs/` | 4 diabetes docs, 1 gestational, 2 pump manuals, 1 diabetes-2 guide |
| Conversation messages | Low (anonymous, no PII collected) | In-memory (server) + localStorage (browser) | No server-side persistence; cleared on circuit disconnect |
| Theme preferences | Negligible | Browser cookies | Clinical/Friendly + Light/Dark |
| Embeddings cache | Internal | JSON files on disk (`embeddings_cache.json`) | Pre-computed vector embeddings for RAG pump advisors |
| Azure OpenAI API key | Secret | .NET User Secrets (dev) / App Service Config (prod) | Never in source code |

**No patient health records, PII, or authentication tokens are handled by this application.**

Source: `README.md:47-49,645-652`, `.gitignore`, `PUMP_ADVISOR_SPEC.md:189-207`

## Deployment and Runtime

- **Deployment method:** Manual ZIP deploy via Azure CLI (`az webapp deploy --type zip`). No CI/CD pipeline exists (no `.github/workflows/`, no Dockerfile).
- **Runtime environment:** Azure App Service, B1 Basic tier, Linux, West Europe region
- **App name:** `medical-advisor-cz` in resource group `medical-advisor-rg`
- **Cold start:** 60-90 seconds (document loading + container setup); `WEBSITES_CONTAINER_START_TIME_LIMIT=600` configured
- **WebSockets:** Required and enabled (Blazor Server uses SignalR)
- **Scaling approach:** Single instance. No auto-scaling configured (B1 tier). Stateless design (scoped services per circuit) would support horizontal scaling if upgraded.
- **Startup command:** `dotnet MedicalAdvisor.Web.dll`
- **Estimated cost:** ~$18-23/month (B1 hosting + Azure OpenAI usage at 100 conversations/day)
- **Azure subscription:** Visual Studio Ultimate with MSDN

Source: `README.md:380-549`, `IMPLEMENTATION_STATUS.md:76-97`

## Tests and Validation

- **Test framework:** xUnit 2.5.3 with Moq 4.20.72 for mocking and coverlet 6.0.0 for coverage
- **Test project:** `tests/MedicalAdvisor.Tests/` (references main project)
- **Test classes (8 total):**
  - `Services/DocumentServiceTests.cs` — document loading, missing files, content verification
  - `Services/ConversationStateTests.cs` — state management, reset, history, session export/import
  - `Services/ThemeServiceTests.cs` — themes, switching, events, MudTheme color values
  - `Services/MedicalAdvisorServiceTests.cs` — AI service orchestration, streaming, quick-reply parsing
  - `Services/AdvisorRegistryTests.cs` — config validation, slug lookup, default resolution
  - `Services/PumpRagServiceTests.cs` — RAG chunking, retrieval, cache
  - `Models/ChatMessageTests.cs` — message creation, properties, role handling
  - `Models/EmbeddingsCacheTests.cs` — cache serialization
- **CI/CD pipeline:** None. Tests are run manually via `dotnet test`.
- **Known gaps:** No integration tests, no end-to-end tests, no load tests. Manual testing noted in spec documents for UI behaviors and conversation flows.

Source: `tests/MedicalAdvisor.Tests/`, `MedicalAdvisor.Tests.csproj`, `README.md:354-375`

## Confirmed Facts

These are established with high confidence from direct file inspection:

1. The application is a .NET 8 Blazor Server app deployed to Azure App Service (B1, Linux, West Europe).
2. It uses Microsoft Semantic Kernel 1.74.0 for Azure OpenAI integration (chat + embeddings).
3. There are 5 configured advisors in `appsettings.json`: diabetes, diabetes-2, gestational-diabetes, insulin-pump (Tandem), insulin-pump-2 (MiniMed 780G).
4. Three advisors use context stuffing (full documents in system prompt); two pump advisors use RAG with in-memory vector search.
5. The shared Azure OpenAI resource is `anote-openai` in West Europe with `gpt-5-4-mini` and `text-embedding-3-small` deployments.
6. No database — all state is in-memory (server) or browser localStorage/cookies (client).
7. Anonymous access — no authentication or user accounts.
8. No CI/CD pipeline — deployment is manual ZIP deploy via Azure CLI.
9. No Docker or container configuration in the repository.
10. The codebase has 8 test classes covering services and models via xUnit + Moq.
11. The `advisor1.2/`, `advisor2/`, `advisor3/`, `advisor3.2/` folders contain source materials (PDFs, DOCXs) used to prepare the runtime `.txt` knowledge files.
12. Quick-reply buttons are AI-generated via `[QUICK_REPLIES]...[/QUICK_REPLIES]` tags parsed from streaming responses.
13. The "Diabeticky poradce 2" advisor has different behavioral rules: it allows insulin dose suggestions, multilingual switching, and uses general medical knowledge as a secondary source.

## Assumptions

These are reasonable inferences that should be verified:

1. **The application is self-contained** — no evidence of runtime communication with the other 2 applications in the healthcare ecosystem. Cross-app integration, if any, would be at the Azure OpenAI resource level (shared `anote-openai` account).
2. **The IMPLEMENTATION_STATUS.md is partially outdated** — it mentions 32 tests and the original diabetes-only advisor, but the current codebase has 5 advisors, 8 test classes, and RAG services, suggesting significant evolution since that document was written.
3. **The `advisor*` source folders are development artifacts** — they contain original PDFs/DOCXs used for one-time text extraction and are not used at runtime. The runtime files are in `src/MedicalAdvisor.Web/docs/`.
4. **The deployment instructions in README.md referencing `gpt-4-1-mini`** may be partially stale — `appsettings.json` now points to `gpt-5-4-mini`, and the README mentions both `gpt-4.1-mini` and `gpt-5.4-mini` in different sections.
5. **No formal medical certification or regulatory approval** is in place — the app is described as educational, with the diabetes-2 advisor explicitly displaying a "This is an educational tool and not a certified medical tool" warning when dose guidance is given.

## Open Questions

1. **What are the other 2 applications in the healthcare ecosystem?** No cross-references or integration contracts were found in this repository.
2. **What is the actual test count?** The README says 57 tests, IMPLEMENTATION_STATUS.md says 32, and there are 8 test classes. The true count needs a `dotnet test` run.
3. **Is the "Diabeticky poradce 2" advisor fully implemented?** The `DIABETES2_IMPLEMENTATION_PLAN.md` describes phases including UI warning banners and emergency call buttons — it is unclear from file inspection alone whether all phases are complete.
4. **Is the `insulin-pump-2` (MiniMed 780G) advisor fully implemented?** It appears in `appsettings.json` with a dedicated docs folder and prompt, but no spec document exists for it (unlike the Tandem pump which has `PUMP_ADVISOR_SPEC.md`).
5. **Are there any compliance or data-handling requirements?** The app handles no PII, but it provides medical information and (in one mode) insulin dose suggestions. Regulatory considerations are not documented.
6. **What is the `anote-openai` Azure resource's ownership?** It is in a different resource group (`ANOTE`) from the app's own infrastructure (`medical-advisor-rg`), suggesting it is a shared organizational resource.
7. **How is the app monitored in production?** No Application Insights or logging infrastructure beyond default ASP.NET Core logging was found. Application Insights is listed as a future improvement.

## Recommended Next Documentation Step

1. **Run `dotnet test` and record the actual test count and pass/fail status** — resolve the conflicting test count claims.
2. **Inspect the other 2 applications** in the ecosystem and document them in `app-2-overview.md` and `app-3-overview.md` to establish cross-project context.
3. **Update `system-landscape.md`** with the confirmed details about this application, the shared Azure OpenAI resource, and the Azure infrastructure topology.
4. **Verify the implementation completeness** of the diabetes-2 and insulin-pump-2 advisors by testing them against their spec documents.
5. **Document the shared Azure OpenAI resource** (`anote-openai`) as a cross-cutting infrastructure concern, including which projects use which model deployments.
