# Implementation Plan: Filtered-Data Summary/Insights Panel

**Spec**: `specs/summary-panel.md`
**Created**: 2026-07-12
**Status**: approved

## Components

### 1. `utils.py` calculation functions
- **Purpose**: `calculate_price_change` and `find_region_extremes`, pure
  functions over the full dataset + filter params.
- **Files**: `src/utils.py`
- **Effort**: S

### 2. Summary panel builder + layout + callback
- **Purpose**: `create_summary_panel` builder, `summary-panel` container
  div in `app.layout`, `update_summary_panel` callback wiring filters to
  the panel.
- **Files**: `src/app.py`
- **Effort**: M

### 3. Styling
- **Purpose**: `.summary-panel` / `.summary-stat*` CSS rules.
- **Files**: `src/assets/style.css`
- **Effort**: XS

### 4. Tests
- **Purpose**: Cover all 5 Gherkin scenarios from issue #2 plus the
  `format_number` formatting table.
- **Files**: `tests/test_app.py`
- **Effort**: S

## Dependencies

### Build Order
1. `utils.py` functions (foundation, no Dash dependency, easiest to unit
   test in isolation)
2. `create_summary_panel` builder (depends on 1)
3. Layout + callback wiring (depends on 2)
4. CSS (independent, can happen alongside 2/3)
5. Tests (written alongside each step, TDD)

### External Dependencies
None.

## Risks & Assumptions

### Risks
- **Risk**: "previous equal-length period" is ambiguous at the boundary
  (inclusive/exclusive day counting). Mitigated by defining it precisely:
  for an inclusive range `[start, end]` of `N` days, the previous period
  is the `N` days immediately before `start` (i.e. `[start - N days, start
  - 1 day]`), verified with an exact assertion in tests using a
  full-calendar-year fixture (2015 vs. 2014).
- **Risk**: Best/worst region ties (identical average price) — resolved
  by `pandas.Series.idxmax`/`idxmin`, which deterministically returns the
  first occurrence in sorted-by-groupby-key order. Not expected in this
  dataset; no special-cased tie-breaking added (YAGNI).

### Assumptions
- The "no data" scenario only needs to consider the primary region+type+
  date filter (matching how the existing three callbacks already treat
  empty `filtered_data`), not the auxiliary previous-period/cross-region
  queries, which already degrade gracefully (`None`) on their own.

## Milestones

- [ ] `calculate_price_change` / `find_region_extremes` unit-tested in
      isolation against hand-computed values.
- [ ] `create_summary_panel` renders correct KPIs for a known filter
      selection and the "no data" message for an empty one.
- [ ] Panel wired into `app.layout` + `update_summary_panel` callback,
      visually verified via `make run`.
- [ ] `poetry run pytest` / `make test` green, `make lint` /
      `make format-check` clean.

## Tasks

### Foundation
- [ ] **Task 1**: Add `calculate_price_change` and `find_region_extremes`
  to `src/utils.py`.
  - **Acceptance**: Both functions pass unit tests against hand-computed
    values; both return `None` on empty input.
  - **Files**: `src/utils.py`, `tests/test_app.py`
  - **Tests**: Direct calls with fixture date ranges.
  - **Effort**: S

### Features
- [ ] **Task 2**: Add `create_summary_panel` to `src/app.py`.
  - **Acceptance**: Returns stat cards for non-empty data, "no data"
    message for empty data; imports `calculate_summary_stats`,
    `format_number` from `utils`.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: Component-tree assertions for both branches.
  - **Effort**: M

### Integration
- [ ] **Task 3**: Wire `summary-panel` div + `update_summary_panel`
  callback into `app.layout`.
  - **Acceptance**: Panel updates on all 4 filter inputs; matches the
    try/except fallback pattern of the other 3 callbacks.
  - **Files**: `src/app.py`
  - **Tests**: Manual verification via `make run`.
  - **Effort**: S

### Polish
- [ ] **Task 4**: Style the panel.
  - **Files**: `src/assets/style.css`
  - **Effort**: XS

## Effort Estimate

**Total**: M (matches issue #2's own estimate)
