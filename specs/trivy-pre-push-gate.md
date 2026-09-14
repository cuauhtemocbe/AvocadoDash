---
title: Fail-Closed Trivy Pre-Push CVE Gate
status: in-progress
created: 2026-09-14
updated: 2026-09-14
issue: meta-projects#41
---

# Fail-Closed Trivy Pre-Push CVE Gate

## Objective

Add a `pre-push` git hook that runs Trivy's filesystem vulnerability scanner
and blocks the push if it finds any CRITICAL-severity, fixable CVE — and
also blocks the push if Trivy itself isn't installed. This is AvocadoDash's
slice of a fleet-wide rollout (meta-projects issue #41) standardizing a
local, fail-closed CVE gate across repos before code leaves a developer's
machine.

## Context

AvocadoDash already has a versioned, opt-in hooks directory: `.githooks/`,
containing `pre-commit`, activated once per clone via `make install-hooks`
(sets `core.hooksPath` to `.githooks` — see `README.md`). That existing
`pre-commit` hook runs `make secret-scan` (gitleaks, `--staged`) plus the
full `make validate` suite (lint/format-check/typecheck/test) inside
Docker. There is currently no local gate for known CVEs in dependencies —
`/trivy-scan` exists as an on-demand skill, and CI has a `trivy-fs` check
(per `CLAUDE.md`), but nothing stops a developer from pushing a branch that
introduces a CRITICAL, fixable vulnerability before CI ever runs.

The activation mechanism (`.githooks/` + `make install-hooks`) already
exists and is already documented in `README.md`; this change only adds a
new hook file to that existing directory. No new install script, no changes
to how hooks are activated.

Unlike `pre-commit` (which orchestrates everything through `make` targets
inside Docker), this hook calls the `trivy` CLI directly on the host. Trivy
is not currently a project dependency (no Docker image bundles it), so the
hook must fail closed — block the push — if `trivy` isn't found on `PATH`,
rather than silently skipping the scan.

## Requirements

### Functional Requirements

- [ ] A new `.githooks/pre-push` hook runs on `git push` once
      `make install-hooks` has been run (same activation as the existing
      `pre-commit` hook — `core.hooksPath` already points at `.githooks`).
- [ ] The hook checks for `trivy` on `PATH`. If missing, it prints a message
      pointing to `.claude/skills/trivy-scan/setup.md` and exits non-zero,
      blocking the push (fail closed, not skip-if-missing).
- [ ] If `trivy` is present, the hook runs
      `trivy fs . --scanners vuln --severity CRITICAL --exit-code 1 --ignore-unfixed --quiet`
      against the repo root.
- [ ] If Trivy finds any CRITICAL-severity vulnerability with an available
      fix, the hook exits non-zero and the push is blocked.
- [ ] If Trivy finds no such vulnerability, the hook exits 0 and the push
      proceeds.

### Non-Functional Requirements

- [ ] No new activation mechanism: reuses `.githooks/` + `make
      install-hooks` exactly as-is; the hook file itself is the only new
      artifact.
- [ ] No changes to `.githooks/pre-commit`, `Makefile`, or the existing
      `README.md` `install-hooks` documentation beyond, at most, a single
      line noting pre-push now also runs a scan.
- [ ] The hook does not require Docker (unlike `pre-commit`) — it depends
      only on `trivy` being present on the developer's host `PATH`, since
      pre-push checks are expected to run fast and Trivy is a single static
      binary.
- [ ] Fail-closed by design: any condition that prevents the scan from
      actually running (missing binary) blocks the push rather than letting
      it through silently, matching the fleet-wide gate's intent.

## Architecture

### Components

- `.githooks/pre-push` (new): POSIX-ish bash script, `set -uo pipefail`
  (deliberately not `-e`, since the script's own `if` branches handle both
  failure paths and must reach their explicit `exit` statements). Two
  gated steps:
  1. `command -v trivy` check → exit 1 with a setup-doc pointer if absent.
  2. `trivy fs . --scanners vuln --severity CRITICAL --exit-code 1
     --ignore-unfixed --quiet` → its exit code determines the hook's exit
     code.
- No wrapper `make` target is introduced — this intentionally diverges from
  `pre-commit`'s `make`-orchestrated style, since Trivy runs directly on
  the host rather than inside a Docker image built by this repo's tooling.

### Data Model

N/A — no persisted state; this is git-hook tooling only.

### External Dependencies

- [Trivy](https://github.com/aquasecurity/trivy) CLI: must be present on
  the developer's `PATH`. Installed per `.claude/skills/trivy-scan/setup.md`
  (the same setup doc the `/trivy-scan` skill already uses).

## User Stories

Tracked at the fleet level in meta-projects issue #41 (cross-repo rollout
of a local, fail-closed Trivy pre-push gate). No repo-local GitHub issue is
created for this slice; this spec is the tracking artifact.

## Testing Strategy

### Unit Tests

N/A — no application code changes; this is shell tooling outside `src/`
and outside pytest's `pythonpath` scope.

### Integration Tests

Manual verification (this is a git hook, not app code with an automated
test harness):

- With `trivy` absent from `PATH`: `git push` (or direct hook invocation)
  fails with the "trivy not found" message and non-zero exit.
- With `trivy` present and the repo clean of CRITICAL fixable CVEs:
  `trivy fs . --scanners vuln --severity CRITICAL --exit-code 1
  --ignore-unfixed --quiet` exits 0, hook exits 0, push proceeds.
- (Not exercised here, left as a fleet-level pattern already proven by
  CI's existing `trivy-fs` check): a CRITICAL fixable CVE present would
  make Trivy exit 1, and the hook propagates that as a blocked push.

### E2E Tests

N/A — no user-facing flow; verified by directly invoking
`.githooks/pre-push` and by the `git push` that lands this change.

## Boundaries & Constraints

### In Scope

- One new hook file, `.githooks/pre-push`, wired into the existing
  `.githooks/` + `make install-hooks` activation mechanism.
- Fail-closed behavior for both "Trivy missing" and "CRITICAL fixable CVE
  found."

### Out of Scope

- Any new hook-activation/install script (`.githooks/` and `make
  install-hooks` already exist and are already documented).
- Changes to `.githooks/pre-commit`, `Makefile`, or CI's existing
  `trivy-fs` workflow check.
- Scanning severities other than CRITICAL, or scanners other than `vuln`
  (e.g. secret/misconfig scanning — secrets are already covered by
  `pre-commit`'s `make secret-scan`).
- Auto-installing Trivy on behalf of the developer (the hook points to the
  setup doc instead).

### Technical Constraints

- Hook script must be POSIX-compatible bash (`#!/usr/bin/env bash`),
  executable (`chmod +x`), and committed under version control in
  `.githooks/` per the existing pattern.
- Must not assume Docker is running or available, unlike `pre-commit`.

## Success Criteria

- [ ] `.githooks/pre-push` exists, is executable, and matches the
      fleet-wide gate's exact script contract (trivy-presence check, then
      `trivy fs . --scanners vuln --severity CRITICAL --exit-code 1
      --ignore-unfixed --quiet`).
- [ ] Running `trivy fs . --scanners vuln --severity CRITICAL
      --ignore-unfixed` against the current repo returns clean (no
      CRITICAL fixable CVEs), confirming the gate starts from a passing
      state.
- [ ] `make install-hooks` (unchanged) activates the new hook alongside the
      existing `pre-commit` hook, with no separate opt-in step.
- [ ] No changes made to `.githooks/pre-commit`, `Makefile`, or app source.

## Implementation Plan

No separate `-plan.md` file — the implementation is a single, fully
specified hook script (see Architecture above) with no components to
sequence or estimate.
