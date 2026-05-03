# Technical Spec: Auto-mapping of Broz CSV to Czech-localized field names

## Metadata

- **Task ID:** TASK-0033
- **Author:** @spec-writer
- **Date:** 2026-04-27
- **App(s):** app-4 (Health-Analysis)
- **Status:** draft
- **Coordinated with:** [TASK-0032](./TASK-0032-spec.md) (Czech vocabulary registry — depends on dictionary keys defined there)

## Summary

When a clinician uploads a "Broz" CSV — the Czech-locale FreeStyle LibreLink export forwarded by Dr. Broz, fixtured at `samples/broz/Test1.csv` and `samples/broz/TEst.csv` — the column-mapping step (`web/app/page.tsx`, mapping endpoint `POST /api/v1/uploads/{id}/mapping`) currently does not auto-suggest values because the existing `suggestColumn` heuristic (`web/app/page.tsx:59-66`) only checks lowercased English variants. This spec adds **server-side source-profile detection** in the upload response and **frontend Czech-aware suggestion** so the mapping step is pre-filled for Broz inputs, while preserving the user's ability to review and override before confirming.

## Objective

- Uploads detected as Broz CSV produce a fully pre-filled mapping for the four CGM fields, using the canonical Czech display labels owned by the TASK-0032 dictionary.
- The user still sees the mapping panel and can override before submitting (matches current `TASK-0022` UX).
- Non-Broz inputs are unaffected; existing English-LibreView and synthetic CGM samples continue to work.

## Scope

- Add a `source_profile` field to `UploadResponse` (`api/app/api/v1/uploads.py:45-56`), populated by detection logic in `loaders.py` or a small new `api/app/ingest/profiles.py`.
- Detection: pattern-match against the four canonical Czech CGM headers in the post-unwrap header row. Conservative — see "Detection rules".
- Frontend: when `upload.source_profile === "broz_libreview_cs"` and `datasetType === "cgm"`, seed the mapping using the Czech header strings instead of (or in addition to) the existing English-suggestion heuristic.
- The Czech display labels visible in the mapping UI are pulled from the `cs` dictionary (`web/lib/i18n/dictionaries/cs.ts`) introduced in TASK-0032. Canonical field IDs (`timestamp`, `record_type`, `glucose_mmol_l`, `scan_glucose_mmol_l`) are unchanged.
- An "auto-detected" affordance in the mapping UI: a small badge `Auto-detected: Broz CSV (Czech LibreView)` next to the dataset-type selector, plus per-row badges on the four pre-filled mapping rows.

## Non-Goals

- No general "upload-profile registry" subsystem. We add **one** named profile: `broz_libreview_cs`. The detection function is structured so a second profile is a small, additive change, but no JSON-driven plugin architecture is built in this slice.
- No backend translation of validation messages or analytics output. Czech labels are display-layer only.
- No automatic submit. The user still clicks "Submit mapping" to advance.
- No support for English-LibreView column names being auto-mapped to Czech labels — those continue to use the English logical-field labels via the existing English `suggestColumn` path.
- No unit conversion. `mmol/L` is already canonical (`TASK-0023`); the four Broz columns are all mmol/L (or non-numeric for `record_type`).

## Current Behavior

Confirmed from repo:

- Mapping suggestion happens **client-side** in `web/app/page.tsx:59-66` (`suggestColumn`) and at upload time `:188-192`. Suggestions live in `CGM_LOGICAL_FIELDS` at `:27-44` and only contain English-variant lowercased names (e.g. `historic glucose mmol/l`, `scan glucose mmol/l`). For a Broz CSV those return `""`, so the mapping rows show `(none)`.
- Backend `UploadResponse` (`api/app/api/v1/uploads.py:45-56`) returns `detected_columns` and `detected_dialect` but no notion of a source profile.
- `loaders.py:83-129` already content-detects the Czech LibreView per-line outer-quoting variant via `_maybe_unwrap_double_quoted_lines` — i.e. a content-fingerprint of Broz inputs already exists implicitly. That is the natural attachment point for explicit profile detection.
- The Broz CSV header row (verified by reading `samples/broz/Test1.csv:1` and `samples/broz/TEst.csv:1`, post-unwrap) is exactly:

  ```
  Zařízení, Sériové číslo, Časová značka zařízení, Typ záznamu,
  Historie údajů o glukóze mmol/L, Skenovat glukózu mmol/L,
  "Inzulín s rychlým účinkem, bez číselného vyjádření",
  Inzulín s rychlým účinkem (jednotky),
  "Potravina, bez číselného vyjádření",
  Karbohydráty (gramy), Karbohydráty (porce),
  "Inzulín s dlouhým účinkem, bez číselného vyjádření",
  Inzulín s dlouhým účinkem (jednotky),
  Poznámky, Proužek na testování glukózy mmol/L, Keton mmol/L,
  Inzulín v jídle (jednotky), Nápravný inzulín (jednotky),
  "Inzulín, uživatelská změna (jednotky)"
  ```

  This is the LibreView Czech-locale export; the first data column shows `FreeStyle LibreLink` as the device. So Broz CSVs **are** Czech LibreView exports.

