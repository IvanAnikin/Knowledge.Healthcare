# Technical Spec — TASK-0003
## Features Section: Anamnéza Floating Animation + Workflow Diagram Fork

> **App:** app-3 (ANOTE-web)
> **Task:** TASK-0003
> **Created:** 2026-04-20
> **Status:** spec-complete — implementation-ready
> **Repo:** `/Users/ivananikin/Documents/ANOTE-web`

---

## 1. Scope

This spec covers two independent visual changes within `src/components/sections/Features.tsx` and the Czech/English dictionaries:

| Sub-task | Nature | Risk |
|----------|--------|------|
| A. Anamnéza floating chips animation | New animated component using `requestAnimationFrame` + React state | Medium |
| B. Workflow diagram fork | JSX and copy change in existing `FeatureVisual` | Low |
| C. String removals (features section) | Dictionary key deletions/edits | Low — see TASK-0001 overlap note |

---

## 2. Confirmed Facts (from source inspection)

1. `src/components/sections/Features.tsx` is a `"use client"` component. It renders the `<section id="features">` block. All feature visuals are hardcoded in the `FeatureVisual` function as a `Record<string, React.ReactNode>` keyed by a `featurePlaceholders` string array indexed by feature position.

2. The `featurePlaceholders` array is:
   ```ts
   const featurePlaceholders = ["transcript", "report", "privacy", "offline", "templates", "workflow"];
   ```
   - Index 1 → `"report"` → this is the visual for the anamnéza/report-structure feature (`features.items[1]`)
   - Index 5 → `"workflow"` → this is the visual for the one-tap workflow feature (`features.items[5]`)

3. The **anamnéza visual** (key `"report"`) currently renders:
   ```tsx
   ["NO", "RA", "OA", "FA", "AA"].map((s) => (
     <div key={s} className="flex items-center gap-3">
       <span className="text-xs font-bold text-primary bg-primary/10 rounded px-2 py-0.5">{s}</span>
       <div className="flex-1 h-2 bg-text-primary/5 rounded" />
     </div>
   ))
   ```
   These are the anamnéza section abbreviation chips. They are currently static.

4. The **workflow visual** (key `"workflow"`) currently renders three inline steps:
   ```
   🔴 Nahrát  →  ⏹️ Stop  →  📋 Kopírovat
   ```
   All three steps are hardcoded JSX inside `FeatureVisual`. No dictionary key is used for these labels.

5. The string `"13 sekcí"` appears in:
   - `cs.json:66` — `features.items[1].title`: `"13 sekcí. Česká terminologie. Automaticky."`
   - `cs.json:53` — `howItWorks.steps[2].description`: `"AI vytvoří strukturovanou lékařskou zprávu s 13 sekcemi dle českých standardů."`
   - `en.json` equivalents: `features.items[1].title` and `howItWorks.steps[2].description`

6. The string `"funguje i bez internetu"` / `"Works Without Internet"` appears in:
   - `cs.json:76` — `features.items[3].title`: `"Funguje i bez internetu"`
   - `en.json:76` — `features.items[3].title`: `"Works Without Internet"`
   - `cs.json:30` — `hero.badges[3]`: `"Funguje i offline"`
   - `en.json:30` — `hero.badges[3]`: `"Works Offline"`

7. The string `"Hlas pacienta nikdy neopustí telefon"` appears in:
   - `cs.json:71` — `features.items[2].title`
   - `en.json:71` — `features.items[2].title`: `"Patient Voice Never Leaves the Phone"`

8. **Framer Motion** (v12.38+) is already a project dependency. It is imported in `HowItWorks.tsx` as `import { motion, type Variants } from "framer-motion"`.

9. No existing physics/bouncing animation component exists in `src/components/animations/`. The available animation components are: `CountUp`, `FadeInOnScroll`, `ParallaxFloat`, `StaggerChildren`, `TypewriterText`. `ParallaxFloat` uses scroll-based `useTransform` only.

10. `src/app/globals.css` defines CSS custom properties and a few `@keyframes` (fade-in, pulse-dot, skeleton-shimmer). No bounce or float keyframes exist yet.

11. Both Czech and English dictionary files have identical structure and parallel keys for all affected strings.

---

