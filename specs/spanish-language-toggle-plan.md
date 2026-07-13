# Implementation Plan: Spanish/English Language Toggle

**Spec**: `specs/spanish-language-toggle.md`
**Created**: 2026-07-13
**Status**: approved

## Components

### 1. `src/translations.py` (new module)
- **Purpose**: `TRANSLATIONS` nested dict (`lang -> dotted-key -> str`) +
  `t(key, lang)` lookup helper. Single source of truth for every cosmetic
  string in both languages.
- **Files**: `src/translations.py`
- **Effort**: M

### 2. Language toggle control + new ids on static text
- **Purpose**: `language-toggle` `dcc.RadioItems` in the header; add `id`s
  to the currently id-less brand subtitle, section headers (`H2` x2),
  header description paragraph, footer text so they're targetable.
- **Files**: `src/app.py`
- **Effort**: S

### 3. `update_ui_language` callback (new)
- **Purpose**: One callback, `Input("language-toggle", "value")`, many
  Outputs — retranslates every static/filter-independent element: filter
  labels + tooltips, section headers, header/footer text, download button
  text, and dropdown *option labels* (region placeholder, type, x-axis,
  y-axis, box-plot-column, box-plot-groupby) without touching `value`s.
- **Files**: `src/app.py`
- **Effort**: M

### 4. Thread `lang` through the 5 data callbacks + chart builders
- **Purpose**: Add `Input("language-toggle", "value")` to
  `update_summary_panel`, `update_download_controls`, `update_charts`,
  `update_scatter_chart`, `update_box_plot`; add a `lang` parameter to
  `create_price_chart`, `create_volume_chart`, `create_box_plot`,
  `create_scatter_chart`, `create_summary_panel`, `empty_state_figure`,
  `filter_data`'s callers (not `filter_data` itself — untouched), replacing
  every hardcoded title/axis-title/hover-word/card-label with
  `translations.t(key, lang)`. Also replaces `col.replace("_", " ").title()`
  with the new explicit column-name lookup (fixes "Averageprice").
- **Files**: `src/app.py`
- **Effort**: L

### 5. Tests
- **Purpose**: Cover all Functional Requirements + regression-proof that
  filtering/query logic is untouched.
- **Files**: `tests/test_translations.py` (new), `tests/test_app.py`
- **Effort**: L

## Dependencies

### Build Order
1. `translations.py` (everything else depends on it existing)
2. Language toggle control + new ids (needed before callback 3/4 can
   target them)
3. `update_ui_language` callback (independent of step 4)
4. Thread `lang` through data callbacks + chart builders (independent of
   step 3, but tested against the same `translations.py`)
5. Tests (written alongside steps 3-4, TDD)

### External Dependencies
None.

## Risks & Assumptions

### Risks
- **Risk**: Forgetting a string during the manual port from hardcoded
  English to `TRANSLATIONS` lookups (e.g. missing one hover-template word).
  Mitigated by the exhaustive inventory already captured in the spec, plus
  the `TRANSLATIONS["es"].keys() == TRANSLATIONS["en"].keys()` test — any
  key added for one language but not the other fails immediately, and a
  manual `make run` pass double-checks visually.
- **Risk**: Column display-name lookup accidentally changes a `value` used
  in `data.query()`/DataFrame column access instead of just the `label`.
  Mitigated by keeping `filter_data()` completely untouched and by the
  existing (unmodified) filter-correctness tests continuing to pass — any
  accidental value change would break them immediately.

### Assumptions
- Updating a `dcc.Dropdown`'s `options` prop via callback does not reset
  its current `value` prop (standard Dash behavior) — confirmed this is
  how Dash works, so filter selections survive a language toggle without
  extra `State` plumbing.

## Milestones

- [ ] `translations.py` complete with identical ES/EN key sets (test-
      enforced).
