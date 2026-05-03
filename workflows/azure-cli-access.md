# Azure CLI Access

## Purpose

Record the current operator guidance for Azure CLI usage across the project so agents do not assume `az` is globally available on every session or machine.

> Last updated: 2026-04-25

## Current Known State

### Confirmed Facts

- In at least one recent session, running `az --version` from the default shell failed with `zsh: command not found: az`.
- The user later clarified that Azure CLI is available from the `ANOTE_mobile` Python/pip virtual environment rather than from the global shell `PATH`.
- Multiple project tasks depend on Azure CLI access, including:
  - App 1 manual ZIP deployment via `az webapp deploy`
  - App 2 backend deployment via `az containerapp up`
  - App 3 environment/config verification and backend updates via commands such as `az staticwebapp ...` and `az containerapp update`

### Assumptions

- The Azure CLI binary can be reached after activating the relevant `ANOTE_mobile` virtual environment or otherwise entering the environment where that venv exposes `az`. (needs verification: yes)
- Azure authentication state is user-managed and may vary by session. (needs verification: yes)

### Open Questions

- What is the exact virtual environment path that currently exposes `az` on this machine?
- Is Azure CLI only installed through one project-local venv, or are there multiple valid access paths?
- Which subscription and tenant should be treated as the default for routine project operations?

## Agent Guidance

- Do not assume `az` is globally installed or on `PATH`.
- Before Azure-dependent work, verify access explicitly.
- If `az` is missing in the default shell, check the `ANOTE_mobile` Python/pip virtual environment before declaring Azure CLI unavailable.
- Treat Azure login/subscription state as session-specific. Verify the active account and subscription before making changes.
- Do not install Azure CLI, change default subscriptions, or run login flows unless the user asked for that action.

## Recommended Verification Steps

Run these checks before Azure-dependent work:

```bash
which az
az --version
az account show --query "{name:name, id:id, tenantId:tenantId}" -o json
```

If `az` is not found from the default shell:

1. Activate or enter the `ANOTE_mobile` Python/pip virtual environment that the user identified.
2. Re-run `which az` and `az --version`.
3. Only if that still fails, record Azure CLI as unavailable for the session and continue with documentation/spec-safe work.

## App-Specific Notes

### App 1 (`medical_advisor`)

- Primary Azure CLI usage is manual App Service deployment.
- Common command family: `az webapp ...`

### App 2 (`ANOTE_mobile`)

- Primary Azure CLI usage is backend deployment and environment inspection for Azure Container Apps.
- Common command family: `az containerapp ...`
- This repo is currently the known place associated with Azure CLI availability via a Python/pip virtual environment.

### App 3 (`ANOTE-web`)

- Primary Azure CLI usage is Static Web Apps inspection and backend/config updates where manual verification is needed.
- Common command families: `az staticwebapp ...`, `az containerapp ...`
- The web repo should not assume Azure CLI is locally available without first following this runbook.

## Recommended Documentation Placement

- Keep the full operational note here in the shared knowledge base because it is a cross-app operator-environment concern.
- In repo-local `AGENTS.md` or Copilot instruction files, add only a short pointer back to this runbook rather than duplicating the full explanation.
- Do not create separate copies of the same Azure CLI note in every repo unless those repos already maintain active local instruction files.
