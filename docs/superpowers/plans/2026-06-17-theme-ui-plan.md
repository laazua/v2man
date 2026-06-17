# Theme + UI Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add dark/light mode toggle and modernize UI with glassmorphism cards, gradients, and smooth transitions.

**Architecture:** CSS custom properties on `:root`/`.light` class, global `theme.css` imported in `main.ts`, all components reference `var(--xxx)`.

**Tech Stack:** Vue 3, CSS custom properties, `prefers-color-scheme` media query

## Global Constraints

- All color values must use CSS variables from `theme.css`
- Theme toggle button in AppLayout header with localStorage persistence
- Users can override system preference manually
- One source of truth for all colors: `theme.css`

---

### Task 1: Create global theme.css

**Files:**
- Create: `web/src/assets/theme.css`

- [ ] Write `theme.css` with all CSS variables for both themes, global resets, transitions, scrollbar styles, and backdrop-filter utility. See design doc for exact variable values.

### Task 2: Import theme.css in main.ts

**Files:**
- Modify: `web/src/main.ts`

- [ ] Add `import './assets/theme.css'`

### Task 3: Update AppLayout.vue with theme toggle

**Files:**
- Modify: `web/src/views/AppLayout.vue`

- [ ] Add theme toggle button in header (sun/moon icons)
- [ ] On mount: check localStorage → system preference → default dark
- [ ] Toggle: switch `.light` class on `document.documentElement`, save to localStorage
- [ ] Replace hardcoded colors with CSS variables

### Task 4-N: Update each page component

**Files:** Modify all 10 view components

- [ ] Update each file: replace all hardcoded color values with `var(--xxx)` equivalents
- [ ] Apply glassmorphism card styles (backdrop-filter, border-radius 12px)
- [ ] Apply gradient progress bars and active nav items
- [ ] Add hover transitions on cards and buttons

### Task 5: Verify build

- [ ] Run `npm run build` and fix any issues
