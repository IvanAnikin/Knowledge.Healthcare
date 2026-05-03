# Technical Spec: Czech localization and language switch for Health-Analysis

## Metadata

- **Task ID:** TASK-0032
- **Author:** @spec-writer
- **Date:** 2026-04-27
- **App(s):** app-4 (Health-Analysis)
- **Status:** draft
- **Coordinated with:** [TASK-0033](./TASK-0033-spec.md) (shares the Czech vocabulary registry defined here)

## Summary

Health-Analysis currently has no internationalization. UI strings are inline in TSX, the document language is hard-coded to English (`web/app/layout.tsx:21` — `<html lang="en">`), and no i18n library is installed (`web/package.json:16-37`). The product audience is Czech-speaking clinicians. This spec introduces a minimal, framework-light i18n layer with **Czech (`cs`) and English (`en`)** dictionaries, a `LanguageSwitch` toggle modeled on the existing `ThemeToggle`, persisted locale, and locale-aware number/date formatting. It also defines the **canonical Czech vocabulary registry** that TASK-0033 (Broz auto-mapping) will consume so the four Broz target labels live in one place.

## Objective

- Czech becomes a first-class UI language with a user-visible switcher.
- A single source of truth (`web/lib/i18n/dictionaries/cs.ts` and `en.ts`) holds all user-facing strings, including the four CGM logical-field labels referenced by TASK-0033.
- Persistence: locale survives reloads via `localStorage`, mirroring the theme pattern.
- Clinical units (`mmol/L`, `mg/dL`) and analytics module identifiers remain unchanged across locales.

## Scope

In scope:

- Add a tiny in-house i18n module under `web/lib/i18n/` (no external library — see "Framework choice" below).
- Add `cs.ts` and `en.ts` dictionaries covering: app shell, upload flow (`web/app/page.tsx`), validation panel, analysis page (`web/app/analysis/[id]/page.tsx`), all `StatsTables.tsx` panels, `ChartPanel` titles, alerts/disclaimers.
- `LanguageSwitch.tsx` component placed next to `ThemeToggle` in the header (`web/app/layout.tsx:38`).
- Persist locale in `localStorage` under key `ha-locale`; pre-paint inline script sets `<html lang>` before hydration (mirrors the existing theme bootstrap at `layout.tsx:13`).
- Locale-aware formatting helpers (`formatNumber`, `formatPercent`, `formatDateTime`) using `Intl` directly, replacing the ad-hoc `fmt`/`pct`/`fmtTime` helpers in `StatsTables.tsx:15-23, 566-570`.
- Czech translations supplied as part of this work for **UI chrome and analytics labels**. The default English copy in the repo today is the canonical English text.
- Establish the canonical Czech vocabulary registry that TASK-0033 will reference.

Out of scope (deferred):

- LLM summary localization. The LLM `findings`, `interpretation`, `cited_values`, and `disclaimer` fields (`web/lib/api.ts:282-296`) are returned by the backend (`api/app/llm/`) and are out of scope for this spec. A short `language` parameter could be added later; for now the LLM panel renders backend-supplied text verbatim, with a small note that the summary is in its source language.
- Server-side validation/error messages localization. Backend `ValidationIssue.message` (`web/lib/api.ts:39-47`) is currently English. We will display them as-is with a localized prefix and a follow-up task to key them by `code`.
- URL-prefixed routing (`/cs/...` vs. `/en/...`). The app is a single-flow internal tool with no SEO requirements; persistence + `<html lang>` is sufficient and avoids touching the routing structure.

## Non-Goals

- No new i18n library (next-intl, next-i18next, react-intl). Justification under "Framework choice".
- No reorganization of files into `web/app/[lang]/...` segments.
- No translation of the LLM-generated summary text in this slice.
- No translation memory / TMS integration.

## Current Behavior

Confirmed from repo:

- `web/app/layout.tsx:21` hard-codes `<html lang="en" data-theme="dark">`. No locale provider, no i18n.
- All UI strings are inline English. Examples: `web/app/page.tsx:269` `<h1>Health-Analysis</h1>`, `:271-274` "Milestone M3: ingest, mapping, …", `:277-279` step labels, dataset-type labels at `:18-25`, logical-field labels at `:27-44`.
- Same for analysis page: `web/app/analysis/[id]/page.tsx:81` "Analysis result", `:93-97` clinician disclaimer text, `:125` "Summary", `:257` "Detailed breakdown", `:281` "Charts".
- All table components in `web/components/StatsTables.tsx` use English column headers and panel titles.
- Number/date formatting in `StatsTables.tsx:15-23` uses `Number.prototype.toFixed` (locale-insensitive) and `pct` returns a `%` suffix with `.` decimal separator.
- `ThemeToggle` (`web/components/ThemeToggle.tsx`) is the precedent for a small client-only toggle persisted in `localStorage` (`ha-theme`, see `layout.tsx:13`).
- `web/package.json` has no i18n dependency.

