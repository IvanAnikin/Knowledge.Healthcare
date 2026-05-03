# Triage Process

## Purpose

Convert raw tasks into assessed, prioritized, actionable items.

## Steps

1. Read the task file in `tasks/inbox/`.
2. Fill out the triage template (`tasks/templates/triage-template.md`).
3. Assign priority using the matrix below.
4. Set recommended status: `active`, `backlog`, `needs-spec`, or `needs-investigation`.
5. Update the `Status` field in the task file to `triaged`.
6. Move the task file to `tasks/triage/`.
7. Update `dashboards/task-board.md`.

## Priority Matrix

| Impact \ Urgency | Immediate | Soon | Scheduled | Someday |
|-------------------|-----------|------|-----------|---------|
| **High** | Critical | High | High | Medium |
| **Medium** | High | Medium | Medium | Low |
| **Low** | Medium | Low | Low | Low |

## Confidence Adjustment

- If confidence is **low**, the recommended status should be `needs-investigation` before committing to active work.
- If confidence is **medium**, note open questions in the triage and proceed cautiously.

## Cross-App Rules

- If a task affects more than one app, tag it as `cross-app`.
- Review `applications/index.md` to identify all impacted repos.
- Reference `workflows/cross-app-change-process.md` for coordination steps.
- Cross-app tasks default to **at least medium priority** unless clearly trivial.

## Output

A completed triage file in `tasks/triage/` and an updated task board.

## Lifecycle Note

After triage, a task advances along the canonical lifecycle:

```
triaged → active → done → tested → deployed
        ↘ backlog (deferred)
```

Tasks may also move backward. For example, a `done` task may return to `active` if testing reveals issues. See `workflows/task-lifecycle.md` for the full set of valid transitions.
