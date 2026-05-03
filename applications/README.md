# Applications

## Purpose

This folder contains overview documents for each application in the project. Each application has its own overview file that summarizes its purpose, tech stack, boundaries, and current state.

## Structure

| File | Application |
|------|-------------|
| `app-1-overview.md` | Application 1 (TBD) |
| `app-2-overview.md` | Application 2 (TBD) |
| `app-3-overview.md` | Application 3 (TBD) |

## Conventions

- Each application gets **one overview file** in this folder.
- Overviews should be kept current as applications evolve.
- Detailed application-specific documentation (API specs, local development guides, etc.) belongs in the application's own repository, not here.
- This folder is for **cross-project context**: what each app does, how it fits into the system, and what other applications need to know about it.
- When an application's name, purpose, or ownership is confirmed, rename the file from `app-N-overview.md` to a descriptive name (e.g., `patient-portal-overview.md`).

## Future Expansion

As the project matures, each application may also have:
- Dedicated agent instructions (how an AI agent should work within that app's repo)
- Integration guides describing contracts with other applications
- Runbooks for operational tasks

These should be added as separate files when needed.
