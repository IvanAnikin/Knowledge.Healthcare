# Technical Spec: Progressive analysis page + foldable Episodes table

## Metadata

- **Task ID:** TASK-0031
- **Author:** @spec-writer
- **Date:** 2026-04-27
- **App(s):** app-4 (Health-Analysis)
- **Status:** draft

## Summary

The Health-Analysis per-analysis page (`web/app/analysis/[id]/page.tsx`) currently fetches the whole analysis payload in a single `Promise.all` and renders all sections — overall summary, TIR, LLM panel, daypart/backward/monthly windows, monthly comparison, episodes, rate-of-change, post-meal, recent meals, 7 Plotly charts, warnings, assumptions — together. For real Broz datasets (e.g. `samples/broz/TEst.csv`, ~96 600 lines) the Episodes table can produce many rows, and the entire screen waits for both the analysis fetch and the LLM-summary fetch to settle before anything paints. This spec covers two coupled changes: (1) progressive top-down rendering so the most clinically important content (Summary + TIR) is visible and interactive first, and (2) making the Episodes table collapsible by default with light-weight virtualization when expanded for large datasets.

## Objective

- The Summary + TIR + Clinician disclaimer block is on screen and interactive in noticeably less time than today, even when the LLM summary or Plotly charts are slow.
- The Episodes table no longer dominates the page when there are hundreds/thousands of episodes; it is collapsed by default and remains usable when expanded.
- No deterministic-analytics result is hidden from the clinician; only the *presentation* changes.

## Scope

In scope (frontend-only):

- Restructure `web/app/analysis/[id]/page.tsx` so sections render progressively as data and code arrive, top to bottom.
- Decouple the LLM-summary fetch from the analysis fetch.
- Lazy-load Plotly chart code so the heavy `plotly.js-dist-min` bundle does not block the first paint of the Summary block.
- Add a `<details>`/disclosure-pattern wrapper around `EpisodesTable` (`web/components/StatsTables.tsx:258-314`) with a clear count, collapsed by default.
- Add lightweight windowed rendering inside `EpisodesTable` when the row count exceeds a threshold (initial render of N rows, with "Show all N" affordance).
- Match the existing dark-mode-first visual system (`TASK-0029`) and respect `prefers-reduced-motion`.

## Non-Goals

- No backend API changes. The `/api/v1/analyses/{id}` contract (`web/lib/api.ts:268-280`) and `CgmAnalysisResult` shape are unchanged.
- No introduction of a new charting library, no SSR/RSC migration of the analysis page (it remains `"use client"`), no pagination of episodes on the server side.
- No change to the ordering or content of deterministic analytics — only the rendering schedule and the Episodes table chrome.
- No change to print/export behavior (none currently exists).

## Current Behavior

Confirmed from repo:

- `web/app/analysis/[id]/page.tsx:36-57` performs `Promise.all([getAnalysis, getSummary])` and only flips `loading=false` after **both** finish; nothing renders meaningful content until then (`page.tsx:99-101`).
- Once `analysis` is set, every section renders synchronously in one tree (`page.tsx:123-315`): `OverallStats`, `TirTable`, the LLM panel, `WindowsTable` ×3, `MonthlyComparisonTable`, `EpisodesTable`, `RateOfChangeTable`, `PostMealTable`, `RecentMealsTable`, then `chart_specs.map(ChartPanel …)`.
- `ChartPanel` (`web/components/ChartPanel.tsx`) is statically imported, dragging Plotly into the initial chunk for `/analysis/[id]`.
- `EpisodesTable` (`web/components/StatsTables.tsx:258-314`) renders `episodes.map(...)` unconditionally — full list, no fold, no windowing.
- The page is a single Client Component (`"use client"` at `page.tsx:1`); Next.js 14 App Router (`web/package.json:17`).

## Proposed Behavior

### 1. Decouple summary fetch from analysis fetch

Replace the single `Promise.all` with two independent fetches and two independent loading states:

- `analysisLoading` flips false as soon as `getAnalysis(id)` resolves → Summary + TIR + Disclaimer paint immediately.
- `summaryLoading` flips false independently. The LLM panel shows a small skeleton until then; a slow/failed LLM fetch never blocks the rest of the page.

### 2. Progressive section reveal

