# Task Lifecycle

## Canonical States

| State | Meaning | Folder |
|-------|---------|--------|
| `inbox` | Raw, unassessed task. Not yet triaged. | `tasks/inbox/` |
| `triaged` | Assessed and prioritized. Not yet started. | `tasks/triage/` |
| `active` | Work in progress. | `tasks/active/` |
| `backlog` | Valid but intentionally deferred. | `tasks/backlog/` |
| `done` | Implementation complete. Not yet validated or released. | `tasks/done/` |
| `tested` | Validated sufficiently (automated and/or manual, as appropriate). | `tasks/tested/` |
| `deployed` | Live in the intended environment. | `tasks/deployed/` |

## Forward Flow

```
inbox → triaged → active → done → tested → deployed
                     ↓
                  backlog (deferred from triaged or active)
```

- **inbox → triaged**: After the `@task-triage` agent completes assessment. Task file moves to `tasks/triage/`.
- **triaged → active**: Work begins. Task file moves to `tasks/active/`.
- **triaged → backlog**: Task is valid but not yet a priority. Task file moves to `tasks/backlog/`.
- **active → backlog**: Work started but intentionally paused/deferred.
- **active → done**: Implementation is complete. Work has not been validated yet. Task file moves to `tasks/done/`.
- **done → tested**: Testing (automated or manual) confirms the implementation is correct and sufficient. Task file moves to `tasks/tested/`.
- **tested → deployed**: The change is live in the intended environment. Task file moves to `tasks/deployed/`.

## Backward Transitions

Tasks may move backward to an earlier state whenever rework, re-triage, re-testing, or re-deployment is needed. This is intentional and expected.

| From | To | Reason |
|------|----|--------|
| `active` | `triaged` | Scope changed significantly; re-triage needed before continuing. |
| `active` | `inbox` | Task was misunderstood at triage; needs full re-assessment. |
| `done` | `active` | Testing revealed implementation is incomplete or incorrect. |
| `tested` | `active` | A regression or new finding requires further implementation. |
| `tested` | `done` | Test results indicate the implementation needs re-validation from scratch. |
| `deployed` | `tested` | Rollback needed; re-validation required before re-deploying. |
| `deployed` | `active` | Rollback and rework required. |
| `backlog` | `triaged` | Task is re-prioritized for upcoming work. |
| `backlog` | `active` | Task is re-activated directly after re-prioritization. |

When moving a task backward, update the `Status` field in the task file and move the file to the appropriate folder.

## State Semantics

### `done`
Implementation is complete. The task has not been validated by testing. A task in `done` state may be pending test execution, or waiting for a testing window. It should not be considered finished.

### `tested`
The implementation has been validated to a sufficient degree. This may include:
- Automated tests (unit, integration, E2E)
- Manual exploratory or smoke testing
- Review by another agent or team member

The definition of "sufficient" is context-dependent and documented in the task or spec.

### `deployed`
The change is live in the intended environment (staging, production, or otherwise defined per task). This is the terminal state for most tasks.

### `backlog`
The task is acknowledged as valid work but has been intentionally deferred. It may be re-activated at any time by updating the status and moving the file to `tasks/active/` or `tasks/triage/`.

## Rules

- Every task gets an ID in the format `TASK-XXXX`.
- Cross-app tasks must be triaged with input on all affected apps.
- Tasks should not stay in Inbox for more than one session without triage.
- The task board and roadmap must stay in sync with task file locations.
- When a task moves folders, update the `Status` field in the task file to match.
- Do not infer `tested` or `deployed` status for existing `done` tasks without confirmation. Existing `done` tasks remain `done` unless explicitly validated and moved forward.

## Stages (Detailed)

### 1. Inbox

A raw task is captured in `tasks/inbox/` using the task template. No assessment yet.

### 2. Triaged

The task is assessed using the triage template and moved to `tasks/triage/`. Outputs:
- Priority, urgency, impact, and confidence ratings.
- Recommended status (active, backlog, needs-spec).
- Entry added to `dashboards/task-board.md`.

### 3. Spec (if needed)

If the task is complex, high-risk, or cross-app, a spec is written in `specs/`. See `workflows/spec-process.md` for criteria.

### 4. Active

Work begins. The task file moves to `tasks/active/`.

### 5. Done

Implementation complete. Task file moves to `tasks/done/`. Work has not yet been validated.

### 6. Tested

Validation complete. Task file moves to `tasks/tested/`.

### 7. Deployed

Change is live. Task file moves to `tasks/deployed/`. Board and roadmap updated.

### 8. Backlog

Deferred tasks sit in `tasks/backlog/` until re-prioritized. May be entered from `triaged` or `active`.
