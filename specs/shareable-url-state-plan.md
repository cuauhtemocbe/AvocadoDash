# Implementation Plan: Shareable Dashboard State via URL Query Parameters

**Spec**: `specs/shareable-url-state.md`
**Created**: 2026-08-01
**Status**: completed

## Components

### 1. Dash-pattern spike: self-referencing callback
- **Purpose**: Confirm, before writing real code, that Dash accepts a
  single callback listing the same component/prop (`url.search`,
  `region-filter.value`, etc.) as both an Output and an Input, without
  raising `CircularDependencyException` at startup, and that it
  self-triggers/settles the way the Dry-Run Review Gate traced (≤2
  dispatches on initial load with a non-empty query string). This is the
  load-bearing architectural assumption the whole feature rests on — see
  the spec's "Risk" section.
- **Files**: a throwaway scratch script/branch, not committed — `make
  run` against a minimal 2-Input/2-Output version of the callback shape.
- **Effort**: XS

### 2. Query-string codec helpers
- **Purpose**: Pure functions `encode_filters_to_query(...)` and
  `decode_query_to_filters(search: str) -> dict`, covering the full
  validation/fallback matrix from the spec (invalid region → default,
  mixed valid/invalid region → keep valid, region key present-but-empty
  → `[]`, region key absent → default, invalid type/dates/x/y/col/groupby
  → their respective defaults). Deterministic param ordering (fixed key
  order, not dict-insertion order) so re-encoding a decoded value is a
  fixed point — this is what makes the self-trigger settle in ≤2
  dispatches instead of rewriting indefinitely.
- **Files**: `src/app.py` (kept in the existing single module per this
  repo's KISS principle — no new `url_state.py`; these are two small
  functions, not a large data table like `translations.py`).
- **Effort**: S (V1 fields only: region/type/start/end)

### 3. `dcc.Location` + V1 combined sync callback
- **Purpose**: Add `dcc.Location(id="url", refresh=False)` to
  `app.layout`, and implement `sync_url_and_filters` — the single
  combined callback from the spec's Architecture section — scoped to V1
  fields only (`region-filter`, `type-filter`, `date-range`). Branches on
  `ctx.triggered_id in (None, "url")` vs. a filter id, using `no_update`
  for the non-firing direction's outputs.
- **Files**: `src/app.py`
- **Effort**: S

### 4. V2 extension: scatter + box-plot fields
- **Purpose**: Extend both the codec helpers and `sync_url_and_filters`
  with the 4 additional fields (`x-axis-dropdown`, `y-axis-dropdown`,
  `box-plot-column`, `box-plot-groupby`) — same function, more
  Inputs/Outputs/query keys, not a second callback (per the spec's
  explicit warning against layering a second cross-referencing callback
  on top).
- **Files**: `src/app.py`
- **Effort**: S

### 5. Tests
- **Purpose**: Cover every Gherkin scenario from issues #36 and #47 as
  automated tests, plus the two gaps the Dry-Run Review Gate surfaced
  (mixed-region, empty-region, round-trip stabilization).
- **Files**: `tests/test_app.py`
- **Effort**: S (split across steps 3 and 4 below rather than one block)

## Dependencies

### Build Order
1. Spike (component 1) — must pass before any real code is written
2. Codec helpers, V1 fields (component 2)
3. `dcc.Location` + V1 callback (component 3), depends on 2
4. V1 tests
5. V2 codec + callback extension (component 4), depends on 3
6. V2 tests
7. Manual E2E pass (`make run`) covering both V1 and V2
8. Lint/format/typecheck/coverage pass

### External Dependencies
None — `urllib.parse` (stdlib) only, no `pyproject.toml` change.

## Risks & Assumptions

