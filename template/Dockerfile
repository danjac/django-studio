
ARG PYTHON_IMAGE=3.14.2-slim-bookworm

# Install Python dependencies
FROM python:${PYTHON_IMAGE} AS python-base
ENV LC_CTYPE=C.utf8 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONFAULTHANDLER=1 \
  UV_PROJECT_ENVIRONMENT="/app/.venv" \
  UV_PYTHON_INSTALL_DIR="/python" \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-group dev --no-install-project

# Compile message catalogues
FROM python-base AS messages
COPY . .
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends gettext && rm -rf /var/lib/apt/lists/*
RUN --mount=type=cache,target=/root/.cache/uv \
  uv run python manage.py compilemessages

# Build static assets
FROM python-base AS staticfiles
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
  uv run python manage.py tailwind build && \
  uv run python manage.py tailwind remove_cli && \
  uv run python manage.py collectstatic --no-input

# Final production image
FROM python:${PYTHON_IMAGE} AS webapp

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Must match postgres.image major version in helm/site/values.yaml
ARG POSTGRES_MAJOR=18
# Install Python dependencies
ENV LC_CTYPE=C.utf8 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  PATH="/app/.venv/bin:$PATH"

# Install postgresql-client (version-matched to production DB) for manage.py dbshell
# hadolint ignore=DL3008
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
  && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
  > /etc/apt/sources.list.d/pgdg.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends postgresql-client-${POSTGRES_MAJOR} \
  && apt-get purge -y --auto-remove curl gnupg \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user FIRST, before any file copies
RUN useradd -m -u 1000 django

WORKDIR /app

# Copy files with correct ownership from the start using --chown
COPY --from=python-base --chown=django:django /app/.venv /app/.venv
COPY --from=staticfiles --chown=django:django /app/staticfiles /app/staticfiles
COPY --from=messages --chown=django:django /app/locale /app/locale

# Copy application code with correct ownership
COPY --chown=django:django . .

USER django

CMD ["./gunicorn.sh"]
