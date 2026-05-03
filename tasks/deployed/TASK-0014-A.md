# Task: ANOTE-web demo config hardening: model selection and min replicas

## Metadata

- **ID:** TASK-0014-A
- **Parent:** TASK-0014
- **Created:** 2026-04-25
- **Updated:** 2026-04-25
- **Author:** Implementation agent (per TASK-0014 spec)
- **Status:** deployed
- **App(s):** app-3
- **Priority:** high
- **Type:** infra

## Problem

`anote-web-api` Container App runs with `minReplicas = 0` (cold-start 500 path through SWA) and uses `AZURE_OPENAI_DEPLOYMENT = gpt-4-1-mini`. TASK-0014 spec Phase 1 (`A-1` / `A-2`) requires evaluating `gpt-4o-mini` vs `gpt-4-1-mini` and applying the faster verified option, plus pinning `minReplicas = 1` to eliminate scale-to-zero wake-up failures.

## Desired Outcome

- Faster verified chat-model deployment selected for the ANOTE-web Czech report workload.
- `anote-web-api` runs with `minReplicas = 1`.
- Before/after values and rollback values are recorded.

## Scope

- `A-1` Chat model deployment evaluation (Azure config, `anote-web-api`).
- `A-2` `minReplicas = 1` on `anote-web-api`.

## Constraints

- ANOTE-web-owned Azure surfaces only: `anote-web-api` Container App env / scale.
- No changes to `anote-api` (mobile) or any mobile OpenAI deployment.
- Env-only / scale-only `az containerapp update`.

## Validation

- `/report` p50 warm `<= 6 s` on representative ~4k-char Czech transcript.
- Cold-start path no longer surfaces SWA-visible 500.

## Implementation Result (2026-04-25)

### A-1 evaluation outcome — keep `gpt-4-1-mini`

- Listed deployments on `anote-openai` (rg `ANOTE`, westeurope) via `az cognitiveservices account deployment list`.
- Available chat deployments: `gpt-4-1-mini` (Standard, cap 30), `gpt-5-mini` (GlobalStandard, 101), `gpt-5-chat` (GlobalStandard, 100), `gpt-5-4-mini` (GlobalStandard, 500), `gpt-5-nano` (GlobalStandard, 30).
- `gpt-4o-mini` is **not deployed** on `anote-openai`.
- TASK-0013 already established `gpt-4-1-mini` as the verified faster option (warm `/report` 4.7–6.3 s) versus `gpt-5-mini` (~19 s).
- Deploying `gpt-4o-mini` and running a paired Czech ~4k-char benchmark is meaningful new work (capacity allocation + benchmark methodology) outside the env-only scope of A-1.
- **Decision:** keep `AZURE_OPENAI_DEPLOYMENT=gpt-4-1-mini` (and `AZURE_OPENAI_FALLBACK_DEPLOYMENT=gpt-5-nano`). No env change applied.
- Optional follow-up (separate task, not blocking): deploy `gpt-4o-mini` on `anote-openai` and benchmark vs `gpt-4-1-mini` on the same Czech transcript.

### A-2 outcome — `minReplicas` set to 1

- Before: `minReplicas=0`, `maxReplicas=3`.
- After: `minReplicas=1`, `maxReplicas=3`. `provisioningState=Succeeded`.
- Command run: `az containerapp update -n anote-web-api -g anote-rg --min-replicas 1 --max-replicas 3`.
- Replica reached `Running` within ~15 s.
- Smoke: 3 warm `GET /health` calls returned `HTTP 200` in 0.29–0.50 s end-to-end.
- Bonus finding: `anote-web-api` already exposes `/health`. Resolves Phase 2 open question; no backend addition required for `E-11`.

### Rollback values

- `az containerapp update -n anote-web-api -g anote-rg --min-replicas 0 --max-replicas 3`
- Env vars unchanged this session, so no env rollback is required for A-1.

### Validation type

- Deployed (Azure live).
- Direct backend `/health` (warm) only. Cold-path SWA-fronted `/report` p50 not re-measured this session; expected to no longer cold-start since `minReplicas=1`.

### Deployment confirmation

- Parent deployment completed on 2026-04-25.
- `anote-web-api` remained on `gpt-4-1-mini` with `gpt-5-nano` fallback and shipped live with `minReplicas=1`.
- Subsequent parent production validation reported `/health` `HTTP 200` in about `0.35 s` and successful streamed/non-streamed `/report` responses from the live system.

### Mobile boundary check

- No files under `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile` were modified.
- ANOTE-web repo: zero diff (config-only change).

## Notes

- Parent: TASK-0014.
- Spec: `specs/app-3/TASK-0014-spec.md` Phase 1.
- Plan: `specs/app-3/TASK-0014-implementation-plan.md` Step 1.
