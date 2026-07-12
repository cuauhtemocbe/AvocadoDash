FROM python:3.12.6-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install "poetry"
RUN poetry config virtualenvs.create false

# Copy application code
COPY . .

# Expose port (Railway will override this)
EXPOSE 8050

# --- Dev image: adds ruff/pytest so `make test`/`make lint` can run in-container ---
FROM base AS dev

RUN poetry install --no-root

CMD ["poetry", "run", "python", "src/app.py"]

# --- Production image (default build target): runtime deps only, no dev tooling ---
FROM base AS production

RUN poetry install --no-root --only main

CMD ["poetry", "run", "python", "src/app.py"]
