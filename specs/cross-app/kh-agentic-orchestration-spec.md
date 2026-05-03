# Technical Specification: KH Agentic Orchestration Layer

| Field | Value |
|---|---|
| Spec ID | SPEC-KH-AGENTIC-001 |
| Status | Draft |
| Author | Ivan Anikin (with Domain Agent thesis context) |
| Date | 2026-05-03 |
| Apps affected | Cross-app (control layer; coordinates work across all four production apps) |
| Source spec | Builds on [`SPEC-KH-AGENT-001`](kh-agent-spike-spec.md) (the `kh_agent` retrieval/telemetry spike) |
| Source thesis | [`Domain_Agent/External_Validation_Healthcare.md`](../../../Domain_Agent/External_Validation_Healthcare.md), [`Domain_Agent/Technical_Architecture.md`](../../../Domain_Agent/Technical_Architecture.md) |
| Upstream code reused | `Domain_Agent/src/{agents,orchestrator,llm,knowledge,evaluation,models}/` |

---

## 0. Reading guide

This spec is long because the scope is wide. Read it in this order:

1. §1 Summary, §2 Objective, §3 Scope (in/out), §4 Non-goals — *what we are committing to*.
2. §5 Phasing overview — *the staged delivery plan*.
3. §6 Architecture — *how the parts fit*.
4. §7–§13 Per-phase specs — *the implementation plan, phase by phase*.
5. §14–§17 Cross-cutting concerns (safety, data, UI, ops).
6. §18–§20 Risks, validation, rollback.
7. §21 Open questions.

Phases 0–2 are committed. Phases 3–5 are sketched in enough detail to make sure Phases 0–2 don't paint into a corner; they will each get their own follow-up spec before being built.

---

## 1. Summary

Build a **multi-agent orchestration layer** on top of the `Knowledge.Healthcare` (KH) control layer that adapts the Domain Agent thesis architecture (`planner → router → workflow → aggregator` over domain-specialised agents with per-domain RAG) to the four-application Czech healthcare portfolio. The system reads and writes the KH markdown corpus, drafts and (under explicit human approval) executes work that crosses application boundaries — task triage, technical specifications, code PRs, content drafts, analytics briefs, financial summaries — and surfaces all of this through a small local-only operator console with an Inbox-style approval queue.

The system is **not** an autonomous publisher of medical content, **not** an autonomous merger of code into application `main` branches, and **not** an autonomous spender of money. Every action with external visibility passes through a typed risk-tier policy with documented per-channel allow-lists, daily caps, and a hard `compliance_agent` gate.

The core architecture is a direct port of the thesis runtime. The work is in (a) the new agent roster, (b) the tool layer, (c) the structured-data substrate that complements the canonical markdown, (d) the operator UI, (e) the healthcare-specific safety/approval policy.

## 2. Objective

Specific, measurable outcomes:

1. **Close the loop** from raw idea → triaged task → spec → implementation PR → deployment → KPI/cost feedback, with human approval at the boundaries that matter and automation everywhere else.
2. **Replace the static reading-list discipline** in `.opencode/agents/{task-triage,spec-writer}.md` with retrieval-backed, structurally-typed agents that emit `AgentMessage`s and follow the Confirmed / Assumption / Open-Question discipline.
3. **Make cross-app work first-class.** A `TASK-0014`-style multi-repo split should be expressible as a typed `SubTask` graph and executed by `WorkflowEngine`, not coordinated by hand.
4. **Make spend visible and bounded.** Every LLM and tool call is logged; daily token-cost caps are enforced before, not after, the fact.
5. **Make freshness measurable.** Index staleness, dedup proposals, and drift between docs (the "57 vs 32 tests" class of bug) are detected automatically and surfaced as triage tasks.
6. **Preserve the markdown-as-source-of-truth invariant.** The orchestration layer reads the corpus, proposes diffs, and writes via approved PRs — it never edits the corpus behind the operator's back.

Non-objective: replacing OpenCode. The OpenCode subagents become thin shims that invoke the new orchestrator; the lifecycle (`tasks/{inbox,triage,active,...,deployed}`) is unchanged.

## 3. Scope

### In scope (committed: Phases 0–2)
- The `kh_agent` package and its retrieval/telemetry surface (already specified in [SPEC-KH-AGENT-001](kh-agent-spike-spec.md); Phase 0 of this spec).
- A new package `kh_orchestrator/` with `BaseAgent`, the per-app and core cross-cutting agents, `Planner`, `Router`, `WorkflowEngine`, `Aggregator`, `Orchestrator`.
- The agent roster up to and including `triage_agent`, `spec_agent`, `dev_agent`, `compliance_agent` (advisory in Phase 1, gating from Phase 2 onward).
- The `Tool` protocol and the tools at risk tiers `read` and `write_local`: `MarkdownWriter`, `GitTool` (branch/commit only), `PRTool` (draft-only).
- The structured-data substrate (SQLite state DB derived from markdown; JSONL ledgers for cost and external actions).
- The local-only `kh-console` UI: Inbox, Now, Health views.
- Healthcare-specific safety policy (§14) and the C/A/OQ output discipline already imported into the thesis prompts.
- Phase-0 → Phase-2 delivery, validation, rollback.

### Sketched, not committed (Phases 3–5)
- `content_agent`, `analytics_agent`, `finance_agent`, `dedupe_agent`, `freshness_agent`, `strategy_agent`.
- `publisher_agent`, `social_agent`, `email_agent` and the `publish` / `send` / `spend` tool tier.
- `kh-console` Money and Outbox views.
- The "covers reality" weekly housekeeping loop (§14.4).
- Each of these gets its own spec before implementation.

### Out of scope (any phase)
- Touching application **source code** in this spec other than via PRs reviewed by the operator.
- Storing patient data, transcripts, CGM time series, or any PII in the orchestration layer.
- Autonomous publication of App 1 (medical advisor) Czech-language content.
- Autonomous code merges into any `main` branch.
- Autonomous financial transactions or ad spend.
- Multi-tenant SaaS, multi-operator auth, hosted UI.
- Replacing the markdown corpus as canonical source.
- Replacing OpenCode or the `tasks/` lifecycle.
- Becoming a regulated medical device or making any medical claim.

## 4. Non-Goals

