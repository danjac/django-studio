# AGENTS.md

This is a Django project using HTMX, AlpineJS, and Tailwind CSS.

## Stack

- **Python 3.14**, **Django 6.0**, **PostgreSQL 18**, **Redis 8**
- **Frontend**: HTMX + AlpineJS + Tailwind CSS (no JS build step; Tailwind compiled via `django-tailwind-cli`)
- **Package manager**: `uv` (not pip/poetry)
- **Task runner**: `just` (see `justfile` for all commands)
- **Background tasks**: Django Tasks (`django-tasks-db`), not Celery

## Project Layout

```
config/             # Django settings, URLs, ASGI/WSGI
{{cookiecutter.app_name}}/              # Main application package
  users/            # User model, authentication
  db/               # Database utilities (search mixin)
  http/             # HTTP utilities (typed requests, responses, decorators)
  tests/            # Shared test fixtures
templates/          # Django templates (HTMX partials + full pages)
static/             # Static assets
conftest.py         # Root pytest config (fixture plugins)
```

## Commands

All commands use `just`. Run `just` with no arguments to list available commands.

### Linting

```bash
just lint
```

Runs `ruff check --fix` (Python) and `djlint --lint templates/` (Django templates).

### Type Checking

```bash
just typecheck
```

Runs `basedpyright`. Configuration is in `pyproject.toml` under `[tool.pyright]`.

### Testing

```bash
just test                         # Run all unit tests with coverage
just test {{cookiecutter.app_name}}/users     # Test a specific module
just tw                           # Watch mode (auto-rerun on .py/.html changes)
just e2e                          # End-to-end tests (Playwright, headless)
just e2e-headed                   # E2E tests with visible browser
```

- Framework: `pytest` with `pytest-django`
- Coverage: **100% required** (`--cov-fail-under=100`)
- Test location: colocated in `{{cookiecutter.app_name}}/**/tests/` directories

### Django Management

```bash
just dj <command>              # Run any manage.py command
just dj migrate                # Run migrations
just dj shell                  # Django shell
just serve                     # Dev server + Tailwind watcher
```

### Dependencies

```bash
just install                   # Install all deps (Python, pre-commit)
just update                    # Update all deps
just pyinstall                 # Install Python deps only (uv sync --frozen)
just pyupdate                  # Update Python deps only (uv lock --upgrade)
```

### Docker Services

```bash
just start                     # Start PostgreSQL, Redis, Mailpit
just stop                      # Stop services
just psql                      # Connect to PostgreSQL
```

## Git Workflow

### Commit Messages

Conventional commits enforced by commitlint. Format: `type: subject`

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

### Branching

Create a well-named branch for each change. Before merging into `main`, squash commits and ensure all tests pass with 100% coverage.

## Code Style

### Python

- Ruff handles linting and formatting
- Absolute imports only (`absolufy-imports` enforced)
- isort profile: `black`, first-party: `{{cookiecutter.app_name}}`
- `pyupgrade --py314` applied automatically
- `django-upgrade --target-version 6.0` applied automatically

### Templates

- `djhtml` for HTML/CSS/JS indentation
- `djlint` for Django template linting (profile: `django`)
- `djade` for Django template formatting
- `rustywind` for Tailwind CSS class ordering

## Testing Conventions

- Tests use `factory-boy` and `faker` for test data
- Fixtures organized as pytest plugins in `*/tests/fixtures.py`
- Coverage source: `{{cookiecutter.app_name}}/`, omits migrations and test files
- E2E tests marked with `@pytest.mark.e2e` and excluded from default test runs

## Working Conventions

- **Search before implementing** — Before writing new code, search the codebase with `rg` or `ast-grep` for existing utilities, mixins, and patterns. Check `{{cookiecutter.app_name}}/admin.py` for admin mixins, `{{cookiecutter.app_name}}/db/search.py` for full-text search, `{{cookiecutter.app_name}}/http/` for request/response utilities.
- **Scope discipline** — Only change what was explicitly requested.
- **Diagnose before changing** — Read the code and state your diagnosis with a file:line reference before editing.
- **Verify runtime behaviour** — Passing tests is necessary but not sufficient.
