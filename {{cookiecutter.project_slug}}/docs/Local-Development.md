# Local Development

This project uses Docker Compose for local services and `just` for command automation.

## Quick Start

```bash
# 1. Start Docker services
just start

# 2. Copy environment file
cp .env.example .env

# 3. Install dependencies
just install

# 4. Run migrations
just dj migrate

# 5. Start dev server
just serve
```

## Docker Compose Services

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:18.1-bookworm
    environment:
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]

  redis:
    image: redis:8.2.2-bookworm
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  mailpit:
    image: axllent/mailpit:v1.27
    ports:
      - "8025:8025"  # Web UI
      - "1025:1025"  # SMTP
```

## Just Commands

```bash
# Development
just serve              # Dev server + Tailwind watcher
just test              # Run unit tests
just test myapp/users  # Test specific module
just tw                # Watch mode
just e2e               # E2E tests (headless)
just e2e-headed        # E2E tests (visible browser)
just lint              # Run linters
just typecheck         # Run type checker

# Docker
just start             # Start Docker services
just stop              # Stop Docker services
just psql              # Connect to PostgreSQL
just dc <args>        # Run docker compose commands

# Dependencies
just install           # Install all deps
just update            # Update all deps
just pyinstall        # Install Python deps only
just pyupdate         # Update Python deps only

# Django
just dj <command>     # Run manage.py command
just dj migrate       # Run migrations
just dj shell         # Django shell
just dj tailwind build  # Build Tailwind

# Pre-commit
just precommit run --all-files  # Run all hooks
just precommitupdate   # Update hook versions
```

## Environment Configuration

This project follows [12-factor app](https://12factor.net/) principles:

- **Single settings.py**: All configuration in one file, driven by environment variables
- **No hardcoded values**: Everything configured via environment variables
- **Environment-specific**: Different values for development, production, etc.

### Using environs

```python
# config/settings.py
from environs import Env

env = Env()
env.read_env()

DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY")
DATABASE_URL = env.dj_db_url("DATABASE_URL")
```

### .env.example

Create a `.env.example` file documenting all required environment variables:

```bash
# .env.example
DEBUG=true
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
```

Never commit `.env` files to version control - they should be in `.gitignore`.

### Best Practices

1. Use `environs` for type-safe environment variable handling
2. Provide sensible defaults for development
3. Document all variables in `.env.example`
4. Use different values for dev/staging/production
5. Never commit secrets to version control

## Running Migrations

```bash
just dj makemigrations
just dj migrate
```

## Creating a Superuser

```bash
just dj createsuperuser
```

## Dependencies

This project uses `uv` for Python dependency management - **never edit pyproject.toml or uv.lock directly**.

```bash
# Add production dependency
uv add <package>

# Add development dependency
uv add --dev <package>

# Update all dependencies
just update

# Install (after adding deps)
just pyinstall
```

> **Important:** Always use `uv add` or `uv add --dev` to add dependencies. Never manually edit `pyproject.toml`.

## Accessing Services

- **App**: http://localhost:8000
- **Mailpit**: http://localhost:8025 (catches emails sent in dev)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
