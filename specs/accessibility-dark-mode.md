---
title: Dark Mode
status: draft
created: 2026-08-08
updated: 2026-10-03
issue: #45, #51
---

# Dark Mode

> The file keeps its original name (`accessibility-dark-mode.md`) so existing
> links stay valid. Accessibility work (#44, #50 and the a11y parts of #51)
> was dropped from the project on 2026-10-03 (issue #89): this spec now
> covers only the dark mode toggle.

## Objective

Add a persisted dark mode toggle covering both page chrome (CSS) and chart
colors (Plotly figure dicts), and re-validate the region/type chart palette
for color-vision-deficiency (CVD) distinctness against the new dark
background.

## Context

Dark mode is issue **#45**, with the chart palette re-validation in **#51**.
The color values introduced while auditing contrast for #44 are shared by
light and dark mode and stay as they are.

## Requirements

### Functional Requirements

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
      (`TYPE_COLOR_MAP`) are re-validated against the new dark chart
      background and for CVD-distinctness, using the same `/dataviz`-skill
      method already used for the light-mode palette (documented in the
      `src/app.py` comment above `REGION_COLOR_PALETTE`).

### Non-Functional Requirements

- [ ] No regression: existing light-mode tests, translations, and the
      `/dataviz`-validated light-mode palette stay unchanged and passing.
- [ ] Consistency: theme threading follows the exact same parameter-
      passing pattern already used for `lang: str = "en"` through the 4
      chart builders and 3 callbacks (`app.py`'s established convention
      — see CLAUDE.md's Architecture section).

## Architecture

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
- #45 — Add a dark mode toggle
- #51 — Re-validate chart color palette for dark-mode contrast

## Testing Strategy

### Unit Tests
- `theme` parameter threading: each `create_*_chart` function returns
  dark-appropriate `CHART_BG`/colors when `theme="dark"`, light when
  `theme="light"`/default — mirrors existing `lang` parameter tests.
- `decode`/`encode` or store-read helpers for theme precedence (explicit
  store value wins; falls back to OS preference only when unset) —
  tested as pure Python logic, not through the clientside JS itself.

### Integration Tests
- Callback-level tests (existing `test_app.py` pattern) verifying
  `update_charts`/`update_scatter_chart`/`update_box_plot` accept and
  honor a `theme` input the same way they already honor `lang`.

### E2E Tests
- Out of scope here (clientside `matchMedia`/`localStorage` behavior
  requires a real browser). Left for the separate E2E milestone.

## Boundaries & Constraints

### In Scope
- #45 (dark mode toggle, page chrome + charts, OS-preference detection,
  persistence, precedence)
- #51 (dark-mode palette re-validation)

### Out of Scope
- Accessibility work (WCAG remediation, screen-reader and keyboard
  support): not a goal of this project (issue #89)
- Any UI redesign beyond what dark mode requires

### Technical Constraints
- Must reuse the existing `lang`-threading pattern for `theme` (per
  CLAUDE.md's architecture guidance: keep the flat, single-module,
  pure-function style — no new abstraction layers).
- First clientside callback in this codebase — keep it minimal (theme
  detection + `data-theme` attribute set only), not a broader JS
  introduction.
- `poetry.lock`/`pyproject.toml` unaffected — no new runtime
  dependencies needed.

## Success Criteria

- [ ] Dark mode toggle works: OS-preference default, explicit override,
      persistence across reload, charts + chrome both re-theme
- [ ] Dark-mode palette re-validated with CVD ΔE ≥ 24.2
- [ ] `make lint`, `make format-check`, `make test` (≥80% coverage) all
      green
- [ ] PR references #45 and #51

## Implementation Plan

See `specs/accessibility-dark-mode-plan.md`.