- The user-supplied target label `Skenovat skenovat glukózu mmol/L` (with the duplicated `Skenovat`) in TASK-0033's original description **does not match** the actual CSV header. The actual header is `Skenovat glukózu mmol/L`. **This spec uses the verbatim CSV header as the canonical Czech display label**, consistent with TASK-0032, and treats the duplicated word as a typo in the original task description.

## Proposed Behavior

### 1. Backend: explicit source-profile detection

Introduce `api/app/ingest/profiles.py`:

```python
from dataclasses import dataclass
from typing import Literal

SourceProfileId = Literal["broz_libreview_cs", "libreview_en", "generic"]

# Canonical Czech CGM headers from samples/broz/Test1.csv:1 (post-unwrap).
BROZ_CS_REQUIRED_HEADERS: tuple[str, ...] = (
    "Časová značka zařízení",
    "Typ záznamu",
    "Historie údajů o glukóze mmol/L",
)
BROZ_CS_OPTIONAL_HEADERS: tuple[str, ...] = (
    "Skenovat glukózu mmol/L",
    "Zařízení",
    "Sériové číslo",
)

@dataclass(slots=True, frozen=True)
class DetectedSourceProfile:
    profile_id: SourceProfileId
    confidence: Literal["high", "medium"]
    notes: tuple[str, ...]

def detect_source_profile(detected_columns: list[str]) -> DetectedSourceProfile:
    cols = set(detected_columns)
    required_hits = sum(h in cols for h in BROZ_CS_REQUIRED_HEADERS)
    optional_hits = sum(h in cols for h in BROZ_CS_OPTIONAL_HEADERS)
    if required_hits == len(BROZ_CS_REQUIRED_HEADERS):
        confidence = "high" if optional_hits >= 2 else "medium"
        return DetectedSourceProfile(
            profile_id="broz_libreview_cs",
            confidence=confidence,
            notes=("Detected Czech LibreView export based on canonical Czech CGM column headers.",),
        )
    # Future: english LibreView, generic time-series, etc.
    return DetectedSourceProfile(profile_id="generic", confidence="medium", notes=())
```

Wire into `app/api/v1/uploads.py`:

- `UploadResponse` gains:
  - `source_profile: SourceProfileId`
  - `source_profile_confidence: Literal["high", "medium"]`
  - `source_profile_notes: list[str]`
- `_record_to_upload_response` calls `detect_source_profile(record.detected_columns)`.

### Detection rules and false-positive guards

- Detection is **exact-match** on Czech header strings. No case-insensitive or whitespace-tolerant matching for the required headers — these strings include diacritics that uniquely identify the Czech locale, and partial matches risk false positives.
- All three required headers must be present for `broz_libreview_cs` confidence ≥ `medium`.
- `confidence === "high"` requires at least two of the optional headers (`Skenovat glukózu mmol/L`, `Zařízení`, `Sériové číslo`) — protects against a synthetic Czech-header CSV that only happens to share names.
- A future-proofing hook (not implemented now): if `confidence === "medium"`, the frontend may still pre-fill but should label the suggestion as *"Possibly Broz CSV — please verify"*. For this slice both `medium` and `high` produce pre-fill; the badge text differs.

### 2. Profile → field mapping

