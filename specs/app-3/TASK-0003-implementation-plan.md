# Implementation Plan — TASK-0003
## Features Section: Anamnéza Floating Animation + Workflow Diagram Fork

> **Spec:** `specs/app-3/TASK-0003-spec.md`
> **App:** app-3 (ANOTE-web)
> **Repo:** `/Users/ivananikin/Documents/ANOTE-web`
> **Created:** 2026-04-20

---

## Prerequisites

Before starting:

- [ ] Resolve open question #1 from the spec: should the workflow diagram labels be localized for the English locale? **Default decision if not resolved:** Keep Czech labels for both locales in the initial implementation. Add a `// TODO: localize workflow diagram labels` comment in the code.
- [ ] Confirm TASK-0001 will handle all `cs.json` / `en.json` string changes. TASK-0003 touches **no dictionary files**.

---

## Execution Order

Work is split into two sequential phases. Each phase can be committed independently.

```
Phase 1: Workflow diagram fork (Sub-task B)
Phase 2: Anamnéza floating animation (Sub-task A)
```

Rationale: Phase 1 is a low-risk JSX change that can be deployed immediately. Phase 2 is more complex and should be developed and tested separately to isolate any regressions.

---

## Phase 1 — Workflow Diagram Fork

**Estimated effort:** ~30 minutes  
**Risk:** Low  
**Files changed:** `src/components/sections/Features.tsx` only

### Step 1.1 — Update the `workflow` visual in `FeatureVisual`

In `src/components/sections/Features.tsx`, locate the `workflow` key in the `visuals` record (lines 66–84) and replace it with the fork layout.

**Before:**
```tsx
workflow: (
  <div className="flex items-center justify-center gap-3 p-4">
    {[
      { icon: "🔴", label: "Nahrát" },
      { icon: "⏹️", label: "Stop" },
      { icon: "📋", label: "Kopírovat" },
    ].map((step, i) => (
      <div key={i} className="flex items-center gap-3">
        <div className="text-center">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-lg mx-auto mb-1">
            {step.icon}
          </div>
          <span className="text-[10px] text-text-secondary">{step.label}</span>
        </div>
        {i < 2 && <span className="text-primary/40 text-lg">→</span>}
      </div>
    ))}
  </div>
),
```

**After:**
```tsx
workflow: (
  // TODO: localize diagram labels for English locale
  <div className="flex items-center justify-center gap-2 p-4 flex-wrap">
    {/* Step 1 */}
    <div className="text-center">
      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-lg mx-auto mb-1">🔴</div>
      <span className="text-[10px] text-text-secondary">Nahrát</span>
    </div>

    <span className="text-primary/40 text-lg">→</span>

    {/* Step 2 */}
    <div className="text-center">
      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-lg mx-auto mb-1">⏹️</div>
      <span className="text-[10px] text-text-secondary">Stop</span>
    </div>

    {/* Fork: two branches */}
    <div className="flex flex-col items-start gap-2 ml-1">
      <div className="flex items-center gap-2">
        <span className="text-primary/40 text-sm leading-none">→</span>
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm">📧</div>
        <span className="text-[10px] text-text-secondary whitespace-nowrap">Odeslat e-mailem</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-primary/40 text-sm leading-none">→</span>
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm">📋</div>
        <span className="text-[10px] text-text-secondary whitespace-nowrap">Kopírovat</span>
      </div>
    </div>
  </div>
),
```

### Step 1.2 — Verify

- [ ] Run `npm run dev` locally
- [ ] Navigate to the homepage and scroll to `id="features"`
- [ ] Confirm the workflow card (last feature card) shows `Nahrát → Stop` then two branches: `📧 Odeslat e-mailem` and `📋 Kopírovat`
- [ ] Resize browser to 320px width — confirm both branches are readable
- [ ] Run `npx tsc --noEmit` — no type errors

### Step 1.3 — Commit

```
git add src/components/sections/Features.tsx
git commit -m "feat(features): update workflow diagram to fork — Odeslat e-mailem / Kopírovat"
```

---

## Phase 2 — Anamnéza Floating Chips Animation

**Estimated effort:** ~2–3 hours  
**Risk:** Medium  
**Files changed:**
- `src/components/animations/BouncingChips.tsx` (new)
- `src/components/sections/Features.tsx` (modify `"report"` visual + container height)

### Step 2.1 — Create `BouncingChips.tsx`

Create `src/components/animations/BouncingChips.tsx` with the following implementation:

