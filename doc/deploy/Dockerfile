# syntax=docker/dockerfile:1.6

#####################################
# Builder stage: clone + build deps
#####################################
FROM python:3.12-slim AS builder

# Install tools needed to clone and build
RUN apt-get update && apt-get install -y --no-install-recommends \
      git openssh-client build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Prepare SSH known_hosts for GitHub
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh && \
    ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> /root/.ssh/known_hosts

WORKDIR /src

# Build args for repo/branch
ARG REPO=git@github.com:jakob-beetz/dictBench.git
ARG BRANCH=main
ARG REPO_DEPTH=1
ARG CACHEBUST=0
# Clone using your SSH agent (requires: docker buildx build --ssh default …)
RUN --mount=type=ssh git clone --depth ${REPO_DEPTH} -b ${BRANCH} ${REPO} app

# Install Python deps into wheels
WORKDIR /src/app
RUN python -m pip install --upgrade pip wheel && \
    if [ -f propbench/requirements.txt ]; then \
        pip wheel --no-cache-dir --no-deps -r propbench/requirements.txt -w /wheels; \
    else \
        pip wheel --no-cache-dir --no-deps . -w /wheels; \
    fi


#####################################
# Runtime stage
#####################################
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Only minimal runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
      gettext ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps from wheels
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*

# Copy the app code
COPY --from=builder /src/app /app

# Directories for persistence
RUN mkdir -p /data /app/staticfiles /app/media && \
    adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app /data

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn","-b","0.0.0.0:8000","propbench.wsgi:application"]