A small mapping table (Python and TypeScript mirrors) defines, for each `(profile_id, dataset_type, logical_field_key)` triple, which CSV header to suggest:

```python
# api/app/ingest/profiles.py
PROFILE_FIELD_HEADERS: dict[SourceProfileId, dict[str, dict[str, str]]] = {
    "broz_libreview_cs": {
        "cgm": {
            "timestamp":           "Časová značka zařízení",
            "record_type":         "Typ záznamu",
            "glucose_mmol_l":      "Historie údajů o glukóze mmol/L",
            "scan_glucose_mmol_l": "Skenovat glukózu mmol/L",
        },
    },
}
```

The same table is exposed to the frontend either:

- (a) **Recommended:** by extending the upload mapping endpoint with a small `suggested_mapping` field on `UploadResponse` that contains `{ "timestamp": "Časová značka zařízení", … }` precomputed by the backend for the chosen profile, OR
- (b) by mirroring the table in `web/lib/i18n/dictionaries/cs.ts` and applying it client-side.

**Recommendation: option (a).** It keeps detection logic, profile definitions, and mapping in one place (backend), and the frontend just renders. The Czech *display labels* on the mapping UI still come from the `cs` dictionary owned by TASK-0032; the `suggested_mapping` carries the **physical CSV header to map to**, not the i18n label.

`UploadResponse` final shape addition:

```python
suggested_mapping: dict[str, dict[str, str]] = Field(default_factory=dict)
# e.g. {"cgm": {"timestamp": "Časová značka zařízení", ...}}
```

### 3. Frontend: pre-fill behavior

In `web/app/page.tsx`:

- After `uploadFile` returns, if `upload.suggested_mapping?.[datasetType]` is non-empty, seed `mapping` from it directly:

  ```ts
  const seeded = upload.suggested_mapping?.[datasetType];
  if (seeded) {
    const next: Record<string, string> = {};
    for (const f of logicalFieldsFor(datasetType)) {
      next[f.key] = seeded[f.key] ?? suggestColumn(upload.detected_columns, f.suggest);
    }
    setMapping(next);
  } else {
    // current behavior
    for (const f of logicalFieldsFor(datasetType)) {
      seed[f.key] = suggestColumn(upload.detected_columns, f.suggest);
    }
  }
  ```

- This preserves the override path: any field the profile does not cover falls back to the existing English heuristic, and the user can still change any select.
- Add a small badge near the dataset-type selector showing `Auto-detected: ${profileLabel}` when `upload.source_profile !== "generic"`. Profile labels themselves come from the i18n dictionary:

  ```ts
  // dictionaries/en.ts -> upload.profiles.broz_libreview_cs = "Broz CSV (Czech LibreView)"
  // dictionaries/cs.ts -> upload.profiles.broz_libreview_cs = "Broz CSV (Czech LibreView)"
  ```

- Per-row badge: when a mapping value came from `suggested_mapping`, decorate the row with a small `auto-mapped` badge. If the user manually changes the value, the badge clears.

### 4. Czech display labels — TASK-0032 coordination

- The mapping table's "Logical field" column already shows English (`f.label` at `web/app/page.tsx:428`). After TASK-0032, that label comes from `t("upload.logicalFields.cgm.glucose")` etc., which in `cs` mode returns exactly the Czech headers listed in TASK-0033. So when locale is `cs`:
  - The Logical-field column reads Czech (e.g. `Historie údajů o glukóze mmol/L`).
  - The Source-column select shows the file's actual header (also Czech for Broz).
  - The two visually align, satisfying the user's "automatic mapping to Czech-localized field names" requirement end-to-end.
- When locale is `en`, the logical-field column shows English (`Glucose (mmol/L)`) but the source-column select still shows Czech CSV headers — that is correct because the source columns are the file's literal headers and should not be translated.

### 5. Missing / extra columns handling

- **Missing required header** in a CSV that otherwise looks Broz-like: detection fails, profile becomes `generic`, no pre-fill, fallback to existing English heuristic. The four English suggestions in `CGM_LOGICAL_FIELDS` will still try.
- **Extra columns** beyond the four mapped ones (insulin, ketone, carbs, notes, etc.): unaffected. Today only four logical fields are wired for the CGM dataset type; extra source columns are ignored by analytics. A follow-up task can extend the logical-field set if the analytics module ever consumes insulin/carb data.
- **Optional `scan_glucose_mmol_l`**: this column may be empty or absent in some exports. If absent, `suggested_mapping["cgm"]["scan_glucose_mmol_l"]` is omitted; the row stays `(none)` and the user can leave it.

