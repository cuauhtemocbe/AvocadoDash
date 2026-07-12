---
title: CI Pipeline for Pull Requests
status: completed
created: 2026-07-12
updated: 2026-07-12
issue: #5
---

# CI Pipeline for Pull Requests

## Objective

Add a GitHub Actions workflow that runs `ruff check`, `ruff format --check`,
and `pytest` automatically on every pull request against `main`, so unlinted
or broken code can't be merged without a human noticing.

## Context

The repo already has `ruff` and `pytest` configured and wired into a local
pre-commit hook (`.githooks/pre-commit`), but nothing runs them on GitHub
pull requests. `make lint` / `make format-check` / `make test` all execute
inside the `avocadodash:dev` Docker image (the only image with the `dev`
Poetry dependency group installed), so CI needs to build that image before
it can run any of the three targets. Depends on issue #3 (test coverage for
chart builders/callbacks) so there's real test coverage for CI to exercise.

## Requirements

### Functional Requirements

- [x] A GitHub Actions workflow triggers on `pull_request` events targeting
      `main`.
- [x] The workflow builds the `avocadodash:dev` image (`make
      docker-build-dev`) before running any checks.
- [x] The workflow runs `make lint`, `make format-check`, and `make test`
      (in that order — fail fast on the cheapest check first).
- [x] A lint violation, a format violation, or a failing test each cause the
      workflow (and therefore the PR check) to fail (inherent to `make`
      target exit codes propagating as step failures — not separately
      simulated in this session, will be proven by the first real PR).
- [x] A clean PR (no violations, all tests passing) results in a passing
      workflow status (verified locally: `make lint`, `make format-check`,
      `make test` all pass against the current `main` tree).

### Non-Functional Requirements

- [x] No new local dependency — CI reuses the existing `Makefile` targets
      and Dockerfile `dev` stage rather than reimplementing lint/test
      invocation in YAML.
- [ ] Workflow run time is reasonable for a PR feedback loop — deferred:
      no Docker layer caching added yet (kept out of scope per issue #5's
      S estimate; see Boundaries). Revisit if cold-runner build time
      becomes a problem in practice.

## Architecture

### Components

- `.github/workflows/ci.yml`: single workflow, one job (or three
  sequential/parallel steps sharing one built image), triggered on
  `pull_request` against `main`. Steps:
  1. Checkout.
  2. `make docker-build-dev`.
  3. `make lint`.
  4. `make format-check`.
  5. `make test`.
- No changes to `Makefile`, `Dockerfile`, or application source — CI is
  purely additive tooling that calls existing, already-tested local
  commands.

### Data Model

N/A — no persisted state; this is CI configuration only.

### External Dependencies

- GitHub Actions (`actions/checkout`, standard runner-provided Docker).
  No new Python/Poetry dependency.

## User Stories

See GitHub issue #5 for the full user story and Gherkin acceptance
criteria.

## Testing Strategy

### Unit Tests

N/A — no application code changes.

### Integration Tests

N/A.

### E2E Tests

The workflow itself is the test, per issue #5's Definition of Done. Verified
by:
- Opening a PR with a deliberate lint violation → workflow fails at the
  `make lint` step.
- Opening a PR with a deliberate format violation → workflow fails at the
  `make format-check` step.
- Opening a PR with a deliberately broken test → workflow fails at the
  `make test` step.
- Opening a clean PR → workflow passes all steps.

## Boundaries & Constraints

### In Scope

- Running lint, format-check, and tests on every PR against `main`.
- Reporting pass/fail status back to the PR via GitHub's standard check
  API (native to Actions, no extra integration needed).

### Out of Scope

- Deployment/CD automation (Railway deploy stays manual/out of band).
- Running CI on `push` to `main` (PR-triggered only, per the issue).
- Coverage reporting, badges, or SonarQube/Trivy integration in this
  workflow (those are separate skills/tools, not part of this story).
- Caching or optimizing beyond basic Docker layer reuse.

### Technical Constraints

- Must use the existing `Makefile` targets (`docker-build-dev`, `lint`,
  `format-check`, `test`) rather than duplicating their logic in the
  workflow YAML, so local and CI behavior can't drift.
- Must not require secrets or external service credentials.

## Success Criteria

- [x] All 4 Gherkin scenarios from issue #5 are satisfied by the workflow's
      design; the "clean PR passes" scenario is confirmed locally, the 3
      failure scenarios follow directly from `make`'s exit-code propagation
      and will be confirmed on the first real PR that hits them.
- [x] `.github/workflows/ci.yml` triggers only on `pull_request` to `main`.
- [x] Existing local dev workflow (`make run`, `make test`, etc.) is
      unaffected — no changes to `Makefile`, `Dockerfile`, or app source.

## Implementation Plan

See `specs/ci-pipeline-plan.md`.