## Proposed Behavior

### Framework choice: in-house

**Recommendation: in-house, ~30 LOC.** Reasoning:

1. The app is small (one upload page, one analysis page, three components, ~4 panels) — the dictionary is bounded.
2. No URL-prefix routing or server-rendered translations are needed.
3. `next-intl` and friends add bundle weight, App-Router segment requirements, and message-format complexity (ICU plurals) that the current copy does not need.
4. Mirroring the `ThemeToggle` pattern keeps the architecture coherent.

If the dictionary grows past ~5 pages or the LLM panel gets translated server-side, migrating to `next-intl` is straightforward because all strings will already be keyed.

### Module layout

```
web/lib/i18n/
  index.ts                # createT(locale), useLocale(), useT(), persistLocale()
  locales.ts              # SUPPORTED_LOCALES = ["en", "cs"] as const; DEFAULT = "en"
  format.ts               # formatNumber, formatPercent, formatDateTime (Intl-based, locale-aware)
  dictionaries/
    en.ts                 # source of truth for English copy
    cs.ts                 # Czech translations (this slice)
    keys.ts               # exported `Messages` type — the dictionary shape
```

The dictionary is a deeply-nested plain object, e.g.:

```ts
// dictionaries/keys.ts
export type Messages = {
  app: { brand: string; brandSub: string };
  upload: {
    h1: string; intro: string;
    steps: { upload: string; map: string; validate: string; run: string };
    panels: { upload: string; preview: string; mapping: string };
    datasetType: string;
    datasetTypes: Record<DatasetType, string>;
    logicalFields: {
      cgm: { timestamp: string; recordType: string; glucose: string; scanGlucose: string };
      generic: { timestamp: string; value: string };
    };
    glucoseSourceUnit: string;
    submit: string; running: string; submitting: string;
  };
  validation: { passed: (n: number) => string; blocked: string; errors: string; warnings: string; suggestedFix: string };
  analysis: {
    h1: string; back: string; summary: string; detailedBreakdown: string; charts: string;
    panels: {
      overall: string; tir: string;
      dayparts: string; backwardWindows: string; monthlyTrend: string;
      monthlyComparison: string; episodes: string; rateOfChange: string;
      postMeal: string; recentMeals: string;
      moduleAssumptions: string; dataQuality: string; llmSummary: string;
    };
    disclaimer: string;
    metrics: { mean: string; median: string; sd: string; cv: string; gmi: string; tirTarget: string; optimal: string; veryLow: string; low: string; high: string; veryHigh: string };
    badges: { heuristic: string };
  };
  llm: { generate: string; refresh: string; generating: string; provider: string; model: string; promptTemplate: string; findings: string; interpretation: string; citedValues: string; warningsCarried: string; heuristicNotes: string; sourceLanguageNote: string };
};
```

Both `en.ts` and `cs.ts` export `const messages: Messages = { ... }`.

### Czech vocabulary registry — coordination with TASK-0033

The four Czech display labels requested by TASK-0033 live here, **once**:

```ts
// dictionaries/cs.ts (excerpt)
upload: {
  logicalFields: {
    cgm: {
      timestamp:   "Časová značka zařízení",
      recordType:  "Typ záznamu",
      glucose:     "Historie údajů o glukóze mmol/L",
      scanGlucose: "Skenovat glukózu mmol/L",
    },
    ...
  },
}
```

**Confirmed against the repo:** these four strings are the literal headers in `samples/broz/Test1.csv:1` and `samples/broz/TEst.csv:1` (verified by reading line 1 of both fixtures). The user-supplied target `Skenovat skenovat glukózu mmol/L` (with the duplicated word) in the original TASK-0033 description is a typo; the canonical Czech CSV header is `Skenovat glukózu mmol/L` and the corrected mapping in TASK-0033's spec uses that form.

**Canonical IDs are stable English snake_case** (`timestamp`, `record_type`, `glucose_mmol_l`, `scan_glucose_mmol_l`) — these match the existing logical-field keys at `web/app/page.tsx:27-44`. The Czech strings are display labels only; they do **not** become field identifiers in storage, API, or analytics. This resolves TASK-0033's "label vs. canonical ID" open question.

