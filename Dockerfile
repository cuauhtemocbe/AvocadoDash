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

# --- Production image (default build target): runtime artifacts only, no poetry/git ---
FROM base AS production

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

COPY --from=builder /app/.venv /app/.venv
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/')" || exit 1

CMD ["python", "src/app.py"]
