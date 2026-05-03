# Spec Process

## Purpose

Determine when a task needs a technical spec and how to produce one.

## When to Write a Full Technical Spec

A full spec (using `specs/templates/technical-spec-template.md`) is required when **any** of these are true:

- The task is cross-app.
- The task involves changes to more than 3 files or 2 modules.
- The task has high risk (data loss, security, compliance implications).
- The task changes shared interfaces, APIs, or data models.
- Confidence from triage is low.

## When a Lightweight Plan Is Sufficient

Use only an implementation plan (`specs/templates/implementation-plan-template.md`) when **all** of these are true:

- Single app, well-understood change.
- Low risk, no shared interface changes.
- Confidence from triage is high.
- Fewer than 3 files affected.

## Process

1. Create a spec request from the triage output using `tasks/templates/spec-request-template.md`.
2. Write the spec in the appropriate `specs/` subdirectory (`app-1/`, `app-2/`, `app-3/`, `app-4/`, or `cross-app/`).
3. If the spec is approved, create an implementation plan if one does not already exist.
4. Link the spec and plan back to the task file.

## Review

Specs should be reviewed before implementation begins. Flag open questions and resolve them before marking the spec as approved.
