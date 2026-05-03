# TASK-0018 — Task Dashboard UI/UX Modernization (Glassmorphism + Dark Mode)

**Status:** draft — awaiting user confirmation
**Owner area:** control-layer tooling (`scripts/generate_dashboard.py` → `dashboards/task-dashboard.html`)
**Scope:** cross-app (tooling only; no application repos affected)
**Date:** 2026-04-24

---

## 1. Context

The task dashboard is a static HTML page produced by [scripts/generate_dashboard.py](../../scripts/generate_dashboard.py) from Markdown task/spec files. It renders:

- A sticky header with title, subtitle, and generation meta
- An Overview section (status totals + per-app totals)
- Current Priorities (parsed from `current-priorities.md`)
- Filters (search, app, priority, status, type, hide-done checkbox, reset)
- A Kanban task board (cards grouped by status column)
- Parser warnings + closing notes

Current look: light theme, flat cards, opaque white surfaces, minimal motion.

## 2. Goals

Modernize the dashboard into a more expressive, polished single-page view:

1. Replace the current sticky header with a compact **overview stat bar** as the top element (status totals + per-app totals, single row, readable on desktop).
2. Reorder the page below the stat bar to: **Filters → Task Board → Current Priorities → Parser Warnings → Footer**.
3. Show done/tested/deployed tasks **by default** (uncheck the "hide" filter).
4. Add a **dark-mode default** with a toggle in the top-right corner, persisted in `localStorage`.
5. Apply a **glassmorphism** visual language: translucent panels, rounded corners, blurred soft glow "lights" behind containers, subtle borders, tasteful animations.
6. Respect `prefers-reduced-motion`.

## 3. Non-Goals

- No changes to the Markdown source of truth or the parsing logic.
- No new data fields, filters, or board columns.
- No changes to modal content/behavior beyond cosmetic restyling for dark mode and glass.
- No server-side rendering, bundler, or external runtime dependencies (page remains a single self-contained HTML file).
- No changes in application repositories.

## 4. User-Confirmed Decisions

| # | Decision | Value |
|---|----------|-------|
| D1 | Dark mode behavior | **Default dark** + toggle button + `localStorage` persistence (key `kh-theme`: `"dark"` \| `"light"`). No OS-preference follow. |
| D2 | Background "lights" | **Animated multi-color blurred blobs** (violet / blue / teal / pink), slow drift. Paused under `prefers-reduced-motion`. |
| D3 | Overview row | Status totals **and** per-app counts must both fit on the top row; smaller padding/typography allowed. Horizontal overflow permitted only below ~900px. |
| D4 | Meta info ("Generated: …", "Regenerate: …") | Moved to a **small one-line footer at the very bottom** of the page. |
| D5 | Animation scope | **Tasteful**: fade/slide-in on page load, hover lift on task cards, smooth filter transitions, animated background blobs. |
| D6 | `prefers-reduced-motion` | **Respected** — disables blob motion, load-in animations, and hover translate (hover color/border only). |

## 5. Information Architecture (new page order)

```
┌──────────────────────────────────────────────────────┐
│ TOP STAT BAR (glass)                    [☾ toggle]   │  ← replaces old header
│ Inbox · Triage · Active · Backlog · Done · Tested ·  │
│ Deployed · | · app-1 · app-2 · app-3 · cross-app     │
├──────────────────────────────────────────────────────┤
│ FILTERS (glass)                                      │
│ [search] [app▾] [priority▾] [status▾] [type▾]        │
│ [ ] Hide done/tested/deployed   [Reset]              │
│ N tasks shown                                        │
├──────────────────────────────────────────────────────┤
│ TASK BOARD — Kanban columns (glass cards)            │
├──────────────────────────────────────────────────────┤
│ CURRENT PRIORITIES (glass)                           │
├──────────────────────────────────────────────────────┤
│ PARSER WARNINGS (glass, only if any)                 │
├──────────────────────────────────────────────────────┤
│ FOOTER: Generated 2026-04-24 13:37 UTC · Regenerate: │
│ python3 scripts/generate_dashboard.py                │
└──────────────────────────────────────────────────────┘
            (animated blurred blobs behind all)
```

Removed from the old header: the title "Knowledge.Healthcare — Task Dashboard", subtitle "Read-only — Markdown files are the source of truth — Click any card for details", and the `Generated:` / `Regenerate:` block. The page `<title>` tag is retained so the browser tab still reads "Knowledge.Healthcare — Task Dashboard".

## 6. Visual Design

### 6.1 Themes (CSS custom properties)

Two variable sets toggled via `<html data-theme="dark|light">`.

**Dark (default):**
- Page background: deep near-black `#0b0d12` with layered radial gradients.
- Glass surface: `rgba(22, 26, 34, 0.55)` with `backdrop-filter: blur(18px) saturate(140%)`.
- Border: `rgba(255, 255, 255, 0.08)` 1px; inner highlight via inset `rgba(255,255,255,0.04)`.
- Text: `#e6e8ef`; muted `#9aa3b2`; faint `#6b7280`.
- Accent: `#6ea8ff` (blue), used for focus rings and links.
- Status column colors: slightly brighter than current (adjusted for dark bg).

**Light:**
- Page background: `#eef1f6` with same blob system at lower opacity.
- Glass surface: `rgba(255, 255, 255, 0.55)` blur 18px.
- Border: `rgba(15, 20, 30, 0.08)`.
- Text tokens carried over from current light palette.

