# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AvocadoDash is a single-page Python Dash web app that visualizes US avocado
price/sales data (2015–2018) from `src/avocado.csv` (Hass Avocado Board
dataset). It is deployed on Railway.

## Commands

Dependency management is via Poetry (Python 3.12.6 pinned in `pyproject.toml`).
Most of these are wrapped by the `Makefile` — run `make help` for the full list.

```bash
# Primary dev workflow: code on the host, app runs/reloads inside Docker
make docker-build               # once, or whenever dependencies change
make run                        # serves on http://localhost:8050 with hot-reload

# Tests and lint also run inside Docker, against the dev image
make docker-build-dev           # once, or whenever dependencies change
make test                       # pytest (config in [tool.pytest.ini_options])
make lint                       # ruff check
make format                     # ruff format
make format-check               # ruff format --check

# Docker (production image, no hot-reload — no dev tooling in the image)
docker build -t avocado-dash .  # or: make docker-build
docker run -p 8050:8050 avocado-dash  # or: make docker-run
```

Ruff (`[tool.ruff]` in `pyproject.toml`) is the linter and formatter — line
length 88, target `py312`. Pytest is configured with `pythonpath = ["src"]`
so tests import `app` directly (see `tests/test_app.py`). A pre-commit git
hook (`.githooks/pre-commit`, enabled via `make install-hooks`) runs
`make lint` + `make format-check` — same as everything else, this runs
against the `avocadodash:dev` image, so `make docker-build-dev` must have
been run at least once (no local Poetry env needed for the hook).

The primary dev workflow is `make run`: code stays on the host (edit with
any local editor/IDE) while the app actually runs inside the container,
bind-mounted at `/app` with `DEBUG=true` so Dash's built-in reloader
(Werkzeug) picks up file changes without restarting the container. It
reuses the `avocadodash:latest` image built by `make docker-build`, so
rebuild only when dependencies change — not on every code edit.
`src/app.py`'s `if __name__ == "__main__"` block reads `DEBUG` from the
environment (default `false`) to enable this without affecting
`make docker-run` or the Railway/production start command, which stay
non-debug.

`make test`/`make lint`/`make format`/`make format-check` follow the same
pattern, but against `avocadodash:dev` (built by `make docker-build-dev`)
instead of `avocadodash:latest` — that's the only image with the `dev`
dependency group (`ruff`, `pytest`) installed, since the Dockerfile is
multi-stage: a shared `base` stage, a `dev` stage (`poetry install
--no-root`, full groups) and the `production` stage (`poetry install
--no-root --only main`, default build target, no dev tooling). Both
`make run` and the `test`/`lint`/`format*` targets bind-mount the repo
into the container, so they always operate on the current code — but they
do NOT pick up new/changed dependencies automatically; rebuild the
relevant image (`docker-build` / `docker-build-dev`) after touching
`pyproject.toml`. `make docker-stop` stops both the `run` dev container
and the `docker-run` production container in one call.

