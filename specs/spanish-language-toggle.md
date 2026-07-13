---
title: Spanish/English Language Toggle
status: completed
created: 2026-07-13
updated: 2026-07-13
issue: none
---

# Spanish/English Language Toggle

## Objective

Add an ES/EN language toggle to AvocadoDash so the dashboard's UI text,
labels, tooltips, and generated chart text can be read in Spanish — the
primary language of the target audience (Mexico/Latin America/Spanish
speakers) — while still supporting English. Spanish is the default
language on load.

## Context

AvocadoDash's UI is currently 100% hard-coded English (headers, filter
labels, tooltips, dropdown option labels, chart titles/axis titles/hover
text, summary-panel card labels, empty-state and error messages — see the
full inventory below). The target audience for the app is now defined as
Mexican/Latin American/Spanish-speaking users, so the interface needs to
read naturally in Spanish, with English kept available via a toggle for
non-Spanish-speaking visitors (e.g. recruiters, portfolio reviewers).

Decisions already made with the user (2026-07-13):
- **ES/EN toggle**, not a one-way hard-coded translation — both languages
  ship, default is Spanish.
- **Dropdown *values* used in `data.query()`/DataFrame column access stay
  in English** (`"conventional"`/`"organic"`, `"AveragePrice"`,
  `"Total Volume"`, etc.) — only the **displayed label** is translated.
  This keeps `filter_data()` and every chart builder's DataFrame access
  untouched.
- **US region names (Albany, California, TotalUS, ...) stay in English** —
  they're proper nouns/toponyms with no natural one-to-one Spanish
  equivalent, and translating ~54 of them would be high effort for no real
  benefit to a bilingual user (region names are recognizable as-is).
- **The brand name "Avocado Analytics" is not translated** (product name,
  like a proper noun) — only the subtitle/description text under it.

## Requirements

### Functional Requirements

- [x] A visible language toggle control (`language-toggle`, e.g.
      `dcc.RadioItems` with options `ES`/`EN`) in the header, default
      value `"es"`.
- [x] Selecting a language immediately re-renders (no page reload) every
      cosmetic string in the app in that language: header/footer text,
      section headers, filter labels, tooltips, dropdown option *labels*,
      chart titles, chart axis titles, chart hover-template label words,
      summary-panel card labels, empty-state messages, and the `"Error: "`
      prefix on error fallbacks.
- [x] Changing language does **not** reset any current filter selection
      (selected regions, type, date range, axis/column/group-by choices) —
      only text changes, not `value` props.
- [x] Dropdown option `value`s (used in filtering/DataFrame access) are
      unchanged by language — only `label`s change.
- [x] Region names and the "Avocado Analytics" brand name are identical in
      both languages.
- [x] Missing/untranslated keys fail loudly in dev (see Testing Strategy),
      not silently, so gaps are caught before merge — no runtime fallback
      string is required in production once the translation dict is
      complete, since it is exhaustively covered by tests.

### Non-Functional Requirements

- [x] No new runtime dependency (`dcc.RadioItems`/existing Dash callback
      mechanism cover this; no `flask-babel`/`gettext`/i18n library).
- [x] Language state does not need to persist across page reloads (out of
      scope — see Boundaries); defaulting to `"es"` on every load already
      matches the primary audience.
- [x] Must not change any `data.query()` expression, DataFrame column
      access, or other filtering/business logic — this is a display-only
      change verified by the existing (unmodified) filter/chart-data test
      assertions continuing to pass.

## Architecture

### Components

- **`src/translations.py`** (new module): a `TRANSLATIONS: dict[str, dict[str, str]]`
  keyed by language (`"es"`, `"en"`) then by a flat dotted string key (e.g.
  `"header.title"`, `"filters.region.label"`, `"tooltips.region_filter"`,
  `"columns.AveragePrice.label"`, `"columns.AveragePrice.tooltip"`,
  `"charts.price.title"`, `"summary.avg_price.label"`, `"errors.prefix"`,
  etc.), plus a `t(key: str, lang: str) -> str` lookup helper. Column
  display-name entries replace today's `col.replace("_", " ").title()`
  logic (which mis-renders `"AveragePrice"` → `"Averageprice"`) with an
  explicit label per column per language — this incidentally fixes that
  pre-existing display quirk for both languages as a side effect, not a
  goal in itself.
- **`src/app.py` layout changes**:
  - New `dcc.RadioItems(id="language-toggle", options=[{"label": "ES",
    "value": "es"}, {"label": "EN", "value": "en"}], value="es")` in the
    header, near the existing GitHub link.
  - Every currently id-less static text element that needs translation
    (`H1` brand subtitle, `H2` section headers, header description
    paragraph, footer text) gets a new `id` so a callback can target its
    `children`.
- **`src/app.py` new callback — `update_ui_language`**:
  - `Input("language-toggle", "value")` only.
  - Outputs: `children`/`placeholder`/`options` for every static,
    filter-independent text element cataloged below (filter labels +
    tooltips, section headers, header/footer text, download button text,
    dropdown *option labels* for region/type/x-axis/y-axis/box-plot-column/
    box-plot-groupby — values unchanged).
  - This callback does not touch `summary-panel`, chart `figure`s, or
    `download-status` — those are already rebuilt by their own callbacks
    from filtered data (see next point).