Render sections in a deliberate order with `React.lazy` + `<Suspense>` boundaries so heavy children do not delay earlier paints:

| Tier | Sections | Behavior |
|------|----------|----------|
| 1 (eager) | Header, disclaimer, `OverallStats`, `TirTable` | Paint as soon as `analysis` is available. |
| 2 (eager-after-tier-1) | LLM panel | Independent state, separate skeleton. |
| 3 (eager) | `WindowsTable` ×3, `MonthlyComparisonTable`, `RateOfChangeTable`, `PostMealTable`, `RecentMealsTable` | Tabular, cheap; render synchronously below tier 1/2. |
| 4 (collapsible) | `EpisodesTable` | Collapsed by default (see §3). |
| 5 (lazy) | Charts (`ChartPanel`) | Lazy-imported via `next/dynamic` with `ssr: false`; render below the fold. |
| 6 (eager) | Warnings, assumptions | Below charts. |

`next/dynamic` is the recommended primitive for tier 5 because `ChartPanel` already pulls `plotly.js-dist-min` (`web/package.json:18`) and Plotly is browser-only.

**Assumption:** The existing visual order (Summary → LLM → Detailed breakdown → Charts → Warnings → Assumptions) is correct clinically and should be preserved. *Reasoning:* `TASK-0029` redesign explicitly chose summary-first; reordering would be a UX decision out of scope here.

### 3. Foldable Episodes table

`EpisodesTable` becomes:

- A panel header that always shows the count and a clickable disclosure (`<button aria-expanded>` pattern, not bare `<details>`, so it can be styled and announce state to screen readers).
- **Default state: collapsed.** The header summarizes counts by kind: `"Episodes (12 total · 4 hypo · 8 hyper) — show table"`.
  - *Rationale for collapsed default:* on Broz-class datasets the table can be large and visually dominate; the kind/total counts are already a complete clinical signal at the summary level. The user-reported symptom is "thousands of records overwhelm the page".
- Expanded state shows the table identical to today plus a small bar at the bottom: `"Showing N of M"` with a `Show all` affordance when windowed.
- **Windowed rendering threshold:** when `episodes.length > 200`, render the first 200 rows initially with a `Show all M` button. Above 1000, keep windowing on but warn in the footer that rendering all rows may be slow.
  - *Rationale for 200/1000:* keeps DOM size predictable; avoids importing a virtualization library (no virtualization deps currently in `web/package.json`). A simple slice is sufficient — a real virtualized list can be a follow-up if 1000-row rendering proves too slow in practice.
- Accessibility: the disclosure button is keyboard-focusable, uses `aria-expanded`/`aria-controls`, and the table region uses `role="region"` with the existing `aria-label="Episodes"`. Reduced-motion: the open/close animation uses `transition: max-height` only, gated by `@media (prefers-reduced-motion: reduce)` to no transition.

### 4. Lazy-loaded charts

Replace the static import of `ChartPanel` in `web/app/analysis/[id]/page.tsx:5` with:

```ts
const ChartPanel = dynamic(
  () => import("../../../components/ChartPanel").then(m => m.ChartPanel),
  { ssr: false, loading: () => <ChartSkeleton /> }
);
```