Dependency groups use Poetry's native `[tool.poetry.group.dev.dependencies]`
table, not the PEP 735 `[dependency-groups]` table — the latter looked
equivalent but silently broke `poetry install`'s resolver for this
project's Poetry version (`SolverProblemError: ... doesn't match any
versions`, even though the packages exist on PyPI). If dev dependencies
ever need to change, edit `[tool.poetry.group.dev.dependencies]` directly
and run `poetry lock` (any Poetry install can regenerate the lock file;
the project doesn't require a specific Poetry version).

Railway deployment config lives in `railway.json`; it runs the same
`poetry run python src/app.py` start command and reads the port from the
`PORT` env var (see bottom of `src/app.py`), building from the `production`
stage of the Dockerfile (the default target when no `--target` is given).

---

## Available Skills

This repository includes the following Claude Code skills:

- **`/spec-driven-dev`**: Complete spec-driven development workflow (idea → spec → plan → tasks → implementation)
- **`/user-stories`**: Write and publish user stories with Gherkin acceptance criteria to GitHub/GitLab Issues
- **`/commit-writer`**: Generate conventional commits following project standards
- **`/testing`**: TDD workflow with mutation testing, coverage targets, and test quality validation
- **`/sonar-check`**: Code quality analysis with SonarQube (MCP-first or Docker fallback)
- **`/trivy-scan`**: Security scanning for vulnerabilities, secrets, IaC misconfigurations, and licenses

Use these skills proactively when relevant to the work at hand.

---

## Recommended Development Workflow

### For New Features

1. **Spec-Driven Development**: Use `/spec-driven-dev` to transform ideas into structured specifications
   - Phase 1 (Specify): Refine idea → create spec in `specs/{feature}.md`
   - Phase 2 (Plan): Create implementation plan → `specs/{feature}-plan.md`
   - Phase 3 (Tasks): Break into tasks → create GitHub/GitLab Issues with `/user-stories`
   - Phase 4 (Implement): Execute tasks with TDD using `/testing`

2. **Implementation**: Follow TDD cycle for each task
   - Write tests first (use Gherkin scenarios from user stories)
   - Run tests and verify they fail
   - Implement the feature
   - Run tests and verify they pass

3. **Quality Gates**: Before committing
   - Run linter and formatter
   - Run `/sonar-check` for code quality validation
   - Run `/trivy-scan` for security scanning
   - Ensure all quality gates pass

4. **Commit**: Use `/commit-writer` to generate conventional commits

5. **Memory**: Save learnings to Engram (see Memory Protocol below)

### For Bug Fixes

1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify test passes
4. Run quality gates (`/sonar-check`, `/trivy-scan`)
5. Commit with `/commit-writer`
6. Save bugfix to memory with `mem_save`

---

## Issue Tracking Integration

### GitHub Issues

Use the `/user-stories` skill to create issues. It auto-detects GitHub and uses MCP integration:

```bash
# The skill handles this automatically, but MCP must be configured
# If not configured, the skill will guide you to set it up
```

### GitLab Issues

Use the `/user-stories` skill (auto-detects GitLab) or use `glab` directly:

```bash
cat > /tmp/issue.md << 'EOF'
## User Story

```
As <role>
I want <action>
```

## Acceptance Criteria

```gherkin
Feature: ...
EOF

glab issue create --repo owner/repo \
  --title "Issue title" \
  --label "feature,sprint-1" \
  --description "$(cat /tmp/issue.md)"
```

---

## Memory (Engram)

You have access to persistent memory via MCP tools (mem_save, mem_search, mem_session_summary, etc.).

- Save proactively after significant work — do not wait to be asked.
- After any compaction or context reset, call `mem_context` to recover the state from previous sessions before continuing.

### When to save
- Finished a bugfix → mem_save (type: bugfix)
- Made an architecture or technology decision → mem_save (type: decision, topic_key: "architecture/xxx")
- Discovered a gotcha or non-obvious pattern → mem_save (type: discovery)
- Configured something non-trivial → mem_save (type: config)
- Identified a project or user preference → mem_save (type: preference)

### When starting a session
1. Call mem_context to review recent history (fast and cheap)
2. If relevant context is missing, call mem_search with keywords for the current topic

### When ending a session
Call mem_session_summary with structure:
- Goal: what was being attempted
- Accomplished: what was completed
- Discoveries: important findings
- Files: relevant modified files

### In case of compaction
If you see a reset or context compaction message:
1. IMMEDIATELY call mem_session_summary with the content of the compacted summary
2. Then call mem_context to recover additional context
Do not skip step 1. Without it, everything done before the compaction is lost from memory.

### Key Learnings pattern
When finishing significant work, include at the end of your response:
## Key Learnings:
1. [learning]
2. [other learning]
Engram will extract and save these items automatically via mem_capture_passive.

### Progressive search
1. First call mem_context (reviews recent session history)
2. If not found, call mem_search with relevant keywords
3. If a match is found, use it as context before answering

---

## Development Guidelines

### Quality Standards

