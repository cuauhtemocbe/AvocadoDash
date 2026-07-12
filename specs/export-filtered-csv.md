---
title: Export the Filtered Dataset as CSV
status: approved
created: 2026-07-12
updated: 2026-07-12
issue: #6
---

# Export the Filtered Dataset as CSV

## Objective

Add a "Download CSV" control to the dashboard that exports exactly the rows
matching the current region/type/date-range filters, so a user who found an
interesting filtered view can analyze it further outside the dashboard.

## Context

GitHub issue #6 requests this. The filtering logic already exists,
duplicated per-callback in `src/app.py` (`data.query("region == @region and
type == @avocado_type and Date >= @start_date and Date <= @end_date")`) —
the same pattern used by `update_summary_panel` / `update_charts`. This
feature reuses that same filter, adds no new filter UI, and needs no new
runtime dependency: Dash's `dcc.Download` + `dcc.send_data_frame` cover
browser-triggered file downloads natively.

## Requirements

### Functional Requirements

- [x] A "Download CSV" button, driven by the same region/type/date-range
      filters as the rest of the dashboard.
- [x] Clicking it downloads a CSV containing exactly the rows matching the
      current filter combination.
- [x] When the current filter combination returns zero rows, the button is
      disabled and a "no data to export" message is shown instead.
- [x] The downloaded file's header row matches the dataset's column names
      (native behavior of `DataFrame.to_csv(index=False)`).

### Non-Functional Requirements

- [x] No new runtime dependency (`dcc.Download`/`dcc.send_data_frame` are
      already part of `dash`).
- [x] Testable without a browser — the callback functions are plain
      Python callables that can be invoked directly in pytest and their
      return values (dict from `send_data_frame`, disabled flag) asserted
      on directly.

## Architecture

### Components

- `src/app.py`:
  - New `export-section` `html.Div` in `app.layout`, placed directly under
    the filter menu (alongside/above `summary-panel`), containing:
    - `html.Button(id="download-csv-button")`
    - `html.Span(id="download-status")` for the "no data to export" message
    - `dcc.Download(id="download-dataframe-csv")` (invisible, triggers the
      browser download)
  - New `update_download_controls` callback: same Input set as
    `update_summary_panel`/`update_charts` (`region-filter`, `type-filter`,
    `date-range` start/end). Outputs `download-csv-button.disabled` and
    `download-status.children`.
  - New `download_filtered_csv` callback: `Input("download-csv-button",
    "n_clicks")` with `State` on the same four filters,
    `prevent_initial_call=True`. Re-applies the same filter query, and
    returns `dcc.send_data_frame(filtered_data.to_csv,
    "avocado_filtered.csv", index=False)`, or `dash.no_update` if the
    filtered slice is empty (defensive: the button is disabled in that
    case, but the callback shouldn't assume the UI guard always fires
    first). Follows the existing try/except-returns-fallback pattern used
    by the other four callbacks.
- `src/assets/style.css`: `.export-section` / `.download-button` /
  `.download-status` rules reusing the existing card/menu visual language.

### Data Model

N/A — derived entirely from the existing `data` DataFrame; no new
persisted state.

### External Dependencies

None added.

## User Stories

See GitHub issue #6 for the full user story and Gherkin acceptance
criteria.

## Testing Strategy

### Unit Tests

Extend `tests/test_app.py`:

- `download_filtered_csv`: for a known non-empty filter combination, parse
  the returned `content` back into a DataFrame (`pd.read_csv(io.StringIO(...))`)
  and assert its shape/values match the directly-queried filtered slice;
  assert the header row equals the dataset's column names.
- `download_filtered_csv` with a filter combination that yields zero rows:
  assert it returns `dash.no_update` rather than a download payload.
- `update_download_controls`: non-empty filter → `disabled=False`, empty
  status message; empty-result filter → `disabled=True`, non-empty "no
  data" status message.
- Exception-handling test mirroring
  `test_update_charts_callback_handles_exception_without_crashing`.

### Integration Tests

Not needed — no external services; callback logic is exercised via direct
function calls.

### E2E Tests

Out of scope (no Selenium/dash.testing dependency in this project).

## Boundaries & Constraints

### In Scope

- CSV export of the currently filtered rows via a single download button.

### Out of Scope

- Export formats other than CSV (e.g. Excel, JSON).
- Exporting chart images.
- A dedicated multi-region comparison export (issue #7's scope).

### Technical Constraints

- Must not add new Python dependencies to `pyproject.toml`.
- Must pass `make lint` / `make format-check`.

## Success Criteria

- [x] All Functional Requirements implemented.
- [x] All 3 Gherkin scenarios from issue #6 have passing automated tests.
- [x] `make lint` and `make format-check` are clean.
- [x] No existing test regresses.

## Implementation Plan

See `specs/export-filtered-csv-plan.md`.