A simple `ChartSkeleton` (a panel-shaped div with the chart's title visible) preserves layout and lets clinicians see chart titles before figures render.

### 5. "Episode" disambiguation

**Confirmed from repo:** "Episodes" in the user's request maps to the deterministic CGM hypoglycaemic / hyperglycaemic episode-detection output (`Episode` type, `web/lib/api.ts:159-167`), rendered by `EpisodesTable` at `web/components/StatsTables.tsx:258-314` and `web/app/analysis/[id]/page.tsx:268`. Not the Recent Meals table (`RecentMealsTable`, `StatsTables.tsx:580-651`) or the post-meal summary. This resolves the open question in TASK-0031.

## Likely Files Affected

| App | File / Module | Change Type |
|-----|---------------|-------------|
| app-4 | `web/app/analysis/[id]/page.tsx` | modify — split fetches, add Suspense, lazy ChartPanel |
| app-4 | `web/components/StatsTables.tsx` (`EpisodesTable`) | modify — disclosure wrapper + windowing |
| app-4 | `web/app/globals.css` | modify — add styles for `.disclosure`, `.episodes-collapsed`, reduced-motion guard |
| app-4 | `web/components/ChartPanel.tsx` | no change (or trivial named-export confirmation) |
| app-4 | `web/e2e/analysis.spec.ts` + snapshots under `web/e2e/analysis.spec.ts-snapshots/` | modify — Playwright will see a collapsed Episodes table by default; snapshots refresh required |
| app-4 | `web/app/page.test.tsx` (vitest) | no change unless asserting Episodes default state |

Total: ~3 source files modified, plus snapshot refresh. **Single app, no shared interface changes, no data-model changes.** Per `workflows/spec-process.md` this is on the boundary between full spec and lightweight plan; a full spec is justified because there are real UX decisions (default collapsed, threshold values, lazy strategy) and Playwright snapshot churn.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Clinicians miss episodes because the table is collapsed by default | medium | Always show kind/total counts in the header; keep `EpisodesTable` immediately under the detailed breakdown; never collapse if `episodes.length === 0` (show existing empty state instead). |
| Lazy-loading Plotly causes a layout shift below the fold | low | `ChartSkeleton` preserves height with each chart's title; CLS measured at 0 for placeholders. |
| `next/dynamic({ ssr: false })` is unnecessary because the page is already `"use client"` | low | True, but using `dynamic` still lets us code-split the chart bundle. The benefit is bundle size, not SSR semantics. |
| Playwright visual snapshot churn collides with the still-pending TASK-0030 snapshot refresh | medium | Sequence work after TASK-0030 snapshot refresh lands; otherwise refresh both in one pass. |
| Windowing with a simple slice is slow above ~1000 rows | low | Footer warning + follow-up task to introduce a virtualized list if real datasets exceed this regularly. |
| Screen-reader users lose discoverability of episodes | low | `aria-expanded`/`aria-controls` on the disclosure; the header text states the counts. |

## Validation

### Acceptance criteria

1. With network throttling at "Slow 3G", `OverallStats` and `TirTable` are visible before the LLM panel and before charts.
2. A failing `/api/v1/analyses/{id}/summary` (e.g. 500) does not block the rest of the analysis page from rendering.
3. With a Broz dataset producing >50 episodes, the Episodes panel is collapsed by default; total/kind counts are visible in the header without expansion.
4. Expanding the Episodes panel reveals the same data the current table shows. With ≥200 episodes, only the first 200 render initially and a "Show all N" button is offered.
5. `prefers-reduced-motion: reduce` disables the expand/collapse transition.
6. Keyboard: Tab focuses the disclosure; Enter/Space toggles; focus-visible ring matches existing button styles.
7. `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build` are clean.
8. `npm run test:e2e` passes after a snapshot refresh that captures the collapsed Episodes default.

### Test strategy

- **Vitest:** Add a unit test in `web/app/page.test.tsx` (or a new `EpisodesTable.test.tsx`) that asserts the table body is not in the DOM before the disclosure is clicked, and is in the DOM after.
- **Playwright** (`web/e2e/analysis.spec.ts`): refresh snapshot for collapsed state; add an assertion that the Summary block is rendered before the chart panels' figures (not just before their skeletons).
- **Manual**: Chrome DevTools Performance trace on `/analysis/{id}` with the Broz `Test1.csv` analysis — confirm Summary FCP improves vs. main.

## Rollout Notes

- Single PR, no migration. Behind no flag; the change is purely UX.
- Snapshot refresh: run `npm run test:e2e:update` and commit `web/e2e/analysis.spec.ts-snapshots/` together.
- Coordinate ordering with TASK-0030's pending snapshot gate.

## Rollback

- Revert the PR. No data, schema, or API surface is changed.

## Open Questions

- None blocking. The "Episodes" disambiguation is now confirmed against the repo. Threshold values (200 / 1000) are recommended defaults; product owner can tune them in review without further design work.

## References

- Triaged task: `tasks/triage/TASK-0031.md`
- Related: `TASK-0029` (visual system), `TASK-0030` (analysis-page additions, pending snapshot refresh)
- Code: `web/app/analysis/[id]/page.tsx:36-57`, `web/components/StatsTables.tsx:258-314`, `web/components/ChartPanel.tsx`, `web/package.json:18`