### 6.2 Background "lights"

A fixed, pointer-events-none layer behind all content:

```
body::before {
  position: fixed; inset: 0; z-index: -1;
  background:
    radial-gradient(blob-a at 10% 20%, rgba(139, 92, 246, .45), transparent 55%),
    radial-gradient(blob-b at 85% 10%, rgba(59, 130, 246, .40), transparent 55%),
    radial-gradient(blob-c at 70% 85%, rgba(14, 165, 233, .38), transparent 55%),
    radial-gradient(blob-d at 20% 90%, rgba(236, 72, 153, .35), transparent 55%);
  filter: blur(60px) saturate(120%);
  animation: blob-drift 40s ease-in-out infinite alternate;
}
```

Blob positions drift via a keyframe animation (translate + scale, 40–60s loop). In light mode, alpha drops to ~0.25 to stay tasteful.

### 6.3 Glass container pattern

All section panels (stat bar, filters, board columns optionally, priorities, warnings, modal) use:

```
.glass {
  background: var(--glass-bg);
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.05);
}
```

Radii: containers `16px`, cards `12px`, pills/inputs `10px`, badges `999px`.

### 6.4 Kanban columns and cards

- Columns get a subtle glass background with a top color accent bar (4px) using the existing per-status color variables.
- Task cards: softer glass, `12px` radius, hover = translateY(-2px) + stronger shadow + border brighten (0.15s ease).
- Badges keep their semantic colors but with slightly higher contrast for dark mode.

### 6.5 Top stat bar layout

- Single flex row, `gap: 10px`, horizontally scroll only <900px viewport.
- Each stat: compact pill (icon/label above number, or number + small label side-by-side) — final visual tuned during implementation.
- A vertical divider separates status totals from per-app totals.
- Theme toggle button sits on the far right, circular 36×36, sun/moon SVG.

### 6.6 Animations

- Page load: stat bar, filters, and board sections fade + translateY(8px→0) with 60ms stagger, total ≤ 350ms.
- Task cards in a column: none on load (avoid jank); only hover/modal-open transitions.
- Filter state change: `transition: opacity .18s, transform .18s` on cards leaving/entering the filtered view (cards use CSS `display` toggle; animate `opacity` only to avoid layout thrash).
- Modal: existing fade/zoom retained; backdrop blur strengthened.
- All disabled under `@media (prefers-reduced-motion: reduce)`.

## 7. Behavior Changes

| Before | After |
|---|---|
| Sticky old header with title/subtitle/meta | Removed. Top stat bar becomes the first element. |
| Overview = separate section titled "Overview" | Merged into the top stat bar; dedicated section removed. |
| `#hide-done` checkbox `checked` by default | **Unchecked** by default; JS default behavior stays identical otherwise. |
| No theme choice | `data-theme="dark"` on `<html>` by default; toggle button persists user choice in `localStorage["kh-theme"]`. Setting is applied pre-paint via an inline script at the top of `<head>` to avoid FOUC. |
| Meta line in header | Moved to a `<footer class="page-footer">` at the end of `<body>`. |

Section titles ("Overview", "Filters", "Current Priorities", "Task Board — click a card to view details", "Parser Warnings") are retained except "Overview" (removed because it's now the full-width stat bar at page top).

## 8. Accessibility

- Preserve all existing ARIA labels on filter inputs and modal.
- Theme toggle: `<button aria-label="Toggle color theme" aria-pressed="…">`; focusable; visible focus ring.
- Contrast: ensure WCAG AA (≥4.5:1 for body text, ≥3:1 for large text/badges) in both themes. Verify dark status-badge colors.
- Focus rings: 2px accent outline with 2px offset, always visible (never `outline: none`).
- `prefers-reduced-motion: reduce` disables blob drift, load-in transitions, and card hover translate.
- Backdrop-filter fallback: browsers without support get solid `var(--glass-bg-solid)` (opaque variant); feature-detected via `@supports not (backdrop-filter: blur(1px))`.

## 9. Out of Scope / Risks

- Safari/iOS backdrop-filter performance at very large blob sizes — mitigated with `will-change: transform` on the blob layer and a single composite layer.
- No new dependencies; page remains offline-openable via `file://`.
- Print styles not updated (out of scope).

## 10. Acceptance Criteria

1. Opening `dashboards/task-dashboard.html` shows dark theme by default; toggling stores preference and survives reload.
2. The old sticky header (title, subtitle, generation meta) is gone; the top of the page is a single-row stat bar containing status totals + per-app totals + theme toggle.
3. The order below is: Filters → Task Board → Current Priorities → Parser Warnings → Footer.
4. The "Hide done / tested / deployed" checkbox is **unchecked** on first load, and done/tested/deployed columns/cards are visible.
5. All panels use the glass treatment; blurred colored blobs are visible through them.
6. Cards have rounded corners (≥12px) and hover lift; on-load fade-in is present.
7. With `prefers-reduced-motion: reduce`, no blob drift and no load-in movement.
8. Page works opened directly from the filesystem with no console errors and no new external requests.
9. Footer at the bottom shows `Generated: {timestamp}` and `Regenerate: python3 scripts/generate_dashboard.py`.
10. Re-running `python3 scripts/generate_dashboard.py` regenerates the HTML without errors.

## 11. Open Questions

None blocking; all D1–D6 are confirmed. Any visual micro-tuning (exact blob hues, exact pill sizing) will be decided during implementation and can be adjusted in a follow-up.
