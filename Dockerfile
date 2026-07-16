FROM python:3.12.6-slim AS base

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
# floating `python:3.12.6-slim` tag — receiving automatic security patches on
# rebuild matters more there than exact reproducibility. This asymmetry is
# deliberate; update the digest (Dependabot bumps it automatically) rather
# than reverting to a floating tag here. ---
FROM python:3.12.6-slim@sha256:ad48727987b259854d52241fac3bc633574364867b8e20aec305e6e7f4028b26 AS production

WORKDIR /app

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

COPY --from=builder /app/.venv /app/.venv
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/')" || exit 1

CMD ["python", "src/app.py"]
