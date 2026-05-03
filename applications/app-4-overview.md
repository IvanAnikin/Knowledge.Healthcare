# Application 4 Overview — Health-Analysis

> Last updated: 2026-04-25. Based on the product-owner task request and local directory creation only.

## Repository Name

`Health-Analysis` — local path: `/Users/ivananikin/Documents/Health-Analysis`

## Purpose

Planned web application for healthcare data analysis with deterministic analytics, chart generation, and an embedded LLM assistant that produces clinician-oriented summaries from validated computed outputs.

The requested MVP starts with continuous glucose monitoring (CGM) analysis and is intended to expand later to laboratory results, medication data, vital signs, diagnoses, and generic time-series datasets.

## Current State

- Local application directory exists at `/Users/ivananikin/Documents/Health-Analysis`.
- No repository structure, source code, package manifests, or runtime services have been created in this session.
- The next requested deliverable is a documentation-first project foundation captured by `TASK-0020`.

## Planned Responsibilities

1. Accept CSV/XLSX healthcare dataset uploads.
2. Support dataset-type selection and manual column mapping.
3. Validate schema and normalize units before analysis.
4. Run deterministic analytics modules and produce statistics, trends, and charts.
5. Pass structured computed outputs to an LLM layer for clinician-facing summaries and interpretation support.
6. Preserve auditability through logging of analysis inputs, versions, prompts, and outputs.

## Safety Framing

- The application is intended for clinical decision-support only.
- Deterministic analytics are meant to come before LLM interpretation.
- The LLM should not be presented as the final clinical authority.
- Recommendations should be framed for clinician consideration and verification.
- Raw patient data exposure to the LLM should be minimized where practical.

## Confirmed Facts

1. The user requested a new application directory named `Health-Analysis` under `/Users/ivananikin/Documents/`.
2. The directory was created in this session.
3. The requested MVP dataset types are: CGM time series, laboratory results, medication data, vital signs, diagnoses, and generic time series.
4. The first analytics module requested for implementation planning is CGM, including LibreView-style CSV parsing, time-in-range metrics, variability metrics, daypart analysis, episode detection, rate-of-change analysis, post-meal spike analysis, and multiple chart outputs.
5. The requested preferred stack is Next.js or React on the frontend, FastAPI on the backend, `pandas`/`numpy` for data processing, Plotly or matplotlib/Plotly exports for charts, local file storage first, PostgreSQL later, an abstract LLM provider interface, and Docker-based sandboxing in later phases.
6. The user wants only task creation and knowledge-layer updates in this session; implementation of the documentation files will happen later in the new app directory.

## Assumptions

1. The application has not yet been initialized as a git repository. (needs verification: yes)
2. The eventual codebase will likely be a single dedicated repository rooted at `/Users/ivananikin/Documents/Health-Analysis`. (needs verification: yes)
3. Phase 2 and Phase 3 capabilities are future-state architecture targets, not immediate MVP implementation requirements. (needs verification: no)

## Open Questions

1. Will this repository be initialized as a monorepo containing both frontend and backend, or as a single-app codebase with a separate service structure later?
2. Which LLM provider and deployment path should be treated as the initial default: Azure OpenAI, a generic OpenAI-compatible API, or another internal abstraction target?
3. What patient-data retention policy and hosting/deployment environment are expected for the MVP?
4. What level of automated testing and synthetic sample data should be required before any clinical-facing pilot use?

## Recommended Next Step

Execute `TASK-0020` inside `/Users/ivananikin/Documents/Health-Analysis` to create the requested initial documentation package before any source-code scaffolding is started.
