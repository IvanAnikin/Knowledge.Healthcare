# Session Handoff: Repo AGENTS Added

## Session Date

2026-04-25

## Goal

Add minimal repo-local `AGENTS.md` files to repositories that did not yet have them, so they point back to the shared knowledge-base instructions and Azure CLI runbook.

## What Was Learned

- `ANOTE-web` already had a local `AGENTS.md`.
- `ANOTE_mobile` and `medical_advisor` did not have local `AGENTS.md` or Copilot instruction files.
- A minimal pointer file is enough here; duplicating the full shared instruction set into each repo is unnecessary.

## Files Reviewed

- `Knowledge.Healthcare/AGENTS.md`
- `Knowledge.Healthcare/workflows/azure-cli-access.md`
- `ANOTE-web/AGENTS.md`

## Files Changed

- `ANOTE_mobile/AGENTS.md` — new minimal repo-local pointer to shared instructions and Azure CLI runbook
- `medical_advisor/AGENTS.md` — new minimal repo-local pointer to shared instructions and Azure CLI runbook
- `Knowledge.Healthcare/current-priorities.md` — recorded the repo-local agent-file addition in recent completions
- `Knowledge.Healthcare/handoffs/2026-04-25-repo-agents-added.md` — this handoff note

## Decisions Made

- Added only minimal pointer-style `AGENTS.md` files.
- Did not create Copilot instruction files or duplicate the shared operational guidance.

## Assumptions

- Repo-local agent discovery will benefit from a short pointer file even without broader repo-specific rules yet. (needs verification: no)

## Unresolved Questions

- Whether either repo will later need richer local instructions beyond the shared knowledge-base guidance.

## Recommended Next Step

- Leave the repo-local `AGENTS.md` files minimal unless repo-specific coding or deployment conventions emerge that cannot be captured cleanly in the shared knowledge base.
