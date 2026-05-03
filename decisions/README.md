# Architecture Decision Records (ADRs)

## Purpose

This folder contains Architecture Decision Records -- short documents that capture important decisions made during the project, along with their context, alternatives, and consequences.

## When to Create an ADR

Create an ADR when:

- A technology, framework, or tool is chosen
- An architectural pattern or approach is selected
- A significant trade-off is made (e.g., performance vs. simplicity)
- A cross-application contract or interface is defined
- A security or compliance-related engineering choice is made
- A decision reverses or supersedes a previous decision

Do **not** create an ADR for routine implementation choices that do not affect the project's direction or other applications.

## How to Write an ADR

1. Copy `adr-template.md` to a new file.
2. Name it `adr-NNN-short-description.md` (e.g., `adr-001-database-choice.md`).
3. Fill in all sections. If a section is not applicable, write "N/A" rather than omitting it.
4. Set the status to `Proposed`, `Accepted`, `Deprecated`, or `Superseded`.
5. Do not modify existing ADRs to change history. If a decision changes, create a new ADR that references and supersedes the old one.

## Status Values

| Status | Meaning |
|--------|---------|
| Proposed | Under discussion, not yet accepted |
| Accepted | Decision is in effect |
| Deprecated | No longer relevant but kept for history |
| Superseded | Replaced by a newer ADR (link to it) |

## Index

<!-- Add entries as ADRs are created -->

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| <!-- adr-001 --> | <!-- Title --> | <!-- Status --> | <!-- Date --> |
