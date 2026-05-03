# Technical Specification: `kh_agent` — Retrieval & Telemetry Spike for the Knowledge.Healthcare Control Layer

| Field | Value |
|---|---|
| Spec ID | SPEC-KH-AGENT-001 |
| Status | Draft |
| Author | Ivan Anikin (with Domain Agent thesis context) |
| Date | 2026-05-03 |
| Apps affected | Cross-app (control layer; infrastructure for all four apps' agent workflows) |
| Source task | (to be created via `@task-triage`) |
| Source thesis section | [`External_Validation_Healthcare.md` §4](../../../Domain_Agent/External_Validation_Healthcare.md) |
| Upstream code reused | `Domain_Agent/src/{knowledge,llm,orchestrator,evaluation}/` |

---

## 1. Summary

Build a small, self-contained Python package, `kh_agent`, that lifts four components from the `Domain_Agent` thesis codebase and adapts them to the `Knowledge.Healthcare` markdown corpus:

1. A **retrieval-backed knowledge runtime** (per-app and per-cross-cutting-concern FAISS indexes).
2. A **token-tracking LLM client** wrapping the shared Azure OpenAI resources `anote-openai` and `anote-openai-swe`.
3. A **CLI/tool surface** that the existing OpenCode subagents (`@task-triage`, `@spec-writer`) can call to retrieve relevant context on demand instead of being told to read a fixed file list.
4. (Optional, second iteration) A **typed cross-app workflow engine** that automates the manual checklist in `workflows/cross-app-change-process.md`.

The spike is intentionally narrow: it adds *infrastructure* to the control layer, it does not introduce new application functionality and does not change any of the four production application repositories.

## 2. Objective

Close three concrete gaps that `current-priorities.md` already flags as operational blockers:

- "No monitoring or observability across any application — no Application Insights, no centralized logging, no alerting." → addressed by `TokenTracker`.
- The implicit "no automated relevance check" in agent context loading. The `AGENTS.md` reading list grows linearly with the corpus and is curated by hand. → addressed by the per-domain retriever.
- "Test counts conflict across documentation" and similar drift between docs. → addressed *secondarily* by an LLM-as-Judge gate over spec/triage outputs (deferred to iteration 2 but its insertion point is specified here so iteration 1 does not paint into a corner).

## 3. Scope

### In scope (Iteration 1, this spec)
- New package `kh_agent/` at the root of `Knowledge.Healthcare/`.
- Ingestion CLI that builds FAISS indexes from the existing markdown corpus.
- Retriever exposed as both a Python API and a thin CLI (`kh-agent retrieve …`) so OpenCode subagents can shell out to it.
- Async LLM client wrapping `anote-openai` (West Europe, primary chat + embeddings) with token tracking and per-call structured logging.
- Updated `.opencode/agents/task-triage.md` and `.opencode/agents/spec-writer.md` instructions that **describe** the new tool and constrain when it must be used. (OpenCode tool registration mechanics are app-of-OpenCode-specific and are an Open Question — see §13.)
- Unit tests, smoke tests, and a small README for `kh_agent/`.
- `.gitignore` entries for the persisted FAISS files.

### In scope (Iteration 2, sketched only here)
- LLM-as-Judge gate over spec/triage outputs.
- Workflow engine port for cross-app tasks.

### Out of scope
- Changes to any of `medical_advisor`, `ANOTE_mobile`, `ANOTE-web`, `Health-Analysis` source code.
- Replacing the markdown corpus as source of truth — the markdown remains canonical, FAISS is a derived artefact.
- Replacing OpenCode itself or moving away from the `tasks/` lifecycle.
- Replacing the existing `scripts/generate_dashboard.py` — `kh_agent` does not write to `dashboards/`.
- Persistence beyond FAISS index files and structured JSONL logs (no database, no service).

## 4. Non-Goals

- This is **not** a multi-agent LLM runtime. The OpenCode subagents remain the orchestration surface; `kh_agent` only provides them with retrieval and an instrumented LLM client.
- This is **not** a regulated or clinical component. It operates on the control-layer markdown corpus, never on patient data, transcripts, or PII.
- No fine-tuning, no custom embedding models, no graph databases.

## 5. Current Behaviour

- `AGENTS.md` instructs every session to read a fixed list of files (`current-priorities.md`, `applications/app-{N}-overview.md`, latest entry in `handoffs/`, relevant workflow files).
- `.opencode/agents/task-triage.md` and `.opencode/agents/spec-writer.md` each enumerate a "Required Inputs" file list that the agent must read at the start of triage / spec writing.
- LLM calls happen inside whatever client the OpenCode runtime uses; from the Knowledge.Healthcare repo's perspective, token usage and cost across `anote-openai` are invisible. `current-priorities.md` flags this as a blocker.
- Cross-app tasks are coordinated by `workflows/cross-app-change-process.md`, a manual checklist.

## 6. Proposed Behaviour

### 6.1 Package layout

```
Knowledge.Healthcare/
  kh_agent/
    __init__.py
    config.py             # Pydantic Settings; reads .env; never reads/writes secrets to git
    chunking.py           # markdown-aware splitter (port of Domain_Agent/src/knowledge/ingestion.py, MD-only)
    embeddings.py         # AsyncAzureOpenAI embeddings wrapper (port of src/knowledge/embeddings.py)
    vector_store.py       # FAISS IndexFlatIP wrapper (port of src/knowledge/vector_store.py)
    retriever.py          # Retriever + UnifiedRetriever (port of src/knowledge/retriever.py)
    llm_client.py         # AsyncAzureOpenAI chat wrapper with retry (port of src/llm/client.py)
    token_tracker.py      # In-process call/cost ledger (port of src/llm/token_tracker.py)
    logger.py             # Structured JSONL logger (port of src/evaluation/logger.py)
    corpus.py             # NEW: maps the KH directory layout → list of (index_name, source_dir) pairs
    cli.py                # NEW: argparse entry points (ingest / retrieve / status / call)
    judge.py              # ITER-2: LLM-as-Judge over spec/triage outputs
    workflow.py           # ITER-2: cross-app workflow engine
    py.typed
  kh_agent_data/
    vector_stores/        # FAISS indexes + metadata JSON, gitignored
    logs/                 # structured JSONL call logs, gitignored
  scripts/
    kh_agent_ingest.sh    # convenience wrapper: rebuild all indexes
  tests/
    test_chunking.py
    test_vector_store.py
    test_retriever.py
    test_llm_client.py
    test_corpus.py
    test_cli.py
  pyproject.toml          # package metadata, ruff + mypy + pytest config
  .env.example            # documents required env vars (no secrets)
```

The `kh_agent_data/` directory is the *only* writable side-effect of `kh_agent`. It is gitignored. Markdown remains the canonical source of truth; FAISS files are reproducible from `kh-agent ingest`.

### 6.2 Index partition (the H2 invariant in this corpus)

The thesis architecture requires that each domain has its own knowledge base ([`Technical_Architecture.md` §5.4](../../../Domain_Agent/Technical_Architecture.md)). Mapped onto the KH corpus, "domain" means **application** for app-specific content and **concern** for cross-cutting content. The partition is therefore:

| Index name | Source directories | Notes |
|---|---|---|
| `app-1` | `applications/app-1-overview.md`, `specs/app-1/**/*.md` | medical_advisor |
| `app-2` | `applications/app-2-overview.md`, `specs/app-2/**/*.md` | ANOTE_mobile |
| `app-3` | `applications/app-3-overview.md`, `specs/app-3/**/*.md` | ANOTE-web |
| `app-4` | `applications/app-4-overview.md`, `specs/app-4/**/*.md` | Health-Analysis |
| `cross-app` | `specs/cross-app/**/*.md` | Cross-app specs |
| `decisions` | `decisions/**/*.md` (excluding `adr-template.md`, `README.md`) | ADR corpus |
| `standards` | `standards/**/*.md` | engineering / testing / security-privacy / documentation |
| `workflows` | `workflows/**/*.md`, `AGENTS.md`, `glossary.md` | Process and terminology |
| `tasks-recent` | `tasks/active/**/*.md`, `tasks/triage/**/*.md`, last 30 entries of `handoffs/`, `current-priorities.md` | Volatile; rebuilt on every `kh-agent ingest --fresh tasks-recent` |

Rules:
- Each index is a separate `VectorStore` instance (one FAISS file + one metadata JSON), exactly mirroring the thesis pattern of one index per `DomainType`.
- Metadata stored on each chunk: `{path, app_id, kind, last_modified, heading_path}`. `heading_path` is the breadcrumb of `#`/`##` headings around the chunk and is added by the markdown-aware chunker.
- `tasks-recent` is special: it is intentionally short-lived and small, so cheap to rebuild. The other indexes are rebuilt on demand.

A retrieval call selects one or more indexes, queries each, and merges by score (the thesis `UnifiedRetriever` already does this).

### 6.3 Chunking

Reuse the recursive-character splitter from [`src/knowledge/ingestion.py`](../../../Domain_Agent/src/knowledge/ingestion.py) with two adaptations specific to a documentation corpus:

1. **Markdown-only.** Drop PDF/JSON branches. The KH corpus is markdown.
2. **Heading-aware.** Before splitting, parse `#`/`##`/`###` headings, attach the heading breadcrumb to chunk metadata as `heading_path`. The retriever surfaces this so the LLM sees not just the chunk but where in the file it came from.

Defaults: `chunk_size=900`, `chunk_overlap=150`. These differ from the thesis defaults (`1000` / `200`) because KH documents are denser per token (tables and bullets) than the GovFlow knowledge bases.

### 6.4 Embeddings & LLM client

Both wrap `AsyncAzureOpenAI` directly, configured against the existing healthcare resources:

| Setting | Default | Source |
|---|---|---|
| `KH_AZURE_OPENAI_ENDPOINT` | `https://anote-openai.openai.azure.com/` | `system-landscape.md` (Confirmed) |
| `KH_AZURE_OPENAI_API_VERSION` | `2024-10-21` | Assumption — verify against the App 1 / App 2 deployment configs |
| `KH_AZURE_OPENAI_API_KEY` | (env only, never committed) | per `standards/security-privacy-standards.md` |
| `KH_CHAT_DEPLOYMENT` | `gpt-5-mini` (or `gpt-4.1-mini`) | `system-landscape.md` lists `gpt-5-mini` as deployed in `anote-openai` |
| `KH_EMBED_DEPLOYMENT` | `text-embedding-3-small` | Confirmed in `system-landscape.md` |
| `KH_TEMPERATURE` | `0.1` (matches the OpenCode subagent files) | confirmed |
| `KH_MAX_TOKENS` | `4096` | thesis default; revisit per call site |

Open question (deferred to iteration 2): whether to also expose the Sweden Central transcription deployment (`anote-openai-swe`). For iteration 1, no — `kh_agent` does no audio.

The client signature mirrors `LLMClient.generate(system_prompt, user_prompt, context="") -> LLMResponse` from the thesis. A `generate_structured(system_prompt, user_prompt, response_format)` overload is included so iteration 2 (`judge.py`) does not require a client change.

### 6.5 Token tracking & logging

Port `TokenTracker` verbatim. Per call, append a JSONL record to `kh_agent_data/logs/calls-YYYY-MM-DD.jsonl` with:

```json
{
  "ts": "2026-05-03T14:22:05Z",
  "kind": "chat" | "embed" | "retrieve",
  "deployment": "gpt-5-mini",
  "prompt_tokens": 412,
  "completion_tokens": 180,
  "total_tokens": 592,
  "estimated_cost_usd": 0.000XYZ,
  "agent": "@task-triage" | "@spec-writer" | "cli" | "<custom>",
  "task_ref": "TASK-XXXX" | null,
  "indexes_queried": ["app-3", "decisions"],
  "duration_ms": 743
}
```

This is the minimal record required to retire the `current-priorities.md` "no observability" blocker for the control layer. Cost rates are loaded from `kh_agent/pricing.yaml` and are **explicitly an Assumption** maintained by hand — no live pricing API call.

A small `kh-agent status` CLI command summarises the last N days from these files (total tokens by deployment, total estimated USD, calls per agent). No external service.

### 6.6 CLI surface

`kh-agent` (entry point declared in `pyproject.toml`):

| Subcommand | Purpose | Example |
|---|---|---|
| `ingest [--index NAME ...] [--fresh]` | Build FAISS indexes from the markdown corpus. `--fresh` deletes the index first; default is incremental by file mtime. | `kh-agent ingest --fresh app-3 cross-app` |
| `retrieve --query "..." [--indexes a,b,c] [--top-k 5] [--json]` | Query one or more indexes, print formatted context (default human-readable, `--json` for tool consumption). | `kh-agent retrieve --query "anote-web-api SSE rollout risks" --indexes app-3,decisions --json` |
| `status [--days 7]` | Summarise token usage and cost from JSONL logs. | `kh-agent status --days 30` |
| `call --system PATH --user "..." [--context-from "kh-agent retrieve …"]` | Single instrumented chat call, intended for tool use by an OpenCode agent. | (see §6.7) |
| `judge --target FILE [--rubric NAME]` | (Iteration 2) LLM-as-Judge over a spec or triage file. | deferred |

All subcommands return non-zero on failure and write structured errors to stderr. All write to `kh_agent_data/logs/`.

### 6.7 OpenCode agent integration

The thesis pattern is *the agent does retrieval as part of its execution*. Translated to OpenCode where tool registration is configuration-dependent, the minimal viable change is a documented protocol that the human or runtime can wire as a tool, plus an updated agent prompt that requires its use.

The exact tool-registration mechanics (e.g., whether to declare `kh-agent` in `.opencode/agents/<name>.md` frontmatter, in `.opencode/commands/`, or as a generic shell tool) is an Open Question — see §13. The agent files themselves are updated as follows:

`.opencode/agents/task-triage.md` — replace the static "Required Inputs" reading list with:

> ## Required Inputs
> 1. **Task description** — from chat message or file in `tasks/inbox/`.
> 2. **Retrieved context** — call `kh-agent retrieve` with a query derived from the task description against the indexes `applications`, `workflows`, `tasks-recent`. If the task mentions a specific app (`app-1`/`app-2`/`app-3`/`app-4`/`cross-app`), include that index. Use `--top-k 8` for triage-time recall.
> 3. **Always-loaded files** (small, high-prior, not in any index): `applications/index.md`, `dashboards/task-board.md`, `tasks/templates/task-template.md`, `tasks/templates/triage-template.md`. Read these directly.
>
> Do not read other files until retrieval suggests they are relevant. If retrieval returns no results above a relevance threshold of 0.25, fall back to the previous explicit reading list and flag the retrieval miss as an Open Question in the triage assessment.

`.opencode/agents/spec-writer.md` — the same substitution, but with default indexes `applications`, `decisions`, `standards`, plus the specific `app-N` / `cross-app` index implied by the triaged task. Always-loaded files: `applications/index.md`, the specific `applications/app-{N}-overview.md`, `workflows/spec-process.md`, `specs/templates/technical-spec-template.md`, `specs/templates/implementation-plan-template.md`.

Both files retain the existing **Confirmed / Assumption / Open-question Information Classification** discipline. The new retrieval results are surfaced under "Confirmed" only when the chunk is verbatim from a primary source; paraphrases of retrieved content remain "Assumption" until cross-checked.

## 7. Likely Files Affected

| App / scope | File or directory | Change type |
|---|---|---|
| KH | `kh_agent/` | New (entire package) |
| KH | `kh_agent_data/` | New (gitignored runtime artefacts) |
| KH | `tests/` | New (or extend if a `tests/` already exists) |
| KH | `pyproject.toml` | New |
| KH | `.gitignore` | Extend with `kh_agent_data/`, `*.faiss`, `__pycache__/`, `.env` |
| KH | `.env.example` | New |
| KH | `scripts/kh_agent_ingest.sh` | New convenience wrapper |
| KH | `.opencode/agents/task-triage.md` | Edit "Required Inputs" |
| KH | `.opencode/agents/spec-writer.md` | Edit "Required Inputs" |
| KH | `.opencode/commands/` | Possibly add a `/retrieve` command. Open Question (§13). |
| KH | `AGENTS.md` | Add a one-paragraph pointer to `kh_agent` under "Before Acting" |
| KH | `current-priorities.md` | Remove the "no observability" blocker once `kh-agent status` is operational |
| KH | `README.md` | Add a short section under "Structure" documenting `kh_agent/` |

No application repositories are touched.

## 8. Reused vs Adapted Code

| Source file in `Domain_Agent` | Destination in `kh_agent` | Treatment |
|---|---|---|
| `src/knowledge/ingestion.py` | `kh_agent/chunking.py` | Adapted: drop PDF/JSON, add heading_path metadata |
| `src/knowledge/embeddings.py` | `kh_agent/embeddings.py` | Verbatim port; rebind to KH settings names |
| `src/knowledge/vector_store.py` | `kh_agent/vector_store.py` | Verbatim port; replace `DomainType` with a free-form `str` index name |
| `src/knowledge/retriever.py` | `kh_agent/retriever.py` | Verbatim port |
| `src/llm/client.py` | `kh_agent/llm_client.py` | Adapted: hard-default to Azure provider; retain retry logic and `generate_structured` |
| `src/llm/token_tracker.py` | `kh_agent/token_tracker.py` | Verbatim port |
| `src/evaluation/logger.py` | `kh_agent/logger.py` | Verbatim port |
| `src/orchestrator/workflow.py` | `kh_agent/workflow.py` | **Iteration 2.** Adapt `SubTask` → KH task file frontmatter. |
| `src/evaluation/llm_judge.py` + `prompts/evaluation/llm_judge.txt` | `kh_agent/judge.py` | **Iteration 2.** Re-target rubric at spec/triage outputs (completeness, risk coverage, rollback presence, cross-app considerations, C/A/OQ-label discipline). |

The package keeps its dependency footprint to: `faiss-cpu`, `numpy`, `openai>=1.0`, `pydantic>=2`, `pydantic-settings`, `tenacity` (or reuse the manual retry from the thesis client), `pyyaml` (for `pricing.yaml`). No web framework, no async runtime beyond `asyncio`.

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Retrieval relevance is too low on the small corpus and surfaces noise instead of the right ADR/spec | Medium | Medium | Keep `tasks-recent` as a separate small index; gate aggregation by score; fall back to explicit reading list on miss (§6.7); ship a `tests/test_corpus.py` with 5–10 known query→expected-doc fixtures before any agent change. |
| Cost of repeated re-embedding on every `ingest` | Low | Low | Incremental ingest by mtime; only `--fresh` triggers full rebuild. Embedding model is `text-embedding-3-small` — cheap. |
| API key leakage via JSONL logs | Low | High | Logger never serialises request payloads, only token counts and metadata. Add an explicit `redactions.py` test that asserts no `api_key` / `Authorization` substrings appear in any log record. |
| FAISS files become stale relative to markdown | High (by default) | Low | Add a `kh-agent ingest --check` mode that compares index timestamps against file mtimes and exits non-zero if any index is stale. Wire into `workflows/session-start-checklist.md` as a recommended pre-flight. |
| Embedding the wrong content (e.g., secrets accidentally pasted into `handoffs/`) | Low | High | Pre-ingest scan for high-entropy strings and Bearer-token patterns; refuse to ingest a file that matches and surface the path. |
| Divergence from the thesis codebase as the upstream evolves | Medium | Low | Pin upstream snapshot in `kh_agent/__init__.py` as a `THESIS_COMMIT_SHA` constant; document the porting policy in `kh_agent/README.md`. |
| OpenCode runtime cannot call `kh-agent` directly as a tool | Medium | Medium | Ship the CLI first; agents are instructed to call it via shell. If OpenCode's MCP tool registration is available, add a thin MCP wrapper in iteration 2. |
| Re-embedding cost is non-zero on every CI run | Low | Low | Indexes live under `kh_agent_data/` (gitignored). CI does a fresh ingest on a fixture corpus, not on the real one. |

## 10. Validation

### 10.1 Unit tests
- `test_chunking.py`: heading-path attached; chunk count and size bounds for fixed-text fixtures; deterministic output.
- `test_vector_store.py`: round-trip ingest → persist → load → query; empty-store query returns `[]`; metadata round-trip.
- `test_retriever.py`: `UnifiedRetriever` merges and sorts by score; per-source `[Source N: file (relevance: X)]` formatting matches the thesis output verbatim.
- `test_corpus.py`: 5–10 hand-curated `(query, expected_top_3_filenames)` pairs against a fixture corpus that mirrors the KH structure (`fixtures/applications/app-1-overview.md` etc.). Asserts the expected file is in top-3.
- `test_llm_client.py`: mock `AsyncAzureOpenAI`; assert `TokenTracker.total_tokens` matches sum of mocked usages; retry on `RateLimitError`.
- `test_cli.py`: subprocess each subcommand against the fixture corpus; asserts exit codes, JSON shape on `retrieve --json`, and that a JSONL log line is produced per call.
- `test_no_secret_leakage.py`: synthesises a fake Bearer token in input, asserts it never appears in any JSONL record, and that pre-ingest scan refuses files containing it.

### 10.2 Smoke test (manual, against the real corpus)
1. `kh-agent ingest --fresh` on a fresh checkout. Assert all 9 indexes are produced and `kh-agent status` reports the embed-call count.
2. `kh-agent retrieve --query "anote-web-api backend split TASK-0014" --indexes app-3,cross-app,tasks-recent`. Top result must be `applications/app-3-overview.md` or a `specs/cross-app/TASK-0014*` file.
3. `kh-agent retrieve --query "Czech safety disclaimer dose modification" --indexes app-1,tasks-recent`. Top result must reference TASK-0034 or `applications/app-1-overview.md`.
4. `kh-agent retrieve --query "GDPR data residency Sweden Central transcription"`. Indexes default; top results must surface `system-landscape.md` and the relevant standards or decisions.
5. Run `@task-triage` against a synthetic raw task ("Add dark-mode toggle to the ANOTE-web cookie banner"). The triage file produced must cite chunks from `app-3` and `standards/` indexes (verifiable from the JSONL log's `indexes_queried`).
6. `kh-agent status --days 1` reports the calls from steps 1–5.

### 10.3 Acceptance criteria
- All unit tests pass under `pytest`.
- All five smoke-test queries return the expected top-result file.
- `kh-agent ingest --check` against an unchanged corpus exits 0; touching a single markdown file flips it to non-zero until re-ingested.
- The "no monitoring or observability" line is removed from `current-priorities.md`'s Blockers section, replaced by a concrete pointer to `kh-agent status` (control-layer-only — applications still have no observability; this is explicit in the wording).
- Both updated agent files (`task-triage.md`, `spec-writer.md`) lint cleanly under whatever YAML-frontmatter check OpenCode applies.

## 11. Rollout

- **Phase 1.1** Land the package and tests, no agent changes. `kh-agent ingest`, `retrieve`, `status` operational locally. No effect on existing workflows.
- **Phase 1.2** Ship the agent prompt edits under a clearly tagged commit. The prompt fallback ("if no result above threshold, use the explicit reading list") guarantees backward compatibility.
- **Phase 1.3** Run the spike on the next 3 real triage / spec sessions. Compare token usage and time-to-first-spec against the prior week's sessions (use git history of `tasks/triage/` and `specs/` as ground truth). Report results in a `handoffs/` entry.
- **Iteration 2** (separate spec): port `judge.py` and `workflow.py`. Iteration 2 is gated on Iteration 1 producing a stable corpus and unblocked observability for at least 2 weeks.

No feature flag is needed; the agents call the new tool by default after Phase 1.2, with a documented fallback to the old reading-list behaviour.

## 12. Rollback

The spike is purely additive. To roll back:

1. Revert the prompt edits in `.opencode/agents/task-triage.md` and `.opencode/agents/spec-writer.md`. Agents return to the static reading list.
2. Optionally `rm -rf kh_agent/ kh_agent_data/ scripts/kh_agent_ingest.sh tests/test_kh_agent_*.py pyproject.toml`. The package leaves no other footprint.
3. No data loss: the markdown corpus is untouched; FAISS files are derived artefacts.

Rollback is safe at any point because:
- No application repository is modified.
- The markdown corpus is canonical and read-only from `kh_agent`'s perspective (it never writes back to `applications/`, `decisions/`, etc.).
- No external state (cloud resource, queue, database) is created.

## 13. Open Questions

1. **OpenCode tool registration mechanics.** What is the cleanest way for `@task-triage` and `@spec-writer` to invoke `kh-agent retrieve`? Options: (a) generic shell-tool capability if the agent has `bash: allow` (current files have `bash: deny`); (b) a `.opencode/commands/retrieve.md` slash command the human invokes and pastes the result into chat; (c) an MCP server wrapping the CLI. The current default in §6.7 assumes (b)+(c) and works around the `bash: deny` permission. **Resolution required before Phase 1.2.**
2. **Azure API version.** What value should `KH_AZURE_OPENAI_API_VERSION` default to? The KH overviews do not pin this; it must be read from the App 1 / App 2 deployment configuration in their respective repos.
3. **Chat deployment.** `system-landscape.md` lists multiple deployments under `anote-openai` (`gpt-5-4-mini`, `gpt-5-mini`, `gpt-5-chat`, `gpt-4.1-mini`, plus embeddings + whisper). Which is the canonical "control-layer" deployment? Recommend `gpt-5-mini` for parity with App 2 backend, but this is an Open Question for Iteration 1.
4. **Pricing source.** How should `kh_agent/pricing.yaml` be kept current? Manually with a documented review cadence is acceptable for Iteration 1; revisit if monthly drift exceeds 10 %.
5. **`tasks-recent` definition.** Is "last 30 entries of `handoffs/` plus everything in `tasks/active/` and `tasks/triage/`" the right cut? A 7-day rolling window may be a better signal once the project has more history.
6. **Should `kh_agent` be a separate repo or stay in-tree?** In-tree is simpler for Iteration 1. If iteration 2 ports the workflow engine and grows the package, splitting may be worthwhile.
7. **Cost-budget alerting.** Should `kh-agent status` exit non-zero above a configurable per-day cost ceiling, so it can fail a session-start hook? Not required for Iteration 1.

## 14. Iteration 2 Sketch (informative, not part of this spec's commitments)

### 14.1 LLM-as-Judge gate
- Port `prompts/evaluation/llm_judge.txt` from the thesis and re-target the rubric at spec/triage outputs. Suggested sub-dimensions: completeness, risk coverage, rollback plan, cross-app considerations, presence of explicit `Confirmed` / `Assumption` / `Open question` labels.
- `kh-agent judge --target specs/app-3/TASK-XXXX-spec.md` returns a structured judgement plus per-dimension score. No automatic blocking — the human sees the score and decides.
- Concretely closes the documentation-drift class of bugs (`current-priorities.md` "test counts conflict") by running the judge on `applications/app-{N}-overview.md` after edits.

### 14.2 Workflow engine
- Port `src/orchestrator/workflow.py`. The KH analogue of `SubTask` is a YAML block in a task file:
  ```yaml
  steps:
    - id: backend-deploy
      app: app-3
      depends_on: []
    - id: web-verify
      app: app-3
      depends_on: [backend-deploy]
    - id: mobile-smoke
      app: app-2
      depends_on: [backend-deploy]
  ```
- `kh-agent workflow run TASK-XXXX` executes ready steps in parallel via `asyncio.gather`, with each step dispatched to an `executor` shim — initially a no-op that just prints the checklist; later, optionally, MCP tool calls into the application repositories.
- This lifts `workflows/cross-app-change-process.md` from manual checklist into typed, dependency-aware automation, matching the thesis [WorkflowEngine](../../../Domain_Agent/src/orchestrator/workflow.py) line for line.

## 15. References

- This spec corresponds to §4 ("What the Field System Lacks") of [`Domain_Agent/External_Validation_Healthcare.md`](../../../Domain_Agent/External_Validation_Healthcare.md).
- Upstream code: [`Domain_Agent/src/knowledge/`](../../../Domain_Agent/src/knowledge/), [`Domain_Agent/src/llm/`](../../../Domain_Agent/src/llm/), [`Domain_Agent/src/orchestrator/workflow.py`](../../../Domain_Agent/src/orchestrator/workflow.py), [`Domain_Agent/src/evaluation/`](../../../Domain_Agent/src/evaluation/).
- KH standards consulted: `standards/security-privacy-standards.md`, `standards/engineering-standards.md`, `standards/testing-standards.md`.
- KH workflows consulted: `workflows/spec-process.md`, `workflows/cross-app-change-process.md`, `workflows/session-start-checklist.md`.
- KH agent files affected: `.opencode/agents/task-triage.md`, `.opencode/agents/spec-writer.md`.
