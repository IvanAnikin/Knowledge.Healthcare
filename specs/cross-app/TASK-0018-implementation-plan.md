# TASK-0018 — Implementation Plan

Companion to [TASK-0018-spec.md](TASK-0018-spec.md). Single-file change in [scripts/generate_dashboard.py](../../scripts/generate_dashboard.py); regenerated [dashboards/task-dashboard.html](../../dashboards/task-dashboard.html) is the visible output.

---

## Files touched

- `scripts/generate_dashboard.py` — update `INLINE_CSS`, the header/overview/section HTML template, add theme-init inline script, add theme toggle button, add footer, flip `hide-done` default.
- `dashboards/task-dashboard.html` — regenerated only; not hand-edited.

No other files are modified. No new dependencies.

## Step-by-step

### Step 1 — Flip `hide-done` default (smallest risk first)

In `generate_dashboard.py` around line 741, change:

```html
<input type="checkbox" id="hide-done" checked />
```

to:

```html
<input type="checkbox" id="hide-done" />
```

Verify JS in the same file (around line 1564, `hideDoneChk`) already reads `.checked` — no JS change needed; default unchecked means done/tested/deployed visible on first paint.

### Step 2 — Inline theme-init script (prevent FOUC)

Add at the very top of `<head>`, before the `<style>` block, a tiny script:

```html
<script>
  (function () {
    try {
      var t = localStorage.getItem('kh-theme');
      document.documentElement.setAttribute('data-theme', t === 'light' ? 'light' : 'dark');
    } catch (e) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  })();
</script>
```

This runs before CSS parses, so the first paint is already themed.

### Step 3 — Restructure CSS `:root` into theme tokens

In `INLINE_CSS`:

- Move current light palette under `:root, html[data-theme="light"] { … }`.
- Add `html[data-theme="dark"] { … }` with the dark palette from spec §6.1.
- Add `--glass-bg`, `--glass-bg-solid`, `--glass-border`, `--glass-shadow`, `--radius-lg: 16px`, `--radius-md: 12px`.
- Keep status column color vars but tune the dark-mode values for contrast.

### Step 4 — Background blob layer

Add global rules:

```css
body { background: var(--page-bg); position: relative; }
.bg-blobs {
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background: /* 4 radial gradients per spec §6.2 */;
  filter: blur(60px) saturate(120%);
  will-change: transform;
  animation: blob-drift 50s ease-in-out infinite alternate;
}
@keyframes blob-drift { … }
@media (prefers-reduced-motion: reduce) { .bg-blobs { animation: none; } }
```

Add `<div class="bg-blobs" aria-hidden="true"></div>` as the first child of `<body>`.

### Step 5 — Replace header template with top stat bar

In `generate_dashboard.py` around lines 1689–1700, replace the `<header class="dashboard-header">…</header>` block and the `<section>` currently labelled "Overview" with a single new top bar:

```html
<header class="top-bar glass">
  <div class="top-bar-inner">
    <div class="stats-row">
      {summary_html}           <!-- status total cards -->
      <span class="stats-divider" aria-hidden="true"></span>
      {app_summary_html}       <!-- per-app cards, split out below -->
    </div>
    <button id="theme-toggle" class="theme-toggle" aria-label="Toggle color theme" aria-pressed="true">
      <svg class="icon-sun">…</svg><svg class="icon-moon">…</svg>
    </button>
  </div>
</header>
```

This requires splitting the existing `summary_html` builder (around line 670) into two pieces: status totals and per-app totals, returned as separate strings. Both arrays already exist in the generator (status counts + `app_counts`); only the concatenation point changes.

Stat cards become compact pills (number + label inline) with smaller font sizes (number ~20px, label ~11px). Column: number on top, tiny caps label below — tuned to fit a single 1440px row.

Remove the old "Overview" section header entirely.

### Step 6 — Reorder sections

Move the `<section>` blocks so output order is:

1. Top bar (step 5)
2. Filters
3. Task Board
4. Current Priorities
5. Parser Warnings
6. `<footer class="page-footer">Generated: … · Regenerate: <code>python3 scripts/generate_dashboard.py</code></footer>`

### Step 7 — Apply `.glass` class to all panels

Add `class="glass"` (alongside existing classes) to:

- `.filters-bar`
- `.kanban-col`
- `.priorities-content`
- `.warnings-section`
- `.modal-content`
- The top-bar element

Update existing panel CSS to use `var(--glass-bg)` / `var(--glass-border)` / `var(--radius-lg)` and `backdrop-filter: blur(18px) saturate(140%)`. Add `@supports not (backdrop-filter: blur(1px)) { .glass { background: var(--glass-bg-solid); } }` fallback.

### Step 8 — Task card restyle

Update `.task-card`:

- `border-radius: var(--radius-md)` (12px)
- Translucent surface tuned to sit on top of column glass
- Hover: `transform: translateY(-2px); box-shadow: …;` with `transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease`
- Under reduced motion: drop translate, keep shadow/border feedback

### Step 9 — Load-in animation

Add a one-shot fade+rise:

```css
@keyframes rise-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.top-bar, .section { animation: rise-in .32s ease both; }
.section:nth-of-type(2) { animation-delay: .06s; }
.section:nth-of-type(3) { animation-delay: .12s; }
@media (prefers-reduced-motion: reduce) { .top-bar, .section { animation: none; } }
```

### Step 10 — Theme toggle JS

Append to the inline JS near other UI handlers:

```js
(function () {
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  function sync() {
    var t = document.documentElement.getAttribute('data-theme');
    btn.setAttribute('aria-pressed', String(t === 'dark'));
  }
  sync();
  btn.addEventListener('click', function () {
    var cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    var next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('kh-theme', next); } catch (e) {}
    sync();
  });
})();
```

### Step 11 — Footer

Add at the end of `<body>` (before closing `</body>`):

```html
<footer class="page-footer">
  Generated: {now} · Regenerate: <code>python3 scripts/generate_dashboard.py</code>{warn_badge_inline}
</footer>
```

`warn_badge_inline` keeps the existing warning-indicator behavior (tiny badge when parser warnings exist).

### Step 12 — Regenerate and visual-verify

```bash
python3 scripts/generate_dashboard.py
open dashboards/task-dashboard.html
```

Manual verification against the acceptance criteria in spec §10:

- [ ] Dark on first open
- [ ] Toggle flips and persists after reload
- [ ] Top bar shows all status + per-app totals in one row on a 1440px viewport
- [ ] Done/Tested/Deployed visible by default
- [ ] Section order matches spec §5
- [ ] Blobs visible through glass, animated (except under reduced motion)
- [ ] No console errors, no external network requests
- [ ] Footer present at bottom with generation info
- [ ] Modal still opens and closes correctly; styled for dark mode

## Rollback

Single-file change. Revert `scripts/generate_dashboard.py` via git and re-run it to regenerate the old HTML. No data migrations, no external state.

## Estimate of blast radius

- Control-layer tooling only.
- No application repo code touched.
- Markdown source files untouched.
- Reviewable as one diff (generator) plus the regenerated HTML artifact.
