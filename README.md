# Knowledge.Healthcare

## Purpose

This folder is the **shared knowledge and memory layer** for a multi-application healthcare software project. It is the single source of truth for durable project context: architecture summaries, decision records, handoff notes, standards, conventions, and reusable agent guidance.

This is **not** a source code repository. Application source code lives in separate repositories. This folder exists to support reasoning, continuity, and coordination across all applications and sessions.

## What Belongs Here

- Project-wide architecture descriptions and system landscape documentation
- Decision records (ADRs) that explain why choices were made
- Handoff notes that preserve session context for future work
- Current priorities and active goals
- Standards and conventions (engineering, testing, security, documentation)
- Glossary of business, clinical, and technical terms
- Application overviews that summarize each app's purpose, stack, and boundaries
- Workflow checklists for starting, ending, and coordinating work
- Templates for consistent documentation

## What Does NOT Belong Here

- Application source code, configuration, or build artifacts
- Secrets, credentials, API keys, or environment-specific values
- Temporary notes or scratch work that has no future value
- Duplicated information that is already maintained in a source repo
- Personal preferences or opinions not grounded in project decisions

## How to Use This Folder

### For Agents

1. **Before acting**, read `AGENTS.md` and the relevant context files (current priorities, app overviews, latest handoffs).
2. **After meaningful work**, update handoffs, current priorities, and any documentation that changed.
3. **Never invent facts.** If something is unknown, say so clearly.

### For Humans

1. Use this folder to orient yourself before starting work on any application.
2. Review `current-priorities.md` to understand what is active.
3. Add handoff notes when ending a work session so the next person (or agent) can continue effectively.

## Structure

```
Knowledge.Healthcare/
  AGENTS.md                  # Agent behavior instructions
  README.md                  # This file
  current-priorities.md      # Active goals and blockers
  project-overview.md        # Mission, stakeholders, scope
  system-landscape.md        # Applications, integrations, data flows
  glossary.md                # Shared terminology
  standards/                 # Engineering, testing, security, docs standards
  decisions/                 # Architecture Decision Records
  handoffs/                  # Session handoff notes
  applications/              # Per-application overviews
  workflows/                 # Checklists and processes
  templates/                 # Reusable document templates
  tasks/                     # Task files (inbox / triage / active / backlog / done)
  specs/                     # Technical specs and implementation plans (per app)
  scripts/                   # Utility scripts
  dashboards/                # Generated dashboards and roadmap
```

## Task Dashboard

The project includes a generated static HTML dashboard that visualises all tasks, priorities, and progress across applications.

**The Markdown task files remain the source of truth. The dashboard is read-only.**

### What it reads

- `tasks/inbox/`, `tasks/triage/`, `tasks/active/`, `tasks/backlog/`, `tasks/done/`
- `specs/app-1/`, `specs/app-2/`, `specs/app-3/`, `specs/app-4/`, `specs/cross-app/`
- `current-priorities.md`

### How to regenerate

```bash
python3 scripts/generate_dashboard.py
```

### How to regenerate and open (macOS)

**Recommended — OpenCode slash command:**

```
/dashboard
```

Defined in `.opencode/commands/dashboard.md`. When invoked inside OpenCode, it runs the generator, verifies the output, and opens `dashboards/task-dashboard.html` in your default browser. No server is started; the browser opens the file directly from disk.

**Shell script (terminal use):**

```bash
bash scripts/open_dashboard.sh
```

**Manual commands:**

```bash
python3 scripts/generate_dashboard.py && open dashboards/task-dashboard.html
```

Or use the npm convenience scripts (requires Node.js, but no dependencies are installed):

```bash
npm run dashboard        # generate only
npm run dashboard:open   # generate and open in browser
```

### Output

`dashboards/task-dashboard.html` — a self-contained, offline-capable HTML file.

### Task detail modal

Clicking any task card on the kanban board opens a structured detail panel as a modal overlay. It displays:

- Task ID, title, app / priority / status / type badges
- Source file path and link
- Spec links (when available)
- Problem / summary
- Desired outcome, constraints, affected areas
- Open questions, dependencies, notes
- Confirmed facts, assumptions, reasoning, cross-app considerations

All modal content is rendered from a JSON blob embedded in the HTML at generation time — no server, no network requests. The Markdown task files remain the source of truth.

Keyboard shortcuts: **Escape** closes the modal. Clicking outside the panel also closes it.

### Notes

- No database. No server. No external dependencies.
- Safe to run repeatedly; the output file is always overwritten.
- If a task file has missing or inconsistent metadata, the generator logs a warning and continues. Parser warnings appear at the bottom of the dashboard.
- Requires Python 3.8+.
