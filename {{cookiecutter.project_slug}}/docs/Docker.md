# Docker Production

This project uses a multi-stage Dockerfile for production deployment.

## Dockerfile Overview

```dockerfile
# Stage 1: Python base
FROM python:3.14.2-slim-bookworm AS python-base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /usr/local/bin/uv

# Install production dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-group dev --no-install-project

# Stage 2: Build static assets
FROM python-base AS staticfiles
COPY . .
RUN uv run python manage.py tailwind build && \
    uv run python manage.py tailwind remove_cli && \
    uv run python manage.py collectstatic --no-input

# Stage 3: Final production image
FROM python:3.14.2-slim-bookworm AS webapp

# Create non-root user FIRST
RUN useradd -m -u 1000 django

WORKDIR /app

# Copy with correct ownership
COPY --from=python-base --chown=django:django /app/.venv /app/.venv
COPY --from=staticfiles --chown=django:django /app/staticfiles /app/staticfiles

# Copy application code
COPY --chown=django:django . .

USER django

CMD ["./gunicorn.sh"]
```

## Key Techniques

### Multi-stage Build

- **python-base**: Installs Python dependencies
- **staticfiles**: Builds Tailwind CSS and collects static files
- **webapp**: Final minimal image

### UV for Dependencies

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /usr/local/bin/uv
```

Using `uv` for fast, reliable dependency installation.

### Caching

```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-group dev --no-install-project
```

Uses Docker layer caching for dependencies.

### Security

- Create non-root user before copying files
- Use `--chown=django:django` for correct ownership
- Run as non-root user with `USER django`

### Environment Variables

```dockerfile
ENV LC_CTYPE=C.utf8 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"
```

## Building

```bash
docker build -t myapp .
```

## Running

```bash
docker run -p 8000:8000 myapp
```

## Gunicorn

Production uses Gunicorn with Uvicorn worker:

```bash
#!/bin/bash
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    config.asgi:application
```

## Best Practices

1. Use multi-stage builds to minimize image size
2. Create non-root user before copying files
3. Use `--chown` for correct ownership
4. Use `uv` for fast dependency installation
5. Cache dependencies with `--mount=type=cache`
6. Build static assets in a separate stage
