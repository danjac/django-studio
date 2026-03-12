# AGENTS.md

This is a Django project using HTMX, AlpineJS, and Tailwind CSS. See `docs/` for detailed documentation on each part of the stack.


## Stack

- **Python 3.14**, **Django 6.0**, **PostgreSQL 18**, **Redis 8**
- **Frontend**: HTMX + AlpineJS + Tailwind CSS (no JS build step; Tailwind compiled via `django-tailwind-cli`)
- **Package manager**: `uv` (not pip/poetry)
- **Task runner**: `just` (see `justfile` for all commands)
- **Background tasks**: Django Tasks (`django-tasks-db`), not Celery
- **Feature flags**: `use_hx_boost`, `use_storage`, `use_pwa`, `use_opentelemetry`, `use_sentry`

**NOTE**: Python 3.14 and Django 6.0 are valid and exist. Do not flag syntax or features from these versions as errors based on knowledge cutoff assumptions.


## Project Layout

```
config/             # Django settings, URLs, ASGI/WSGI
{{cookiecutter.package_name}}/              # Main application package
  users/            # User model, authentication
  db/               # Database utilities (search mixin)
  http/             # HTTP utilities (typed requests, responses, decorators)
  partials.py       # render_partial_response() - HTMX partial swap helper
  paginator.py      # render_paginated_response() + no-COUNT Paginator
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
just test {{cookiecutter.package_name}}/users     # Test a specific module
just tw                           # Watch mode (auto-rerun on .py/.html changes)
just test-e2e                     # End-to-end tests (Playwright, headless)
just test-e2e-headed              # E2E tests with visible browser
```

- Framework: `pytest` with `pytest-django`
- Coverage: reported on every run (`--cov-report=term-missing`); the 100% gate is commented out in `pyproject.toml` - enable it when the project is mature
- Test location: colocated in `{{cookiecutter.package_name}}/**/tests/` directories

### Django Management

```bash
just dj help                   # Show list of available commands
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

Conventional commits enforced by commitlint. Format: `type: subject`

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

## Code Style

### Python

- Ruff handles linting and formatting
- Absolute imports only (`absolufy-imports` enforced)
- isort profile: `black`, first-party: `{{cookiecutter.package_name}}`
- `pyupgrade --py314` applied automatically
- `django-upgrade --target-version 6.0` applied automatically

### Design System

A component library lives in `design/`. It documents every ready-made UI component and when to use it:

| Doc                    | Components covered                                  |
| ---------------------- | --------------------------------------------------- |
| `design/buttons.md`    | `btn`, `btn-primary`, `btn-secondary`, `btn-danger` |
| `design/messages.md`   | Django messages toast, HTMX OOB swap                |
| `design/forms.md`      | `form.html`, `form/field.html`, widget classes      |
| `design/navigation.md` | `navbar.html`, `sidebar.html`, user dropdown        |
| `design/headers.md`    | `header.html` - page title with optional subtitle   |
| `design/cards.md`      | `card.html` - vertical tile for grids               |
| `design/lists.md`      | `browse.html` - divided list layout                 |
| `design/badges.md`     | Status badges, count chips, category tags           |
| `design/pagination.md` | `paginate.html` - Previous/Next with HTMX           |
| `design/typography.md` | `markdown.html`, prose, heading scale, link style   |
| `design/layout.md`     | Base templates, two-column layout, HTMX indicator   |

**Before writing new UI markup**, check `design/` first - the component you need likely already exists.

### Frontend Dependencies

**Never use CDNs** for third-party frontend dependencies (JS, CSS, icons, fonts, etc.), and do not introduce `npm` or any Node-based build tooling unless the user explicitly requests it.

Always vendor the latest stable minified library file directly into the project:

- Place vendored files under `static/vendor/` with the version in the filename (e.g. `static/vendor/htmx.2.0.4.min.js`).
- Reference them with Django's `static` template tag in templates.
- See the existing HTMX and AlpineJS files in `static/vendor/` as examples.

### Icons

Use `heroicons[django]` (already in `pyproject.toml`) for all icons. Load the tag at the top of any template that needs icons and prefer the built-in set over custom SVGs.

```html
{% raw %}{% load heroicons %} {% heroicon_mini "x-mark" class="size-4" %} {%
heroicon_outline "arrow-right" class="size-5" %}{% endraw %}
```

Use custom inline SVGs only when no heroicon exists for the shape you need. Never use character entities (`&times;`) or emoji as icons.

See `docs/UI-Design-Patterns.md` for the full icon guide.

### Templates

- `djhtml` for HTML/CSS/JS indentation
- `djlint` for Django template linting (profile: `django`)
- `djade` for Django template formatting
- `rustywind` for Tailwind CSS class ordering

#### Form field rendering

Hierarchy - use the first that fits:

{% raw %}1. `{{ form.title.as_field_group }}` - explicit field-by-field control over order 2. `{% for field in form %} {{ field.as_field_group }} {% endfor %}` - all fields, default order 3. `{{ form }}` - renders all fields using the configured template renderer

Never use `{{ form.as_div }}` - it bypasses the configured renderer. Never use `{% include "form/field.html" %}`.{% endraw %}

See `design/forms.md` for full field template documentation.

### Internationalisation

All user-visible text **must** be wrapped in translation functions. Never
hardcode plain strings in templates or Python code.

**Templates** — use `{% translate %}` (Django 4.0+, not the legacy `{% trans %}`):

```html
{% load i18n %}
<h1>{% translate "Welcome" %}</h1>
<p>{% blocktranslate with name=user.name %}Hello, {{ name }}.{% endblocktranslate %}</p>
```

You can also use `_("string")` directly in tag arguments — this is often cleaner
than a separate `{% translate "x" as var %}` assignment:

```html
{% include "header.html" with title=_("Dashboard") %}
{% include "header.html" with title=_("Dashboard") subtitle=_("Manage your account") %}
<title>{% block title %}{% translate "Home" %}{% endblock %}</title>
```

**Python** — use `gettext_lazy` for class-level declarations, `gettext` (aliased
`_`) in function bodies, and `ngettext` for plurals:

```python
from django.utils.translation import gettext as _, gettext_lazy as _l, ngettext