- **Test Coverage**: Use `/testing` skill to maintain coverage targets and mutation scores
- **Code Quality**: Use `/sonar-check` to validate Quality Gates (complexity, duplication, maintainability)
- **Security**: Use `/trivy-scan` to detect vulnerabilities, secrets, and misconfigurations
- **Commit Messages**: Use `/commit-writer` for conventional commits with proper body and co-authoring

### TDD Cycle (use `/testing` skill)

1. **Red**: Write failing tests (use Gherkin scenarios from `/user-stories` as guide)
2. **Green**: Implement minimum code to pass tests
3. **Refactor**: Improve code while keeping tests green
4. **Verify**: Run quality gates (`/sonar-check`, `/trivy-scan`)
5. **Commit**: Generate commit with `/commit-writer`
6. **Remember**: Save learnings with `mem_save`

### Before Merging

- [ ] All tests passing (unit, integration, E2E)
- [ ] Test coverage meets targets (use `/testing` for guidance)
- [ ] Mutation score acceptable (use `/testing` for interpretation)
- [ ] SonarQube Quality Gate passed (use `/sonar-check`)
- [ ] Security scan clean (use `/trivy-scan`)
- [ ] Linter and formatter run
- [ ] Commit messages follow conventions (use `/commit-writer`)
- [ ] User stories updated/closed with evidence (use `/user-stories`)

---

## Architecture

The entire app is one file: `src/app.py`. It follows the standard Dash
module-level pattern rather than a factory/class structure:

1. **Data load (module import time)** — `load_data()` reads
   `src/avocado.csv` relative to the script's own location (not cwd), parses
   `Date`, and sorts by it. The result is bound to a module-level `data`
   DataFrame that every callback below closes over and filters — there is no
   per-request data loading or caching layer.
2. **Layout** — `app.layout` is a single large `html.Div` tree built with
   Dash's declarative `html`/`dcc` components (no external UI framework).
   Styling is in `src/assets/style.css`, loaded automatically by Dash's
   assets convention. Filter controls (`region-filter`, `type-filter`,
   `date-range`) at the top drive multiple chart sections below.
3. **Chart builders** — `create_price_chart`, `create_volume_chart`,
   `create_box_plot`, `create_scatter_chart` each take an already-filtered
   DataFrame and return a plain Plotly figure dict (`{"data": ..., "layout":
   ...}`), not a `go.Figure` object. Keep this pattern when adding charts —
   the callbacks below assume dict returns.
4. **Callbacks** — three `@app.callback` functions
   (`update_charts`, `update_scatter_chart`, `update_box_plot`) each
   independently re-filter the module-level `data` via `DataFrame.query`
   based on `region-filter`/`type-filter`/`date-range` plus their own extra
   inputs (axis dropdowns for scatter, column/group-by dropdowns for the box
   plot). Note `update_box_plot` varies which filters it applies depending on
   `group_by`, so that the grouped dimension isn't also pinned by the
   top-level filter (e.g. grouping by `type` intentionally ignores
   `type-filter` so both avocado types are shown). Each callback has its own
   try/except that falls back to an empty/error figure — follow this
   pattern for new callbacks rather than letting exceptions propagate to
   Dash's default error UI.
5. **`server = app.server`** is exposed for Railway/Gunicorn-style
   deployment, and the app binds `0.0.0.0:$PORT` at the bottom under
   `if __name__ == "__main__"`.

`src/utils.py` contains `calculate_summary_stats` and `format_number` but
neither is currently imported by `app.py` — treat it as scaffolding for
future summary-stat UI, not active code.

**KISS Principle:** This app deliberately stays flat (one module, plain
dict-returning chart builders, no service/repository layers). Prefer pure
functions over classes, and don't introduce a layered architecture
(api/domain/infrastructure) unless the app actually grows beyond a single
Dash file.

---

## Spec-Driven Development Workflow

When starting a new feature or application, use the `/spec-driven-dev` skill:

### Phase 1: SPECIFY
- Refine the idea through clarifying questions
- Create structured spec: `specs/{feature-name}.md`
- Define objective, requirements, architecture, testing strategy, success criteria
- Get approval before advancing

