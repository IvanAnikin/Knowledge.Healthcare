# Project Overview

> Last updated: 2026-04-20. Synthesized from inspection of all 3 application repositories.

## Mission

Build AI-powered tools that assist Czech healthcare professionals and patients — specifically diabetes patient education and medical dictation/report generation for doctors.

## Users and Stakeholders

| Role | Description | Notes |
|------|-------------|-------|
| Diabetes patients (Czech-speaking) | Use AI chatbot for diabetes education and insulin pump guidance | Anonymous access, no accounts. App 1. |
| Doctors (Czech-speaking internists, diabetologists, gastroenterologists) | Dictate patient visits and receive structured medical reports | Known pilot user: Dr. Jan Brož. App 2. |
| Prospective doctor customers | Evaluate the ANOTE dictation product via marketing site and live demo | Anonymous public visitors. App 3. |
| Developer/operator (Ivan Anikin) | Sole developer, deployer, and operator of all 3 applications | Single-person team (confirmed from repo inspection). |

## Business Purpose

The project addresses two problems in Czech healthcare:

1. **Patient education gap** — Diabetes patients need accessible, reliable information in Czech. The Medical Advisor (App 1) provides grounded AI chat that cannot hallucinate, using doctor-verified Czech medical documents.
2. **Clinical documentation burden** — Doctors spend significant time writing visit reports. ANOTE (Apps 2+3) converts spoken Czech dictation into structured medical reports via on-device transcription and LLM processing, with a privacy-first design (audio never leaves the device).

## Scope

### In Scope

- Czech-language AI chatbot for diabetes patient education (App 1)
- Mobile medical dictation with on-device speech-to-text and LLM report generation (App 2)
- Marketing website with live browser demo for the ANOTE dictation product (App 3)
- Shared Azure OpenAI infrastructure across all applications

### Out of Scope

- EHR/EMR integration
- Patient authentication or user accounts (beyond static bearer tokens)
- Clinical data storage or persistence (beyond device-local JSON)
- Multi-language support beyond Czech (partial English in App 3 marketing site only)
- Regulatory certification as a medical device

## Non-Goals

- This project is not building a certified medical device or claiming regulatory compliance
- Not replacing clinical judgment — explicitly positioned as educational (App 1) and documentation assistance (App 2)
- Not building a multi-tenant SaaS platform — current architecture is single-user/anonymous

## Major Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Medical misinformation from AI | Medium | High | Document grounding (App 1), structured templates (App 2), educational disclaimers |
| Single-person team — bus factor of 1 | High | High | This knowledge layer; comprehensive READMEs in each repo |
| Shared Azure OpenAI resource rate limits | Medium | Medium | Not yet mitigated; no monitoring in place |
| Hardcoded bearer token in App 2 mobile source | High | Medium | Acceptable for pilot; needs remediation before broader distribution |
| No staging environments for any application | High | Medium | Not yet mitigated |
| No automated tests in App 3 | High | Low | CI does type-check and build validation only |
| Azure SWA file-based storage (App 3 contact form) may be ephemeral | Medium | Low | Contact submissions may be lost on redeployment |

## Compliance and Regulatory Concerns

- **GDPR / EU data residency:** ANOTE Mobile (App 2) processes transcripts via Azure OpenAI in West Europe (EU). Audio never leaves the device in default mode. The optional Sweden Central resource is also EU. Needs legal review to confirm sufficiency.
- **Medical device regulation:** The diabetes-2 advisor (App 1) provides insulin dose suggestions with an educational disclaimer. Whether this triggers medical device classification under EU MDR has not been assessed. Requires legal review.
- **Data retention:** No formal retention policy exists for device-local medical reports (App 2) or contact form submissions (App 3).
- **Azure OpenAI abuse monitoring opt-out:** Not yet submitted for App 2 (noted in PRODUCTION_CHECKLIST.md). Relevant for zero data retention guarantees.

## Success Criteria

- App 1: Patients can get accurate, grounded diabetes information in Czech without hallucinated medical advice
- App 2: A doctor can dictate a patient visit and receive a usable structured report in under 2 minutes (confirmed viable by pilot testing with Dr. Jan Brož)
- App 3: Prospective customers can experience the dictation product via live demo and submit contact inquiries
- Cross-cutting: Shared knowledge layer enables continuity across development sessions and future contributors
