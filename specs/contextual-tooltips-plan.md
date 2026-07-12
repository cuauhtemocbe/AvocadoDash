# Implementation Plan: Contextual Tooltips on Dashboard Controls

**Spec**: `specs/contextual-tooltips.md`
**Created**: 2026-07-11
**Status**: draft

## Components

### 1. Tooltip text constants
- **Purpose**: Static dicts mapping control labels and metric column names to
  short definition strings.
- **Files**: `src/app.py` (near existing `numeric_columns` constant)
- **Effort**: XS

### 2. Wire tooltips into the layout
- **Purpose**: Pass `title=...` into the `menu-title` `html.Div`s, and add a
  `"title"` key to the option dicts for `x-axis-dropdown`, `y-axis-dropdown`,
  `box-plot-column`, and `box-plot-groupby`.
- **Files**: `src/app.py` (`app.layout`)
- **Effort**: S

### 3. Tests
- **Purpose**: Prop-level assertions on `app.layout` proving each tooltip is
  present and non-empty, and that dropdown options are otherwise unchanged.
- **Files**: `tests/test_app.py`
- **Effort**: S

## Dependencies

### Build Order
1. Tooltip text constants (foundation)
2. Wire into layout (depends on 1)
3. Tests (depends on 2; written first per TDD, see Tasks)

### External Dependencies
None.

## Risks & Assumptions

### Risks
- **Risk**: `app.layout` is a `Dash`/plain-Python component tree; walking it
  in tests requires knowing Dash's component API (`.children`, keyword
  props). Mitigated by targeting components directly by their existing
  `id`s via a small recursive finder helper in the test file, rather than
  hardcoding tree paths.

### Assumptions
- `dcc.Dropdown` option dicts support an optional `"title"` key rendered as
  the native HTML `title` attribute on that option — confirmed by Dash's
  component API (Dash ^3.2.0, already pinned).
- Native `title` tooltips satisfy the issue's intent ("tooltip explaining...
  is displayed") even though they are plain-text, delayed-by-OS tooltips
  rather than a styled popover. Flagged in the spec's Out of Scope.

## Milestones

- [ ] Tooltip constants added and reused (no duplication of text across
      filter tooltips vs. option tooltips).
- [ ] All filters/controls and dropdown options have `title` set.
- [ ] `poetry run pytest` green, `make lint` / `make format-check` clean.

## Tasks

### Foundation
- [ ] **Task 1**: Add `CONTROL_TOOLTIPS` and `COLUMN_TOOLTIPS` dicts to
  `src/app.py`
  - **Acceptance**: Dicts exist with an entry for every control label
    (Region, Type, Date Range, X-Axis Column, Y-Axis Column, Column to
    Analyze, Group By) and every value in `numeric_columns` plus the three
    `box-plot-groupby` options (type, region, year).
  - **Files**: `src/app.py`
  - **Tests**: covered by Task 3
  - **Effort**: XS

### Features
- [ ] **Task 2**: Apply tooltips in `app.layout`
  - **Acceptance**: Each `menu-title` div listed above renders with
    `title=CONTROL_TOOLTIPS[...]`; each option dict for
    `x-axis-dropdown`/`y-axis-dropdown`/`box-plot-column` includes
    `"title": COLUMN_TOOLTIPS[col]`; `box-plot-groupby` options include a
    `"title"` per option. No `label`/`value` pairs change.
  - **Files**: `src/app.py`
  - **Tests**: covered by Task 3
  - **Effort**: S

### Integration
- [ ] **Task 3**: Tests in `tests/test_app.py`
  - **Acceptance**: New tests fail before Task 1/2 and pass after; assert
    non-empty `title` on each of the 7 control labels (by component `id`)
    and on every option in the 4 dropdowns.
  - **Files**: `tests/test_app.py`
  - **Tests**: this task *is* the tests
  - **Effort**: S

## Effort Estimate

**Total Estimated**: well under 1 day (issue is tagged Effort: S)

| Phase | Effort |
|-------|--------|
| Foundation | XS |
| Features | S |
| Testing | S |
