---
title: Filtered-Data Summary/Insights Panel
status: completed
created: 2026-07-12
updated: 2026-07-12
issue: #2
---

# Filtered-Data Summary/Insights Panel

## Objective

Add a KPI summary panel to the dashboard that shows headline numbers (average
price, total volume, price trend, best/worst region) for the currently
filtered selection, so a user doesn't have to read every chart to get the
top-level picture.

## Context

GitHub issue #2 requests this panel. `src/utils.py` already has
`calculate_summary_stats()` and `format_number()` but neither is imported by
`src/app.py` — they've been dead scaffolding since the app was written. This
story wires them into the UI, extending `utils.py` with the two calculations
`calculate_summary_stats` doesn't cover (period-over-period price change,
cross-region best/worst).

## Requirements

### Functional Requirements

- [x] Summary panel shows average price and total volume for the exact
      current filter selection (region + type + date range).
- [x] Summary panel shows the percentage price change vs. the immediately
      preceding period of equal length (e.g. a one-year selection is
      compared to the prior year).
- [x] Summary panel shows the best- and worst-performing region by average
      price for the current type + date filters, across all regions (the
      region filter is single-select, so this KPI is inherently
      cross-region rather than scoped to the one selected region).
- [x] When the current region + type + date combination has zero rows, the
      panel shows a "no data for this selection" message instead of blank
      or broken KPIs.
- [x] Numbers are formatted for readability via `format_number` (e.g.
      1500000 → "1.5M", 2500 → "2.5K", 850 → "850").

### Non-Functional Requirements

- [x] No new runtime dependency.
- [x] Testable without a browser — panel content is built by a plain
      Python function callable directly with a DataFrame, verifiable with
      pytest assertions on the returned Dash component tree / calculation
      functions.

## Architecture

### Components

- `src/utils.py`: keep `calculate_summary_stats` and `format_number`
  as-is (they already cover avg price / total volume / formatting), add
  two new pure functions:
  - `calculate_price_change(data, region, avocado_type, start_date,
    end_date)` — average price of the selected period vs. the immediately
    preceding period of equal length. Returns `None` if either period has
    no data (edge case, not in current dataset but kept for robustness).
  - `find_region_extremes(data, avocado_type, start_date, end_date)` —
    average price per region (filtered by type + date only, all regions),
    returns the best and worst region + their average price. Returns
    `None` if the filter matches no rows.
- `src/app.py`:
  - `create_summary_panel(filtered_data, region, avocado_type, start_date,
    end_date)` — builds the panel's Dash component tree (stat cards) from
    `filtered_data` plus the two new util functions. Returns a "no data"
    message `html.Div` when `filtered_data` is empty. Mirrors the existing
    chart-builder pattern (`create_price_chart` etc.) but returns Dash
    components instead of a Plotly figure dict, since this is markup, not
    a chart.
  - New `summary-panel` container `html.Div` in `app.layout`, placed
    directly under the filter menu and above the price/volume charts.
  - New `update_summary_panel` callback, same Input set
    (`region-filter`, `type-filter`, `date-range` start/end) as
    `update_charts`, with the same try/except-returns-fallback pattern as
    the other three callbacks.
- `src/assets/style.css`: `.summary-panel` / `.summary-stat*` rules
  reusing the existing card/menu visual language (white card, teal
  accents, box-shadow) and the app's established green/red palette for
  positive/negative price-change coloring.

### Data Model

N/A — derived entirely from the existing `data` DataFrame; no new
persisted state.

### External Dependencies

None added.

## User Stories

See GitHub issue #2 for the full user story and Gherkin acceptance
criteria.

## Testing Strategy

### Unit Tests

Extend `tests/test_app.py`:

- `calculate_price_change`: known region/type/date-range fixture, assert
  percentage matches a manually computed value; assert `None` when the
  previous period has no rows.
- `find_region_extremes`: assert best/worst region and prices match a
  manual `groupby` computation over a small filtered slice.
- `create_summary_panel`: for a non-empty filtered slice, assert the
  returned component tree contains the formatted average price and total
  volume; for an empty slice, assert it returns the "no data" message
  component instead of stat cards.
- Parametrized `format_number` cases from the issue's Scenario Outline
  (1500000 → "1.5M", 2500 → "2.5K", 850 → "850") — already covered by
  `format_number`'s existing implementation; test locks in the contract.

### Integration Tests

Not needed — no external services; callback logic is exercised via direct
function calls to `create_summary_panel` / `update_summary_panel`.

### E2E Tests

Out of scope (no Selenium/dash.testing dependency in this project).

## Boundaries & Constraints

### In Scope

- The four KPIs listed in Functional Requirements, computed from the
  existing `data` DataFrame.

### Out of Scope

- New filters/comparison UI (e.g. an explicit multi-region "comparison
  view" toggle) — the best/worst-region KPI is always computed
  cross-region regardless of the single-select region filter, which
  satisfies the issue's scenario without adding new UI surface. A
  dedicated comparison view is issue #7's scope, not this one.
- Persisting or exporting summary numbers.
- Adding a testing/browser-automation dependency to verify rendered
  layout — verified at the component-prop / calculation level, consistent
  with the existing test suite.

### Technical Constraints

- Must not add new Python dependencies to `pyproject.toml`.
- Must pass `make lint` / `make format-check`.

## Success Criteria

- [x] All Functional Requirements implemented.
- [x] All 5 Gherkin scenarios from issue #2 have passing automated tests.
- [x] `make lint` and `make format-check` are clean.
- [x] No existing test regresses.

## Implementation Plan

See `specs/summary-panel-plan.md`.
