FROM python:3.14-slim AS base

# Set working directory
WORKDIR /app

# --- Builder stage: resolves and installs runtime dependencies into a venv.
# Only this stage (and dev) needs poetry/git — production copies the venv only. ---
FROM base AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --no-root --only main --no-interaction

# virtualenv seeds pip into the venv, and pip vendors its own copies of
# msgpack/setuptools (pip/_vendor) that Trivy flags. pip is never invoked at
# runtime, so drop it before production copies the venv (same rationale as
# the system pip uninstall in the production stage below).
RUN .venv/bin/python -m pip uninstall -y pip

# --- Dev image: full toolchain (poetry, git, dev deps) so `make test`/`make lint` can run in-container ---
FROM base AS dev

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false

# Copy application code
COPY . .

RUN poetry install --no-root

# Expose port (Railway will override this)
EXPOSE 8050

CMD ["poetry", "run", "python", "src/app.py"]

# --- Production image (default build target): runtime artifacts only, no poetry/git.
# Base image pinned by digest here (NOT via the shared `base` stage above) for
# byte-for-byte reproducible builds. dev/builder intentionally stay on the
# floating `python:3.14-slim` tag — receiving automatic security patches on
# rebuild matters more there than exact reproducibility. This asymmetry is
# deliberate; update the digest (Dependabot bumps it automatically) rather
# than reverting to a floating tag here.
#
# Use a tag that's actively rebuilt (`python:3.14-slim`, currently 3.14.7),
# not a frozen historical patch tag like `python:3.14.0-slim` — the latter
# stops receiving OS security patches once superseded, so pinning its digest
# just freezes in known CVEs instead of freezing in a known-good state. ---
FROM python:3.14-slim@sha256:0741d101873c12ab927e6f8653feb8862b9bd58771177acb1b885b95141f91b4 AS production

WORKDIR /app

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

# pip ships in the base image but is never invoked at runtime (dependencies
# are already installed in the venv copied from `builder`) — removing it
# drops whatever CVEs land on it (e.g. CVE-2025-8869) instead of carrying
# them for no reason.
RUN python -m pip uninstall -y pip

# The pinned base image can lag Debian security updates by days. Upgrade only
# the packages Trivy flags with a fix already published (currently libpcre2,
# CVE-2026-103111) instead of carrying the CVE until the next digest bump,
# then drop apt's lists so no extra layer weight or tooling state remains.
# Remove this once the digest above ships libpcre2-8-0 >= 10.46-1~deb13u3.
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade libpcre2-8-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/')" || exit 1

CMD ["python", "src/app.py"]
