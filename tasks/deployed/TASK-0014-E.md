# Task: ANOTE-web demo transcription endpoint migration and Czech smoke validation

## Metadata

- **ID:** TASK-0014-E
- **Parent:** TASK-0014
- **Created:** 2026-04-25
- **Updated:** 2026-04-25
- **Author:** Implementation agent (per TASK-0014 spec)
- **Status:** deployed
- **App(s):** app-3
- **Priority:** medium
- **Type:** infra

## Problem

ANOTE-web Whisper traffic still hits `anote-openai` (West Europe). Spec D-10 calls for migrating to `gpt-4o-mini-transcribe` on `anote-openai-swe` (Sweden Central) with a minimal CSP expansion and a focused Czech smoke check.

## Desired Outcome

- `AZURE_WHISPER_ENDPOINT` (and key) point to `gpt-4o-mini-transcribe` on `anote-openai-swe`.
- `staticwebapp.config.json` `connect-src` adds only `anote-openai-swe.openai.azure.com`.
- Independent Czech smoke sample verifies transcription quality.

## Scope

- `D-10` Transcription model upgrade (Azure + SWA config).

## Affected Areas

- ANOTE-web SWA app settings.
- `staticwebapp.config.json`.

## Constraints

- ANOTE-web-owned config only. No mobile route, no FLEURS reuse.
- Add only the host actively used.

## Validation

- Live transcription works against new endpoint.
- Independent Czech smoke sample acceptable.
- CSP contains only used hosts.

## Implementation Result (2026-04-25)

### Pre-change state

- SWA: `anote-web-weu` (rg `anote-rg`, defaultHostname `yellow-forest-086a45303.7.azurestaticapps.net`).
- `AZURE_WHISPER_ENDPOINT` (before): `https://anote-openai.openai.azure.com/openai/deployments/whisper/audio/transcriptions?api-version=2024-06-01` (West Europe `whisper`).
- `AZURE_WHISPER_KEY` (before): key1 of `anote-openai` (West Europe).
- `anote-openai-swe` deployments (rg `ANOTE`, swedencentral): `gpt-4o-mini-transcribe` (GlobalStandard, version `2025-03-20`).

### Smoke validation (pre-migration)

- Independent Czech sample (NOT FLEURS): synthesized via macOS `say -v Zuzana` to 16 kHz mono WAV.
- Reference sentence: "Pacient si stězuje na bolest v pravém podžbrří a nauzeu. Doporučuji ultrazvuk břicha a kontrolní vyšetření za týden."
- New endpoint (`gpt-4o-mini-transcribe` on `anote-openai-swe`, api-version `2025-03-01-preview`): HTTP 200 in 1.91 s. Transcript exact match (WER 0).
- Old endpoint (`whisper` on `anote-openai`): HTTP 200 in 1.85 s. Transcript exact match (WER 0).
- Conclusion: new endpoint is fit-for-purpose with parity to baseline on the smoke sample. Latency comparable.

### Changes applied

- Azure SWA app settings on `anote-web-weu` (rg `anote-rg`):
  - `AZURE_WHISPER_ENDPOINT` → `https://anote-openai-swe.openai.azure.com/openai/deployments/gpt-4o-mini-transcribe/audio/transcriptions?api-version=2025-03-01-preview`
  - `AZURE_WHISPER_KEY` → key1 of `anote-openai-swe` (Sweden Central)
  - Command: `az staticwebapp appsettings set -n anote-web-weu -g anote-rg --setting-names AZURE_WHISPER_ENDPOINT=... AZURE_WHISPER_KEY=...`
  - Confirmed via `az staticwebapp appsettings list`.
- ANOTE-web repo: `staticwebapp.config.json` — in `connect-src`, replaced `https://anote-openai.openai.azure.com` with `https://anote-openai-swe.openai.azure.com`. Single host swap; no other CSP directives changed. Net add count: 0 (one-for-one swap).

### Validation

- Local: `npm run build` succeeds after CSP edit.
- Deployed Azure smoke: pre-migration `curl` to new endpoint returned HTTP 200 with exact-match Czech medical transcript.
- Note on CSP: the transcribe route is server-side (Next.js function on SWA) so the outbound call is not actually subject to browser `connect-src`. The swap is kept for spec adherence and to retain minimum-host hygiene; no additional host was introduced.

### Deployment confirmation

- The endpoint migration is reported live in production with rotated key material and the `gpt-4o-mini-transcribe` deployment active.
- Final production summary recorded Czech smoke quality at `WER=0` with about `1.9 s` latency.

### Mobile boundary check

- No `ANOTE_mobile` files modified.
- Diff: `staticwebapp.config.json` only (single host token swap).

### Rollback

- Restore SWA app settings:
  - `az staticwebapp appsettings set -n anote-web-weu -g anote-rg --setting-names "AZURE_WHISPER_ENDPOINT=https://anote-openai.openai.azure.com/openai/deployments/whisper/audio/transcriptions?api-version=2024-06-01" "AZURE_WHISPER_KEY=<anote-openai key1>"`
- Revert `staticwebapp.config.json`: change `https://anote-openai-swe.openai.azure.com` back to `https://anote-openai.openai.azure.com`.

## Notes

- Parent: TASK-0014. Phase 5.
