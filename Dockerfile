FROM python:3.12.6-slim

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

# Install Python dependencies
RUN poetry install --no-root --no-dev

# Expose port (Railway will override this)
EXPOSE 8050

# Command to run the application
CMD ["poetry", "run", "python", "src/app.py"]