- This is **not** an attempt to remove the human from the loop. It is an attempt to remove the human from the *trivial* part of the loop and give them a structured queue for the non-trivial part.
- This is **not** a replacement for clinical judgement, legal review, or marketing approval. Those remain human responsibilities; the system makes them faster, not optional.
- This is **not** a generic agent framework. It targets exactly the four KH applications and the existing KH lifecycle, and reuses the thesis runtime instead of inventing one.

## 5. Phasing Overview

Each phase is independently useful and independently rollback-able. Each phase produces a working system (the previous phase's behaviour plus a strictly additive capability). No phase is required by the next, technically; they are sequenced by risk and by dependency on operator-only secrets/decisions.

| Phase | Title | Capability gained | Status |
|---|---|---|---|
| 0 | Retrieval & telemetry | `kh_agent` ingest / retrieve / status; agent prompt edits; cost ledger | Spec'd, see [SPEC-KH-AGENT-001](kh-agent-spike-spec.md). Committed here as a dependency. |
| 1 | Multi-agent read & write-local | `kh_orchestrator` core; per-app + triage + spec agents; `MarkdownWriter`; first version of `kh-console` Inbox | Committed, this spec |
| 2 | Implementation PRs | `dev_agent`; `GitTool` + `PRTool` (draft); workflow engine running cross-app SubTask graphs; `compliance_agent` as hard gate on outputs touching `app-1` patient-facing surfaces | Committed, this spec |
| 3 | Content & analytics (read-side) | `content_agent` (drafts only), `analytics_agent`, `finance_agent`, weekly briefs as markdown PRs | Sketched only |
| 4 | Gated external publication | `publisher_agent`, `social_agent`, `email_agent`; `publish` / `send` tool tier; `kh-console` Outbox | Sketched only |
| 5 | Strategy & dedup loop | `strategy_agent`, `dedupe_agent`, `freshness_agent`; closes the priorities → tasks → deploy → analytics → priorities loop | Sketched only |

The thesis-defined H2 invariant (per-domain knowledge isolation) is preserved across all phases by the FAISS partition from Phase 0. The thesis-defined H3 invariant (centralised orchestrator with role specialisation and standardised inter-agent messages) is what we are operationalising from Phase 1 onward.

## 6. Architecture

### 6.1 Layered view

```
┌─────────────────────────────────────────────────────────────────┐
│  kh-console  (FastAPI + Next.js, localhost-only)                │
│  Views: Inbox · Now · Health · (P3+) Money · (P4+) Outbox       │
└──────────────────────────────────────┬──────────────────────────┘
                                       │ HTTP (localhost)
┌──────────────────────────────────────▼──────────────────────────┐
│  kh_orchestrator                                                │
│   Orchestrator(Planner, Router, WorkflowEngine, Aggregator)     │
│   ApprovalGate · ComplianceGate · CostGate                      │
└──────────────────┬───────────────────────────────────┬──────────┘
                   │                                   │
        ┌──────────▼─────────┐               ┌─────────▼────────┐
        │ Per-app agents     │               │ Cross-cutting    │
        │  app1 / app2 /     │               │ agents           │
        │  app3 / app4       │               │  triage / spec / │
        │ (knowledge-only)   │               │  dev / content / │
        │                    │               │  publisher / ... │
        └──────────┬─────────┘               └─────────┬────────┘
                   │ retrieve()                        │ retrieve() + tool calls
        ┌──────────▼───────────────────────────────────▼────────┐
        │ kh_agent (Phase 0): retriever, llm_client, tracker    │
        │ FAISS indexes: app-1..4 / cross-app / decisions /     │
        │ standards / workflows / tasks-recent                  │
        └──────────┬────────────────────────────────────────────┘
                   │
        ┌──────────▼────────────────────────────────────────────┐
        │ Substrate                                             │
        │  Markdown corpus (canonical)                          │
        │  state.db (SQLite, derived)                           │
        │  cost ledger / action log (JSONL, append-only)        │
        │  KPI parquet (Phase 3+)                               │
        └───────────────────────────────────────────────────────┘
```

### 6.2 Reuse map (Domain_Agent → KH)

Verbatim ports (preserve module names where possible):

| Domain_Agent module | kh_orchestrator destination | Treatment |
|---|---|---|
| `src/models/task.py` | `kh_orchestrator/models/task.py` | Adapted: `DomainType` enum becomes a `Literal` union of agent names (`"app1"`, `"app2"`, `"app3"`, `"app4"`, `"triage"`, `"spec"`, `"dev"`, `"content"`, ...). |
| `src/models/agent_message.py` | `kh_orchestrator/models/agent_message.py` | Verbatim; add optional `tool_calls` field for Phase 2+. |
| `src/models/evaluation.py` | `kh_orchestrator/models/evaluation.py` | Verbatim. |
| `src/agents/base_agent.py` | `kh_orchestrator/agents/base.py` | Adapted: pluggable `tools: list[Tool]` parameter; default empty. |
| `src/orchestrator/planner.py` | `kh_orchestrator/orchestrator/planner.py` | Adapted: new decomposition prompt that knows the KH agent roster. |
| `src/orchestrator/router.py` | `kh_orchestrator/orchestrator/router.py` | Verbatim. |
| `src/orchestrator/workflow.py` | `kh_orchestrator/orchestrator/workflow.py` | Adapted: adds an optional `human_approval` step type. |
| `src/orchestrator/aggregator.py` | `kh_orchestrator/orchestrator/aggregator.py` | Verbatim. |
| `src/orchestrator/orchestrator.py` | `kh_orchestrator/orchestrator/orchestrator.py` | Adapted to wire the gates (Approval / Compliance / Cost). |
| `src/evaluation/llm_judge.py` | `kh_orchestrator/judge/llm_judge.py` | Adapted: rubric retargeted at specs / drafts. |
| `src/evaluation/logger.py` | `kh_orchestrator/logger.py` | Verbatim. |

New modules (no thesis equivalent):

| New module | Purpose |
|---|---|
| `kh_orchestrator/tools/` | `Tool` Protocol + concrete tools per §6.4. |
| `kh_orchestrator/gates/` | `ApprovalGate`, `ComplianceGate`, `CostGate`. |
| `kh_orchestrator/state/` | SQLite schema and read/write helpers; markdown ↔ DB sync. |
| `kh_orchestrator/console/` | FastAPI app + Next.js front-end (`kh-console`). |
| `kh_orchestrator/policy/` | Risk tiers, allow-lists, daily caps, channel registry. |
| `kh_orchestrator/cli.py` | `kh-orch run …`, `kh-orch sync-state`, `kh-orch console`. |

### 6.3 Agent roster

**Per-application "ground-truth" agents** (knowledge-only; never call external tools; emit structured proposals for other agents to act on):

| Agent | Owns index | System-prompt anchors |
|---|---|---|
| `app1_agent` | `app-1` | medical_advisor scope, Czech medical accuracy, App 1 non-goals, TASK-0034 disclaimer pattern |
| `app2_agent` | `app-2` | ANOTE_mobile, Flutter + FastAPI, on-device transcription, no patient data leaves device |
| `app3_agent` | `app-3` | ANOTE-web, Next.js + anote-web-api, post-`TASK-0014` backend split |
| `app4_agent` | `app-4` | Health-Analysis, deterministic CGM core + LLM summary boundary |

**Cross-cutting agents** (call retriever; some call tools; gated by §14):

| Agent | Phase | Reads | Writes (via tool) | External tools |
|---|---|---|---|---|
| `triage_agent` | 1 | `tasks-recent`, all per-app | `tasks/triage/TASK-XXXX.md`, `dashboards/task-board.md` (proposals) | `MarkdownWriter` |
| `spec_agent` | 1 | per-app, `decisions`, `standards` | `specs/app-N/...md` (proposals) | `MarkdownWriter` |
| `dev_agent` | 2 | spec + target app repo (read-only via local FS) | branch + commit + draft PR | `GitTool`, `PRTool` |
| `compliance_agent` | 2 (advisory in 1) | `standards/security-privacy-standards.md`, glossary, all outbound drafts | red/amber/green verdict + rationale | none — pure judge |
| `content_agent` | 3 | `applications/`, marketing brief, glossary | `marketing/drafts/*.md` (proposals) | `MarkdownWriter` |
| `analytics_agent` | 3 | KPI parquet, app logs (where exposed) | `analytics/briefs/YYYY-WW.md` | `PlausibleTool` (read) |
| `finance_agent` | 3 | cost ledger, Azure billing CSV, manual P&L | `finance/briefs/YYYY-MM.md` | `AzureCostTool` (read) |
| `publisher_agent` | 4 | approved drafts | publication record JSONL | `CMSTool` |
| `social_agent` | 4 | approved drafts + brand standards | post record JSONL | per-platform tools |
| `email_agent` | 4 | approved campaign + recipient allow-list | send log JSONL | `EmailTool` |
| `dedupe_agent` | 5 | full corpus + state DB | `dedupe_proposals/YYYY-MM-DD.md` (never auto-merges) | none |
| `freshness_agent` | 5 | full corpus + Azure deploy state | `tasks/triage/HOUSEKEEPING-WW.md` | `AzureCostTool` (read), git tag check |
| `strategy_agent` | 5 | KPI + cost + roadmap | PR against `current-priorities.md`, `dashboards/roadmap.md` | none |

### 6.4 Tool layer

```python
class Tool(Protocol):
    name: str
    risk: Literal["read", "write_local", "publish", "send", "spend"]

    async def plan(self, intent: AgentMessage) -> Action: ...
    async def dry_run(self, action: Action) -> ActionPreview: ...
    async def execute(self, action: Action, approval: Approval) -> ActionResult: ...
```

- `plan` is pure: it converts an agent's intent into a typed `Action` (fully serialised payload, no side effects). Always called.
- `dry_run` returns an `ActionPreview` (e.g., diff, rendered email, post text) that the operator sees in `kh-console`. Always called, always logged.
- `execute` runs only after an `Approval` object has been issued by the appropriate gate. Idempotency keys are mandatory.

Risk-tier policy (enforced by `gates/`):
- `read` → auto.
- `write_local` (proposes a markdown edit, opens a draft branch in the KH repo or an app repo) → auto, with logger entry, but the result is reviewed via PR before merge.
- `publish` / `send` / `spend` → **always** require explicit human approval in v1, with a per-tool, per-channel allow-list and a per-day volume/cost cap. Graduation to "auto with override" is a per-tool, per-channel decision and requires its own spec amendment.

Concrete tools, per phase:

| Tool | Risk | Phase |
|---|---|---|
| `MarkdownWriter` | `write_local` | 1 |
| `GitTool` (branch/commit) | `write_local` | 2 |
| `PRTool` (draft) | `write_local` | 2 |
| `PRTool` (mark-ready) | `publish` | 2 (gated) |
| `AzureCostTool` (read) | `read` | 3 |
| `PlausibleTool` (read) | `read` | 3 |
| `CMSTool` | `publish` | 4 |
| `EmailTool` | `send` | 4 |
| `SocialTool` (per-platform) | `publish` | 4 |

### 6.5 Inter-agent message format

Verbatim from [`Domain_Agent/Technical_Architecture.md` §6](../../../Domain_Agent/Technical_Architecture.md):

```json
{
  "task_id": "TASK-0042",
  "subtask_id": "TASK-0042.spec",
  "from_agent": "triage_agent",
  "to_agent": "spec_agent",
  "message_type": "instruction",
  "content": "Write a full spec for the dark-mode toggle on ANOTE-web cookie banner, app-3 only.",
  "context": {
    "retrieved": [...],
    "dependency_outputs": {...},
    "indexes_queried": ["app-3", "standards"]
  },
  "metadata": {
    "tokens": {"prompt": 412, "completion": 180},
    "compliance_verdict": "green",
    "approval": null
  }
}
```

The C / A / OQ discipline is enforced at the agent level (§14.5).

## 7. Phase 0 — Retrieval & Telemetry (dependency)

This phase is fully specified in [SPEC-KH-AGENT-001](kh-agent-spike-spec.md). It is a hard prerequisite for every subsequent phase. The orchestrator imports `kh_agent.retriever`, `kh_agent.llm_client`, `kh_agent.token_tracker`, `kh_agent.logger` and depends on the FAISS partition described there (`app-1..4`, `cross-app`, `decisions`, `standards`, `workflows`, `tasks-recent`).

Acceptance gate before Phase 1 starts:
- `kh-agent ingest --fresh` produces all 9 indexes.
- `kh-agent status` operational and reading the JSONL ledger.
- Both prompt edits to `.opencode/agents/{task-triage,spec-writer}.md` landed (with the documented fallback).

## 8. Phase 1 — Multi-Agent Read & Write-Local

### 8.1 Deliverables

| # | Item | Path |
|---|---|---|
| 1.1 | `kh_orchestrator/` package skeleton, `pyproject.toml`, `.env.example` | repo root |
| 1.2 | Models (`Task`, `SubTask`, `TaskResult`, `AgentMessage`, `RunMetadata`, `EvaluationResult`) | `kh_orchestrator/models/` |
| 1.3 | `BaseAgent` (port of thesis `BaseAgent`, adds `tools: list[Tool]`) | `kh_orchestrator/agents/base.py` |
| 1.4 | Per-app agents `app1_agent`, `app2_agent`, `app3_agent`, `app4_agent` | `kh_orchestrator/agents/app{1..4}.py` |
| 1.5 | `triage_agent`, `spec_agent` | `kh_orchestrator/agents/{triage,spec}.py` |
| 1.6 | `compliance_agent` (advisory mode in Phase 1) | `kh_orchestrator/agents/compliance.py` |
| 1.7 | Agent system prompts (one file per agent, KH-specific, with C/A/OQ discipline) | `prompts/agents/*.txt` |
| 1.8 | `Planner`, `Router`, `WorkflowEngine`, `Aggregator`, `Orchestrator` | `kh_orchestrator/orchestrator/` |
| 1.9 | Orchestrator system prompts (`decompose.txt`, `aggregate.txt`) | `prompts/orchestrator/` |
| 1.10 | `Tool` Protocol + `MarkdownWriter` tool | `kh_orchestrator/tools/{base.py,markdown_writer.py}` |
| 1.11 | `ApprovalGate` (rejects everything except `read`/`write_local` until approved); `CostGate` (per-day cap) | `kh_orchestrator/gates/` |
| 1.12 | `state.db` schema + sync from markdown task files | `kh_orchestrator/state/{schema.sql,sync.py}` |
| 1.13 | `kh-orch` CLI (`run`, `sync-state`, `console`) | `kh_orchestrator/cli.py` |
| 1.14 | `kh-console` minimal: Inbox + Now + Health | `kh_orchestrator/console/` |
| 1.15 | Update `.opencode/agents/{task-triage,spec-writer}.md` to call orchestrator instead of running prompts inline | `.opencode/agents/` |
| 1.16 | Tests: unit per agent, smoke per orchestrator path, e2e of triage→spec→PR-draft (against fixture corpus) | `tests/` |

### 8.2 Verification

- `kh-orch run --task "Add dark-mode toggle to ANOTE-web cookie banner"` produces:
  1. A `triage_agent` run that creates a draft `tasks/triage/TASK-XXXX.md` via `MarkdownWriter`, citing chunks from `app-3` and `standards`.
  2. A `spec_agent` run that creates a draft `specs/app-3/TASK-XXXX-spec.md`, citing chunks from `app-3`, `decisions`, `standards` indexes.
  3. A `compliance_agent` advisory verdict on each output.
- All outputs land as markdown files in `kh_proposals/` (a sibling directory, gitignored — they only enter the canonical corpus via PR after operator approval).
- `kh-console` Inbox shows both proposals with diff view, `AgentMessage` chain, retrieved sources, token cost, and Approve/Reject/Comment actions.
- Approving a proposal moves it to its canonical path (`tasks/triage/...` or `specs/app-3/...`), commits it on a new branch, and opens a draft PR — *Phase 1 stops at the draft PR; merging is human in another tab*.
- All 15 thesis-style task levels (S1–S5, M1–M5, C1–C5) have analogues in this domain (single-app S; two-domain spec-needed M; cross-app planner-needed C); a smoke matrix runs at least one of each.

### 8.3 Backwards compatibility

`.opencode/agents/{task-triage,spec-writer}.md` retain their existing structure; their "Required Inputs" section is replaced by a single instruction to invoke `kh-orch run --agent {triage,spec} --task <inbox-path>` and surface the returned summary into the chat. If the orchestrator is unavailable, the previous explicit reading-list behaviour is the documented fallback. The C / A / OQ discipline already in those files is preserved verbatim.

## 9. Phase 2 — Implementation PRs & Cross-App Workflow

### 9.1 Deliverables

| # | Item | Path |
|---|---|---|
| 2.1 | `dev_agent` (specialises per target app via system-prompt selection) | `kh_orchestrator/agents/dev.py` |
| 2.2 | `GitTool` (clone-or-update local checkout, branch, commit) | `kh_orchestrator/tools/git_tool.py` |
| 2.3 | `PRTool` (open draft PR via `gh` CLI; mark-ready is `publish` tier and stays gated) | `kh_orchestrator/tools/pr_tool.py` |
| 2.4 | `applications/index.md` mapping consumed by `GitTool` to resolve repo paths | (existing) |
| 2.5 | `compliance_agent` graduates from advisory to **hard gate** for any `dev_agent` output touching App 1 (`medical_advisor`) Czech-language patient-facing files | `kh_orchestrator/gates/compliance.py` |
| 2.6 | `WorkflowEngine.execute_with_approvals` — extends the thesis engine with optional `human_approval` step type | `kh_orchestrator/orchestrator/workflow.py` |
| 2.7 | Per-app `dev_agent` system prompts (Blazor / Flutter+FastAPI / Next.js / FastAPI+Next.js) | `prompts/agents/dev_app{1..4}.txt` |
| 2.8 | E2E test: a `TASK-0014`-style three-step cross-app graph (one app-3 backend change, one app-3 frontend change, one app-2 verification step) executed against fixture clones | `tests/e2e/test_cross_app.py` |
| 2.9 | `kh-console` Inbox extended with PR-diff view | `kh_orchestrator/console/` |

### 9.2 Verification

- A spec produced by Phase 1 can be handed to `dev_agent` and result in a draft PR, on a feature branch, in the correct application repo.
- For an App 1 spec, `compliance_agent` issues a verdict before `PRTool.execute`; a `red` verdict aborts the workflow; `amber` requires explicit operator override in `kh-console`.
- A cross-app `SubTask` graph with two parallel app-3 changes and one dependent app-2 verification executes via `WorkflowEngine` against fixture clones; the dependency graph is respected.
- No PR is marked ready for review by the agent; merges remain human.
- `kh-console` Inbox shows the PR diff alongside the originating spec.

### 9.3 Constraints

- `dev_agent` never runs the application's own test suite or build inside its own process — it stops at "branch + commit + draft PR" and leaves CI to do its job. (App test suites are flagged as unverified in `current-priorities.md`; running them inside the orchestrator would create false confidence.)
- `dev_agent` never force-pushes, never amends published commits, never modifies `main` directly.
- `GitTool` and `PRTool` operate against a configured local clone path per app, which is read-only outside agent operations (never used as a working tree by the operator concurrently — enforced by a lockfile in `kh_orchestrator_data/locks/`).

## 10. Phase 3 — Content & Analytics (read-side)  *(sketch only)*

### 10.1 Capability
Drafts marketing content; produces weekly KPI and finance briefs as markdown PRs. No external publication, no spend.

### 10.2 Agents introduced
- `content_agent` — drafts blog posts, landing-page sections, social copy. Output: markdown files under `marketing/drafts/`. Uses the App 3 marketing brief and `standards/documentation-standards.md` as anchors. Never publishes.
- `analytics_agent` — pulls Plausible exports (already configured in App 3), produces a weekly brief, top-N pages, conversion funnel deltas, anomalies. Output: `analytics/briefs/YYYY-WW.md`.
- `finance_agent` — reads the `kh_agent` cost ledger, an Azure billing CSV (manually exported by the operator on a schedule), and a small manual P&L sheet. Output: monthly summary `finance/briefs/YYYY-MM.md`. Never executes transactions.

### 10.3 New tools
- `PlausibleTool` (`read`).
- `AzureCostTool` (`read`) — read-only against Cost Management API.

### 10.4 Open issues to resolve in the Phase 3 spec
- Plausible API auth pattern in a single-operator setup.
- Whether App 4 CGM analytics outputs are exposed to `analytics_agent` (default: no — they are clinical, not product analytics).

## 11. Phase 4 — Gated External Publication  *(sketch only)*

### 11.1 Capability
The system can publish content, send emails, and post to social — only with explicit per-action approval, only to allow-listed channels, and only after a `green` `compliance_agent` verdict.

### 11.2 Agents introduced
- `publisher_agent` — turns approved drafts into CMS publications (App 3 site content + RSS).
- `social_agent` — turns approved drafts into platform posts (LinkedIn / X / Bluesky).
- `email_agent` — sends approved campaigns to allow-listed recipients via the existing App 3 nodemailer/Gmail SMTP path or Resend/Postmark.

### 11.3 New tool tier (`publish` / `send`)
- `CMSTool` (`publish`).
- `EmailTool` (`send`) — recipient allow-list defaults to `[operator]`; expansion is a separate spec amendment.
- `SocialTool` (`publish`) — per platform, with a draft queue and explicit "post now" approval.

### 11.4 Healthcare-specific constraints
- App 1 patient-facing Czech content is **excluded** from autonomous draft → publish pipelines in Phase 4. Drafts may exist; their publication path stays manual until a separate clinical review process is documented.
- All outbound copy for any channel passes through `compliance_agent` (`green` required) and is checked against `project-overview.md` non-goals (no medical-device claim, no clinical-replacement claim).
- Daily caps on emails/posts are enforced by `policy/`.

### 11.5 Open issues to resolve in the Phase 4 spec
- Per-platform OAuth flows in a single-operator, localhost-bound deployment.
- Retraction policy (LinkedIn allows edit, X allows delete, email is irrevocable; the operator UI must reflect this honestly).
- Whether to require two-step approval (first the draft, then the send time) for emails.

## 12. Phase 5 — Strategy & Dedup Loop  *(sketch only)*

### 12.1 Capability
Closes the priorities → tasks → deploy → analytics → priorities loop; surfaces drift in the corpus automatically.

### 12.2 Agents introduced
- `dedupe_agent` — runs near-duplicate detection (cosine ≥ 0.92 across chunks; fuzzy title match in `tasks/`, `specs/`, `decisions/`, `handoffs/`). Emits `dedupe_proposals/YYYY-MM-DD.md`. **Never auto-merges.** The operator approves a merge plan; `dev_agent` applies the merge as a normal PR.
- `freshness_agent` — scans for `// TODO: replace with production domain`, broken links, references to deployed app versions older than the current Azure deployment (via tag check), counts that disagree across docs (the "57 vs 32 tests" class). Output: `tasks/triage/HOUSEKEEPING-WW.md`.
- `strategy_agent` — reads cost ledger, KPI snapshots, roadmap, and proposes priority changes as PRs against `current-priorities.md` and `dashboards/roadmap.md`. Never edits the corpus directly.

### 12.3 The "covers reality" loop
Runs on a weekly schedule (cron + `kh-orch run`):
1. `kh-agent ingest --check` → fail-loud if any index is stale.
2. `dedupe_agent` → proposals.
3. `freshness_agent` → housekeeping task.
4. `strategy_agent` → priority PR.
5. Operator reviews all four artefacts in `kh-console` Inbox and approves selectively.

### 12.4 Hard rules
- No agent **deletes** content from the canonical corpus. Dedup happens via PR-and-merge with the operator as the merger.
- `strategy_agent` never modifies application code; it only proposes priority changes.

## 13. Phasing summary table

| Phase | Adds | Tools at risk tier | Operator role |
|---|---|---|---|
| 0 | retrieval, telemetry | `read` | none new |
| 1 | per-app + triage + spec agents, `MarkdownWriter`, `kh-console` Inbox | +`write_local` | reviews proposals, merges PRs |
| 2 | dev_agent, Git/PR tools, hard compliance gate on App 1 | unchanged | reviews diffs, merges PRs |
| 3 | content/analytics/finance agents (drafts only) | +`read` external | reviews briefs |
| 4 | publisher/social/email agents | +`publish`, `send` | per-action approval |
| 5 | dedup/freshness/strategy agents | unchanged | reviews weekly housekeeping |

## 14. Healthcare-Specific Safety Policy

The KH portfolio is not a generic SaaS — App 1 publishes Czech medical advice and App 2 processes patient dictation. The constraints below apply to **every phase** and override conveniences elsewhere in this spec.

### 14.1 No patient data in the orchestration layer
- App 2 transcripts, App 4 CGM CSVs, and any PII are explicitly excluded from `kh_agent` ingestion and from any agent context window.
- A pre-ingest scanner (extending the one in [SPEC-KH-AGENT-001](kh-agent-spike-spec.md) §9) refuses files matching CGM-CSV signatures, Bearer tokens, or PHI patterns.
- The orchestrator's structured store contains no patient identifiers, ever.

### 14.2 No autonomous publication of medical content
- Anything affecting App 1 patient-facing surfaces or the App 3 demo passes through `compliance_agent` and human approval.
- The TASK-0034 Czech safety disclaimer pattern is encoded as a content-template requirement; `compliance_agent` rejects any App 1-targeted draft that strips it.

### 14.3 `compliance_agent` is a hard gate from Phase 2 onward
- Returns `red` / `amber` / `green` plus rationale.
- The workflow engine refuses to dispatch any `publish` / `send` action with a non-green verdict, regardless of operator preference, until a future spec introduces an explicit override with audit logging.
- For App 1 patient-facing changes specifically, even `green` does not bypass operator review.

### 14.4 GDPR-by-construction
- No recipient list contains EU residents without a documented lawful basis.
- The email tool's recipient allow-list defaults to `[operator]` in Phase 4.
- Logs never contain message body content for emails or social posts; only counts, recipients-by-id, and rendered hashes.

### 14.5 Confirmed / Assumption / Open-Question discipline
- Already imported into the thesis prompts ([prompts/agents/business_system.txt](../../../Domain_Agent/prompts/agents/business_system.txt) etc.). Re-imported into every KH agent system prompt.
- `compliance_agent` checks the discipline on every outgoing draft; missing labels on contestable claims are an `amber` verdict at minimum.

### 14.6 No medical-device claims, ever
- The `project-overview.md` non-goals are surfaced verbatim to every content-producing agent's system prompt and judged against by `compliance_agent`.

### 14.7 Fail-shut on unknown channels
- `policy/channels.yaml` is the registry. A channel not in the registry yields `red` automatically. Adding a channel is a spec-amendment-level change.

## 15. Data Substrate

### 15.1 Layout

```
Knowledge.Healthcare/
  kh_orchestrator/                 # package
  kh_orchestrator_data/            # gitignored runtime
    state.db                       # SQLite, derived from markdown
    cost_ledger/                   # JSONL, append-only
    action_log/                    # JSONL, append-only (tool calls)
    proposals/                     # agent-written markdown awaiting approval
    locks/                         # concurrency locks for app repo clones
    kpi/                           # parquet (Phase 3+)
```

### 15.2 SQLite state DB

The DB is **derived**, not authoritative. Rebuilt by `kh-orch sync-state` from the markdown corpus. Tables:

| Table | Source of truth | Purpose |
|---|---|---|
| `tasks` | `tasks/*/*.md` frontmatter | task graph queries; status transitions |
| `specs` | `specs/**/*.md` frontmatter | spec ↔ task linkage |
| `decisions` | `decisions/**/*.md` frontmatter | ADR query |
| `handoffs` | `handoffs/*.md` frontmatter + filename date | rolling 30-day window for `tasks-recent` |
| `apps` | `applications/index.md` | repo paths for `GitTool` |
| `cost_daily` | derived from `cost_ledger/` | per-day token spend, surfaces in `CostGate` |
| `actions` | derived from `action_log/` | full audit of tool calls |

### 15.3 Append-only logs

- `cost_ledger/calls-YYYY-MM-DD.jsonl` — schema from [SPEC-KH-AGENT-001](kh-agent-spike-spec.md) §6.5.
- `action_log/actions-YYYY-MM-DD.jsonl` — every `Tool.execute` call: `{ts, tool, action_id, idempotency_key, agent, task_ref, dry_run_hash, approval_id, result, error?}`.
- Logs are append-only by file system convention. Any agent attempt to delete or rewrite is a code defect and is asserted against in `tests/test_no_log_mutation.py`.

### 15.4 The "covers reality, no duplicates, up-to-date" honest answer

- **Up-to-date**: `freshness_agent` (Phase 5) detects drift; the operator approves the fixes. `kh-agent ingest --check` is a session-start hook.
- **No duplicates**: `dedupe_agent` (Phase 5) detects, the operator approves merges. The system never silently merges.
- **Covers reality**: the SQLite state DB is regenerable from markdown, so any disagreement between markdown and DB is a reproducible bug, not data loss.

This is the only honest answer. Anything more aggressive (autonomous deduplication or autonomous "freshness" rewriting) silently corrupts history and will not be built.

## 16. Operator UI: `kh-console`

### 16.1 Stack
FastAPI backend in `kh_orchestrator/console/api/` + Next.js front-end in `kh_orchestrator/console/web/`. Bound to `127.0.0.1` only. No auth in v1 (single operator, localhost). Reuses the App 3 stack the operator already runs.

### 16.2 Views (Phase 1)

| View | Purpose |
|---|---|
| **Inbox** | Pending agent proposals (specs, drafts, dedupe merges, posts, emails). Each card shows: diff view, originating chain of `AgentMessage`s, retrieved sources, token cost, `compliance_agent` verdict (when present). Actions: Approve · Reject · Comment. Approval issues a typed `Approval` and triggers the queued `Tool.execute`. |
| **Now** | Live task graph for in-flight runs; what's running, what's blocked, ongoing token burn vs daily cap. Read-only. |
| **Health** | Per-index staleness; dedupe-candidate count; unresolved Open Questions count across the corpus. |

### 16.3 Views (Phase 3+)
- **Money** — `finance_agent` view: Azure cost rollup, per-agent / per-tool spend, projection vs cap.

### 16.4 Views (Phase 4+)
- **Outbox** — scheduled publications, sent emails, social posts. Buttons: retract (where the platform supports it), reissue, mark-incident.

### 16.5 Hard rules
- No write happens without an explicit user action in the UI (or an explicit CLI invocation by the operator).
- Every approval emits a typed `Approval(id, scope, expires_at, granted_by="operator")`. Approvals are single-use, scoped to one `Action`, and time-bounded.
- The UI never displays raw API keys, even masked. It displays which deployment / channel was used, by name.

## 17. CLI

`kh-orch` (entry point declared in `pyproject.toml`):

| Subcommand | Purpose | Example |
|---|---|---|
| `run` | Dispatch a single high-level task through the orchestrator | `kh-orch run --task "Add dark-mode toggle to ANOTE-web cookie banner"` |
| `run --agent NAME` | Run a single agent directly (skip planner) | `kh-orch run --agent triage --task tasks/inbox/raw.md` |
| `sync-state` | Rebuild `state.db` from markdown | `kh-orch sync-state` |
| `console` | Start the local console (`uvicorn` + Next.js dev or built bundle) | `kh-orch console` |
| `judge` | (Phase 1.5+) Run the LLM-as-Judge over a target file | `kh-orch judge specs/app-3/TASK-0042-spec.md` |
| `cost` | Wrapper around `kh-agent status` plus action-log rollup | `kh-orch cost --days 30` |

## 18. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `dev_agent` opens a PR that breaks an app's build | High | Low | Drafts only; CI enforces; operator merges. |
| `compliance_agent` false-negative (lets through a clinical claim) | Medium | High | Hard gate on App 1 patient-facing surfaces requires operator override regardless of verdict; periodic audit of `green` verdicts against actual outcomes. |
| `compliance_agent` false-positive (blocks legitimate content) | High | Low | Operator override path documented; verdicts include rationale to inform prompt iteration. |
| Cost runaway via planner/agent loops | Medium | Medium | `CostGate` enforces per-day cap; `WorkflowEngine` refuses to dispatch when cap breached; `kh-console` Now view shows live burn. |
| Patient data accidentally ingested | Low | Critical | Pre-ingest scanner refuses on signature; tests assert refusal; ingestion is opt-in per index, not opt-out. |
| Markdown ↔ state.db drift | Medium | Low | DB is derived, regenerable; `sync-state` is idempotent; tests round-trip a fixture corpus. |
| Approval bypass (operator approves blindly) | Medium | High | `kh-console` cards must surface diff + sources + cost before the Approve button is enabled in the UI. |
| Tool credential leakage in logs | Low | High | Logger redaction tested with synthetic Bearer tokens; structured logging never serialises request payloads, only metadata. |
| Operator dependency on the system's continued availability | Medium | Medium | Every fallback path is documented: orchestrator down → use the original `.opencode/agents/` reading-list behaviour; console down → use `kh-orch run` directly. The system is augmentation, not infrastructure. |
| Scope creep (Phase 3+ pulled into Phase 1) | High | Medium | Phase 1/2 acceptance criteria are explicit; Phases 3–5 have their own specs as a hard gate. |
| Regulatory misclassification (a publish loop ends up looking like a clinical decision support feature) | Low | Critical | `project-overview.md` non-goals are surfaced to every content agent; `compliance_agent` rubric explicitly checks for medical-device-class claims. |
| OpenCode tool registration limitations (re. `bash: deny`) | Medium | Medium | The orchestrator runs as a separate process invoked via the OpenCode shim; no `bash` permission needed inside the OpenCode agents themselves. |

## 19. Validation

### 19.1 Phase 1 acceptance
- All unit + smoke tests pass.
- The five smoke queries from [SPEC-KH-AGENT-001](kh-agent-spike-spec.md) §10.2 still pass after the orchestrator wraps them.
- `kh-orch run --task "Add dark-mode toggle to ANOTE-web cookie banner"` produces a triage proposal and a spec proposal in `kh_orchestrator_data/proposals/`, both visible in `kh-console` Inbox.
- Approving each proposal moves it to its canonical path on a feature branch with a draft PR.
- `compliance_agent` advisory verdicts are present on every output.
- Token cost per run is reported accurately by `kh-orch cost --days 1`.
- The C / A / OQ discipline is observable in every produced markdown file.

### 19.2 Phase 2 acceptance
- A spec produced by Phase 1 can be handed to `dev_agent` and produces a correctly-scoped draft PR.
- A `TASK-0014`-style three-step cross-app graph executes against fixture clones; dependency order is respected; parallelism is observed in the `Now` view.
- An App 1 patient-facing change is **blocked** at the gate when `compliance_agent` returns `red`; an `amber` verdict requires explicit override; both paths are reflected in `action_log/`.
- No PR is auto-marked-ready; merges remain human.

### 19.3 Cross-phase invariants (asserted by tests)
- No agent can write outside `kh_orchestrator_data/proposals/` without a `MarkdownWriter` action with a valid `Approval`.
- No `Tool.execute` call appears in `action_log/` without a matching `Approval` (for `publish`/`send`/`spend` tiers).
- No log file contains an API key, Bearer token, or recognisable PHI pattern.
- `kh-orch sync-state` is idempotent: running it twice produces no changes the second time.

## 20. Rollback

Each phase is purely additive and rollback-safe:

- **Phase 0 rollback**: revert prompt edits in `.opencode/agents/`; `rm -rf kh_agent/ kh_agent_data/`. (See SPEC-KH-AGENT-001 §12.)
- **Phase 1 rollback**: revert prompt edits to `.opencode/agents/{task-triage,spec-writer}.md` (back to the Phase 0 state); `rm -rf kh_orchestrator/ kh_orchestrator_data/`. The original `@task-triage` / `@spec-writer` behaviour is restored.
- **Phase 2 rollback**: remove `dev_agent`, `GitTool`, `PRTool` from the agent/tool registries; the rest of Phase 1 keeps working.
- **Phase 3+ rollback**: per phase, by removing the introduced agents and tools.
- **Data integrity**: nothing in this system holds canonical data. The markdown corpus is the only source of truth and is never modified by the orchestrator without a PR and operator merge. State DB and logs are reproducible from the corpus and from the action history respectively.

The orchestration layer is intentionally a *cache and proposal generator* over the markdown corpus. Removing it leaves the corpus exactly where it was.

## 21. Implementation Plan

### 21.1 Phase 0 (dependency)
Refer to [SPEC-KH-AGENT-001](kh-agent-spike-spec.md) §11 (Rollout). Acceptance gate before Phase 1 starts is in §7 of this document.

### 21.2 Phase 1 sequencing
| Step | What | Where | Validation | Rollback |
|---|---|---|---|---|
| 1.1 | Skeleton package + `pyproject.toml` + tests harness | `kh_orchestrator/` | `pytest` runs zero tests cleanly | `rm -rf kh_orchestrator/` |
| 1.2 | Models port from thesis | `kh_orchestrator/models/` | `tests/test_models.py` | revert |
| 1.3 | `BaseAgent` + per-app agents (4) with KH prompts | `kh_orchestrator/agents/`, `prompts/agents/` | per-agent unit test loads correct index, retrieves, returns `AgentMessage` | revert |
| 1.4 | `Planner`, `Router`, `WorkflowEngine`, `Aggregator`, `Orchestrator` | `kh_orchestrator/orchestrator/` | thesis-style unit tests reused | revert |
| 1.5 | `Tool` Protocol + `MarkdownWriter` | `kh_orchestrator/tools/` | `dry_run` produces diff; `execute` requires `Approval`; tests assert refusal without one | revert |
| 1.6 | `ApprovalGate` + `CostGate` | `kh_orchestrator/gates/` | injected `Approval` allows; missing approval blocks; cap exceeded blocks | revert |
| 1.7 | `triage_agent`, `spec_agent`, `compliance_agent` (advisory) | `kh_orchestrator/agents/{triage,spec,compliance}.py` | E2E: raw task → triage proposal → spec proposal | revert |
| 1.8 | `state.db` schema + sync | `kh_orchestrator/state/` | `sync-state` round-trip on fixture corpus is idempotent | drop DB, regenerate |
| 1.9 | `kh-orch` CLI | `kh_orchestrator/cli.py` | `kh-orch run` produces proposals; `kh-orch sync-state` works | revert |
| 1.10 | `kh-console` Inbox + Now + Health | `kh_orchestrator/console/` | manual: open `localhost:PORT`, see proposals, approve one | stop service, revert |
| 1.11 | OpenCode agent prompt shims | `.opencode/agents/{task-triage,spec-writer}.md` | invoking `@task-triage` ends up calling `kh-orch run --agent triage` | restore previous file |
| 1.12 | Smoke matrix (one S-, M-, C-tier task each) | `tests/e2e/` | matrix passes against fixture corpus | revert tests |

### 21.3 Phase 2 sequencing
| Step | What | Where | Validation | Rollback |
|---|---|---|---|---|
| 2.1 | `GitTool` + `PRTool` (draft-only) | `kh_orchestrator/tools/` | unit tests against a temp Git repo + a `gh` CLI mock | revert |
| 2.2 | Per-app `dev_agent` system prompts | `prompts/agents/dev_app{1..4}.txt` | per-prompt golden-output tests | revert |
| 2.3 | `dev_agent` | `kh_orchestrator/agents/dev.py` | E2E: spec → branch + commit + draft PR (against fixture clone) | revert |
| 2.4 | `compliance_agent` upgraded to hard gate for App 1 patient-facing files | `kh_orchestrator/gates/compliance.py` | E2E: red verdict on a clinical-claim draft aborts; amber requires override | revert to advisory |
| 2.5 | `WorkflowEngine.execute_with_approvals` | `kh_orchestrator/orchestrator/workflow.py` | E2E: cross-app three-step graph executes against fixture clones | revert engine |
| 2.6 | `kh-console` Inbox PR-diff view | `kh_orchestrator/console/` | manual: see diff for a Phase-2-produced PR | revert |
| 2.7 | E2E `TASK-0014`-style smoke | `tests/e2e/test_cross_app.py` | green | revert |

### 21.4 Operator workflow once Phases 1+2 are live
1. Raw task arrives in `tasks/inbox/` (or in chat → operator runs `kh-orch run --task ...`).
2. Orchestrator decomposes via `Planner`, dispatches to per-app + cross-cutting agents.
3. Proposals land in `kh_orchestrator_data/proposals/` and surface in `kh-console` Inbox with `compliance_agent` verdicts.
4. Operator reviews, approves, comments, or rejects.
5. On approval, `MarkdownWriter` (Phase 1) writes the file to its canonical path on a feature branch and `PRTool` opens a draft PR.
6. From Phase 2, `dev_agent` can pick up an approved spec and open a draft PR in the relevant app repo.
7. CI and the operator handle merging.
8. Cost and action history are visible in `kh-console` Now / Health, and via `kh-orch cost`.

## 22. Open Questions

1. **OpenCode integration mechanics** — same as in [SPEC-KH-AGENT-001](kh-agent-spike-spec.md) §13. The orchestrator runs as a separate process so the `bash: deny` permission on the existing OpenCode agents is a non-issue, but the cleanest invocation surface (slash command, MCP server, plain CLI) is still to be decided. Resolution required before Phase 1.11.
2. **Per-app `dev_agent` vs. single `dev_agent` with per-app prompt selection** — current spec says single agent with per-app prompts. Revisit if cross-stack reasoning becomes a bottleneck.
3. **Whether `compliance_agent` uses a different (higher-quality, more expensive) model than the rest** — likely yes for App 1 patient-facing changes. Needs a small ablation in Phase 1.
4. **Concurrency model for app repo clones** — current spec uses a per-repo lockfile. Sufficient for single operator; revisit if multiple `dev_agent` runs against the same repo become routine.
5. **State DB rebuild cost on a large corpus** — likely negligible (markdown only) but measure before assuming.
6. **Phase 4 OAuth flows** — deferred to the Phase 4 spec; flagged here so Phase 1/2 don't accidentally bake in assumptions about persistent platform credentials.
7. **Whether `kh-console` should be a single React app served by FastAPI, or a Next.js app talking to FastAPI** — both work; pick the one closer to App 3 conventions for operator familiarity.
8. **Daily cost cap value** — placeholder; operator-set in `kh_orchestrator/policy/caps.yaml`. Suggest USD 5/day for Phase 1, raise once observed.
9. **Whether `tasks-recent` should narrow to a 7-day rolling window** — same Open Question as in SPEC-KH-AGENT-001 §13.
10. **Multi-operator support** — explicitly out of scope; flagged so a future spec can revisit auth and per-operator approval scoping.

## 23. References

- This spec is an extension of [SPEC-KH-AGENT-001](kh-agent-spike-spec.md), which is its hard prerequisite (Phase 0).
- Thesis architecture: [`Domain_Agent/Technical_Architecture.md`](../../../Domain_Agent/Technical_Architecture.md), [`Domain_Agent/Implementation_Plan.md`](../../../Domain_Agent/Implementation_Plan.md), [`Domain_Agent/External_Validation_Healthcare.md`](../../../Domain_Agent/External_Validation_Healthcare.md).
- Upstream code reused: [`Domain_Agent/src/`](../../../Domain_Agent/src/) — see §6.2 reuse map for module-by-module mapping.
- KH standards consulted: `standards/security-privacy-standards.md`, `standards/engineering-standards.md`, `standards/testing-standards.md`, `standards/documentation-standards.md`.
- KH workflows consulted: `workflows/spec-process.md`, `workflows/cross-app-change-process.md`, `workflows/session-start-checklist.md`, `workflows/triage-process.md`, `workflows/task-lifecycle.md`.
- KH context anchors: `project-overview.md` (mission and non-goals), `system-landscape.md` (apps, integrations, shared `anote-openai`), `current-priorities.md` (active blockers), `applications/index.md` (app-id ↔ repo path).
- Existing OpenCode agents replaced by orchestrator shims: `.opencode/agents/task-triage.md`, `.opencode/agents/spec-writer.md`.