```tsx
"use client";

import { useEffect, useRef } from "react";

interface ChipState {
  x: number;
  y: number;
  vx: number;
  vy: number;
  w: number;
  h: number;
}

interface BouncingChipsProps {
  chips: string[];
  chipClassName?: string;
}

export function BouncingChips({ chips, chipClassName = "" }: BouncingChipsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chipRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const stateRef = useRef<ChipState[]>([]);
  const rafRef = useRef<number>(0);
  const inViewRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Respect prefers-reduced-motion
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    // Measure chip sizes after first paint
    const chipEls = chipRefs.current.filter(Boolean) as HTMLSpanElement[];
    if (chipEls.length === 0) return;

    const containerW = container.clientWidth;
    const containerH = container.clientHeight;

    // Initialise state with random positions and velocities
    stateRef.current = chipEls.map((el) => {
      const w = el.offsetWidth || 40;
      const h = el.offsetHeight || 24;
      const speed = 0.6 + Math.random() * 0.6; // px/frame
      const angle = Math.random() * 2 * Math.PI;
      return {
        x: Math.random() * Math.max(1, containerW - w),
        y: Math.random() * Math.max(1, containerH - h),
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        w,
        h,
      };
    });

    // Apply initial positions
    stateRef.current.forEach((s, i) => {
      const el = chipEls[i];
      if (el) el.style.transform = `translate(${s.x}px, ${s.y}px)`;
    });

    let cW = containerW;
    let cH = containerH;

    // ResizeObserver to re-clamp on resize
    const ro = new ResizeObserver(([entry]) => {
      cW = entry.contentRect.width;
      cH = entry.contentRect.height;
      stateRef.current.forEach((s) => {
        s.x = Math.min(s.x, Math.max(0, cW - s.w));
        s.y = Math.min(s.y, Math.max(0, cH - s.h));
      });
    });
    ro.observe(container);

    // IntersectionObserver to pause when off-screen
    const io = new IntersectionObserver(
      ([entry]) => { inViewRef.current = entry.isIntersecting; },
      { threshold: 0.1 }
    );
    io.observe(container);

    function tick() {
      rafRef.current = requestAnimationFrame(tick);
      if (!inViewRef.current) return;

      const state = stateRef.current;
      const n = state.length;

      // Move and wall-bounce
      for (let i = 0; i < n; i++) {
        const s = state[i];
        s.x += s.vx;
        s.y += s.vy;
        if (s.x <= 0) { s.x = 0; s.vx = Math.abs(s.vx); }
        if (s.x >= cW - s.w) { s.x = cW - s.w; s.vx = -Math.abs(s.vx); }
        if (s.y <= 0) { s.y = 0; s.vy = Math.abs(s.vy); }
        if (s.y >= cH - s.h) { s.y = cH - s.h; s.vy = -Math.abs(s.vy); }
      }

      // Chip-chip collision (simplified: swap vx on overlap)
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          const a = state[i];
          const b = state[j];
          const overlapX = a.x < b.x + b.w && a.x + a.w > b.x;
          const overlapY = a.y < b.y + b.h && a.y + a.h > b.y;
          if (overlapX && overlapY) {
            // Swap velocity x-components to simulate bounce
            [a.vx, b.vx] = [b.vx, a.vx];
            [a.vy, b.vy] = [b.vy, a.vy];
            // Separate to avoid sticking
            const sepX = (a.w + b.w) / 2 - Math.abs(a.x - b.x + (a.w - b.w) / 2);
            const sepY = (a.h + b.h) / 2 - Math.abs(a.y - b.y + (a.h - b.h) / 2);
            if (sepX < sepY) {
              if (a.x < b.x) { a.x -= sepX / 2; b.x += sepX / 2; }
              else { a.x += sepX / 2; b.x -= sepX / 2; }
            } else {
              if (a.y < b.y) { a.y -= sepY / 2; b.y += sepY / 2; }
              else { a.y += sepY / 2; b.y -= sepY / 2; }
            }
          }
        }
      }

      // Write positions to DOM
      for (let i = 0; i < n; i++) {
        const el = chipEls[i];
        if (el) el.style.transform = `translate(${state[i].x}px, ${state[i].y}px)`;
      }
    }

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      io.disconnect();
    };
  }, [chips]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden"
      aria-hidden="true"
    >
      {chips.map((label, i) => (
        <span
          key={label}
          ref={(el) => { chipRefs.current[i] = el; }}
          className={`absolute text-xs font-bold text-primary bg-primary/10 rounded px-2 py-0.5 whitespace-nowrap select-none ${chipClassName}`}
          style={{ top: 0, left: 0 }}
        >
          {label}
        </span>
      ))}
    </div>
  );
}
```

