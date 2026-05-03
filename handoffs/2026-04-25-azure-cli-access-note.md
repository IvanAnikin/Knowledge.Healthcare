# Session Handoff: Azure CLI Access Note

## Session Date

2026-04-25

## Goal

Capture the Azure CLI access note in the shared knowledge base and decide where this guidance should live long term.

## What Was Learned

- The project already references Azure CLI commands across multiple app overviews and task files, but there was no single operator-facing note explaining current Azure CLI availability.
- A recent session showed `az` was not available from the default shell.
- The user clarified that Azure CLI is available from the `ANOTE_mobile` pip virtual environment.
- This is a cross-app operator-environment concern, not an app-specific implementation detail.
- `ANOTE-web` already has a repo-local `AGENTS.md`; `ANOTE_mobile` and `medical_advisor` currently do not have repo-local `AGENTS.md` or Copilot instruction files.

## Files Reviewed

- `Knowledge.Healthcare/AGENTS.md`
- `Knowledge.Healthcare/README.md`
- `Knowledge.Healthcare/current-priorities.md`
- `Knowledge.Healthcare/applications/app-2-overview.md`
- `Knowledge.Healthcare/applications/app-3-overview.md`
- `Knowledge.Healthcare/applications/README.md`
- `Knowledge.Healthcare/standards/documentation-standards.md`
- `ANOTE-web/AGENTS.md`

## Files Changed

- `workflows/azure-cli-access.md` — new shared runbook for Azure CLI availability and verification
- `AGENTS.md` — added a short pointer for Azure-dependent work
- `current-priorities.md` — recorded the documentation update in recent completions
- `handoffs/2026-04-25-azure-cli-access-note.md` — this handoff note

## Decisions Made

- The full Azure CLI note should live in the shared knowledge base as a cross-app workflow/runbook.
- Repo-local instruction files should contain only a short pointer back to the shared runbook.
- New Copilot-instruction or AGENTS files should not be created solely to duplicate this note unless a repo is already using those files actively.

## Assumptions

- The user-provided statement that Azure CLI is available from the `ANOTE_mobile` pip virtual environment is accurate. (needs verification: yes)

## Unresolved Questions

- What is the exact venv path that exposes `az` on this machine?
- Should `ANOTE_mobile` and `medical_advisor` gain repo-local `AGENTS.md` or Copilot instruction files for broader reasons beyond this Azure CLI note?

## Recommended Next Step

- When the next Azure-dependent task comes up, verify the exact venv path that exposes `az`, then update `workflows/azure-cli-access.md` with the concrete activation/access command if it is stable enough to document.
