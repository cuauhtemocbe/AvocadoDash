---
title: Support Comparing Multiple Regions at Once
status: completed
created: 2026-07-12
updated: 2026-07-12
issue: #7
---

# Support Comparing Multiple Regions at Once

## Objective

Turn the single-select `region-filter` dropdown into a multi-select so a
data analyst can compare price/volume trends across several US regions on
the same charts, instead of switching the filter back and forth and
memorizing values.

## Context

GitHub issue #7 requests this. `region-filter` is the dashboard's global
region control — every callback that reads it
(`update_summary_panel`, `update_download_controls`,
`download_filtered_csv`, `update_charts`, `update_scatter_chart`,
`update_box_plot`) currently assumes a single region string and filters
with `region == @region`. Scoping this change to only the price/volume
charts (as the issue's spike note suggests) would leave the summary panel,
CSV export, scatter chart and box plot silently pinned to a single region
while the filter itself displays several — a confusing, inconsistent UX.
This spec covers the whole dashboard: every callback driven by
`region-filter` switches from a single region to a list of regions.

## Requirements

### Functional Requirements

- [x] `region-filter` allows selecting one or more regions (`dcc.Dropdown`
      with `multi=True`), defaulting to `["Albany"]` on load (same default
      region as today, now as a one-item list).
- [x] Price chart and volume chart show one line per selected region, each
      with a distinct color and a legend identifying the region. A single
      selected region renders exactly as it does today (one line, tooltip
      unchanged in substance).
- [x] Scatter chart and box plot (when grouped by `type` or `year`) filter
      their data to the selected regions instead of a single region. Box
      plot grouped by `region` is unaffected — it already ignores the
      top-level region filter and always shows every region.
- [x] Summary panel KPIs (Average Price, Total Volume, Price Change vs.
      Previous Period) are computed over the combined rows of all selected
      regions. "Best/Worst Region" cards are unaffected — they already
      compare across every region in the dataset regardless of the filter.
- [x] CSV export includes rows for every selected region.
- [x] Removing all regions from the filter shows a "select at least one
      region" message in place of each chart/panel/download control,
      instead of the generic empty-filter error.
- [x] No cap on the number of regions that can be selected.

### Non-Functional Requirements

- [x] No new runtime dependency — `multi=True` is a built-in `dcc.Dropdown`
      option already shipped with `dash`.
- [x] Testable without a browser — callback functions remain plain Python
      callables invoked directly in pytest.
- [x] `make lint` / `make format-check` stay clean.

## Architecture

### Components

- `src/app.py`:
  - `region-filter` `dcc.Dropdown`: add `multi=True`, change `value` from
    `"Albany"` to `["Albany"]`, keep `clearable=True` so all chips can be
    cleared at once (individual chips are already removable one-by-one
    under `multi=True` regardless of `clearable`).
  - New `filter_data(regions, avocado_type, start_date, end_date)` helper
    (near `load_data`) replacing the `region ==`/`region == @region`
    query string that's currently duplicated across all six callbacks —
    `region in @regions and type == @avocado_type and Date >= @start_date
    and Date <= @end_date`. Every callback below calls this instead of
    building its own query string, so the region → regions change only
    has to be made correctly once. `update_box_plot`'s `group_by ==
    "region"` branch keeps its existing `type`-only query (unchanged,
    still ignores the region filter by design).
  - New `EMPTY_REGION_MESSAGE` constant (e.g. `"Select at least one region
    to see data."`) and a small `empty_state_figure(message)` helper
    (replacing the `empty_fig`/`{"data": [], "layout": {...}}` dict
    that's already duplicated across `update_charts`,
    `update_scatter_chart`, `update_box_plot`), so the existing generic
    "no data for this filter" state and the new "no region selected"
    state share one code path parameterized by message text.
  - All six callbacks: rename their `region` parameter/arg to `regions`
    (list), add an early `if not regions:` branch returning the
    region-specific empty state before querying, and call `filter_data`
    instead of the current per-callback query string.
  - `create_price_chart` / `create_volume_chart`: change signature to
    group `filtered_data` by `region` and emit one trace per region
    (`name` = region, hovertemplate includes the region), instead of
    assuming a single implicit region. Reuse the existing
    `show_legend = len(traces) > 1` pattern already used by
    `create_box_plot`/`create_scatter_chart`. Colors: an 8-hue qualitative
    palette (picked with the `/dataviz` skill). Assigned by each region's
    position within the *current* selection (alphabetical), not by a fixed
    global region → color mapping — browser QA caught that a global
    `index % 8` mapping aliases regions 8 apart alphabetically onto the
    same color (e.g. "Albany" and "Chicago", the issue's own example,
    collided). Position-based assignment guarantees distinct colors for
    any 2-8 concurrently selected regions at the cost of a region's color
    shifting if the selection changes, which is an acceptable trade-off
    since the legend and hover tooltip always name the region directly.
  - `calculate_price_change` (in `src/utils.py`): change its `region`
    parameter to `regions` (list) and its query from `region ==
    @region` to `region in @regions` for both the current and previous
    period slices. The percentage change is computed the same way as
    today (`AveragePrice.mean()` over the matched rows), now naturally
    aggregated across all matched rows regardless of region — no
    volume-weighting is introduced, consistent with how
    `calculate_summary_stats` already averages `AveragePrice` with a
    plain `.mean()`.
  - `find_region_extremes`: unchanged — it already scans every region in
    the dataset regardless of the filter.
- `src/assets/style.css`: verify the multi-select dropdown's chip/tag
  rendering matches the existing dropdown visual language; add minimal
  rules only if the default `react-select`-based rendering looks broken
  against the current theme (checked manually via `make run` in a
  browser, per project convention for UI changes).

### Data Model

N/A — derived entirely from the existing `data` DataFrame; no new
persisted state.

### External Dependencies

None added.

## User Stories

See GitHub issue #7 for the full user story and Gherkin acceptance
criteria.

## Testing Strategy

### Unit Tests

Extend `tests/test_app.py` (which already covers `src/utils.py`'s
functions too — there's no separate `test_utils.py`):

- `region-filter` layout: `multi=True` is set, default `value ==
  ["Albany"]`.
- `filter_data`: single region behaves identically to today's single-value
  query; multiple regions returns the union of their rows; empty list
  returns an empty DataFrame.
- `create_price_chart` / `create_volume_chart`: single region → one trace,
  named for that region (matches current fixture expectations); multiple
  regions → one trace per region, each with the correct `name` and only
  that region's rows in `x`/`y`.
- `update_charts`, `update_scatter_chart`, `update_box_plot`,
  `update_summary_panel`, `update_download_controls`,
  `download_filtered_csv`: parametrized over `regions=["Albany"]` (must
  match existing single-region behavior/fixtures) and
  `regions=["Albany", "Chicago"]` (must include rows from both); each also
  gets a `regions=[]` case asserting the "select at least one region"
  state (empty-state figure text / summary panel message / disabled
  download button with matching status text) instead of the generic
  no-data state.
- `calculate_price_change`: existing single-region test continues to pass
  with `regions=["Albany"]`; add a multi-region case comparing its output
  against manually computing the mean over the combined current/previous
  slices.
- Exception-handling tests mirroring the existing
  `*_callback_handles_exception_without_crashing` tests, run with a
  multi-region input.

### Integration Tests

Not needed — no external services; callback logic is exercised via direct
function calls, as with the rest of the test suite.

### E2E Tests

Out of scope (no Selenium/`dash.testing` dependency in this project).

## Boundaries & Constraints

### In Scope

- Multi-region selection on the global `region-filter`, applied
  consistently to every chart, the summary panel, and CSV export.
- The three Gherkin scenarios from issue #7.

### Out of Scope

- Per-chart region overrides (e.g. picking different regions for the
  scatter chart than the price chart).
- A maximum-selections limit or region search/autocomplete changes beyond
  what `dcc.Dropdown(multi=True, searchable=True)` already provides.
- Changing what the box plot's `group_by == "region"` mode shows (it
  already shows all regions, by design, unaffected by this change).
- Volume-weighted (as opposed to simple-mean) price aggregation for
  multi-region summary stats.

### Technical Constraints

- Must not add new Python dependencies to `pyproject.toml`.
- Must pass `make lint` / `make format-check`.
- Must not regress any existing single-region test/behavior.

## Success Criteria

- [x] All Functional Requirements implemented.
- [x] All 3 Gherkin scenarios from issue #7 have passing automated tests.
- [x] `make lint` and `make format-check` are clean.
- [x] No existing test regresses.

## Implementation Plan

See `specs/multi-region-comparison-plan.md`.