## Likely Files Affected

| App | File / Module | Change Type |
|-----|---------------|-------------|
| app-4 | `api/app/ingest/profiles.py` | add — `detect_source_profile`, `PROFILE_FIELD_HEADERS` |
| app-4 | `api/app/ingest/loaders.py` | no change (detection runs after `load`) |
| app-4 | `api/app/api/v1/uploads.py` | modify — extend `UploadResponse`, call detection in `_record_to_upload_response` |
| app-4 | `api/app/storage/uploads.py` | modify (small) — store the detected profile alongside the record so subsequent calls don't re-detect |
| app-4 | `api/tests/test_ingest_profiles.py` | add — unit tests for detection on Broz fixtures and a non-Broz fixture |
| app-4 | `api/tests/test_broz_pipeline.py` | modify — assert the mapping endpoint returns a `suggested_mapping` for Broz |
| app-4 | `web/lib/api.ts` | modify — extend `UploadResponse` type with the three new fields |
| app-4 | `web/app/page.tsx` | modify — consume `suggested_mapping` in seeding logic; render auto-detected badge and per-row badges |
| app-4 | `web/lib/i18n/dictionaries/{en,cs}.ts` (TASK-0032) | modify — add `upload.profiles.*` strings and `upload.autoDetectedBadge` |
| app-4 | `web/app/page.test.tsx` | modify — assert pre-fill behavior with a mock `suggested_mapping` |
| app-4 | `web/e2e/analysis.spec.ts` (or a new e2e) | modify/add — happy-path test that uploads `samples/broz/Test1.csv` and asserts pre-filled mapping |

Total: ~3 backend files, ~3 frontend files, 2 test files. **Single app, additive backend contract change (new optional fields), no breaking change.** Full spec is justified because the work crosses the API boundary, has a clinical-data-mapping safety dimension, and coordinates with TASK-0032.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| False positive: a non-Broz CSV is auto-mapped, silently mis-mapping clinical data | medium | Exact-match-on-diacritics required headers; user *always* sees the mapping panel and must click "Submit mapping"; per-row "auto-mapped" badge makes the suggestion explicit. |
| False negative: a Broz-like CSV with one renamed header is not detected, leaving the user with empty suggestions | low | Falls back to existing English heuristic; user manually sets values. No regression vs. today. |
| Diacritics get mangled by an upstream proxy and detection silently fails | low | The double-quoted-line preprocessor already preserves bytes; CSV is decoded as utf-8/utf-8-sig (`loaders.py:73-80`). Add a unit test that explicitly checks `Časová značka zařízení` survives `_maybe_unwrap_double_quoted_lines`. |
| The literal CSV header changes between LibreView versions | medium | Profile detection is centralized; updating one tuple in `profiles.py` covers it. Detection notes propagate to UI for transparency. |
| Coordination drift with TASK-0032: dictionary keys and CSV headers diverge | medium | One canonical place for the Czech strings: TASK-0032 owns them. This spec consumes them. A vitest test asserts that `cs` dictionary values for the four CGM logical fields equal the strings in `samples/broz/Test1.csv:1`. |
| Backwards compat: existing clients depending on `UploadResponse` shape | low | All new fields are optional/defaulted (`Field(default_factory=dict)`); response remains backward-compatible JSON. |

## Validation

### Acceptance criteria

1. Uploading `samples/broz/Test1.csv`:
   - `UploadResponse.source_profile === "broz_libreview_cs"` with `confidence === "high"`.
   - `UploadResponse.suggested_mapping.cgm` is `{timestamp: "Časová značka zařízení", record_type: "Typ záznamu", glucose_mmol_l: "Historie údajů o glukóze mmol/L", scan_glucose_mmol_l: "Skenovat glukózu mmol/L"}`.
   - The mapping panel renders with all four selects pre-filled to those headers.
   - The Czech display labels (after TASK-0032 lands and locale is `cs`) match the source-column values, so each mapping row shows the same string on both sides.