## 3. Assumptions (Inferred)

- **Inferred:** The container for `FeatureVisual` renders at `min-h-[120px]` with `overflow-hidden`. The animation bounding box must be the inner dimensions of this container. The exact pixel size varies by viewport — the implementation must use `ResizeObserver` or equivalent to get runtime dimensions.
- **Inferred:** The `"report"` visual key in `featurePlaceholders[1]` is what will become the floating anamnéza animation. The key name `"report"` can remain (it is internal only) or be renamed to `"anamneза"` — either is acceptable.
- **Inferred:** The feature card at index 1 (`features.items[1]`) is the one whose visual should animate. The title currently says `"13 sekcí. Česká terminologie. Automaticky."` — TASK-0001 will update this title separately. This spec does not change dictionary content for items[1] except to note the overlap.
- **Inferred:** The workflow labels `"Nahrát"`, `"Stop"`, `"Kopírovat"` are hardcoded strings in the component (not in dictionaries). The new labels `"Odeslat e-mailem"` and `"Kopírovat"` will also be hardcoded for simplicity, since they are visual-only labels in a decorative diagram, not UI text that needs i18n. **Decision:** hardcode the new Czech labels; the English locale will show the same diagram with English labels — this must be verified. See Open Questions.
- **Inferred:** The animation should run continuously while the section is visible, regardless of scroll position beyond initial visibility.

---

## 4. Open Questions (Remaining)

1. **Language handling for workflow diagram labels:** The `FeatureVisual` component currently receives no `lang` or `dict` prop — it is hardcoded Czech. If English visitors should see English labels in the workflow diagram (`Send via email` / `Copy`), the component needs to receive a dictionary or lang prop. **Recommendation:** Pass the dict to `FeatureVisual` and read labels from the dictionary, or accept that this decorative diagram remains Czech-only for now. Resolve before implementing the diagram.

2. **Animation on mobile:** Should the floating animation run on narrow viewports (< 640px)? The container may be very short on mobile. **Recommendation:** Run the animation on all viewport sizes, but ensure a minimum container height of `160px` so chips have room to float. Disable collision detection on reduced-motion preference.

3. **`prefers-reduced-motion`:** Should the animation respect the OS accessibility setting? **Recommendation:** Yes — if `prefers-reduced-motion: reduce` is set, render chips statically without animation.

---

## 5. Sub-task A: Anamnéza Floating Chips Animation

### 5.1 Behavior Requirements