### Switcher placement and behavior

- New `web/components/LanguageSwitch.tsx`, structurally mirroring `ThemeToggle.tsx`. Two-button segmented control: `EN` | `CS`.
- Placed in `web/app/layout.tsx:38` next to `<ThemeToggle />` inside `app-header-inner`.
- Selecting a locale: writes `localStorage["ha-locale"]`, sets `document.documentElement.lang`, and updates the React context so all consumers re-render.

### Pre-paint bootstrap

Extend the existing inline bootstrap script at `layout.tsx:13` to also pick up `ha-locale` and set `<html lang>` before hydration:

```ts
const localeBootstrap = `(function(){try{var l=localStorage.getItem('ha-locale');document.documentElement.setAttribute('lang', (l==='cs'?'cs':'en'));}catch(e){document.documentElement.setAttribute('lang','en');}})();`;
```

This avoids a hydration mismatch on the `<html lang>` attribute.

### Default locale resolution

Order: `localStorage["ha-locale"]` → `navigator.language` (if `cs*`, use `cs`) → `en`. Resolution happens client-side only; SSR/initial HTML uses `en` and the bootstrap script reconciles before paint.

### Locale-aware formatting

`format.ts`:

```ts
export const formatNumber  = (locale: Locale, n: number, digits = 2)
  => new Intl.NumberFormat(locale === "cs" ? "cs-CZ" : "en-US",
       { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(n);
export const formatPercent = (locale, fraction, digits = 1) => /* … */;
export const formatDateTime = (locale, isoLike) => /* … 24h, "yyyy-MM-dd HH:mm" with cs comma decimals where applicable */;
```

Replaces `fmt`, `pct`, `fmtTime` in `StatsTables.tsx`. **Czech `cs-CZ` will produce comma decimals** (`5,4` instead of `5.4`) which already matches how the Broz CSV stores glucose values (`samples/broz/Test1.csv:2` `"4,7"`). Unit symbols (`mmol/L`, `%`) remain Latin.

### Module IDs are not translated

`result.module_id`, `module_version`, episode `kind` (`hypo`/`hyper`), and band names (`target`, `optimal`, `very_low`, …) are technical identifiers, not display labels. They are wrapped as `<code>` (already done in `StatsTables.tsx:117-119, 169-171, 178-180`) and kept untranslated. Their human-readable counterparts are pulled from the dictionary.

### LLM summary handling

For this slice the LLM panel:

1. Sends locale neither as a parameter to `POST /api/v1/analyses/{id}/summary` nor in any prompt — backend behavior unchanged.
2. Renders backend-supplied text verbatim.
3. Shows a small localized note above the summary content: `"This summary is generated in its source language."` / `"Tento souhrn je generován ve zdrojovém jazyce."` This makes the gap explicit and creates a clean follow-up.

A separate task should add `?language=cs` or a request body field once we want true bilingual summaries; that touches `api/app/llm/` and the prompt template, which are out of scope here.

## Likely Files Affected

| App | File / Module | Change Type |
|-----|---------------|-------------|
| app-4 | `web/lib/i18n/index.ts` | add — provider, hooks, persistence |
| app-4 | `web/lib/i18n/locales.ts` | add — `SUPPORTED_LOCALES`, defaults |
| app-4 | `web/lib/i18n/format.ts` | add — Intl-based formatters |
| app-4 | `web/lib/i18n/dictionaries/keys.ts` | add — `Messages` type |
| app-4 | `web/lib/i18n/dictionaries/en.ts` | add — English source of truth |
| app-4 | `web/lib/i18n/dictionaries/cs.ts` | add — Czech translations |
| app-4 | `web/components/LanguageSwitch.tsx` | add |
| app-4 | `web/app/layout.tsx` | modify — add locale provider + bootstrap script + switcher |
| app-4 | `web/app/page.tsx` | modify — replace inline strings with `t(...)`, swap `DATASET_TYPES` and `CGM_LOGICAL_FIELDS` to use the dictionary |
| app-4 | `web/app/analysis/[id]/page.tsx` | modify — replace inline strings with `t(...)`; LLM source-language note |
| app-4 | `web/components/StatsTables.tsx` | modify — replace inline headers/labels and `fmt`/`pct`/`fmtTime` with locale-aware helpers |
| app-4 | `web/components/ChartPanel.tsx` | modify — translate chart titles/notes if locally rendered (chart figure data still comes from backend) |
| app-4 | `web/app/page.test.tsx`, `web/e2e/analysis.spec.ts` | modify — assert default `en`, switch to `cs`, snapshot refresh |