# model field verbose_name, form labels, etc.
title = models.CharField(_l("title"), max_length=200)

# function body
messages.success(request, _("Profile saved."))

# plurals
msg = ngettext("%(count)s item", "%(count)s items", count) % {"count": count}
```

Use `/djstudio translate <locale>` to extract, translate, and compile message
catalogues.

## Testing Conventions

- Tests use `factory-boy` and `faker` for test data
- Fixtures organized as pytest plugins in `*/tests/fixtures.py`
- Coverage source: `{{cookiecutter.package_name}}/`, omits migrations and test files
- E2E tests marked with `@pytest.mark.e2e` and excluded from default test runs

## Working Conventions

### Required reading before implementation

**Read `docs/Django.md` before starting any implementation.** It documents
installed apps, middleware order, settings conventions, admin patterns, and
migrations. It also indexes the focused docs below.

| What you are about to implement | Read first                                                 |
| ------------------------------- | ---------------------------------------------------------- |
| Any view (new or modified)      | `docs/Views.md`                                            |
| Any model or queryset           | `docs/Models.md`                                           |
| Any form                        | `design/forms.md`                                          |
| Admin registration              | `docs/Django.md`                                           |
| Adding a dependency             | `docs/Packages.md`                                         |
| Any feature handling user data, accounts, or PII | `docs/GDPR.md`                        |
| Any template or UI component    | also `docs/Accessibility.md`                               |
| Async view                      | `docs/Views.md`                                            |
| Any template or UI component    | `docs/UI-Design-Patterns.md` + all of `design/`            |
| Background task                 | `docs/Django-Tasks.md`                                     |
| Migrations / linear-migrations  | `docs/Models.md`                                           |
| HTMX interaction                | `docs/HTMX.md`                                             |
| AlpineJS component              | `docs/Alpine.md`                                           |
| Tailwind / CSS                  | `docs/Tailwind.md`                                         |
| Authentication / allauth        | `docs/Authentication.md`                                   |
| File uploads / media storage    | `docs/File-Storage.md`                                     |
| Deployment / infrastructure     | `docs/Helm-Terraform.md`, `docs/k3s-Hetzner-Cloudflare.md` |
| Testing patterns                | `docs/Testing.md`                                          |
| Any of the above                | `docs/Project-Structure.md`                                |

If a doc contradicts what you see in existing code, flag it - do not silently pick one.

- **Search before implementing** - Before writing new code, search the codebase with `rg` or `ast-grep` for existing utilities, mixins, and patterns. Check `{{cookiecutter.package_name}}/db/search.py` for full-text search, `{{cookiecutter.package_name}}/http/` for request/response utilities, `{{cookiecutter.package_name}}/partials.py` for HTMX partial rendering, and `{{cookiecutter.package_name}}/paginator.py` for paginated views.
- **Scope discipline** - Only change what was explicitly requested.
- **Diagnose before changing** - Read the code and state your diagnosis with a file:line reference before editing.
- **Verify runtime behaviour** - Passing tests is necessary but not sufficient.

## Slash Commands

Project-level slash commands are available in `.claude/commands/`. Invoke them
with `/djstudio <subcommand>` in Claude Code.

`.claude/` is gitignored. Force-add the skill file once after `git init` so it
is tracked in version control:

```bash
git add -f .claude/commands/djstudio.md
```

All project commands live under `/djstudio <subcommand>`:

| Subcommand | Purpose |
| ------------------------------------ | ----------------------------------------------- |
| `create-app <app_name>` | Create a basic Django app (apps.py, models, views, urls, admin, tests) |
| `create-view <app_name> <view>` | Add a view + template + URL following HTMX and design system conventions |
| `create-task <app_name> <task>` | Add a background task using `django-tasks-db` with correct async/keyword-only patterns |
| `create-model <app_name> <model>` | Design and write a Django model with factory, fixture, and model tests |
| `create-crud <app_name> <model>` | Generate full CRUD views, templates, URLs, and tests; runs `create-model` first if the model does not exist |
| `gdpr` | Audit the project for GDPR compliance issues |
| `translate <locale>` | Extract strings, translate via Claude, compile `.mo` catalogue (e.g. `fr`, `de`, `es`) |
| `prelaunch` | Audit all deployment config for missing or placeholder values before first deploy |
| `feedback` | Report a bug or improvement against the django-studio template repo |

## Template Feedback

This project was generated from [django-studio](https://github.com/danjac/djstudio).
To report a bug or improvement in the template, use the built-in slash command:

```
/djstudio feedback
```

This files a GitHub issue directly against the template repo. Use it whenever you notice
something worth fixing in the template itself rather than in this project.
