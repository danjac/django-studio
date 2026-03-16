# Project Structure

This project follows a Django project layout with a clear separation of concerns.

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
├── myapp/             # Main application package
│   ├── __init__.py
│   ├── admin.py          # Admin configuration
│   ├── apps.py           # App configuration
│   ├── context_processors.py
│   ├── middleware.py
│   ├── templatetags.py
│   │
│   ├── db/               # Database utilities
│   │   └── search.py     # Full-text search mixin
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
│   ├── default_base.html
│   ├── hx_base.html
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

The `myapp/` directory contains the main application package. Each sub-app should be self-contained:

```
myapp/subapp/
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
├── hx_base.html          # HTMX base (minimal)
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
myapp/subapp/
├── models.py
└── tests/
    ├── __init__.py
    ├── fixtures.py      # Pytest fixtures
    ├── factories.py    # factory-boy factories
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