- **Extend the 5 existing data callbacks** (`update_summary_panel`,
  `update_download_controls`, `update_charts`, `update_scatter_chart`,
  `update_box_plot`) with an added `Input("language-toggle", "value")`,
  threading `lang` through to the chart-builder functions
  (`create_price_chart`, `create_volume_chart`, `create_box_plot`,
  `create_scatter_chart`, `create_summary_panel`, `empty_state_figure`),
  each gaining a `lang: str` parameter used to look up translated titles/
  axis labels/hover words/card labels via `translations.t()`. This means
  toggling language re-triggers these callbacks (via the new Input) and
  they naturally emit translated chart text using the *same* filtered data
  — no separate rebuild path needed for dynamic content.
  `download_filtered_csv` is unaffected (its only UI-facing text is
  `no_update`/an error not routed to a visible string beyond the shared
  `update_download_controls` status).

### Data Model

N/A — no change to `data`/DataFrame handling. `TRANSLATIONS` is a static,
in-memory nested dict; `language-toggle`'s `value` prop (`"es"` | `"en"`)
is the single source of truth for current language (no `dcc.Store`
needed).

### External Dependencies

None added.

## Full String Inventory (from codebase audit — drives the `TRANSLATIONS` dict)

**Static (needs new callback + new ids where missing):**
- Header: brand subtitle "by @Kuautli", header description paragraph,
  "View on GitHub" (x2), footer "Created by @Kuautli"
- Filter labels: "Region", "Type", "Date Range", "X-Axis Column",
  "Y-Axis Column", "Column to Analyze", "Group By"
- Section headers: "Scatter Plot Analysis", "Box Plot Analysis"
- Tooltips: all 7 `CONTROL_TOOLTIPS`, all 7 `COLUMN_TOOLTIPS`, all 3
  `GROUPBY_TOOLTIPS`
- Dropdown option labels (values unchanged): region-filter placeholder
  "Select a region...", type-filter ("Conventional"/"Organic"), the 7
  numeric-column display names (x-axis/y-axis/box-plot-column dropdowns),
  box-plot-groupby ("Avocado Type"/"Region"/"Year")
- "Download CSV" button text

**Dynamic (threaded via `lang` param into existing callbacks/builders):**
- `EMPTY_REGION_MESSAGE`, "No data available for selected filters", "Try
  adjusting your filters", "No data to export.", "No data available for
  this selection."
- Chart titles: "Average Price of Avocados", "Avocados Sold (Volume)", the
  box-plot title template ("{column} Distribution by {group_by}"), the
  scatter title template ("{x_col} vs {y_col}")
- Axis titles: "Date", "Price (USD)", "Volume", plus column/group-by
  display names reused from the static dict
- Hover-template label words: "Date: ", "Price: ", "Volume: ", "Region: "
- Summary-panel card labels: "Average Price", "Total Volume", "Price
  Change vs. Previous Period", "Best Region (avg. price)", "Worst Region
  (avg. price)"
- Error fallback prefix: "Error: " (the exception message itself,
  `str(e)`, stays untranslated — see Boundaries)

## Testing Strategy

### Unit Tests

Extend `tests/test_app.py` and add `tests/test_translations.py`:

- `tests/test_translations.py`: assert `TRANSLATIONS["es"]` and
  `TRANSLATIONS["en"]` have **identical key sets** (catches missing
  translations at test time — the "fail loudly" requirement above), and
  that `t(key, lang)` raises/returns clearly for an unknown key rather
  than silently returning `None`/empty string.
- `update_ui_language("es")` / `update_ui_language("en")`: assert a
  representative sample of Outputs (e.g. the region/type/date-range labels,
  the download button text, the box-plot-groupby option labels) match the
  expected translated strings for each language, and that dropdown option
  `value`s are unchanged between the two calls.
- For each of the 5 extended data callbacks: add a `lang="en"` /
  `lang="es"` parametrized case (alongside existing filter-combination
  tests) asserting the chart title / axis title / summary label text
  matches the expected language, while the numeric/data content is
  unaffected by `lang`.
- Regression: all existing filter/data-correctness assertions in
  `tests/test_app.py` continue to pass unmodified (proves `value`s/query
  logic are untouched).

### Integration Tests

Not needed — no external services.

### E2E Tests

Manual verification via `make run`: toggle ES→EN→ES, confirm all charts/
labels/tooltips update and that an in-progress filter selection (e.g. 2
selected regions + a custom date range) survives the toggle unchanged.

## Boundaries & Constraints

### In Scope

- ES/EN toggle for all cosmetic text cataloged above.
- Fixing the `.title()`-derived "Averageprice" display quirk as a side
  effect of introducing explicit column display-name translations.

### Out of Scope

- Translating region names (proper nouns) or the "Avocado Analytics" brand
  name.
- Persisting the language choice across page reloads/sessions (would need
  `dcc.Store(storage_type="local")` or a URL param — not requested, and
  defaulting to `"es"` already serves the primary audience on every load).
- Locale-aware number/date formatting (decimal separators, date order,
  currency symbol placement) — prices stay `$X.XX`/USD-formatted
  regardless of language; only words are translated.
- Translating the raw Python exception text (`str(e)`) inside error
  fallbacks — only the `"Error: "` prefix is translated.
- Translating the downloaded CSV filename (`avocado_filtered.csv`) or the
  browser tab title (`app.title`) — low value, out of proportion effort
  (tab title would need a clientside callback).
- Any additional language beyond ES/EN.

### Technical Constraints

- Must not add new Python dependencies to `pyproject.toml`.
- Must not modify any `data.query()` expression or DataFrame column name.
- Must pass `make lint` / `make format-check`.

## Success Criteria

- [x] All Functional Requirements implemented.
- [x] `TRANSLATIONS["es"]`/`TRANSLATIONS["en"]` have identical key sets
      (enforced by test).
- [x] Toggling language changes 100% of the cataloged cosmetic strings and
      changes zero `value` props / filtering behavior.
- [x] `make lint` and `make format-check` are clean.
- [x] No existing test regresses.

## Implementation Plan

See `specs/spanish-language-toggle-plan.md`.
