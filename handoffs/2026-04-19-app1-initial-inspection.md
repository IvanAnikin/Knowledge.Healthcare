# Session Handoff: Initial Inspection of Application 1 (Medical Advisor)

## Session Date

2026-04-19

## Goal

Inspect the `medical_advisor` repository and produce a grounded application summary in the shared knowledge base, identifying confirmed facts, assumptions, and open questions.

## What Was Learned

- The application is a .NET 8 Blazor Server chatbot deployed to Azure App Service (B1, Linux, West Europe)
- It has evolved significantly beyond its original single-advisor design into a multi-advisor platform with 5 configured advisors
- Three advisors use context stuffing; two pump advisors use RAG with in-memory vector search and cached embeddings
- The "Diabeticky poradce 2" advisor has materially different behavioral rules (allows dose guidance, multilingual, uses general knowledge)
- No CI/CD pipeline exists — deployment is manual ZIP deploy via Azure CLI
- No database — all persistence is client-side (localStorage, cookies) or in-memory
- The shared Azure OpenAI resource (`anote-openai`) is used across multiple projects
- No inter-application integration was detected — this app appears self-contained
- Documentation is extensive (README: 799 lines, plus 5 detailed spec documents) but some is partially outdated

## Files Reviewed

- `README.md` — primary documentation (799 lines, very comprehensive)
- `MedicalAdvisor.sln` — solution structure
- `TECH_SPEC.md` — original technical specification
- `MULTI_ADVISOR_SPEC.md` — multi-advisor architecture design
- `PUMP_ADVISOR_SPEC.md` — RAG-based pump advisor design
- `DIABETES2_TECH_SPEC.md` — confident advisor variant specification
- `DIABETES2_IMPLEMENTATION_PLAN.md` — phased implementation plan
- `UI_ENHANCEMENT_SPEC.md` — modern chat UX design
- `IMPLEMENTATION_STATUS.md` — deployment tracking (partially outdated)
- `src/MedicalAdvisor.Web/MedicalAdvisor.Web.csproj` — project dependencies
- `src/MedicalAdvisor.Web/Program.cs` — entry point and DI configuration
- `src/MedicalAdvisor.Web/appsettings.json` — 5 advisors + Azure OpenAI config
- `tests/MedicalAdvisor.Tests/MedicalAdvisor.Tests.csproj` — test dependencies
- `.gitignore` — secrets and build artifact exclusions
- All directory listings for source tree, models, services, components, prompts, docs, tests

## Files Changed

- `/Users/ivananikin/Documents/Knowledge.Healthcare/applications/app-1-overview.md` — replaced template with full grounded overview
- `/Users/ivananikin/Documents/Knowledge.Healthcare/glossary.md` — populated with 18 confirmed terms across all categories
- `/Users/ivananikin/Documents/Knowledge.Healthcare/system-landscape.md` — filled in App 1 details, external services, data flows, shared dependencies
- `/Users/ivananikin/Documents/Knowledge.Healthcare/handoffs/2026-04-19-app1-initial-inspection.md` — this file

## Decisions Made

- Classified the application as "Active (deployed to production)" based on the live production URL and deployment history in IMPLEMENTATION_STATUS.md
- Noted 5 advisors (not 2) based on actual `appsettings.json` content, even though some spec documents only describe the original diabetes + gestational setup
- Did not run `dotnet test` — limited to file inspection to avoid side effects

## Assumptions

- The `advisor1.2/`, `advisor2/`, `advisor3/`, `advisor3.2/` folders are development artifacts for one-time text extraction (needs verification: yes)
- IMPLEMENTATION_STATUS.md is outdated relative to the current codebase state (needs verification: yes)
- The diabetes-2 and insulin-pump-2 advisors may not be fully implemented (needs verification: yes)
- No regulatory or compliance framework applies to this application currently (needs verification: yes)

## Unresolved Questions

- What are Applications 2 and 3 in the ecosystem?
- What is the actual current test count? (Conflicting claims: 32, 57, 8 test classes)
- Is the diabetes-2 advisor's emergency call button and dose-warning UI fully implemented?
- Is the MiniMed 780G pump advisor (insulin-pump-2) fully tested?
- What monitoring exists in production beyond default ASP.NET Core logging?

## Recommended Next Step

- Inspect Applications 2 and 3 to complete the system landscape and identify any cross-application dependencies
- Run `dotnet test` in the medical_advisor repo to get the actual test count and verify all tests pass
- Update the `project-overview.md` with confirmed mission, users, and scope from the combined application inspections
