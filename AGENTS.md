# AGENTS.md

## Role of This Folder

This folder (`Knowledge.Healthcare/`) is the **persistent shared memory layer** for a multi-application healthcare software project. It supports multiple applications and enables cross-application reasoning, continuity across sessions, and durable project knowledge.

Application source code is maintained in separate repositories. This folder contains only knowledge, decisions, standards, and coordination artifacts.

## Agent Instructions

### Before Acting

- Read this file (`AGENTS.md`) at the start of every session.
- Read `current-priorities.md` to understand what is active, blocked, or recently completed.
- Read the relevant `applications/app-*-overview.md` for any application you will work on.
- Read the latest entry in `handoffs/` to understand recent session context.
- Review `workflows/session-start-checklist.md` and follow it.
- For Azure-dependent work, read `workflows/azure-cli-access.md` first. Do not assume `az` is globally available on `PATH`.

### During Work

- **Do not invent facts.** If information is unavailable, state that clearly. Do not guess project details, stakeholder names, compliance status, or technical specifics that have not been confirmed.
- **Clearly separate** confirmed facts, assumptions, open questions, and recommendations in all documentation you produce.
- **Keep documentation concise but useful.** Write for a reader who needs to act on the information, not just understand it.
- **When making decisions**, document them in `decisions/` using the ADR template. Include context, alternatives, and consequences.
- **This folder supports multiple applications.** When reasoning about changes, consider cross-application impacts. Use `workflows/cross-app-change-process.md` when changes span more than one application.

### After Meaningful Work

- Update `current-priorities.md` to reflect any changes in goals, blockers, or completed items.
- Add a handoff note in `handoffs/` using the template if the session produced meaningful context for future work.
- Update any documentation files that are now stale or incomplete because of work performed.
- Review `workflows/session-end-checklist.md` and follow it.

### Quality Standards

- Follow the conventions in `standards/` for documentation, engineering, testing, and security.
- Use templates from `templates/` when creating new documents to maintain consistency.
- Prefer updating existing files over creating new ones, unless a new file is clearly needed.
- Use clear, professional language. Avoid jargon unless it is defined in `glossary.md`.

### Task and Spec System

For non-trivial work, use the task management and specification system:

- **New work items:** Create a task file in `tasks/inbox/` using `tasks/templates/task-template.md`.
- **Triage:** Assess tasks using `workflows/triage-process.md` and the triage template. Update `dashboards/task-board.md`.
- **Specs:** Follow `workflows/spec-process.md` to determine if a full spec or lightweight plan is needed. Write specs in `specs/app-{N}/` or `specs/cross-app/`.
- **Lifecycle:** Follow `workflows/task-lifecycle.md` for the full flow from inbox to done.
- **Roadmap:** Keep `dashboards/roadmap.md` current when priorities change.
- **App references:** Use `applications/index.md` to map app IDs to repos.

Trivial changes (typo fixes, single-line edits with no risk) do not require a task or spec.

### What Not to Do

- Do not store secrets, credentials, or environment-specific configuration in this folder.
- Do not create files outside the established structure without justification.
- Do not overwrite handoff notes or decision records; they are append-only historical records.
- Do not claim legal or regulatory compliance on behalf of the project. Document engineering guidance and flag areas that require legal review.

## Specialized Agents

This project includes specialized OpenCode agents for common control-layer workflows. These agents are defined in `.opencode/agents/` and can be invoked using the `@` mention syntax.

### Task Triage Agent (`@task-triage`)

**Purpose:** Convert raw task descriptions into structured, prioritized task files.

**When to invoke:**
- A new task has been submitted (verbally in chat or as a file in `tasks/inbox/`)
- An existing inbox task needs triage assessment
- A task's priority or status needs re-evaluation
- Cross-app impact analysis is needed for a proposed change

**When NOT to invoke:**
- The task is already triaged and needs a spec (use `@spec-writer` instead)
- You need to execute code changes (work in the application repo instead)
- The request is a simple question, not an actionable task

**Outputs:**
- Structured task file in `tasks/inbox/` or `tasks/triage/`
- Updated `dashboards/task-board.md`
- Optionally updated `dashboards/roadmap.md` for high-priority items

**Example invocation:**
```
@task-triage Please triage this task: "Add dark mode support to the ANOTE-web marketing site"
```

### Spec Writer Agent (`@spec-writer`)

**Purpose:** Produce technical specs and implementation plans from triaged tasks.

**When to invoke:**
- A triaged task has `needs-spec` status
- A task is cross-app and requires coordination planning
- A task is high-risk (data loss, security, compliance)
- A task changes shared interfaces, APIs, or data models
- Confidence from triage is low and detailed analysis is needed

**When NOT to invoke:**
- The task is not yet triaged (use `@task-triage` first)
- The task is trivial (single-file, low-risk, high-confidence)
- You need to execute code changes (work in the application repo instead)

**Outputs:**
- Technical spec in `specs/app-{N}/` or `specs/cross-app/`
- Implementation plan (embedded or separate)
- Updated task file with spec link

**Example invocation:**
```
@spec-writer Please write a spec for TASK-0001 (dark mode for ANOTE-web)
```

### Agent Workflow

The typical flow for non-trivial work:

1. **Capture** — Raw task appears in chat or `tasks/inbox/`
2. **Triage** — Invoke `@task-triage` to assess and prioritize
3. **Spec** — If `needs-spec`, invoke `@spec-writer` to produce the spec
4. **Execute** — Work in the application repository using the Build agent
5. **Update** — Return to this control layer to update task status and documentation

### Application-Specific Execution

For execution work in application repositories, use the standard OpenCode Build agent. Each application has its own context:

| App ID | Name | Repo Path | Notes |
|--------|------|-----------|-------|
| app-1 | medical_advisor | `/Users/ivananikin/Documents/medical_advisor` | .NET 8 Blazor Server |
| app-2 | ANOTE_mobile | `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile` | Flutter + FastAPI |
| app-3 | ANOTE-web | `/Users/ivananikin/Documents/ANOTE-web` | Next.js 16 |
| app-4 | Health-Analysis | `/Users/ivananikin/Documents/Health-Analysis` | FastAPI + Next.js (CGM analytics + LLM summary) |

When executing tasks in application repos, refer back to specs in this control layer for implementation guidance.
