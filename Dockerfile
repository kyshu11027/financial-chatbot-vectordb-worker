# Use an official Python runtime as a parent image
FROM python:3.13.3-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        git \
        curl \
        wget \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create a non-root user for security
RUN useradd -m appuser
USER appuser

# Expose the port FastAPI will run on
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --method=GET --no-verbose --tries=1 http://localhost:8090/health || exit 1

# Set environment variables for production
ENV GUNICORN_CMD_ARGS="--workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8090 --log-level error --timeout 120"

# Start the application with Gunicorn and Uvicorn worker
CMD sh -c "gunicorn main:app $GUNICORN_CMD_ARGS"