### Phase 2: PLAN
- Create implementation plan: `specs/{feature-name}-plan.md`
- Break into components, identify dependencies, estimate effort
- Document risks and assumptions
- Get approval before advancing

### Phase 3: TASKS
- Break plan into discrete, testable tasks
- Create GitHub/GitLab Issues with `/user-stories`
- Link issues to spec files
- Get approval before advancing

### Phase 4: IMPLEMENT
- Execute tasks one-by-one using TDD (`/testing`)
- Verify against acceptance criteria
- Update task status and link commits
- Close issues with evidence when complete

**Key principle**: Specs are source of truth, code is regenerable. Keep specs updated when requirements change.

---

## Testing Guidelines

Use the `/testing` skill for comprehensive testing guidance:

- **TDD Workflow**: Red → Green → Refactor cycle
- **Coverage Targets**: Risk-based targets (critical: 90-100%, core: 80-90%, utility: 70-80%)
- **Mutation Testing**: Interpretation of mutation scores and how to improve
- **Test Quality**: Assertion strength, async patterns, E2E best practices
- **Debugging**: When tests fail, how to diagnose and fix

See `/testing` skill for detailed guidance and examples.

---

## Security Scanning

Use the `/trivy-scan` skill to detect security issues before they reach production:

**What it scans:**
- **Vulnerabilities**: OS packages, language dependencies (npm, pip, go.mod, etc.)
- **Secrets**: API keys, passwords, tokens accidentally committed
- **IaC Misconfigurations**: Kubernetes, Docker, Terraform security issues
- **Licenses**: License compliance for dependencies

**When to run:**
- Before committing (catches secrets before they enter git history)
- Before merging PRs (validates dependencies are secure)
- On schedule (detect newly discovered CVEs in existing dependencies)

**Workflow:**
```bash
# The skill handles this automatically:
# 1. Detects what scanners are needed (based on project files)
# 2. Runs scans (filesystem, secrets, IaC, licenses)
# 3. Triages by severity (CRITICAL > HIGH > MEDIUM > LOW)
# 4. Provides remediation guidance
```

**Ignore workflow**: Use `.trivyignore` for accepted risks (document why)

See `/trivy-scan` skill for detailed usage and examples.

---

## Code Quality Analysis

Use the `/sonar-check` skill to validate code quality metrics:

**What it analyzes:**
- **Code Smells**: Complexity, duplication, maintainability issues
- **Security Hotspots**: Potential security vulnerabilities
- **Bugs**: Probable bugs detected by static analysis
- **Coverage**: Test coverage gaps
- **Technical Debt**: Estimated time to fix all issues

**Quality Gates** (customize per project):
- Maintainability Rating: A or B
- Reliability Rating: A
- Security Rating: A
- Coverage: >= 80% (adjust based on risk)
- Duplication: < 3%

**Workflow:**
```bash
# The skill uses MCP-first approach:
# 1. Ping SonarQube MCP to check availability
# 2. If available: use fast MCP tools for analysis
# 3. If not: fall back to Docker + sonar-scanner CLI
# 4. Triage issues by severity (BLOCKER > CRITICAL > MAJOR > MINOR)
```

**Scoped analysis**: For fix-loop iterations, analyze only changed code (faster feedback)

See `/sonar-check` skill for setup and detailed usage.

---

## User Stories and Issue Management

Use the `/user-stories` skill to write and manage user stories:

**What it does:**
- Write user stories in domain language (not technical implementation)
- Validate stories with **INVEST** criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable)
- Write acceptance criteria in **Gherkin** format (Given/When/Then)
- Split large stories using **SPIDR** (Spike, Paths, Interfaces, Data, Rules)
- Publish to GitHub/GitLab Issues with proper formatting and labels
- Close issues with evidence (changes, tests, links to PRs)

**Fundamental rule**: Every acceptance criterion MUST have an automated test. No exceptions.

**When to use:**
- Planning new features (write stories before coding)
- Refining backlog (split large stories, add missing criteria)
- Publishing to issue tracker (create issues with proper format)
- Closing completed work (document what was done with evidence)

See `/user-stories` skill for templates, examples, and INVEST/SPIDR guidance.
