# Documentation Standards

## Purpose

These standards define how documentation should be written and maintained across the project. Consistent documentation reduces onboarding time, prevents knowledge loss, and supports continuity across sessions and contributors.

## General Principles

- **Write for the next reader.** Assume they have technical competence but no project context.
- **Be concise.** Prefer short, actionable statements over verbose explanations.
- **Separate facts from assumptions.** Always make it clear what is confirmed and what is provisional.
- **Keep documentation current.** Update docs when the thing they describe changes. Stale documentation is worse than no documentation.
- **Use templates.** Use the templates in `templates/` for consistency.

## File Naming

- Use lowercase with hyphens: `my-document-name.md`
- Use descriptive names that indicate content, not status: `api-authentication.md` not `new-doc-v2.md`
- Prefix ADRs with `adr-` followed by a sequential number: `adr-001-database-choice.md`
- Prefix handoffs with the date: `2025-01-15-session-handoff.md`

## Markdown Conventions

- Use ATX-style headers (`#`, `##`, `###`).
- Use tables for structured data.
- Use `<!-- comments -->` for placeholder instructions that should be replaced.
- Use blockquotes (`>`) for important notes or caveats.
- Do not use HTML unless Markdown is insufficient.

## Structure of a Good Document

1. **Title** -- Clear and descriptive.
2. **Purpose or context** -- Why does this document exist? One or two sentences.
3. **Content** -- The main information, organized with headers.
4. **Open questions** -- Anything unresolved, listed explicitly.
5. **Last updated** -- Date of most recent meaningful change.

## What to Document

- Decisions and their rationale (use ADRs)
- Architecture and system boundaries
- Integration points and contracts between applications
- Standards and conventions
- Session context and handoffs
- Known issues and open questions

## What NOT to Document Here

- Source code (belongs in application repos)
- Secrets or credentials
- Ephemeral information with no future value
