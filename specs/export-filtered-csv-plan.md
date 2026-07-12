# Implementation Plan: Export the Filtered Dataset as CSV

**Spec**: `specs/export-filtered-csv.md`
**Created**: 2026-07-12
**Status**: approved

## Components

### 1. Export controls callback (`update_download_controls`)
- **Purpose**: Enable/disable the download button and show a "no data to
  export" message based on the current filters.
- **Files**: `src/app.py`
- **Effort**: S

### 2. Download callback (`download_filtered_csv`)
- **Purpose**: Build the CSV payload for the current filter selection via
  `dcc.send_data_frame`.
- **Files**: `src/app.py`
- **Effort**: S

### 3. Layout
- **Purpose**: `export-section` div (button, status span, `dcc.Download`)
  in `app.layout`.
- **Files**: `src/app.py`
- **Effort**: XS

### 4. Styling
- **Purpose**: `.export-section` / `.download-button` / `.download-status`
  CSS rules.
- **Files**: `src/assets/style.css`
- **Effort**: XS

### 5. Tests
- **Purpose**: Cover all 3 Gherkin scenarios from issue #6.
- **Files**: `tests/test_app.py`
- **Effort**: S

## Dependencies

### Build Order
1. Layout (button/status/`dcc.Download` need to exist for callbacks to
   target)
2. `update_download_controls` (no dependency on callback 2)
3. `download_filtered_csv` (independent of callback 1, but tested against
   the same filter fixtures)
4. CSS (independent, can happen alongside 1-3)
5. Tests (written alongside each step, TDD)

### External Dependencies
None.

## Risks & Assumptions

### Risks
- **Risk**: Relying solely on the disabled button to prevent empty
  downloads could break if a client bypasses `disabled` (e.g. a stale
  `n_clicks` fires before the UI re-renders). Mitigated by having
  `download_filtered_csv` independently re-check emptiness and return
  `dash.no_update` rather than trusting `update_download_controls` alone.

### Assumptions
- `dcc.send_data_frame(df.to_csv, filename, index=False)` returns a plain
  (non-base64) `content` string for CSV, confirmed by a quick manual check
  against the project's Dash version — safe to assert on `result["content"]`
  directly in tests.

## Milestones

- [ ] `download_filtered_csv` returns a CSV payload whose parsed content
      exactly matches the filtered slice, for a known filter combination.
- [ ] `download_filtered_csv` returns `dash.no_update` for an empty
      filter combination.
- [ ] `update_download_controls` disables the button + shows the message
      only when the filter combination is empty.
- [ ] Button/status/`dcc.Download` wired into `app.layout`, visually
      verified via `make run`.
- [ ] `poetry run pytest` / `make test` green, `make lint` /
      `make format-check` clean.

## Tasks

### Foundation
- [ ] **Task 1**: Add `export-section` div (button, status span,
  `dcc.Download`) to `app.layout`.
  - **Acceptance**: Components exist with the expected ids.
  - **Files**: `src/app.py`
  - **Tests**: `find_component_by_id` lookups.
  - **Effort**: XS

### Features
- [ ] **Task 2**: Add `download_filtered_csv` callback.
  - **Acceptance**: Non-empty filter → CSV payload matches filtered rows +
    correct header; empty filter → `dash.no_update`.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: Parse `content` back into a DataFrame and compare.
  - **Effort**: S
- [ ] **Task 3**: Add `update_download_controls` callback.
  - **Acceptance**: Empty filter → `disabled=True` + message; non-empty →
    `disabled=False` + empty message.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: Direct calls with fixture filter combinations.
  - **Effort**: S

### Integration
- [ ] **Task 4**: Wire both callbacks + layout together, exception-safety
  test mirroring the existing four callbacks' try/except pattern.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: `patch(..., side_effect=RuntimeError(...))` style test.
  - **Effort**: S

### Polish
- [ ] **Task 5**: Style the export section.
  - **Files**: `src/assets/style.css`
  - **Effort**: XS

## Effort Estimate

**Total**: S (matches issue #6's own estimate)