**Key implementation notes:**
- Positions are written directly to `el.style.transform` to bypass React's render cycle. This is intentional for performance.
- `aria-hidden="true"` — the animation is decorative and should not be read by screen readers.
- The `useEffect` dependency is `[chips]` — the animation reinitialises only if the chip list changes (it won't in this use case).

### Step 2.2 — Update `Features.tsx`

1. Add the import:
   ```tsx
   import { BouncingChips } from "@/components/animations/BouncingChips";
   ```

2. Replace the `"report"` visual in `FeatureVisual`:

   **Before:**
   ```tsx
   report: (
     <div className="space-y-3 p-4">
       {["NO", "RA", "OA", "FA", "AA"].map((s) => (
         <div key={s} className="flex items-center gap-3">
           <span className="text-xs font-bold text-primary bg-primary/10 rounded px-2 py-0.5">{s}</span>
           <div className="flex-1 h-2 bg-text-primary/5 rounded" />
         </div>
       ))}
     </div>
   ),
   ```

   **After:**
   ```tsx
   report: (
     <div className="w-full h-full min-h-[160px] p-2">
       <BouncingChips chips={["NO", "RA", "OA", "FA", "AA"]} />
     </div>
   ),
   ```

3. Update the outer container in the return of `FeatureVisual`:

   **Before:**
   ```tsx
   <div className="rounded-2xl bg-background border border-border overflow-hidden min-h-[120px] flex items-center justify-center">
   ```

   **After:**
   ```tsx
   <div className="rounded-2xl bg-background border border-border overflow-hidden min-h-[160px] flex items-center justify-center">
   ```

   > Note: This affects the height of **all** feature visuals, not just the anamnéza one. Verify the other visuals still look good at the taller height. If needed, apply the height increase only to the `report` visual's wrapper div rather than the shared outer container.

### Step 2.3 — Verify

- [ ] Run `npm run dev`
- [ ] Navigate to homepage, scroll to the anamnéza feature card (second feature item: "13 sekcí…")
- [ ] Confirm chips `NO`, `RA`, `OA`, `FA`, `AA` float and bounce inside the container
- [ ] Scroll the section out of view and back — confirm animation pauses/resumes
- [ ] Resize window to 320px — confirm chips remain inside the container bounds
- [ ] In Chrome DevTools > Rendering > "Emulate CSS media feature prefers-reduced-motion: reduce" — confirm chips render statically
- [ ] Open DevTools Performance tab, record for 5 seconds while animation runs — confirm CPU usage is minimal (< 5% on a modern laptop)
- [ ] Check all other feature visuals still render correctly (transcript, privacy, offline, templates, workflow)
- [ ] Run `npx tsc --noEmit`
- [ ] Run `npm run build`

### Step 2.4 — Commit

```
git add src/components/animations/BouncingChips.tsx src/components/sections/Features.tsx
git commit -m "feat(features): add floating bouncing chips animation to anamnéza visual"
```

---

## Suggested PR Description

```
feat(TASK-0003): Features section — anamnéza animation + workflow diagram fork

## Changes
- New component: `BouncingChips` — physics-based floating chip animation using rAF
  - 5 anamnéza chips (NO, RA, OA, FA, AA) float and bounce within container
  - Pauses when off-screen (IntersectionObserver)
  - Respects prefers-reduced-motion
  - Recalculates on resize (ResizeObserver)
- Updated workflow diagram: `Nahrát → Stop → [Odeslat e-mailem / Kopírovat]`
  - Simple fork arrow design, mobile-friendly flex layout

## Not changed
- No dictionary files modified (string updates are in TASK-0001)
- No new npm packages added

## Open question
- Workflow diagram labels are currently Czech-only for both locales.
  See: TODO comment in Features.tsx. Resolve when English locale is prioritised.
```

---

## Coordination Notes

| Item | Note |
|------|------|
| **TASK-0001 overlap** | TASK-0003 does **not** modify `cs.json` or `en.json`. All string removals for `features.items[1..3]` are TASK-0001's responsibility. No coordination required beyond sequencing — TASK-0001 and TASK-0003 can be developed in parallel since they touch different files. |
| **Merge order** | Either task can merge first. No shared file writes. |
| **Deployment** | Phase 1 (diagram fork) can be deployed independently. Phase 2 (animation) can follow. |
