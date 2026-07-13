# Implementation Plan: Structured Error Logging in Callbacks

**Spec**: `specs/structured-error-logging.md`
**Created**: 2026-07-12
**Status**: approved

## Components

### 1. Logger setup
- **Purpose**: Module-level `logging.Logger` instance for `src/app.py`.
- **Files**: `src/app.py`
- **Effort**: XS

### 2. Replace `print()` calls
- **Purpose**: Swap all 6 `except` block `print()` calls for
  `logger.error(..., exc_info=True)`.
- **Files**: `src/app.py`
- **Effort**: XS

### 3. Tests
- **Purpose**: Cover both Gherkin scenarios from issue #8.
- **Files**: `tests/test_app.py`
- **Effort**: S

## Dependencies

### Build Order
1. Logger setup (needed before any callback can use it)
2. Replace `print()` calls (depends on 1)
3. Tests (written alongside step 2)

### External Dependencies
None.

## Risks & Assumptions

### Risks
- **Risk**: `caplog` doesn't capture records by default unless propagation
  is enabled and level is set. Mitigated by using `caplog.at_level`/
  `caplog.set_level(logging.ERROR)` and not disabling propagation on the
  module logger.

### Assumptions
- Railway's log viewer captures stdout/stderr, and Python's `logging`
  module writes to stderr by default with no handler configured — so no
  extra handler setup is needed for logs to reach Railway.

## Milestones

- [ ] All 6 callbacks log via `logger.error(..., exc_info=True)` instead of
      `print()`.
- [ ] `grep -n "print(" src/app.py` returns nothing.
- [ ] `poetry run pytest` / `make test` green, `make lint` /
      `make format-check` clean.

## Tasks

### Foundation
- [ ] **Task 1**: Add `import logging` and `logger =
  logging.getLogger(__name__)` to `src/app.py`.
  - **Acceptance**: Logger is importable/usable from callbacks.
  - **Files**: `src/app.py`
  - **Tests**: Covered indirectly by Task 2's tests.
  - **Effort**: XS

### Features
- [ ] **Task 2**: Replace all 6 `print(f"Error in ... callback: {str(e)}")`
  calls with `logger.error(f"...", exc_info=True)`, keeping messages and
  fallback returns unchanged.
  - **Acceptance**: No `print(` remains in `src/app.py`; each `except`
    block logs at `ERROR` with traceback.
  - **Files**: `src/app.py`
  - **Tests**: Update the 6 existing
    `..._handles_exception_without_crashing` tests with `caplog` assertions.
  - **Effort**: S

### Integration
- [ ] **Task 3**: Add a test asserting no `print(` occurrences remain in
  `src/app.py` (Scenario 2).
  - **Files**: `tests/test_app.py`
  - **Effort**: XS

## Effort Estimate

**Total**: XS (matches issue #8's own estimate)
