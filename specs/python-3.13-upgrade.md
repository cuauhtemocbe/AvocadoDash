---
title: Upgrade Python Base Image and Constraint to 3.13
status: draft
created: 2026-08-08
updated: 2026-08-08
issue: #65
---

# Upgrade Python Base Image and Constraint to 3.13

## Objective

Move AvocadoDash's runtime from Python 3.12 to 3.13 across the Docker images
and the Poetry constraint, so the project tracks the Python version now
standardized across the maintainer's other projects, while keeping the
repo's existing floating-tag / digest-pinning conventions intact.

## Context

The project currently constrains Python to `>=3.12,<3.13` in
`pyproject.toml` and builds all Docker stages from `python:3.12-slim`
(floating tag for `base`/`dev`/`builder`, digest-pinned for `production`,
per the policy documented in `CLAUDE.md`). The maintainer wants to
standardize on 3.13. Dependencies are lightweight (pandas, dash,
sentry-sdk) with no known 3.13 incompatibilities, so this is a mechanical
version bump rather than a risky migration — effort is estimated as S.

This spec formalizes GitHub issue #65, which already contains a full
Gherkin acceptance-criteria set; that issue remains the tracking issue and
is not duplicated here beyond what's needed for planning.

## Requirements

### Functional Requirements

- [ ] `Dockerfile` line 1 (`base` stage, used by `dev`/`builder`): `FROM python:3.12-slim` → `FROM python:3.13-slim` (stays a floating tag, per existing policy)
- [ ] `Dockerfile` line 54 (`production` stage): `FROM python:3.12-slim@sha256:...` → new digest resolved for current `python:3.13-slim`
- [ ] `pyproject.toml` line 9: `python = ">=3.12,<3.13"` → `python = ">=3.13,<3.14"`
- [ ] `pyproject.toml` line 26: `[tool.ruff] target-version = "py312"` → `"py313"`
- [ ] `poetry.lock` regenerated (`poetry lock`) so the `python-versions` marker and resolved versions match the new constraint, keeping `lock-check` CI green
- [ ] `CLAUDE.md` version-specific mentions (`3.12.13`, `py312`, `>=3.12,<3.13`, `python:3.12-slim`, the "72 CRITICAL/HIGH vs. 11" Trivy comparison) updated to the 3.13 equivalents to avoid documentation drift
- [ ] `README.md` Python badge (`Python-3.12.6-blue`) and prose (`Python 3.12.6`) updated to the new resolved 3.13.x patch version
- [ ] `.trivyignore.yaml` header comment (references `python:3.12-slim`) updated to `python:3.13-slim`

### Non-Functional Requirements

- [ ] Compatibility: production and dev images build successfully with no errors on `python:3.13-slim`
- [ ] Quality: `make lint` and `make test` pass inside the 3.13 dev image, coverage stays at or above the existing 80% floor (`--cov-fail-under=80`)
- [ ] Reliability: production container reports `docker inspect` health status `healthy` after the configured start-period
- [ ] CI: `lint`, `test`, `lock-check`, `license-check`, `trivy-fs` checks stay green (required by branch protection)

## Architecture

### Components

No new components — this is a version-bump change touching existing
infrastructure files only:

- `Dockerfile` — `base`, `dev`, `builder`, `production` stages
- `pyproject.toml` — Python constraint, ruff target-version
- `poetry.lock` — regenerated lock file
- `CLAUDE.md`, `README.md`, `.trivyignore.yaml` — documentation/comments referencing the version

### Data Model

Not applicable — no data model changes.

### External Dependencies

- `python:3.13-slim` (Docker Hub) — new base image tag/digest for all four Dockerfile stages
- No application dependency (pandas, dash, sentry-sdk) version changes required; existing constraints in `pyproject.toml` already support Python 3.13

## User Stories

See GitHub issue #65 for the full user story and Gherkin acceptance
criteria (reproduced in Testing Strategy below).

## Testing Strategy

### Build Verification

```gherkin
Feature: Upgrade Python base image and constraint in AvocadoDash

  Scenario: Production image builds on the new Python version
    Given the Dockerfile's production stage points to the new python:3.13-slim digest
    When the image is built with "docker build --target production -t avocado-dash ."
    Then the build completes successfully with no errors

  Scenario: Dev image builds on the new Python version
    Given the Dockerfile's dev stage now derives from python:3.13-slim
    When the image is built with "make docker-build-dev"
    Then the build completes successfully with no errors

  Scenario: Quality gates pass on Python 3.13
    Given the dev image is built on python:3.13-slim
    When "make lint" and "make test" run inside it
    Then both complete successfully and coverage stays at or above the existing 80% floor

  Scenario: Production container passes its health check
    Given the production image built on python:3.13-slim is running
    When the container has been up for at least the configured start-period
    Then "docker inspect" reports the container health status as "healthy"

  Scenario: pyproject.toml constraint matches the new Python version
    Given pyproject.toml declares "python = \">=3.12,<3.13\""
    When the Dockerfiles are updated to python:3.13-slim
    Then the constraint becomes ">=3.13,<3.14" and ruff's target-version becomes "py313"
```

### Unit / Integration Tests

No new tests required — the existing `pytest` suite (run via `make test`
inside the rebuilt 3.13 dev image) is the regression check that the app
still behaves correctly on the new interpreter.

### CI Verification

Push to a branch and confirm all five required checks (`lint`, `test`,
`lock-check`, `license-check`, `trivy-fs`) report green before merging.

## Boundaries & Constraints

### In Scope

- Bumping the Python version used by this repo's Docker images and Poetry constraint from 3.12 to 3.13
- Updating documentation (`CLAUDE.md`, `README.md`, `.trivyignore.yaml`) that hard-codes the old version
- Regenerating `poetry.lock`

### Out of Scope

- `.github/workflows/dependabot-socket-firewall.yml`'s `python-version: "3.12"` — this pins the *CI runner's* Python for installing the Socket Firewall CLI tool, decoupled from the app runtime; not part of this change
- Any application dependency version bumps beyond what `poetry lock` naturally re-resolves under the new Python constraint
- Changing the digest-pinning policy itself (floating `base`/`dev`/`builder`, digest-pinned `production`) — this spec follows the existing policy, doesn't revisit it
- Re-evaluating the `.trivyignore.yaml` CVE exceptions — they're Debian-base-image findings independent of the Python version and may still apply after the bump; only the comment's version reference is updated here

### Technical Constraints

- Must preserve the four-stage Dockerfile structure (`base`/`builder`/`dev`/`production`) and the floating-tag vs. digest-pin asymmetry documented in `CLAUDE.md`
- Must use a currently-maintained tag (`python:3.13-slim`), not a frozen historical patch tag, consistent with the repo's documented rationale
- `poetry.lock` must stay in sync with `pyproject.toml` (`poetry check --lock` / `make lock-check`)

## Success Criteria

- [ ] All five Gherkin scenarios above verified (production build, dev build, lint+test in 3.13, healthcheck, constraint match)
- [ ] CI required checks green: `lint`, `test`, `lock-check`, `license-check`, `trivy-fs`
- [ ] No remaining references to `3.12`/`py312` in `Dockerfile`, `pyproject.toml`, `CLAUDE.md`, `README.md`, `.trivyignore.yaml` (except the intentionally out-of-scope CI-runner pin)
- [ ] Code review approved, issue #65 closed with evidence

## Implementation Plan

See `specs/python-3.13-upgrade-plan.md` (created in Phase 2, after this
spec is approved).