### Risks
- **Risk 1 — spike fails**: if Dash *does* reject the self-referencing
  callback (contrary to the spec's analysis), fall back to a
  `dcc.Store(id="filters-store")` as the single canonical state holder:
  one callback `filters (Input) → store (Output)`, one callback `store
  (Input) → url.search (Output)`, one callback `url.search (Input,
  initial only via prevent_initial_call=False) → store (Output)`, one
  callback `store (Input) → filters (Output)`. This still needs care to
  avoid the same 2-cycle at the store↔url and store↔filters boundaries,
  so it is *not* a first choice — only pursue if the spike disproves the
  simpler design. Mitigation: run the spike first, before sizing any
  other task.
- **Risk 2 — encoding non-determinism**: if `encode_filters_to_query`
  isn't a true fixed point over `decode_query_to_filters`'s output (e.g.
  inconsistent param ordering), the self-trigger on initial load won't
  settle in 2 dispatches and could rewrite the URL on every subsequent
  unrelated filter change too. Mitigation: fixed key order in the
  encoder (never dict/kwargs iteration order), covered by the round-trip
  stability test from the spec's Testing Strategy.

### Assumptions
- `dash.ctx.triggered_id` reliably distinguishes "no trigger / url
  trigger" from "a specific filter changed" even when multiple Outputs
  from a prior dispatch land simultaneously — validated by the spike and
  by the round-trip stabilization test, not assumed from documentation
  alone.

## Milestones

- [x] **M1**: Spike confirms the self-referencing single-callback pattern
      works in this Dash version without `CircularDependencyException`
      (go/no-go gate for the rest of the plan) — verified 2026-08-01: a
      callback with `url.search` as both Output and Input registers and
      serves (`GET /` and `GET /_dash-dependencies` both return 200)
      without error against this repo's Dash version, via the real Flask
      test client (not a hand-simulation). Exact client-side dispatch
      count on load still to be confirmed visually in Task 3's manual
      E2E pass — the test-client check can't observe browser-side
      re-triggering.
- [x] **M2**: V1 scope complete — all 5 Gherkin scenarios from issue #36
      pass as automated tests, including the round-trip stabilization and
      empty/mixed-region cases from the Dry-Run Review Gate
- [x] **M3**: V2 scope complete — all 3 Gherkin scenarios from issue #47
      pass as automated tests
- [x] **M4**: `make lint` / `make format-check` / `make typecheck` /
      `make test` all green (159 tests, 97.67% coverage). Manual
      browser walkthrough **not performed** — this environment has no
      browser automation available, and `make run` itself is broken
      (pre-existing, unrelated bug: it runs `avocadodash:latest`, the
      production image, which has no `poetry` installed — see
      "Findings" below). Verified instead via the real Flask app
      (`app.server.test_client()`, confirming no
      `CircularDependencyException` and a valid `/_dash-dependencies`
      graph) plus direct calls to the real registered
      `sync_url_and_filters` function with Dash's actual
      `ctx.triggered_id` context, covering all 8 Gherkin scenarios.
      **A real browser check is still recommended before merging.**

## Tasks

### Foundation (Build First)
- [x] **Task 1**: Spike — validate self-referencing callback pattern
  - **Acceptance**: A minimal throwaway Dash callback with `url.search`
    as both Input and Output (plus one filter prop) starts without
    `CircularDependencyException` and settles within 2 dispatches when
    loaded with a non-canonical query string
  - **Files**: none committed (scratch only)
  - **Tests**: manual, via `make run`
  - **Effort**: XS
  - **Result**: PASS, verified 2026-08-01 via `app.server.test_client()`
    against `avocadodash:dev` — registration and layout/dependency
    serving both succeed. Dispatch-count settling still to be confirmed
    visually in Task 3.

- [x] **Task 2**: `encode_filters_to_query` / `decode_query_to_filters`
      for V1 fields (region, type, start, end)
  - **Acceptance**: All validation/fallback rules from the spec
    implemented, including all-invalid-region → `["Albany"]`, mixed
    valid/invalid region → valid subset only, `region` key present-empty
    → `[]`, `region` key absent → default; fixed, deterministic param
    order in the encoder
  - **Files**: `src/app.py`
  - **Tests**: `tests/test_app.py` — table-driven cases per the spec's
    Testing Strategy (V1 subset)
  - **Effort**: S

### Features (Build Second)
- [x] **Task 3**: Add `dcc.Location` + `sync_url_and_filters` callback
      (V1 scope: region/type/date-range only)
  - **Acceptance**: All 5 issue #36 Gherkin scenarios pass manually via
    `make run`; app starts cleanly (no circular-dependency error)
  - **Files**: `src/app.py`
  - **Tests**: none yet (covered by Task 4)
  - **Effort**: S

- [x] **Task 4**: Automated tests for V1 callback behavior
  - **Acceptance**: Both directions tested (`triggered_id="url"` and
    `triggered_id=<filter id>`), idempotency test (repeated identical
    filter state → `no_update` on `url.search`), round-trip
    stabilization test (non-canonical input URL settles in ≤2 conceptual
    dispatches)
  - **Files**: `tests/test_app.py`
  - **Tests**: this task *is* the tests
  - **Effort**: S

### Integration (Build Third)
- [x] **Task 5**: Extend codec + callback to V2 fields (x-axis, y-axis,
      box-plot-column, box-plot-groupby)
  - **Acceptance**: Same callback (not a new one) gains 4 more
    Inputs/Outputs and 4 more query keys; all 3 issue #47 Gherkin
    scenarios pass manually via `make run`
  - **Files**: `src/app.py`
  - **Tests**: none yet (covered by Task 6)
  - **Effort**: S

- [x] **Task 6**: Automated tests for V2 fields
  - **Acceptance**: Same test shape as Task 4, extended to the 4 new
    fields plus their individual validation/fallback cases
  - **Files**: `tests/test_app.py`
  - **Effort**: S

### Polish (Build Last)
- [x] **Task 7**: Quality gate pass
  - **Acceptance**: `make lint`, `make format-check`, `make typecheck`,
    `make test` all green; coverage stays ≥80%; manual full-scope
    walkthrough (`make run`): change each of the 7 controls, copy the
    URL, open in a new tab, confirm exact restore; edit URL to an invalid
    region and reload, confirm fallback with no error dialog
  - **Files**: n/a
  - **Effort**: XS

## Findings During Implementation

- **`make run` is broken, pre-existing, unrelated to this feature**: the
  `run` target (`Makefile:16-22`) invokes `poetry run python src/app.py`
  against `$(IMAGE_NAME):latest` — the **production** image built by
  `make docker-build`. Per this repo's own Dockerfile design (documented
  in `CLAUDE.md`), the production stage deliberately has no `poetry`
  installed, so `make run` fails immediately with `exec: "poetry":
  executable file not found in $PATH`. Worked around for this session's
  manual verification by running `avocadodash:dev` directly with the same
  volume mount/port/env instead. Not fixed here — out of scope for this
  story — but flagged for a follow-up fix (likely: `run` should target
  `$(IMAGE_NAME):dev`, matching how `test`/`lint`/`format*` already do).

## Effort Estimate

**Total Estimated Effort**: S–M (roughly 1–1.5 days), consistent with
both issues being individually sized "M" but sharing one mechanism
instead of two.

| Phase | Effort |
|-------|--------|
| Foundation (spike + V1 codec) | S |
| Features (V1 callback + tests) | S |
| Integration (V2 extension + tests) | S |
| Polish | XS |
