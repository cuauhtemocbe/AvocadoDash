---
title: Accessibility & Dark Mode
status: draft
created: 2026-08-08
updated: 2026-08-08
issue: #44, #45, #51
---

# Accessibility & Dark Mode

## Objective

Remediate the addressable WCAG 2.1 AA accessibility gaps in the dashboard's
color tokens and keyboard reachability, then add a persisted dark mode
toggle covering both page chrome (CSS) and chart colors (Plotly figure
dicts), and re-validate the region/type chart palette for contrast and
color-vision-deficiency (CVD) distinctness against the new dark background.

## Context

This spec covers GitHub milestone **"Accessibility & Dark Mode"**
(milestone #2), scoped to issues **#44**, **#45**, **#51** — in that
sequence, per each issue's own stated dependency. Issue **#50** (manual
NVDA/VoiceOver screen-reader walkthrough) is explicitly **out of scope**
for this spec/PR: it requires a human to actually run a screen reader,
which this implementation pass cannot do; it stays open as a separate
issue.

Scope decision on #44's axe-core scenario (confirmed with the user): Dash
renders entirely client-side via React, so axe-core requires a real
browser (Selenium/`dash[testing]`) to have anything to scan — there is no
way to satisfy that Gherkin scenario statically. Rather than pull the E2E
Selenium infrastructure (issue #42, milestone "E2E Test Coverage") into
this smaller milestone, that scenario is **deferred and documented as
blocked on #42**. Everything else in #44 that *is* addressable from
`app.py`/`style.css` alone ships now.

## Requirements

### Functional Requirements

- [ ] Every currently-used text/background color pairing in
      `src/assets/style.css` meets or exceeds 4.5:1 contrast (WCAG AA for
      normal-size text). Audited by computing WCAG relative luminance for
      each pairing actually used in the layout (see Architecture →
      Contrast Audit below for the concrete findings and fixes).
- [ ] All interactive filter controls (region, type, date range, language
      toggle, and the new theme toggle) remain reachable via keyboard in
      logical (DOM source) order — verified by asserting no positive/
      overriding `tabIndex` is set anywhere in `app.layout` (Dash's
      default DOM order already matches visual order; the risk is a
      future explicit `tabIndex` breaking that, not the current absence
      of one).
- [ ] The header's Cross-Section Mark decorative image is not announced
      by assistive technology (`alt=""`) — already true in the current
      code; locked in with an explicit regression test.
- [ ] axe-core automated scan scenario: **deferred**, documented in this
      spec and in issue #44 as blocked on #42 landing.
- [ ] A dark mode toggle switches both page chrome (CSS custom
      properties) and all four chart types (price, volume, scatter, box
      plot) between light/dark palettes.
- [ ] Theme precedence: an explicit user choice (persisted in
      `dcc.Store(storage_type="local")`) always wins; the OS/browser
      `prefers-color-scheme` is used only when no explicit choice has
      been stored yet.
- [ ] Theme choice persists across page reloads without re-checking the
      OS preference once an explicit choice exists.
- [ ] The region color palette (`REGION_COLOR_PALETTE`) and type palette
      (`TYPE_COLOR_MAP`) are re-validated for contrast against the new
      dark chart background and for CVD-distinctness, using the same
      `/dataviz`-skill method already used for the light-mode palette
      (documented in the `src/app.py` comment above
      `REGION_COLOR_PALETTE`).

### Non-Functional Requirements

- [ ] Accessibility: WCAG 2.1 AA contrast (4.5:1) for all *currently
      used* color pairings — not hypothetical/unused pairings.
- [ ] No regression: existing light-mode tests, translations, and the
      `/dataviz`-validated light-mode palette stay unchanged and passing.
- [ ] Consistency: theme threading follows the exact same parameter-
      passing pattern already used for `lang: str = "en"` through the 4
      chart builders and 3 callbacks (`app.py`'s established convention
      — see CLAUDE.md's Architecture section).

## Architecture

### Contrast Audit (computed via WCAG relative-luminance formula against
the actual hex values in `style.css`, current pairings only)

| Pairing (element) | Ratio | AA (4.5:1)? | Fix |
|---|---|---|---|
| `--pit` text on `--parchment` (`.menu-title`) | 5.18 | Pass | none |
| `--flesh` text on `#FFFFFF` (`.summary-stat-up`) | 3.59 | **Fail** | new darker green `#5C7A2E` (4.91:1), used only for this class — `--flesh` itself is unchanged since it already passes everywhere else it's used (on `--ink`) |
| `--pit` text on `--ink` (`.header-link:hover`, `.footer-link:hover`) | 3.03 | **Fail** | new warm tan `#C99B5E` (7.01:1) for the `:hover` state only |
| `ink @ 60% opacity` on `--parchment` (`.download-status`) | 4.45 | **Fail** (marginal) | bump opacity 0.6 → 0.65 (5.23:1) |
| `ink @ 60% opacity` on `#FFFFFF` (`.summary-stat-label`, `.summary-empty`) | 4.64 | Pass | none |
| `--bruise` text on `#FFFFFF` (`.summary-stat-down`) | 5.55 | Pass | none |

`--bruise` on `--ink` was checked and is not actually used anywhere in
the current CSS (only `--pit`/`--flesh` appear on the `--ink` background)
— not included as a fix target, per this repo's "don't validate scenarios
that can't happen" principle.

### Dark Mode Theming

- **Page chrome**: a `[data-theme="dark"]` attribute on `<html>` (or a
  wrapping element) redefines the existing `:root` custom properties
  (`--ink`, `--parchment`, `--flesh`, `--pit`, `--bruise`, `--cream-text`)
  for dark mode, plus a `@media (prefers-color-scheme: dark)` fallback
  block guarded so an explicit `data-theme="light"` can still override it
  (same pattern documented in this environment's artifact-design
  conventions, applied here to the app's own CSS).
- **Chart colors**: `CHART_BG`, `CHART_GRIDCOLOR` become theme-dependent;
  `TYPE_COLOR_MAP` and `REGION_COLOR_PALETTE` get a dark-mode variant
  (from the #51 re-validation). A `theme: str = "light"` parameter is
  threaded through `create_price_chart`, `create_volume_chart`,
  `create_box_plot`, `create_scatter_chart`, and the 3 chart callbacks —
  identical shape to the existing `lang` parameter threading.
- **Theme detection & persistence**:
  - `dcc.Store(id="theme-store", storage_type="local")` holds the
    explicit user choice (`"light"` / `"dark"` / unset).
  - A clientside callback (`app.clientside_callback`, this repo's first)
    reads `window.matchMedia("(prefers-color-scheme: dark)")` once, on
    load, to seed the *initial* render only when `theme-store` is empty.
  - A `dcc.RadioItems`/toggle control (same pattern as
    `language-toggle`) lets the user set an explicit choice, which
    always overrides OS preference from then on.
  - Setting `data-theme` on the root element (for CSS) is also done via
    a small clientside callback, since Dash server-side callbacks can't
    set attributes on elements outside `app.layout`'s own tree (`<html>`
    itself).

### Palette Re-validation (#51)

Rerun the same `/dataviz`-skill CVD-simulation + contrast method
documented in the `src/app.py` comment above `REGION_COLOR_PALETTE`,
against the new dark chart background instead of `--parchment`. Produces
a `REGION_COLOR_PALETTE_DARK` / `TYPE_COLOR_MAP_DARK` (or adjusted
in-place values, whichever the validation determines) with the same
worst-adjacent-CVD-ΔE bar as the light palette (≥24.2, the value recorded
for the current light palette).

## User Stories

Embedded from the existing GitHub issues (already INVEST/Gherkin-complete,
not rewritten here):
- #44 — Remediate accessibility findings for WCAG AA compliance
- #45 — Add a dark mode toggle
- #51 — Re-validate chart color palette for dark-mode contrast

## Testing Strategy

### Unit Tests
- Pure contrast-ratio assertions for each fixed pairing (can hardcode the
  computed ratios as a regression guard, similar to existing
  `test_style.py` patterns).
- `theme` parameter threading: each `create_*_chart` function returns
  dark-appropriate `CHART_BG`/colors when `theme="dark"`, light when
  `theme="light"`/default — mirrors existing `lang` parameter tests.
- `decode`/`encode` or store-read helpers for theme precedence (explicit
  store value wins; falls back to OS preference only when unset) —
  tested as pure Python logic, not through the clientside JS itself.
- No-positive-`tabIndex` assertion over the full `app.layout` tree.
- Regression test: header mark image has `alt=""`.

### Integration Tests
- Callback-level tests (existing `test_app.py` pattern) verifying
  `update_charts`/`update_scatter_chart`/`update_box_plot` accept and
  honor a `theme` input the same way they already honor `lang`.

### E2E Tests
- Out of scope here (clientside `matchMedia`/`localStorage` behavior
  requires a real browser — same infra gap as the deferred axe-core
  scenario). Left for the separate E2E milestone.

## Boundaries & Constraints

### In Scope
- #44 (minus the axe-core browser scenario)
- #45 (dark mode toggle, page chrome + charts, OS-preference detection,
  persistence, precedence)
- #51 (dark-mode palette re-validation)

### Out of Scope
- #50 (manual screen-reader walkthrough) — separate issue, needs a human
- axe-core / Lighthouse automated browser scans — blocked on #42
  (E2E Test Coverage milestone), documented as a known gap
- Literal Tab-key-press E2E simulation — same reason
- Any UI redesign beyond what dark mode requires

### Technical Constraints
- Must reuse the existing `lang`-threading pattern for `theme` (per
  CLAUDE.md's architecture guidance: keep the flat, single-module,
  pure-function style — no new abstraction layers).
- First clientside callback in this codebase — keep it minimal (theme
  detection + `data-theme` attribute set only), not a broader JS
  introduction.
- `poetry.lock`/`pyproject.toml` unaffected — no new runtime
  dependencies needed (no Selenium/dash[testing] in this scope).

## Success Criteria

- [ ] All contrast-audit fixes applied and covered by regression tests
- [ ] Keyboard-reachability and decorative-image tests pass
- [ ] axe-core scenario documented as deferred/blocked in issue #44
- [ ] Dark mode toggle works: OS-preference default, explicit override,
      persistence across reload, charts + chrome both re-theme
- [ ] Dark-mode palette re-validated with CVD ΔE ≥ 24.2 and contrast
      parity with the light-mode bar
- [ ] `make lint`, `make format-check`, `make test` (≥80% coverage) all
      green
- [ ] PR opened against the milestone, referencing #44, #45, #51

## Implementation Plan

See `specs/accessibility-dark-mode-plan.md`.
