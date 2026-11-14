# Every Python base image in this file uses the same exact-patch tag plus
# index digest, so the next CPython release is one search-and-replace of that
# string (Dependabot's docker entry opens the PR).
FROM python:3.14.10-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f AS base

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
# Starts from the same pinned string as the `base` stage above (not via that
# stage) so the final image carries nothing but the venv and `src/`. All stages
# share one exact patch release + digest for byte-for-byte reproducible builds.
# An exact patch tag stops receiving OS security patches once superseded, so
# keep it moving: bump the string (Dependabot bumps it automatically) rather
# than reverting to a floating tag. ---
FROM python:3.14.10-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f AS production

WORKDIR /app

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

# pip ships in the base image but is never invoked at runtime (dependencies
# are already installed in the venv copied from `builder`) — removing it
# drops whatever CVEs land on it (e.g. CVE-2025-8869) instead of carrying
# them for no reason.
RUN python -m pip uninstall -y pip

# The pinned base image can lag Debian security updates by days. Upgrade only
# the packages Trivy flags with a fix already published (currently libpcre2,
# CVE-2026-103111, and zlib1g, CVE-2026-76844 and CVE-2026-85091) instead of
# carrying the CVE until the next digest bump, then drop apt's lists so no extra
# layer weight or tooling state remains.
# Remove libpcre2-8-0 once the digest above ships >= 10.46-1~deb13u3, and zlib1g
# once it ships >= 1:1.3.dfsg+really1.3.1-1+deb13u1 (meta-projects#92).
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade libpcre2-8-0 zlib1g && \
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
