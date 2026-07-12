# Implementation Plan: CI Pipeline for Pull Requests

**Spec**: `specs/ci-pipeline.md`
**Created**: 2026-07-12
**Status**: completed

## Components

### 1. `.github/workflows/ci.yml`
- **Purpose**: Single workflow, triggered on `pull_request` against `main`.
  Builds `avocadodash:dev`, then runs `make lint`, `make format-check`,
  `make test` in that order (fail fast on the cheapest checks first).
- **Files**: `.github/workflows/ci.yml`
- **Effort**: S

## Dependencies

### Build Order
1. Workflow file (single, self-contained component — no code changes
   elsewhere).

### External Dependencies
- `actions/checkout@v4` (standard, no new Python/Poetry dependency).
- GitHub-hosted Ubuntu runner's built-in Docker daemon (no extra setup
  action needed).

## Risks & Assumptions

### Risks
- **Risk**: `make docker-build-dev` + three `docker run` invocations could
  be slow on a cold runner cache. Mitigated with `actions/cache` keyed on
  `poetry.lock`/Dockerfile hash for Docker layer reuse; acceptable to skip
  if it complicates the workflow beyond issue #5's scope (effort S) — can
  be added later without changing behavior.
- **Risk**: Makefile targets use `docker run` (not `docker compose`), so
  each `make` target is a separate container invocation reusing the same
  built `:dev` image — confirmed compatible with a single job's steps
  since the image is built once and cached in the runner's local Docker
  daemon for the rest of the job.

### Assumptions
- The GitHub-hosted runner's default Docker installation is sufficient
  (no need for `docker/setup-buildx-action` since we're not pushing images
  or using BuildKit-specific features beyond what `docker build` already
  does).

## Milestones

- [x] Workflow file created, syntactically valid YAML.
- [x] Workflow triggers only on `pull_request` to `main` (verified by
      reading the `on:` block, not by opening a live PR in this session).
- [x] Steps match the Makefile targets exactly (no duplicated logic).

## Tasks

### Foundation
- [x] **Task 1**: Create `.github/workflows/ci.yml` with `pull_request`
  trigger (branches: `main`), checkout step, `make docker-build-dev`,
  `make lint`, `make format-check`, `make test`.
  - **Acceptance**: Valid YAML; steps call existing Makefile targets only;
    no secrets required.
  - **Files**: `.github/workflows/ci.yml`
  - **Tests**: YAML syntax validated (`python3 -c "import yaml; ..."`);
    all three make targets (`docker-build-dev`, `lint`, `format-check`,
    `test`) run locally in this session with the same commands the
    workflow uses, all green (31 tests passed, ruff clean). Live
    verification of the 3 failure scenarios happens on the first real PR
    that exercises this workflow, since GitHub Actions can't be dry-run
    locally without additional tooling out of scope for this story.
  - **Effort**: S

## Effort Estimate

**Total**: S (matches issue #5's own estimate)