- [ ] Toggling `language-toggle` updates every static label/tooltip/button/
      dropdown-option-label with `value`s unchanged.
- [ ] Toggling `language-toggle` updates all 4 chart titles/axis titles/
      hover words and the 5 summary-panel card labels, using the currently
      filtered data (not resetting filters).
- [ ] `poetry run pytest` / `make test` green, `make lint` /
      `make format-check` clean.
- [ ] Manual `make run` check: select 2 regions + custom date range, toggle
      ES→EN→ES, confirm selections survive and all text updates.

## Tasks

### Foundation
- [ ] **Task 1**: Create `src/translations.py` with the full `TRANSLATIONS`
  dict (both languages, every key from the spec's Full String Inventory)
  and `t(key, lang)`.
  - **Acceptance**: `TRANSLATIONS["es"]` and `TRANSLATIONS["en"]` have
    identical key sets; `t()` returns the right string per key/lang.
  - **Files**: `src/translations.py`, `tests/test_translations.py`
  - **Tests**: key-set parity test, spot-check `t()` calls for both
    languages.
  - **Effort**: M

### Features
- [ ] **Task 2**: Add `language-toggle` `dcc.RadioItems` to the header
  layout; add missing `id`s to brand subtitle, `H2` section headers,
  header description, footer text.
  - **Acceptance**: All previously id-less static text elements are now
    targetable by id; toggle renders with `ES`/`EN`, default `"es"`.
  - **Files**: `src/app.py`
  - **Tests**: `find_component_by_id` lookups for the new ids.
  - **Effort**: S
- [ ] **Task 3**: Add `update_ui_language` callback covering all static
  text (labels, tooltips, section headers, header/footer, download button,
  dropdown option labels).
  - **Acceptance**: Calling the callback with `"es"`/`"en"` returns the
    correct translated `children`/`options` for every targeted output;
    dropdown option `value`s identical between calls.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: direct callback invocation with both language values,
    assert translated text + unchanged values.
  - **Effort**: M
- [ ] **Task 4**: Add `lang` parameter to `create_price_chart`,
  `create_volume_chart`, `create_box_plot`, `create_scatter_chart`,
  `create_summary_panel`, `empty_state_figure`; replace hardcoded
  titles/axis titles/hover words/card labels with `translations.t()`
  lookups; replace `.title()`-based column/group-by display names with the
  explicit lookup.
  - **Acceptance**: Each builder produces translated text for `lang="es"`
    and `lang="en"` while numeric/data content is identical regardless of
    `lang`.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: parametrized `lang` cases added to each builder's existing
    tests.
  - **Effort**: L
- [ ] **Task 5**: Add `Input("language-toggle", "value")` to
  `update_summary_panel`, `update_download_controls`, `update_charts`,
  `update_scatter_chart`, `update_box_plot`; thread `lang` through to the
  builders from Task 4 and to the empty-state/error-prefix strings.
  - **Acceptance**: Each of these 5 callbacks returns translated content
    for the currently filtered data, for both languages, without altering
    which rows are included.
  - **Files**: `src/app.py`, `tests/test_app.py`
  - **Tests**: `lang="es"`/`lang="en"` parametrized cases added to each
    callback's existing filter-combination tests; existing exception-
    handling tests extended to also assert the translated `"Error: "`
    prefix.
  - **Effort**: L

### Integration
- [ ] **Task 6**: Full-suite regression pass + manual `make run` check
  (toggle survives filter selections; visually confirm no leftover English
  strings in Spanish mode and vice versa).
  - **Files**: n/a (verification only)
  - **Effort**: S

## Effort Estimate

**Total**: M-L (largest single-session feature so far in this repo; touches
every callback and all 4 chart builders, but each change is mechanical
once `translations.py` exists)

| Phase | Effort |
|-------|--------|
| Foundation (`translations.py`) | M |
| Features (toggle, static callback, chart/data callbacks) | L |
| Integration & manual verification | S |
