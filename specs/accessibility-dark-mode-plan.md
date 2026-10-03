# Implementation Plan: Dark Mode

**Spec**: `specs/accessibility-dark-mode.md`
**Created**: 2026-08-08
**Updated**: 2026-10-03
**Status**: draft

> The accessibility components (#44 contrast fixes, keyboard/decorative-image
> tests, axe-core note) were removed from this plan on 2026-10-03 (issue #89):
> accessibility is not a goal of the project. Component and task numbers
> below are the original ones, so gaps are expected.

## Components

### 4. Dark-mode CSS tokens (#45)
- **Purpose**: Add `[data-theme="dark"]` and
  `@media (prefers-color-scheme: dark)`-guarded redefinitions of the
  `:root` custom properties in `style.css`, following this
  environment's light/dark token-swap convention (define light on bare
  `:root`, redefine under the media query guarded by
  `:not([data-theme="light"])`, redefine again under
  `[data-theme="dark"]` so an explicit toggle always wins).
- **Files**: `src/assets/style.css`
- **Effort**: S

### 5. Theme store + toggle control + clientside callbacks (#45)
- **Purpose**: Add `dcc.Store(id="theme-store", storage_type="local")`,
  a theme toggle control (same shape as `language-toggle`), and two
  small clientside callbacks: (a) seed `theme-store` from
  `prefers-color-scheme` only when empty, on load; (b) mirror
  `theme-store`'s value onto a `data-theme` attribute on the app's root
  element.
- **Files**: `src/app.py`
- **Effort**: M (first clientside callback in this codebase)

### 6. Thread `theme` through chart builders + callbacks (#45)
- **Purpose**: Add `theme: str = "light"` to `create_price_chart`,
  `create_volume_chart`, `create_box_plot`, `create_scatter_chart`, and
  wire `theme-store` as an `Input` to `update_charts`,
  `update_scatter_chart`, `update_box_plot` — identical shape to the
  existing `lang` threading.
- **Files**: `src/app.py`
- **Effort**: M

### 7. Palette re-validation for dark mode (#51)
- **Purpose**: Rerun the `/dataviz`-skill CVD-simulation + contrast
  check against the new dark chart background; produce
  dark-mode-specific `REGION_COLOR_PALETTE`/`TYPE_COLOR_MAP` values (or
  confirm the existing hues already clear the bar unchanged — either
  outcome is a valid result of "re-validate").
- **Files**: `src/app.py`
- **Effort**: S–M (depends on whether the existing hues need adjustment)

### 8. Tests for theme threading + palette validation
- **Purpose**: Cover chart-builder theme branching, callback `theme`
  input wiring, theme-precedence logic, and a regression test recording
  the dark-mode CVD ΔE result (mirrors the existing light-mode palette
  comment/test pattern).
- **Files**: `tests/test_app.py`
- **Effort**: S

## Dependencies

### Build Order
3. Component 4 (dark CSS tokens)
4. Component 5 (store/toggle/clientside) — depends on 4
5. Component 6 (theme threading through charts) — depends on 5
6. Component 7 (#51 palette re-validation) — depends on 6 (needs the
   actual dark `CHART_BG` to validate against)
7. Component 8 (tests) — alongside 4–7, not strictly after

### External Dependencies
None new — no additional Poetry packages required.

## Risks & Assumptions

### Risks
- **Clientside callback correctness without a browser**: this repo has
  no Selenium/E2E infra yet, so the `matchMedia`/`localStorage`
  clientside callback can only be verified by manual `make run` browser
  testing, not an automated test. Mitigation: keep the JS minimal (≤10
  lines per callback), test the Python-side precedence logic separately
  as pure functions, and manually verify in-browser before opening the
  PR.

### Assumptions
- The existing `REGION_COLOR_PALETTE` hues may or may not need
  adjustment for the dark background — validated empirically in
  component 7, not assumed upfront either way.

## Milestones

- [ ] M2: Dark mode toggle functional in `make run` (manual browser
      check) — chrome + all 4 charts re-theme, persists across reload,
      explicit choice overrides OS preference
- [ ] M3: #51 palette re-validated, ΔE/contrast bar met or adjusted
      palette committed
- [ ] M4: `make lint` / `make format-check` / `make test` (≥80% cov) all
      green
- [ ] M5: PR opened, issues #45/#51 linked

## Tasks

### Features
- [ ] **Task 3**: Add dark-mode CSS custom-property overrides
  - **Acceptance**: `[data-theme="dark"]` and guarded
    `prefers-color-scheme` block both redefine all 6 tokens; explicit
    `data-theme="light"` still wins over OS dark preference
  - **Files**: `src/assets/style.css`
  - **Tests**: manual browser check (CSS-only, no automated DOM test
    infra in this repo)
  - **Effort**: S

- [ ] **Task 4**: Add `theme-store`, toggle control, and clientside
      callbacks
  - **Acceptance**: store persists via `localStorage`; explicit choice
    always wins; OS preference seeds only when store is empty;
    `data-theme` attribute reflects the resolved theme
  - **Files**: `src/app.py`
  - **Tests**: pure-function precedence tests (Python side); manual
    browser check (JS side)
  - **Effort**: M

- [ ] **Task 5**: Thread `theme` through chart builders and callbacks
  - **Acceptance**: all 4 `create_*_chart` functions and all 3 chart
    callbacks accept/honor `theme`, mirroring the `lang` pattern exactly
  - **Files**: `src/app.py`
  - **Tests**: `tests/test_app.py` — theme branch coverage per chart
    builder and per callback
  - **Effort**: M

### Integration
- [ ] **Task 6**: Re-validate `REGION_COLOR_PALETTE`/`TYPE_COLOR_MAP` for
      dark mode
  - **Acceptance**: CVD ΔE and contrast bar recorded, matching or
    exceeding the light-mode bar (≥24.2 ΔE); values (adjusted or
    confirmed unchanged) committed with an explanatory comment
  - **Files**: `src/app.py`
  - **Tests**: regression test recording the computed dark-mode ΔE,
    same style as the existing light-mode comment
  - **Effort**: S–M

### Polish
- [ ] **Task 7**: Full quality gate + manual dark-mode browser walkthrough
  - **Acceptance**: `make lint`, `make format-check`, `make test`
    (≥80% cov) green; manual `make run` check of toggle/persistence/
    OS-preference/all 4 charts in both themes
  - **Files**: n/a
  - **Tests**: n/a (verification step)
  - **Effort**: XS

- [ ] **Task 8**: Open PR against the milestone
  - **Acceptance**: PR references #45, #51
  - **Files**: n/a
  - **Effort**: XS

## Effort Estimate

**Total Estimated**: ~1 focused implementation session (M-and-under
tasks, no new infra/dependencies)

| Phase | Effort |
|-------|--------|
| Features (#45) | S + M + M |
| Integration (#51) | S–M |
| Polish | XS + XS |