- The 5 anamnéza abbreviation chips (`NO`, `RA`, `OA`, `FA`, `AA`) float inside the `FeatureVisual` bounding container.
- Each chip moves continuously with a random initial velocity vector.
- On collision with a container wall, the velocity component perpendicular to that wall reverses (elastic bounce).
- On collision between two chips, velocities are exchanged along the collision axis (simplified elastic collision — same-mass approximation is acceptable for this decorative animation).
- The animation runs in a `requestAnimationFrame` loop.
- The animation pauses when the component is not visible (use `IntersectionObserver` or Framer Motion's `useInView`).
- The animation respects `prefers-reduced-motion` — if set, chips render statically at their initial positions.

### 5.2 Implementation Approach

**New file:** `src/components/animations/BouncingChips.tsx`

This is a self-contained client component. It:
1. Accepts a `chips: string[]` prop (the chip labels) and an optional `chipClassName` prop.
2. Uses a `useRef` on the container `<div>` to get bounding dimensions via `ResizeObserver`.
3. Maintains chip state as a `useRef` (not `useState`) for position and velocity — to avoid React re-render on every animation frame. Chip positions are written directly to DOM via `style.transform`.
4. Uses `requestAnimationFrame` via `useEffect` for the animation loop.
5. Each chip is a `<span>` with `position: absolute` styling.
6. Collision detection runs per-frame: wall bounces first, then pairwise chip-chip collision.

**Chip dimensions:** Each chip is approximately `32px × 24px` (estimated from the existing `px-2 py-0.5 text-xs` styling). The exact size is measured once on mount using `getBoundingClientRect()` on the chip refs.

**Initial positions:** Randomized within the container bounds, with a minimum separation of 1 chip-width to avoid overlap at start.

**Velocity:** Random direction, magnitude `0.6–1.2px per frame` (approximately 36–72px/s at 60fps). This gives slow, calm floating rather than fast chaotic motion.

**Container:** The outer `<div>` from `FeatureVisual` currently uses `min-h-[120px]`. For the animation to work, it should be `h-[160px]` (explicit height) to give a stable bounding box.

### 5.3 Simplified Physics

```
per frame:
  for each chip:
    pos.x += vel.x
    pos.y += vel.y
    if pos.x < 0 || pos.x > (containerW - chipW): vel.x *= -1
    if pos.y < 0 || pos.y > (containerH - chipH): vel.y *= -1

  for each pair (i, j):
    if overlap(chip_i, chip_j):
      swap vel.x components (simplified 1D collision along x-axis)
```

This is not physically precise, but is visually convincing and computationally O(n²) for n=5 chips (25 comparisons per frame — negligible).

### 5.4 Reduced Motion

```tsx
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (prefersReducedMotion) { /* render chips at static grid positions */ }
```

### 5.5 Pause When Off-Screen

Use Framer Motion's `useInView` hook to detect when the section enters/exits the viewport. When `inView === false`, cancel the `requestAnimationFrame` loop. Resume when `inView === true`.

### 5.6 Changes to `Features.tsx`

- Replace the `"report"` visual in `FeatureVisual` with `<BouncingChips chips={["NO", "RA", "OA", "FA", "AA"]} />`.
- Change the container height from `min-h-[120px]` to `min-h-[160px]` for the animation to have vertical room.
- Add `import { BouncingChips } from "@/components/animations/BouncingChips"`.

---

## 6. Sub-task B: Workflow Diagram Fork

### 6.1 Behavior Requirements

- The `"workflow"` visual in `FeatureVisual` is updated.
- The new layout shows:
  ```
  🔴 Nahrát  →  ⏹️ Stop  →⌐ Odeslat e-mailem (📧)
                           └→ Kopírovat (📋)
  ```
- The fork is represented by a single arrow from `Stop` that branches into two rows.
- Both branches are labeled clearly.
- The layout is mobile-friendly: on narrow viewports, the fork branches stack vertically.

### 6.2 Proposed JSX Structure

```tsx
workflow: (
  <div className="flex items-center justify-center gap-3 p-4 flex-wrap">
    {/* Step 1: Nahrát */}
    <div className="text-center">
      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-lg mx-auto mb-1">🔴</div>
      <span className="text-[10px] text-text-secondary">Nahrát</span>
    </div>

    {/* Arrow 1 */}
    <span className="text-primary/40 text-lg">→</span>

    {/* Step 2: Stop */}
    <div className="text-center">
      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-lg mx-auto mb-1">⏹️</div>
      <span className="text-[10px] text-text-secondary">Stop</span>
    </div>

    {/* Fork arrow + two branches */}
    <div className="flex flex-col items-start gap-2 ml-1">
      {/* Branch 1: Email */}
      <div className="flex items-center gap-2">
        <span className="text-primary/40 text-sm">→</span>
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-base">📧</div>
        <span className="text-[10px] text-text-secondary whitespace-nowrap">Odeslat e-mailem</span>
      </div>
      {/* Branch 2: Copy */}
      <div className="flex items-center gap-2">
        <span className="text-primary/40 text-sm">→</span>
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-base">📋</div>
        <span className="text-[10px] text-text-secondary">Kopírovat</span>
      </div>
    </div>
  </div>
)
```

This uses only existing Tailwind utility classes — no new CSS is needed.

### 6.3 Mobile Behavior

The outer `flex-wrap` allows the `Stop` step and the fork block to wrap to a new line on very narrow screens. Both branch labels use `whitespace-nowrap` where label length permits, and fall back to wrapping only at the text level. No media query breakpoints are needed — Tailwind flex wrapping handles this passively.

### 6.4 Language Note

The labels `Nahrát`, `Stop`, `Odeslat e-mailem`, `Kopírovat` are Czech. The same component renders for both `cs` and `en` locales. **If English localization is required**, the `FeatureVisual` component must receive a `lang` or `dict` prop and render locale-appropriate labels. For now, these are decorative diagram labels — they may remain Czech for both locales in the initial implementation, pending a decision on open question #1.

---

## 7. Sub-task C: String Removals — TASK-0001 Overlap

> **Coordination note:** The following strings are also targeted for removal/update by **TASK-0001**. To avoid duplicate work or merge conflicts, **string removals in the `features` section should be handled in one PR only** — either TASK-0001 or TASK-0003, not both.

### Strings overlapping between TASK-0001 and TASK-0003

| String | Location | Which task should own it |
|--------|----------|--------------------------|
| `"Hlas pacienta nikdy neopustí telefon"` | `cs.json` `features.items[2].title`, `en.json` equivalent | **TASK-0001** (it is a misleading claim requiring replacement copy) |
| `"funguje i bez internetu"` / `"Funguje i bez internetu"` | `cs.json` `features.items[3].title`, `hero.badges[3]` | **TASK-0001** (requires replacement copy per guidelines) |
| `"13 sekcí"` (in features item title) | `cs.json` `features.items[1].title` | **TASK-0001** (requires rewrite of the title) |

### Recommendation

**TASK-0003 does not need to touch `cs.json` or `en.json` at all** for these strings. The animation and diagram changes are purely in `Features.tsx` (component code). String cleanup is TASK-0001's responsibility.

TASK-0003 only needs to update `Features.tsx` JSX and add one new animation component. This eliminates the coordination risk entirely.

---

## 8. Affected Files

| File | Change | Sub-task |
|------|--------|----------|
| `src/components/animations/BouncingChips.tsx` | **New file** — floating chip animation component | A |
| `src/components/sections/Features.tsx` | Replace `"report"` visual with `<BouncingChips>`, update `"workflow"` visual JSX, update container height | A + B |
| `src/dictionaries/cs.json` | **None** — string changes owned by TASK-0001 | — |
| `src/dictionaries/en.json` | **None** — string changes owned by TASK-0001 | — |
| `src/app/globals.css` | No changes needed — animation uses JS, not CSS keyframes | — |

---

## 9. Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `requestAnimationFrame` loop continues running after unmount | Medium | Clear RAF handle in `useEffect` cleanup return |
| Chip positions escape container on resize | Medium | `ResizeObserver` callback re-clamps all chip positions to new bounds |
| Performance regression on low-end mobile | Low | 5 chips × O(n²)=25 comparisons per frame is negligible. Test on a mid-range Android device. |
| Chip text wraps inside chip on small font size | Low | Use `whitespace-nowrap` on chip `<span>` and size chip dimensions after mount |
| English locale shows Czech diagram labels | Low | Known limitation; document and decide via open question #1 |
| Merge conflict with TASK-0001 on dict files | None | TASK-0003 does not touch dict files |

---

## 10. Non-Goals

- This spec does not change any marketing copy or dictionary strings (delegated to TASK-0001).
- This spec does not redesign the Features section layout or card structure.
- This spec does not add physics-accurate multi-body collision. A simplified elastic model is sufficient.
- This spec does not require any new npm packages.

---

## 11. Validation Plan

| Check | Method |
|-------|--------|
| Animation runs on desktop Chrome/Firefox/Safari | Manual browser test |
| Animation pauses when section scrolled out of view | Manual scroll test, observe CPU with DevTools Performance tab |
| Animation stops on `prefers-reduced-motion: reduce` | Toggle in Chrome DevTools: Rendering > Emulate CSS media feature > prefers-reduced-motion |
| No chips escape container bounds at any viewport width | Resize browser window from 320px to 1440px while animation runs |
| Workflow diagram renders correctly at 320px viewport | Chrome DevTools Device toolbar, iPhone SE size |
| Both branches of fork are legible at 320px | Visual inspection |
| TypeScript build passes | `npx tsc --noEmit` |
| Production build succeeds | `npm run build` |
| No layout shift caused by animation | Lighthouse CLS score should remain 0 |

---

## 12. Rollback

- The animation component is additive (new file + change to one function in `Features.tsx`). To revert: delete `BouncingChips.tsx` and restore the `"report"` visual to the original static list in `Features.tsx`.
- The workflow diagram change is a self-contained JSX block within `FeatureVisual`. To revert: restore the original 3-step JSX array.
- No database changes, no API changes, no config changes — rollback is a single git revert.
