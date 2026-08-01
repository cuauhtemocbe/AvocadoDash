---
title: Shareable Dashboard State via URL Query Parameters
status: completed
created: 2026-08-01
updated: 2026-08-01
issue: "#36, #47"
milestone: "Shareable Dashboard State (URL)"
---

# Shareable Dashboard State via URL Query Parameters

## Objective

Let a user share the exact filtered/configured view they're looking at by
copy-pasting the browser URL — no export step, no verbal instructions. The
dashboard's filter and chart-configuration state round-trips through the
URL's query string: changing a control updates the URL, and loading a URL
with query parameters restores that exact state.

Delivered in two stories on the same mechanism:
- **V1 (issue #36)**: top filter bar only — `region-filter`, `type-filter`,
  `date-range`.
- **V2 (issue #47)**: extends the same encoding to the scatter chart's axis
  dropdowns and the box plot's column/group-by dropdowns.

## Context

AvocadoDash (`src/app.py`) currently has no `dcc.Location` and no URL state
at all — every control resets to its hard-coded default on page load. A
data analyst who's found an interesting view (e.g. organic avocados in
Boston and Chicago, 2015–2016) has no way to hand that exact view to a
colleague except by describing the clicks verbally.

`language-toggle` is explicitly **out of scope** for both stories (per
issue #36's technical context) — language is a display preference, not
"the view," and mixing it into the same query string adds encoding
surface for no clear user benefit.

## Requirements

### Functional Requirements

- [x] `dcc.Location(id="url", refresh=False)` added once to `app.layout`
      (not inside any existing container — a top-level sibling, since it
      renders nothing).
- [x] **V1**: `region-filter`, `type-filter`, `date-range` (`start_date`/
      `end_date`) round-trip through the URL query string.
- [x] **V2**: `x-axis-dropdown`, `y-axis-dropdown`, `box-plot-column`,
      `box-plot-groupby` round-trip through the same query string, using
      the same encoding scheme and the same sync callback pattern.
- [x] Changing any covered control updates `url.search` to match.
- [x] Loading a URL with query parameters sets every covered control to
      the parsed values.
- [x] Loading a URL with no query string (or with only some params
      present) uses the existing hard-coded defaults for whichever
      controls aren't specified.
- [x] Every parsed value is validated against the corresponding known-good
      set before being applied; an invalid/unparseable value for a given
      control falls back to that control's existing default instead of
      crashing, showing an empty chart, or leaving other controls
      unaffected by the one bad field:
      - `region`: each comma-separated value checked against the
        module-level `regions` list; if **none** are valid, fall back to
        `["Albany"]` (per issue #36). If **some** are valid, keep just the
        valid ones and drop the invalid entries — mixed lists are not
        all-or-nothing (resolved 2026-08-01, see Dry-Run Review Gate
        Findings below).
      - `region` **explicitly empty** (`?region=` present with no value,
        or all comma-separated entries empty): treated as a deliberate
        "zero regions selected" state — **not** the same as the `region`
        key being absent from the query string entirely, and **not**
        overridden by the `["Albany"]` fallback. This requires
        `urllib.parse.parse_qs(qs, keep_blank_values=True)` (the stdlib
        default drops blank values, which would otherwise silently
        collapse an intentional empty selection back to "unspecified" —
        resolved 2026-08-01, see Dry-Run Review Gate Findings below).
      - `type`: checked against `avocado_types`; invalid → default
        `"organic"`.
      - `start`/`end`: parsed as ISO dates; invalid or out of
        `[data["Date"].min(), data["Date"].max()]` → default to the
        dataset's min/max respectively.
      - `x`/`y`/`col`: checked against `numeric_columns`; invalid →
        default `"AveragePrice"` (`x`, `col`) / `"Total Volume"` (`y`).
      - `groupby`: checked against `("type", "region", "year")`; invalid →
        default `"type"`.
- [x] No infinite update loop between controls and the URL, under repeated
      or rapid control changes, or on initial page load.

### Non-Functional Requirements

- [x] No new runtime dependency — encode/decode the query string with the
      standard library (`urllib.parse.urlencode`/`parse_qs`), not a new
      package in `pyproject.toml`.
- [x] Must not change `filter_data()`, any `data.query()` expression, or
      any chart-builder function signature beyond what's already there —
      this is purely a layout + callback addition.
- [x] Must not interfere with the existing `language-toggle` behavior or
      any of the 5 data callbacks' existing Inputs/Outputs beyond adding
      the new URL-sync callbacks alongside them.

## Architecture

### Components

- **`src/app.py` layout**: add `dcc.Location(id="url", refresh=False)` as
  a top-level child of the root `html.Div`.
- **`src/app.py` — query-string helpers** (pure functions, easy to unit
  test in isolation):
  - `encode_filters_to_query(regions, avocado_type, start_date, end_date, x, y, col, groupby) -> str`
    — builds the query string. Region list is comma-joined
    (`?region=Albany,Boston`); all values pass through
    `urllib.parse.urlencode` for proper escaping (e.g. `"Total Volume"` →
    `Total%20Volume`).
  - `decode_query_to_filters(search: str) -> dict` — parses `url.search`
    (`urllib.parse.parse_qs`), applies the validation/fallback rules
    above per field, and returns a dict of resolved values (always
    complete — every key present, defaulted where absent/invalid).
- **`src/app.py` — one combined callback per sync boundary**, not two
  cross-referencing callbacks (see Risk below):

  ```python
  @app.callback(
      Output("url", "search"),
      Output("region-filter", "value"),
      Output("type-filter", "value"),
      Output("date-range", "start_date"),
      Output("date-range", "end_date"),
      Output("x-axis-dropdown", "value"),
      Output("y-axis-dropdown", "value"),
      Output("box-plot-column", "value"),
      Output("box-plot-groupby", "value"),
      Input("url", "search"),
      Input("region-filter", "value"),
      Input("type-filter", "value"),
      Input("date-range", "start_date"),
      Input("date-range", "end_date"),
      Input("x-axis-dropdown", "value"),
      Input("y-axis-dropdown", "value"),
      Input("box-plot-column", "value"),
      Input("box-plot-groupby", "value"),
  )
  def sync_url_and_filters(
      url_search, regions, avocado_type, start_date, end_date, x, y, col, groupby
  ):
      if ctx.triggered_id in (None, "url"):
          parsed = decode_query_to_filters(url_search)
          return (
              no_update,
              parsed["region"],
              parsed["type"],
              parsed["start"],
              parsed["end"],
              parsed["x"],
              parsed["y"],
              parsed["col"],
              parsed["groupby"],
          )
      new_search = encode_filters_to_query(
          regions, avocado_type, start_date, end_date, x, y, col, groupby
      )
      if new_search == url_search:
          return (no_update,) * 9
      return (new_search,) + (no_update,) * 8
  ```

  V1 ships this callback with just the 4 top-filter Inputs/Outputs (no
  `x`/`y`/`col`/`groupby`); V2 extends the same callback (same function,
  more Inputs/Outputs) — it is **not** a second callback layered on top,
  since that would reintroduce the same cycle problem this design avoids.

### Data Model

N/A — no new persisted state. `url.search` is the single source of truth
for shareable state, mirrored into the existing filter components' `value`
props.

### External Dependencies

None added (`urllib.parse` is stdlib).

## Risk: naive two-callback design is statically rejected by Dash

The obvious design — one callback `Input(filters...) -> Output(url.search)`
and a second callback `Input(url.search) -> Output(filters...)` — creates a
two-node cycle in Dash's callback dependency graph (`region-filter.value ->
url.search` in one callback, `url.search -> region-filter.value` in the
other), which Dash's static validation rejects at app-startup time with
`CircularDependencyException`, before the idempotency question in issue
#36's technical context ("only write when it differs") is even reached —
that idempotency guard solves a *runtime* re-trigger loop, not this
*startup-time* graph-validation failure. The single-callback-with-
`ctx.triggered_id` design above (self-referencing `url.search` as both
Input and Output of the *same* callback) is the standard safe pattern for
bidirectional Dash↔URL sync and avoids the static check entirely, while the
`no_update` early-return on an unchanged query string still provides the
runtime idempotency issue #36 asks for.

**This should be validated with a small throwaway prototype at the start of
the Plan phase** (confirm Dash doesn't also reject a callback that lists
the same component/prop as both Input and Output) before committing to
task estimates.

## Dry-Run Review Gate Findings (2026-08-01)

Read-only dry-run of all 8 Gherkin scenarios (5 from issue #36, 3 from
issue #47) against the current `src/app.py` — no code written.

**Feasibility verdicts**: all 8 scenarios are Feasible; issue #36's
scenario 5 ("repeated filter changes do not create a URL sync loop") is
**Feasible with caveat** — it depends on an invariant the issue doesn't
state explicitly: `encode_filters_to_query(decode_query_to_filters(x))`
must be a fixed point of `decode_query_to_filters(x)`. Tracing the
combined callback's initial-load path shows *why* this matters: because
`region-filter.value` (and the other 7 filter props) are declared as both
Input and Output of the same callback, loading a URL with a query string
causes two dispatches, not one — (1) `triggered_id=None` parses the URL
and sets the 8 filter values; (2) those Output writes are also this
callback's own Inputs, so it re-fires immediately with a filter id as
`triggered_id`, rebuilds the query string from the just-set values, and
compares it to the original. If the rebuilt string isn't byte-identical
to what was in the URL (param order, `%20` vs `+`, etc.), this second
dispatch rewrites the URL to canonical form — harmless, but it's a second
network-free but observable callback round-trip on every load with a
non-empty query string, not zero. This needs its own test (settles within
2 dispatches, doesn't loop further), not just the idempotency test issue
#36 already asks for.

**Gap found (not covered by any existing scenario)**: clearing
`region-filter` to `[]` is already a supported app state today (renders
`empty_state_figure`/`EMPTY_REGION_MESSAGE`), but the naive decode design
can't distinguish "user explicitly selected zero regions" from "region
wasn't in the query string at all" — `urllib.parse.parse_qs`'s default
`keep_blank_values=False` drops `?region=` entirely, so reloading or
sharing that URL would silently restore `["Albany"]` instead of the
empty selection the user actually had. Neither issue's scenarios exercise
this because they only test *invalid* region values, not an *intentionally
empty* one.

**Decisions (confirmed with user 2026-08-01)**:
- Mixed valid/invalid region lists (e.g. `?region=Boston,Atlantis`): keep
  the valid entries (`["Boston"]`), drop the invalid ones — not
  all-or-nothing.
- Explicit empty region selection: preserved through the URL round-trip
  via `keep_blank_values=True` plus decode logic that treats "key present,
  value empty" as `[]`, distinct from "key absent" (which still means
  "use the default `["Albany"]`"). Cost was trivial (~3 lines) relative to
  the gap it closes, so it's folded into this story rather than deferred
  to a follow-up.

**Simplicity vs. robustness**: no separate follow-up story warranted —
both resolved gaps above are small, in-scope fixes to the same
`decode_query_to_filters` function, not a meaningfully larger design.

## User Stories

- Issue #36 — "Reflect dashboard filters in the URL for shareable views"
  (V1: region/type/date-range). Full Gherkin scenarios already published on
  the issue.
- Issue #47 — "Extend shareable URL state to scatter and box-plot
  selections" (V2: axis + column/group-by dropdowns). Full Gherkin
  scenarios already published on the issue.

## Testing Strategy

### Unit Tests

Extend `tests/test_app.py`:
- `encode_filters_to_query(...)`: known inputs → exact expected query
  string (including multi-region comma-join and space-containing column
  names like `"Total Volume"` being percent-encoded).
- `decode_query_to_filters(...)`: table-driven cases covering every
  Gherkin scenario from both issues — valid full query string, empty
  query string, partially-specified query string, all-invalid region →
  default `["Albany"]`, mixed valid/invalid region (`?region=Boston,
  Atlantis` → `["Boston"]`), `region` key present but empty (`?region=` →
  `[]`, distinct from `region` key absent → default), invalid type,
  invalid/out-of-range dates, invalid x/y/col/groupby.
- Round-trip stability: for a representative non-canonical query string
  (different param order, `Total%20Volume` vs `Total+Volume`), assert
  `encode_filters_to_query(**decode_query_to_filters(x))` run twice in a
  row is stable after at most one rewrite (models the two-dispatch
  self-trigger the combined callback produces on initial load — see Dry-
  Run Review Gate Findings).
- `sync_url_and_filters(...)` called directly with `ctx.triggered_id`
  mocked/patched for each direction:
  - triggered by `"url"` (or `None`, simulating initial load): asserts
    the 8 filter Outputs match `decode_query_to_filters`'s result and
    `url.search`'s Output is `no_update`.
  - triggered by a filter prop id: asserts `url.search`'s Output matches
    `encode_filters_to_query`'s result and the 8 filter Outputs are all
    `no_update`.
  - called twice in a row with the same resulting query string (the
    idempotency case from issue #36's last scenario): asserts the second
    call's `url.search` Output is `no_update`, not a re-write.

### Integration Tests

Not needed — no external services.

### E2E Tests

Manual verification via `make run`:
1. Change `region-filter` twice in a row → confirm the URL updates both
   times and the page doesn't flicker/loop.
2. Copy a URL with query params, open in a new tab → confirm all 7
   (V1+V2) controls restore to the encoded values.
3. Open the bare app URL (no query string) → confirm all defaults are
   unchanged from current behavior.
4. Manually edit the URL to `?region=Atlantis` and reload → confirm
   `region-filter` falls back to `["Albany"]` with no error dialog.

## Boundaries & Constraints

### In Scope

- `region-filter`, `type-filter`, `date-range` (V1).
- `x-axis-dropdown`, `y-axis-dropdown`, `box-plot-column`,
  `box-plot-groupby` (V2).

### Out of Scope

- `language-toggle` (explicitly excluded per issue #36).
- Any new persistence beyond the URL itself (no `dcc.Store`, no
  server-side session, no shortened/hashed URLs).
- Browser history entries per filter change (`refresh=False` and no
  `dcc.Location`-driven navigation — a single evolving URL, not a stack of
  back-button-navigable states).

### Technical Constraints

- No new Python dependency.
- Must not modify `filter_data()`, any chart-builder signature, or the
  existing 5 data callbacks' current Inputs/Outputs (they gain no new
  Inputs from this feature — they already read the same filter component
  `value` props, which this feature now also drives from the URL).
- Must pass `make lint` / `make format-check` / `make typecheck`.

## Success Criteria

- [x] All Gherkin scenarios in issue #36 and issue #47 pass as automated
      tests.
- [x] Single combined callback per sync direction (not two
      cross-referencing callbacks) — app starts without
      `CircularDependencyException`.
- [x] Repeated/rapid filter changes produce no visible loop and no runaway
      callback re-invocation (verified by the idempotency unit test).
- [x] `make lint`, `make format-check`, `make typecheck` clean.
- [x] No existing test regresses.

## Implementation Plan

See `specs/shareable-url-state-plan.md`.
