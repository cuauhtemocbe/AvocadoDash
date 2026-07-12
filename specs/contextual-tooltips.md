---
title: Contextual Tooltips on Dashboard Controls
status: completed
created: 2026-07-11
updated: 2026-07-12
issue: #1
---

# Contextual Tooltips on Dashboard Controls

## Objective

Add hover tooltips to the dashboard's filters and chart controls so a user can
understand what each filter or metric means without leaving the page.

## Context

AvocadoDash exposes several filters (Region, Type, Date Range) and per-chart
controls (scatter X/Y axis, box-plot column and group-by) whose labels are
short and, for some metrics (e.g. "Total Bags" vs "Small Bags"), not
self-explanatory to a first-time user. GitHub issue #1 requests contextual
tooltips for these controls.

## Requirements

### Functional Requirements

- [ ] The "Region" filter label shows a tooltip explaining what it filters.
- [ ] The "Type" filter label shows a tooltip explaining conventional vs
      organic.
- [ ] The "Date Range" filter label shows a tooltip explaining its effect.
- [ ] The scatter plot's "X-Axis Column" / "Y-Axis Column" labels show a
      tooltip explaining the control's purpose.
- [ ] The box plot's "Column to Analyze" label shows a tooltip explaining the
      control's purpose.
- [ ] The box plot's "Group By" label shows a tooltip explaining the grouping
      options (type, region, year).
- [ ] Each individual option in the scatter/box-plot metric dropdowns
      (AveragePrice, Total Volume, Total Bags, Small Bags, Large Bags,
      XLarge Bags, year) shows a short definition tooltip on hover.
- [ ] Tooltips never intercept clicks — opening a dropdown or picking a date
      must work exactly as before.

### Non-Functional Requirements

- [ ] No new runtime dependency (KISS — use the native HTML `title`
      attribute, which Dash's `html.*` and `dcc.Dropdown` option dicts
      support directly; do not add dash-bootstrap-components or similar).
- [ ] Testable without a browser/Selenium — tooltip text is a static prop on
      the layout tree, verifiable with plain pytest assertions.
- [ ] Control-label tooltips must be discoverable without prior knowledge —
      a plain-text hover target isn't enough (see Changelog: revised after
      first manual test).

## Architecture

### Components

- A single `TOOLTIPS` dict (or two small dicts: control labels + column
  definitions) added near the top of `src/app.py`, next to the existing
  `numeric_columns` constant, since it's the same kind of static lookup data.
- `info_icon(tooltip_text)` helper — returns a small `html.Span("i",
  className="info-icon", title=tooltip_text)` badge. Each of the 7
  `menu-title` control labels renders as `children=[label_text,
  info_icon(...)]` instead of putting `title=` on the label `html.Div`
  itself, so there's a visible hover target instead of plain text.
- `.info-icon` CSS in `src/assets/style.css`: small circular badge (brand
  teal background, white "i", `cursor: help`).
- `"title": COLUMN_TOOLTIPS[col]` added to each option dict already built by
  the list comprehensions for `x-axis-dropdown`, `y-axis-dropdown`,
  `box-plot-column`, and `box-plot-groupby` — left as native per-option
  tooltips (no icon), since these are already inside an opened dropdown
  list and don't have the same discoverability problem.

No new files, no new components, no changes to callbacks or chart builders.

### Data Model

N/A — static string lookup tables only, keyed by existing column/region
names already present in `numeric_columns` / `box-plot-groupby` options.

### External Dependencies

None added. Uses Dash's built-in support for the HTML `title` attribute on
`html.Div` and the `title` key in `dcc.Dropdown` option dicts (both native to
Dash ^3.2.0, already in `pyproject.toml`).

## User Stories

See GitHub issue #1 for the full user story and Gherkin acceptance criteria.

## Testing Strategy

### Unit Tests

Extend `tests/test_app.py` with assertions against `app.layout` (Dash
components are plain Python objects, so this needs no browser):

- For each filter/control `menu-title` `html.Div`, find the nested
  `info-icon` span and assert its `title` is a non-empty string.
- For each option in the `x-axis-dropdown` / `y-axis-dropdown` /
  `box-plot-column` options list, assert a `title` key with non-empty text.
- For each option in `box-plot-groupby`, assert a `title` key with non-empty
  text.
- Assert dropdown `options` still contain the original `label`/`value` pairs
  unchanged (guards against the click-blocking scenario indirectly: no
  overlay component is introduced, so this is a structural guarantee rather
  than a behavioral one — documented in Boundaries below).

### Integration Tests

Not needed — no callback behavior changes.

### E2E Tests

Out of scope (no Selenium/dash.testing dependency in this project).

## Boundaries & Constraints

### In Scope

- Native `title`-attribute tooltips on the filters and chart controls listed
  above (surfaced via a visible ⓘ icon next to each label) and on
  individual options of the metric-selection dropdowns (no icon there).

### Out of Scope

- Adding the PLU-code columns (`4046`, `4225`, `4770`) to the dropdowns.
  Issue #1's example scenario mentions "PLU 4046" as a tooltip example, but
  that column is not currently exposed in `numeric_columns` — adding it
  would be a separate scope decision, not a tooltip change. Tooltips are
  added only to columns already selectable today.
- Custom-styled tooltip popovers (own box/arrow/animation via CSS
  `::after`/`::before` or a JS library) — still the browser's native
  tooltip, just with a visible icon as the hover target instead of plain
  label text.
- Adding a testing/browser-automation dependency (e.g. Selenium,
  dash.testing) to verify actual mouse-hover rendering — verified instead at
  the component-prop level, consistent with the existing test suite.

### Technical Constraints

- Must not add new Python dependencies to `pyproject.toml`.
- Must keep `src/app.py` as the single module (per CLAUDE.md's KISS
  guidance) — no new files.
- Must pass `make lint` / `make format-check`.

## Success Criteria

- [ ] All bullet points under Functional Requirements are implemented.
- [ ] New/updated tests in `tests/test_app.py` pass and cover each tooltip.
- [ ] `make lint` and `make format` are clean.
- [ ] No existing test regresses.

## Implementation Plan

See `specs/contextual-tooltips-plan.md`.

## Changelog

- **2026-07-12**: First manual test (native `title` on the plain-text label
  `html.Div`) showed nothing on hover — plain text with no visual affordance
  is easy to miss, and the initially-tested build was also a stale
  production container that hadn't picked up the code (no hot-reload).
  Revised to a visible ⓘ `info-icon` badge next to each control label as
  the hover target, keeping the same native `title` mechanism (still zero
  new dependencies). Per-option dropdown tooltips unchanged.
