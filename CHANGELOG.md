# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Docker HEALTHCHECK and a non-root `appuser` in the production image.
- `LICENSE` (MIT) and a `license-check` CI job.
- `lock-check` CI job verifying `poetry.lock` stays in sync with `pyproject.toml`; `poetry.lock` is now tracked in git.
- Trivy filesystem scan (`trivy-fs`) on every push, and a Trivy image scan as part of a new `build` job gated to `main`.
- Dependabot configuration for the `pip`, `docker`, and `github-actions` ecosystems.
- `mypy --strict` type checking for `src/`, wired into `make typecheck` and CI.
- Enforced minimum test coverage via `pytest-cov` (`--cov-fail-under`).
- `make validate` as a single entry point for lint, format-check, typecheck, and test.
- Secret scanning (staged diff) in the pre-commit hook.
- This changelog.
- `dependabot-socket-firewall` CI workflow: runs Socket Firewall Free against Dependabot PRs and auto-closes any PR proposing a known-malicious/compromised dependency.
- Slack notification when a Railway deployment fails: a project-level Railway webhook (filtered to the `Deployment Failed` event, no application code) piped through Slack's incoming-webhook Muxer. `scripts/verify_slack_webhook.sh` verifies the Slack side of the wiring on demand.

### Changed

- Production Docker image now builds via a dedicated `builder` stage and no longer ships `poetry`/`git` — runtime artifacts only.
- Production base image moved from the frozen `python:3.12.6-slim` tag to the actively-maintained `python:3.12-slim` tag, pinned by digest (dev/builder stay on the floating tag).
- CI's single `lint-and-test` job split into independent `lint` and `test` jobs; workflow now also triggers on push to `main` and declares explicit `permissions: read-all`.
- Third-party GitHub Actions (`actions/checkout`, `aquasecurity/trivy-action`) pinned by commit SHA instead of floating tags.

## [0.1.0] - 2026-07-13

### Added

- Initial AvocadoDash release: a single-page Dash app visualizing US avocado price/volume data (2015–2018) with region/type/date-range filters, price and volume charts, a scatter chart, a box plot, and a filtered-data summary panel.
- CSV export of the filtered dataset.
- Multi-region comparison.
- Spanish/English UI language toggle.
- Structured logging (replacing `print`) in callback error handling.
- Avocado-derived visual identity: color tokens, typography system, the Cross-Section Mark brand element, a redesigned filter bar and summary panel, recolored chart chrome.
- Test suite (pytest) covering chart builders, callbacks, summary stats, translations, and the visual-identity CSS regression checks.
- GitHub Actions CI running lint and tests on pull requests.
