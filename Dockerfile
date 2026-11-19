FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project specification files, app, and static distribution
COPY pyproject.toml ./
COPY app ./app
COPY assets ./assets
COPY static_dist ./static_dist

# Install Python dependencies using uv
RUN uv pip install --system -e .


# Expose web port
EXPOSE 8080

# Run the interactive dashboard web server using cloud-assigned port
CMD ["sh", "-c", "python -m uvicorn app.dashboard:app --host 0.0.0.0 --port ${PORT:-8080}"]

