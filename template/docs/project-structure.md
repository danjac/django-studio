# Project Structure

This project follows a Django project layout with a clear separation of concerns.

## Contents

- [Directory Structure](#directory-structure)
- [Config Directory](#config-directory)
- [Apps Directory](#apps-directory)
- [Templates](#templates)
- [Static Files](#static-files)
- [Tests](#tests)
- [Key Files](#key-files)
- [Best Practices](#best-practices)

## Directory Structure

```
myproject/
├── config/                 # Django settings, URLs, ASGI/WSGI
│   ├── __init__.py
│   ├── settings.py        # Main settings
│   ├── urls.py           # Root URL configuration
│   ├── asgi.py          # ASGI application
│   └── wsgi.py          # WSGI application
│
├── my_package/             # Main application package
│   ├── __init__.py
│   ├── admin.py          # Admin configuration
│   ├── apps.py           # App configuration
│   ├── context_processors.py
│   ├── middleware.py
│   ├── templatetags.py
│   ├── search.py         # Full-text search
│   │
│   ├── http/             # HTTP utilities
│   │   ├── request.py    # Typed request classes
│   │   ├── response.py   # Custom response classes
│   │   └── decorators.py # View decorators
│   │
│   ├── users/            # User app
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── fixtures.py
│   │       ├── factories.py
│   │       └── test_models.py
│   │
│   └── tests/            # Shared test fixtures
│       ├── fixtures.py
│       ├── e2e_fixtures.py
│       └── asserts.py
│
├── templates/             # Django templates
│   ├── base.html
│   ├── home.html
│   ├── messages.html
│   ├── 400.html
│   ├── 403.html
│   ├── 404.html
│   └── 500.html
│
├── tailwind/             # Tailwind CSS source
│   ├── app.css
│   ├── theme.css
│   ├── tweaks.css
│   ├── htmx.css
│   ├── buttons.css
│   ├── forms.css
│   └── messages.css
│
├── static/               # Static files
│   └── vendor/           # Vendor JS (HTMX, Alpine.js)
│
├── docker-compose.yml    # Local development services
├── Dockerfile           # Production image
├── justfile            # Command runner
├── pyproject.toml      # Python project config
└── uv.lock            # Dependency lock file
```

## Config Directory

The `config/` directory contains Django project configuration:

- `settings.py` - All Django settings
- `urls.py` - Root URL configuration
- `asgi.py` - ASGI application for async
- `wsgi.py` - WSGI application

## Apps Directory

The `my_package/` directory contains the main application package. Each sub-app should be self-contained:

```
my_package/my_app/
├── models.py         # Core business logic
├── views.py          # Request handlers (function-based)
├── urls.py           # URL routes for this app
├── tasks.py         # Background tasks
├── admin.py          # Admin interface
└── tests/            # Colocated tests
```

## Templates

Templates are in the root `templates/` directory:

```
templates/
├── base.html              # Main base template
├── partials/             # Reusable partials
│   └── ...
└── package_name/              # App-specific templates
    ├── list.html
    └── detail.html
```

## Static Files

- Source Tailwind CSS in `tailwind/`
- Compiled to `static/app.css` (via `django-tailwind-cli`)
- Vendor libraries in `static/vendor/`

## Tests

Tests are colocated with modules:

```
my_package/my_app/
├── models.py
└── tests/
    ├── __init__.py
    ├── fixtures.py      # Pytest fixtures
    ├── factories.py    # model-bakery recipes
    ├── test_models.py
    ├── test_views.py
    └── test_playwright.py  # E2E tests
```

## Key Files

### pyproject.toml

Python project configuration including:
- Dependencies
- Dev dependencies
- pytest configuration
- Ruff configuration
- Type checking settings

### justfile

Command runner with shortcuts for:
- Development server
- Testing
- Linting
- Docker management

### docker-compose.yml

Local development services:
- PostgreSQL
- Redis
- Mailpit (email testing)

## Best Practices

1. One sub-app per logical domain
2. Colocate tests with modules they test
3. Use function-based views (not class-based)
4. Keep templates organized by app
5. Use custom management commands for tasks
6. Use django-tasks for background jobs
