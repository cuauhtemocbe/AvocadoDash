---
title: Structured Error Logging in Callbacks
status: approved
created: 2026-07-12
updated: 2026-07-12
issue: #8
---

# Structured Error Logging in Callbacks

## Objective

Replace the `print()` calls in `src/app.py`'s callback `except` blocks with
Python's `logging` module, so callback errors are visible and searchable in
Railway's log viewer instead of only appearing on stdout.

## Context

GitHub issue #8 requests this. All six `@app.callback` functions in
`src/app.py` (`update_summary_panel`, `update_download_controls`,
`download_filtered_csv`, `update_charts`, `update_scatter_chart`,
`update_box_plot`) follow the same try/except pattern documented in
`CLAUDE.md`: catch broadly, `print()` the error, return a fallback/error
value. `print()` output isn't leveled, isn't structured, and is harder to
find/filter in a production log viewer than a proper logging call.

## Requirements

### Functional Requirements

- [x] A module-level `logging.Logger` is configured in `src/app.py`.
- [x] Each of the six callback `except` blocks logs the caught exception at
      `ERROR` level via the logger, including the traceback (`exc_info=True`).
- [x] No `print()` calls remain in `src/app.py`.
- [x] Existing fallback return values (empty figures, error messages,
      `no_update`, etc.) are unchanged — this is a logging-only change.

### Non-Functional Requirements

- [x] No new runtime dependency (`logging` is stdlib).
- [x] Testable without a browser: log output is asserted via pytest's
      `caplog` fixture against the existing directly-invoked callback tests.

## Architecture

### Components

- `src/app.py`:
  - New module-level `import logging` + `logger =
    logging.getLogger(__name__)`, placed with the existing imports.
  - Each `except Exception as e: print(...)` becomes `except Exception as e:
    logger.error(..., exc_info=True)`, keeping the same descriptive message
    text and the existing fallback return statement.

### Data Model

N/A.

### External Dependencies

None added.

## User Stories

See GitHub issue #8 for the full user story and Gherkin acceptance criteria.

## Testing Strategy

### Unit Tests

Extend `tests/test_app.py`:

- Update each of the six existing
  `test_update_*_callback_handles_exception_without_crashing` /
  `test_download_filtered_csv_callback_handles_exception_without_crashing`
  tests to also use `caplog` (set to `logging.ERROR`) and assert a record
  was emitted at `ERROR` level with the exception traceback present
  (`record.exc_info` is not `None`), in addition to the existing
  return-value assertions.
- New test: scan `src/app.py`'s source text and assert no `print(`
  occurrences remain, covering Gherkin Scenario 2 directly.

### Integration Tests

Not needed — no external logging backend to integrate against; stdlib
`logging` output is captured directly via `caplog`.

### E2E Tests

Out of scope.

## Boundaries & Constraints

### In Scope

- Converting the six existing `print()` calls in callback error handling to
  `logging` calls.

### Out of Scope

- Configuring log handlers/formatters/log level for production (Railway
  captures stdout/stderr regardless of handler config; default `logging`
  behavior is sufficient).
- Logging outside of callback `except` blocks (e.g. `load_data()`'s
  exceptions, which already propagate rather than being caught/printed).
- Structured (JSON) log formatting — out of scope per issue #8, which only
  asks for the `logging` module at `ERROR` level.

### Technical Constraints

- Must not add new Python dependencies to `pyproject.toml`.
- Must pass `make lint` / `make format-check`.

## Success Criteria

- [x] All Functional Requirements implemented.
- [x] Both Gherkin scenarios from issue #8 have passing automated tests.
- [x] `make lint` and `make format-check` are clean.
- [x] No existing test regresses.

## Implementation Plan

See `specs/structured-error-logging-plan.md`.
