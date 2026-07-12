# Implementation Plan: Support Comparing Multiple Regions at Once

**Spec**: `specs/multi-region-comparison.md`
**Created**: 2026-07-12
**Status**: completed

## Components

### 1. Shared filtering/empty-state helpers
- **Purpose**: `filter_data(regions, avocado_type, start_date, end_date)`
  and `empty_state_figure(message)` in `src/app.py`, plus the
  `EMPTY_REGION_MESSAGE` constant. These replace the query string and
  empty-figure dict currently duplicated across the six callbacks, so the
  `region` → `regions` change is made once instead of six times.
- **Files**: `src/app.py`
- **Effort**: S

### 2. `region-filter` layout
- **Purpose**: `dcc.Dropdown(id="region-filter", multi=True, value=["Albany"])`.
- **Files**: `src/app.py`
- **Effort**: XS

### 3. `calculate_price_change` (multi-region)
- **Purpose**: Accept `regions` (list) instead of `region`, query with
  `region in @regions` for both current and previous period slices.
- **Files**: `src/utils.py`
- **Effort**: S

### 4. Price/volume chart builders
- **Purpose**: `create_price_chart` / `create_volume_chart` emit one trace
  per region instead of assuming a single implicit region; extend
  `colorway` to a qualitative palette (via `/dataviz` skill) and reuse the
  `show_legend = len(traces) > 1` pattern from `create_box_plot`.
- **Files**: `src/app.py`
- **Effort**: M

### 5. Callback migration (all six)
- **Purpose**: `update_summary_panel`, `update_download_controls`,
  `download_filtered_csv`, `update_charts`, `update_scatter_chart`,
  `update_box_plot` — rename `region` param to `regions`, add the
  `if not regions:` empty-region branch, switch to `filter_data`.
- **Files**: `src/app.py`
- **Effort**: M

### 6. Styling check
- **Purpose**: Verify the multi-select dropdown's chip rendering fits the
  existing visual language; add CSS only if needed.
- **Files**: `src/assets/style.css`
- **Effort**: XS

### 7. Tests
- **Purpose**: Cover all 3 Gherkin scenarios from issue #7, plus
  regression coverage for every touched callback/helper.
- **Files**: `tests/test_app.py`
- **Effort**: L

## Dependencies

### Build Order
1. Shared helpers (`filter_data`, `empty_state_figure`,
   `EMPTY_REGION_MESSAGE`) — everything else calls these.
2. `region-filter` layout (`multi=True`, list default) — callbacks assume
   `value` is now a list.
3. `calculate_price_change` multi-region signature — needed before
   `update_summary_panel` can be migrated.
4. Price/volume chart builders (`create_price_chart`/`create_volume_chart`)
   — needed before `update_charts` can be migrated.
5. Callback migration (all six), each paired with its tests (TDD, one
   callback at a time — order within this step doesn't matter, they don't
   depend on each other).
6. Styling check (independent, can happen alongside step 5 once the
   dropdown renders with `multi=True`).

### External Dependencies
None.

## Risks & Assumptions

### Risks
- **Risk**: Introducing `filter_data`/`empty_state_figure` mid-refactor
  touches every callback at once, so a mistake in the helper breaks all
  six call sites simultaneously instead of one. Mitigated by writing the
  helpers' own unit tests first (single-region case must reproduce
  today's exact query results) before migrating any callback.
- **Risk**: `dcc.Dropdown(multi=True)` changes the shape of
  `Input("region-filter", "value")` from `str` to `list[str]` — any test
  fixture or manual QA step still passing a bare string will silently
  break `region in @regions` (a string is iterable, so `"Albany" in
  "Albany"` type bugs could pass accidentally if not careful). Mitigated
  by using `.isin()`/`in @regions` only against an explicit `list`, and by
  every test fixture passing `regions=[...]` explicitly.
- **Risk**: Extending the price/volume chart `colorway` to more colors
  could clash with the box/scatter charts' existing
  conventional/organic color mapping (`#17B897`/`#E12D39`) if reused
  carelessly. Mitigated by picking the new multi-region palette with the
  `/dataviz` skill during implementation, scoped to price/volume charts
  only.

### Assumptions
- No region names collide with reserved pandas `query()` syntax (existing
  single-region behavior already relies on this).
- The dataset's ~50 regions are few enough that no dropdown
  virtualization/performance work is needed for `multi=True`.

## Milestones

- [x] `filter_data`/`empty_state_figure` unit-tested and match today's
      single-region query results exactly.
- [x] `region-filter` renders as multi-select, default `["Albany"]`,
      visually verified via `make run`.
- [x] Price and volume charts show one line per region, verified visually
      with 2+ regions selected.
- [x] Summary panel, scatter chart, box plot (`type`/`year` grouping), and
      CSV export all correctly reflect a multi-region selection.