2. Uploading `samples/broz/TEst.csv` (long version, ~96k lines): same as above.
3. Uploading the existing English-LibreView synthetic CGM sample: `source_profile === "generic"`, `suggested_mapping` is empty, existing English heuristic still pre-fills correctly. No regression.
4. Uploading a Broz-shaped CSV with `Typ záznamu` renamed to `Type` (manually edited fixture): detection returns `generic`; no auto-pre-fill.
5. The user can still change any pre-filled mapping value before submitting; the per-row "auto-mapped" badge clears on user edit.
6. `pytest -q` passes including new `test_ingest_profiles.py` and updated `test_broz_pipeline.py`.
7. `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` clean.
8. `npm run test:e2e` passes; the Broz upload e2e asserts pre-fill end-to-end.

### Test strategy

- **Backend unit:** `test_ingest_profiles.py` covers (a) high-confidence detection on full Broz header set, (b) medium confidence on minimum required only, (c) `generic` on missing required, (d) `generic` on Broz with one diacritic stripped (false-positive guard).
- **Backend integration:** add a case in `test_broz_pipeline.py` that POSTs `samples/broz/Test1.csv` and asserts the upload response's `suggested_mapping`.
- **Frontend unit:** Vitest test mounts `HomePage`, mocks `uploadFile`/`getPreview` to return a Broz-shaped response, asserts mapping selects render the four expected values without user interaction.
- **E2E:** Playwright uploads `samples/broz/Test1.csv` (already a fixture in the repo) and asserts the four `<select>` values and the auto-detected badge.

## Rollout Notes

- This spec **must land after TASK-0032** because it consumes dictionary keys defined there. Sequence:
  1. TASK-0032 implementation (i18n + Czech dictionary including the four CGM logical-field labels).
  2. TASK-0033 implementation (backend profile detection + frontend pre-fill + badges).
- Single PR for TASK-0033. No migration. The `UploadResponse` change is additive; existing clients (e.g. test suites) that don't read the new fields are unaffected.

## Rollback

- Revert the PR. Removes `profiles.py`, the `UploadResponse` extra fields, and frontend changes. Existing uploads continue to work via the English heuristic. No data, schema, or persisted-state changes.

## Open Questions

- None blocking. Previously open items resolved:
  - **What is "Broz"?** Resolved by user context: a doctor (Dr. Broz) who forwards Czech-locale FreeStyle LibreLink exports. Treated as a labeled data-source profile, not a vendor signature. The CSVs are LibreView Czech-locale exports (`samples/broz/Test1.csv:2` shows `FreeStyle LibreLink` as the device).
  - **Label vs. canonical ID?** Resolved: canonical IDs stay English snake_case (`timestamp`, `record_type`, `glucose_mmol_l`, `scan_glucose_mmol_l`). Czech strings are display labels, owned by TASK-0032's dictionary.
  - **Detection strategy?** Resolved: exact-match on three required Czech headers, with optional headers raising confidence to `high`.
  - **Full Broz column set?** Confirmed by reading `samples/broz/Test1.csv:1`: 19 columns; we map the four CGM-relevant ones and leave the rest unmapped (no analytics consumes them yet).
  - **`Skenovat skenovat …` typo?** Resolved: the literal CSV header is `Skenovat glukózu mmol/L`. The duplicated word in TASK-0033's original description is a typo and is corrected here.
- **Informational (not blocking):** the user may eventually want a generalized profile registry (JSON-driven) so non-engineers can add new source profiles. Recommend a follow-up task once a third profile appears.

## References

- Triaged task: `tasks/triage/TASK-0033.md`
- Coordinated: `specs/app-4/TASK-0032-spec.md`
- Code: `api/app/ingest/loaders.py:83-129`, `api/app/api/v1/uploads.py:45-56,91-92,168-200`, `web/app/page.tsx:18-44,59-66,175-198`, `web/lib/api.ts:1-12`
- Fixtures: `samples/broz/Test1.csv:1`, `samples/broz/TEst.csv:1`
- Prior: `TASK-0022` (mapping flow), `TASK-0023` (validation/normalization), `TASK-0030` (Broz double-quoted-line loader fix and CGM module bump to 1.1.0)
