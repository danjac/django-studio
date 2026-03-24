# Docker Production

This project uses a multi-stage Dockerfile for production deployment.

## Dockerfile Overview

The build uses four stages:

| Stage | Base | Purpose |
|-------|------|---------|
| `python-base` | `python:3.14-slim-bookworm` | Install Python deps via uv |
| `messages` | `python-base` | Install `gettext`, run `compilemessages` |
| `staticfiles` | `python-base` | Build Tailwind CSS, run `collectstatic` |
| `webapp` | `python:3.14-slim-bookworm` | Final minimal image |

The final image copies compiled artefacts from all three build stages:

```dockerfile
COPY --from=python-base  --chown=django:django /app/.venv      /app/.venv
COPY --from=staticfiles  --chown=django:django /app/staticfiles /app/staticfiles
COPY --from=messages     --chown=django:django /app/locale      /app/locale
```

## Key Techniques

### Multi-stage Build

- **python-base**: Installs Python dependencies with uv (no dev group, bytecode compiled)
- **messages**: Installs `gettext`, compiles translation catalogues (`compilemessages`)
- **staticfiles**: Builds Tailwind CSS and collects static files
- **webapp**: Final image — no build tools, only the compiled artefacts above

### UV for Dependencies

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /usr/local/bin/uv
```

All dep installs use `--mount=type=cache,target=/root/.cache/uv` for layer caching.

### PostgreSQL Client

The `webapp` stage installs `postgresql-client-${POSTGRES_MAJOR}` from the official PGDG apt repo, version-matched to the production database (default: 18). This enables `manage.py dbshell` inside the container.

### Security

- Non-root user (`django`, uid 1000) created before any file copies
- All copies use `--chown=django:django`
- `curl` and `gnupg` purged after the apt key is imported

### Environment Variables

```dockerfile
ENV LC_CTYPE=C.utf8 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    UV_PROJECT_ENVIRONMENT="/app/.venv" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"
```

## Building

```bash
docker build -t my_project .
```

## Running

```bash
docker run -p 8000:8000 my_project
```

## Gunicorn

Production uses Gunicorn with Uvicorn worker, configured via two files:

**`gunicorn.sh`** — entrypoint script:

```bash
#!/bin/bash
set -euo pipefail
exec gunicorn --config gunicorn.conf.py config.asgi:application
```

**`gunicorn.conf.py`** — configuration (binding, workers, logging, timeouts, memory-aware `max_requests`):

```python
import multiprocessing
import psutil

bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() + 1

accesslog = "-"
errorlog = "-"

timeout = 30
graceful_timeout = timeout + 10

memory = int(psutil.virtual_memory().total * 0.7 // (2**20))
max_requests = max(200, memory * 50 // 1024)
max_requests_jitter = max_requests // 20
```

## Best Practices

1. Use multi-stage builds to minimize image size
2. Create non-root user before copying files
3. Use `--chown` for correct ownership
4. Use `uv` for fast dependency installation
5. Cache dependencies with `--mount=type=cache`
6. Build static assets in a separate stage
