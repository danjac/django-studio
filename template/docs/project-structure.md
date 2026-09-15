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
- [Locality of Behaviour](#locality-of-behaviour)

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
│   ├── management/       # Project-wide management commands
│   │   └── commands/
│   │       ├── set_default_site.py
│   │       └── sync_vendors.py
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
│   │       ├── recipes.py
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

The project uses an "onion" layout: an **outer** app that wraps one or more **inner** domain apps.

### Outer app (`my_package/`)

The top-level package is itself a Django app, registered in `INSTALLED_APPS` alongside the
inner apps. It holds everything that is project-wide rather than tied to one domain:

- HTTP types, responses and decorators (`http/`)
- Middleware, context processors and template tags
- Pagination, partial renderers, and other utilities
- Site-wide views (home page, error pages, etc.)
- Shared test fixtures (`tests/`)
- Management commands (`management/commands/`)

The outer app should not define models. Models are domain objects by definition, so they
belong in an inner app.

### Inner apps (`my_package/<app>/`)

Each inner app covers one logical domain (e.g. `users`) and should be self-contained:

```
my_package/my_app/
├── models.py         # Models, fields, QuerySets
├── views.py          # Request handlers (function-based)
├── urls.py           # URL routes for this app
├── tasks.py         # Background tasks
├── admin.py          # Admin interface
├── gdpr.py           # Feature module, named for its purpose (e.g. users/gdpr.py)
└── tests/            # Colocated tests
```

Workflow logic lives in modules named after the feature, not in `services.py` or on the
model. See "Module Naming" in `docs/python-style-guide.md`.

### Why outer/inner?

- **Dependencies point one way.** Inner apps import shared infrastructure from the
  outer app (e.g. `from my_package.http.request import AuthenticatedHttpRequest`). The outer
  app does not import inner apps at runtime; type-only imports under `TYPE_CHECKING` are fine
  (`http/request.py` does this for `User`). This keeps circular imports out of the project.
- **No `core`/`common`/`utils` app.** Shared code has one obvious home that is already
  namespaced under the project package, instead of a catch-all sibling app.
- **Inner apps can depend on each other, but not in cycles.** For example, a `cart` app will
  naturally depend on a `products` app, and many apps will have a `ForeignKey` to
  `users.User`. Keep those dependencies one-directional: `cart` imports from `products`, but
  `products` should not import from `cart`. Generic helpers that aren't domain logic belong in the outer app.
- **Domain apps are easy to add or remove.** A new domain is a new inner app; nothing in the
  outer layer needs to change beyond URL and `INSTALLED_APPS` wiring.

### Management commands

Django only discovers management commands in the `management/commands/` directory of an
installed app. Because the outer package is a registered app, project-wide commands live in
`my_package/management/commands/`. The template ships with:

| Command | Purpose |
|---------|---------|
| `set_default_site` | Set the domain and name of the default `Site` |
| `sync_vendors` | Update vendored frontend dependencies defined in `vendors.json` |

Run them with `just dj <command>`. Commands that belong to a single domain go in that inner
app's own `management/commands/` directory instead. Tests for all management commands live in
`my_package/tests/test_commands.py`.

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
    ├── recipes.py       # model-bakery recipes
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
5. Use custom management commands for tasks (project-wide ones in `my_package/management/commands/`)
6. Use django-tasks for background jobs
7. Follow Locality of Behaviour (below)

## Locality of Behaviour

> "The behaviour of a unit of code should be as obvious as possible by looking only at
> that unit of code." — Carson Gross,
> [Locality of Behaviour](https://htmx.org/essays/locality-of-behaviour/)

Put code where a reader looking at a feature will find it. Prefer code that is obvious
in place over code that is abstracted away, even at the cost of some repetition.

How the project applies it:

| Area | Local | Not |
| ---- | ----- | --- |
| Tests | `<app>/tests/` beside the modules they test | A top-level `tests/` tree mirroring the package |
| Feature code | `<app>/api/`, `<app>/webhooks/` packages inside the owning app | Project-wide `api/views.py` collecting every app's endpoints |
| Helpers | A private function in the module of its only caller | A new `utils.py` "in case it's needed elsewhere" |
| Templates | `templates/<app>/`, partials defined with `{% partialdef %}` in the page that uses them | One-off include files scattered across shared directories |
| Front-end behaviour | `hx-*` and `x-data` attributes on the element (see `docs/htmx.md`, `docs/alpine.md`) | Event listeners attached from a separate JavaScript file |
| Permissions | Named rules in `<app>/rules.py`, checked where the decision is made (see `docs/authorization.md`) | Access logic re-implemented inline in each view |

Rules of thumb:

- **Extract on the second caller, not the first.** Duplication is cheaper than the
  wrong abstraction. When a second app needs the same helper, move it to the shared
  package (`my_package/http/`, `my_package/db/`, a top-level app such as `api/`).
- **Reuse what already exists.** Locality does not mean re-implementing shared
  utilities — search `my_package/http/`, `my_package/db/`, `partials.py` and
  `paginator.py` first.
- **Locality is not "everything in one file".** Separate concerns (views, schemas,
  URLs) into modules, but keep those modules together in the package that owns the
  feature.
- **Cross-cutting infrastructure is the exception.** Middleware, settings, auth
  backends, and shared API plumbing are genuinely used everywhere and belong in
  shared locations.
