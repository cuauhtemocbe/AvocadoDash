---
title: Statistical Price Anomaly Flags
status: approved
created: 2026-08-09
updated: 2026-08-09
issue: #39
---

# Statistical Price Anomaly Flags

## Objective

Visually flag price points on the price chart that deviate more than a
configurable number of standard deviations from their region's mean over
the currently selected date range, so a data analyst can spot unusual
spikes/drops without manually scanning the data.

## Context

Part of the "Data & Forecasting Research" milestone (issue #39). The
sibling research spike (#38) backtested rolling-window statistics for
forecasting and found no benefit over a naive baseline — that result is
why this story computes anomalies over the whole selected range rather
than a rolling window (already decided in the issue itself, not
re-litigated here).

## Requirements

### Functional Requirements

- [ ] A new pure function `detect_price_anomalies(prices, std_threshold=2.0)`
      in `src/utils.py`, returning a boolean mask.
- [ ] `create_price_chart` (only — not `create_volume_chart`, not the
      shared `_region_traces` helper) adds a separate anomaly-marker
      trace per region that has any anomalies.
- [ ] Anomaly markers: one fixed color/symbol (not per-region), one
      shared "Anomaly" legend entry via `legendgroup` (not one per
      region).
- [ ] Deviation rule: strictly greater than the threshold (`> 2.0`, not
      `>=`).
- [ ] Fewer than 2 points in a region's range → no anomalies (std is
      undefined), no exception.

### Non-Functional Requirements

- [ ] Consistent with existing code style: pure function in `utils.py`
      following `calculate_summary_stats`/`find_region_extremes`'s
      pattern; chart-building stays in `app.py`.

## Architecture

### Components

- `utils.detect_price_anomalies(prices: pd.Series, std_threshold: float = 2.0) -> pd.Series[bool]`
  — whole-range mean/std per call; caller passes one region's series at
  a time.
- `app._anomaly_traces(filtered_data, std_threshold) -> list[dict]` —
  new private helper, mirrors `_region_traces`'s per-region loop but
  only emits a trace for regions with ≥1 anomaly; sets
  `legendgroup="anomaly"` and `showlegend=True` only on the first
  emitted trace.
- `create_price_chart` calls `_anomaly_traces` and appends its output
  to the existing region-line traces.

## Testing Strategy

### Unit Tests

- `detect_price_anomalies`: boundary values (2.0 → False, 2.01 → True),
  <2 points → all False, no-anomaly series → all False, std==0 (flat
  series) → all False (no div-by-zero).
- `create_price_chart`: anomaly marker present/absent, single shared
  legend entry across multiple regions with anomalies, empty-state path
  unchanged (anomaly logic never invoked when `filtered_data` is empty
  — already true today since callers short-circuit before calling
  `create_price_chart`).

## Boundaries & Constraints

### Out of Scope

- Rolling-window anomaly detection (evaluated and deferred by #38).
- Anomaly flags on volume/scatter/box-plot charts.

## Success Criteria

- [ ] All 5 Gherkin scenarios from issue #39 covered by passing tests
- [ ] `make lint` / `make format-check` / `make typecheck` / `make test`
      green

## Implementation Plan

Single-pass implementation (small, well-scoped M-effort story — no
separate plan file needed):

1. `detect_price_anomalies` in `utils.py` + unit tests
2. `_anomaly_traces` + wire into `create_price_chart` in `app.py` +
   tests
3. Translation key for the "Anomaly" legend label (ES/EN)
4. Full quality gate