- [x] Clearing all regions shows the "select at least one region" message
      everywhere instead of an error/generic empty state.
- [x] `poetry run pytest` / `make test` green, `make lint` /
      `make format-check` clean.

## Tasks

### Foundation
- [x] **Task 1**: Add `filter_data(regions, avocado_type, start_date,
  end_date)` helper.
  - **Acceptance**: For `regions=["Albany"]`, returns rows identical to
    today's `region == @region` query; for `regions=["Albany",
    "Chicago"]`, returns the union; for `regions=[]`, returns an empty
    DataFrame.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: Direct calls compared against `data.query("region ==
    'Albany' ...")` equivalents.
  - **Effort**: S
- [x] **Task 2**: Add `EMPTY_REGION_MESSAGE` constant and
  `empty_state_figure(message)` helper; refactor the existing
  `update_charts`/`update_scatter_chart`/`update_box_plot` empty-figure
  dicts to use it (message unchanged for the existing generic case).
  - **Acceptance**: Existing "no data available for selected filters"
    tests still pass unmodified.
  - **Files**: `src/app.py`
  - **Tests**: Existing empty-state tests act as regression coverage.
  - **Effort**: XS
- [x] **Task 3**: Change `region-filter` to `dcc.Dropdown(multi=True,
  value=["Albany"], clearable=True)`.
  - **Acceptance**: Layout test asserts `multi=True` and `value ==
    ["Albany"]`.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: `find_component_by_id("region-filter")` attribute checks.
  - **Effort**: XS

### Features
- [x] **Task 4**: Migrate `calculate_price_change` to `regions` (list).
  - **Acceptance**: Existing single-region test passes with
    `regions=["Albany"]`; new multi-region test's output matches a
    manually computed mean over the combined slices.
  - **Files**: `src/utils.py`, `tests/test_app.py`
  - **Tests**: Parametrized single- vs. multi-region cases.
  - **Effort**: S
- [x] **Task 5**: Update `create_price_chart`/`create_volume_chart` to
  emit one trace per region (name, hovertemplate, palette, conditional
  legend).
  - **Acceptance**: Single region → 1 trace (matches today's fixture
    output); 2+ regions → N traces, each scoped to its region's rows.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: Trace count/name/data assertions for 1- and 2-region cases.
  - **Effort**: M
- [x] **Task 6**: Migrate `update_charts` to `regions`, using
  `filter_data`/`empty_state_figure`/`EMPTY_REGION_MESSAGE`.
  - **Acceptance**: Scenario 1 and 2 from issue #7's Gherkin pass; empty
    `regions` shows the region-specific message.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: `regions=["Albany"]`, `regions=["Albany","Chicago"]`,
    `regions=[]`, exception-handling case.
  - **Effort**: S
- [x] **Task 7**: Migrate `update_summary_panel` (and
  `create_summary_panel`) to `regions`.
  - **Acceptance**: Avg Price/Total Volume aggregate across selected
    regions; Price Change uses the multi-region `calculate_price_change`;
    Best/Worst Region cards unchanged; empty `regions` shows the
    region-specific message.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: Single- and multi-region KPI assertions, empty-regions
    case.
  - **Effort**: S
- [x] **Task 8**: Migrate `update_scatter_chart` to `regions`.
  - **Acceptance**: Data pooled from all selected regions; empty
    `regions` shows the region-specific message.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: Single- and multi-region cases, exception-handling case.
  - **Effort**: S
- [x] **Task 9**: Migrate `update_box_plot` to `regions` (`type`/`year`
  branches only — `region` branch unchanged).
  - **Acceptance**: `type`/`year` grouping pools all selected regions;
    `region` grouping still shows every region regardless of selection;
    empty `regions` shows the region-specific message for `type`/`year`
    grouping.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: All three `group_by` modes, single- and multi-region.
  - **Effort**: S
- [x] **Task 10**: Migrate `update_download_controls` and
  `download_filtered_csv` to `regions`.
  - **Acceptance**: CSV export includes rows for every selected region;
    empty `regions` disables the button with the region-specific message.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: Single- and multi-region export content checks, empty
    `regions` case.
  - **Effort**: S

### Polish
- [x] **Task 11**: Visually verify the multi-select dropdown and
  multi-line charts via `make run`; add `.export-section`-style CSS only
  if the default chip rendering looks off.
  - **Files**: `src/assets/style.css` (maybe)
  - **Effort**: XS

## Effort Estimate

**Total**: L (matches issue #7's own estimate; larger than the rest of
the backlog because it touches all six region-driven callbacks plus two
chart builders and one utils function).

| Phase | Effort |
|-------|--------|
| Foundation (Tasks 1-3) | S |
| Features (Tasks 4-10) | L |
| Polish (Task 11) | XS |
