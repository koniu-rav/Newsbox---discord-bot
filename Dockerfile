# Build and runtime stage using official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Set work directory
WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and project configs
COPY src/ ./src/
COPY pyproject.toml .

# Create non-root user for security
RUN useradd -u 1000 -m newsboxuser && chown -R newsboxuser:newsboxuser /app
USER newsboxuser

# Run bot
CMD ["python", "-m", "newsbox"]