Total: ~7 files added, ~6 modified, plus snapshot refresh. **Single app, no shared interface changes, no schema/API changes.** This is a full spec because the work touches every user-facing surface and a wrong framework choice is expensive to undo.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Hydration mismatch on `<html lang>` | medium | Pre-paint bootstrap script sets `lang` before React hydrates, mirroring the working theme pattern. Server always emits `lang="en"`; client reconciles. |
| Czech translations drift from English source | medium | `Messages` type forces every key to exist in both dictionaries; `tsc` catches any missing key. |
| Comma decimals (`5,4 mmol/L`) confuse non-Czech users / chart hover labels | low | Plotly hover formatting comes from backend `figure` data; backend currently emits standard JSON numbers. Client UI labels formatted via `Intl` honor the active locale only — if user picks `en`, dots are used. |
| Backend validation messages remain English | low | Out of scope. Add follow-up task to key validation messages by `code` in `api/app/validation/`. |
| LLM panel mixed-language UX | low | Explicit localized "source language" note; tracked as an explicit follow-up. |
| Czech translations introduce typos (e.g. duplicated word as in original TASK-0033 description) | medium | Review pass against Broz CSV ground truth (`samples/broz/Test1.csv:1`); product owner review of `cs.ts` before merge. |
| Bundle size grows due to dictionaries | low | Two small TS files (~5–10 KB combined). No external library. |

## Validation

### Acceptance criteria

1. With a fresh browser profile, the app renders in English with `<html lang="en">`.
2. Clicking `CS` in the header switches all UI chrome, panel titles, table headers, the disclaimer, and metric labels to Czech without a page reload.
3. After reload, the chosen locale persists; `<html lang>` matches before hydration (no flash).
4. In `cs` mode, numeric values use comma decimals (`5,4`) and percent uses `%` with a comma (`72,3 %`); in `en` mode, dots and `72.3%`.
5. Unit suffixes (`mmol/L`, `mg/dL`, `min`) are unchanged across locales.
6. Selecting `cs` does not change LLM summary content, but a localized "source language" note is shown.
7. The four CGM logical-field Czech labels in the dictionary match the Broz CSV headers verbatim (`samples/broz/Test1.csv:1`).
8. `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` are clean.
9. `npm run test:e2e` passes after a snapshot refresh that captures both locales (or, alternatively, only the default English path with one focused `cs` test).

### Test strategy

- **Vitest:** add tests for `formatNumber`/`formatPercent`/`formatDateTime` covering both locales; add a test that renders `HomePage` with the i18n provider in `cs` mode and asserts the H1 reads `Health-Analysis` (brand stays untranslated) and the Step 1 panel header is Czech.
- **Playwright:** one new test that toggles to `cs`, asserts a known Czech header is visible, reloads, and confirms persistence.
- **Manual:** verify alignment with `samples/broz/Test1.csv:1` headers exactly (TASK-0033 will mechanically depend on this).

## Rollout Notes

- Single PR. No backend changes, no migration.
- TASK-0033 (auto-mapping for Broz CSV) **must land after this spec** because it imports the Czech labels from the dictionary defined here.
- No feature flag needed. Default locale is `en`, identical to current behavior; switching to `cs` is opt-in.

## Rollback

- Revert the PR. Deletes `web/lib/i18n/`, `LanguageSwitch.tsx`, and restores inline strings. No data, schema, or contract changes.

## Open Questions

- None blocking. The previously open framework / persistence / scope questions are resolved by recommended defaults above. Czech translations themselves should be product-owner-reviewed before merge — that is a copy review, not a spec blocker.

## References

- Triaged task: `tasks/triage/TASK-0032.md`
- Coordinated: `specs/app-4/TASK-0033-spec.md`
- Code: `web/app/layout.tsx:13,21,38`, `web/app/page.tsx:18-44,269-279`, `web/app/analysis/[id]/page.tsx:81-97`, `web/components/StatsTables.tsx:15-23,566-570`, `web/components/ThemeToggle.tsx`, `web/package.json:16-37`, `samples/broz/Test1.csv:1`
- Precedent: app-3 ANOTE-web bilingual `[lang]/` routing (intentionally not adopted here — see "Out of scope")
