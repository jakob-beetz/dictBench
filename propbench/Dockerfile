# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone the repository (replace with your actual repo URL)
ARG REPO_URL=https://github.com/yourusername/propbench.git
ARG BRANCH=main
RUN git clone --branch ${BRANCH} ${REPO_URL} .

# Install Python dependencies
COPY requirements-docker.txt /app/
RUN pip install --no-cache-dir -r requirements-docker.txt

# Create necessary directories
RUN mkdir -p /app/static /app/media /app/logs

# Copy production settings
COPY docker/settings_production.py /app/propbench/settings_production.py

# Create non-root user
RUN groupadd -r propbench && useradd -r -g propbench propbench

# Set ownership of app directory
RUN chown -R propbench:propbench /app

# Switch to non-root user
USER propbench

# Collect static files
RUN python manage.py collectstatic --noinput --settings=propbench.settings_production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/ || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--settings", "propbench.settings_production", "propbench.wsgi:application"]