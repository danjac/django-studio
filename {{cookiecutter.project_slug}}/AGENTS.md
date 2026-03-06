# AGENTS.md

This is a Django project using HTMX, AlpineJS, and Tailwind CSS. See `docs/` for detailed documentation on each part of the stack.

## Environment / Tech Stack

Python 3.14 and Django 6.0 are valid and exist. Do not flag syntax or features from these versions as errors based on knowledge cutoff assumptions.

## Session Workflow

### Session Zero

Before any development work on a new project, run Session Zero:

1. Ask the user in a single message:
   - What problem is this project solving?
   - Who are the users and stakeholders?
   - What are the key features and success criteria?
   - What should the project **not** do (out of scope)?
   - What similar projects exist for reference?
   - What is the intended license? (MIT, BSD-3, GPL-3, AGPL-3, or proprietary)
2. Update `README.md` with a project overview based on the answers.
3. Create `ROADMAP.md` with milestones and checkbox tasks (`- [ ] Task`).
4. Present the roadmap to the user and wait for explicit approval before starting any work.

### Process

At the start of every session:

1. **Fix bugs first.** Check GitHub issues for open bugs. Fix every one before doing any roadmap work. A stable codebase is the baseline.
2. **Resume the roadmap.** Open `ROADMAP.md`, find the next unchecked task, and continue from there.

If `ROADMAP.md` does not exist yet, run Session Zero first.

## Bug Workflow

Bugs are tracked as GitHub issues. For each bug:

1. Create a branch: `git checkout -b fix/<short-description>`
2. Diagnose — state root cause with `file:line` reference before touching code
3. Fix and write a regression test
4. Run `just lint && just typecheck && just test` — all must pass
5. Merge into `main` with: `fix: <description>`
6. Close the GitHub issue

## Roadmap Workflow

The roadmap lives in `ROADMAP.md`, broken into milestones. Each milestone has tasks with checkboxes.

For each milestone:

1. Create a branch: `git checkout -b milestone-<N>`
2. Work through each task. When a task is done, mark it: `- [x] Task name`
3. After each task, run `just lint && just typecheck && just test`
4. When all tasks in the milestone are complete, **stop and report to the user** — do not merge or continue to the next milestone. Wait for explicit approval.
5. After the user approves: tell the user to run `git rebase -i` themselves to squash the branch commits into logical units (this is interactive and cannot be done by the agent). Once they confirm it's done, run:

   ```bash
   git checkout main
   git merge milestone-<N>
   git branch -d milestone-<N>
   ```

## Stack

- **Python 3.14**, **Django 6.0**, **PostgreSQL 18**, **Redis 8**
- **Frontend**: HTMX + AlpineJS + Tailwind CSS (no JS build step; Tailwind compiled via `django-tailwind-cli`)
- **Package manager**: `uv` (not pip/poetry)
- **Task runner**: `just` (see `justfile` for all commands)
- **Background tasks**: Django Tasks (`django-tasks-db`), not Celery
- **Feature flags**: `use_hx_boost`, `use_storage`, `use_pwa`, `use_opentelemetry`, `use_sentry`

## Project Layout

```
config/             # Django settings, URLs, ASGI/WSGI
{{cookiecutter.package_name}}/              # Main application package
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
just test {{cookiecutter.package_name}}/users     # Test a specific module
just tw                           # Watch mode (auto-rerun on .py/.html changes)
just test-e2e                     # End-to-end tests (Playwright, headless)
just test-e2e-headed              # E2E tests with visible browser
```

- Framework: `pytest` with `pytest-django`
- Coverage: **100% required** (`--cov-fail-under=100`)
- Test location: colocated in `{{cookiecutter.package_name}}/**/tests/` directories

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

**NOTE**: on initial project generation, run `just install` to set up the environment before doing anything else. This will install Python dependencies and set up pre-commit hooks. You should then run `just update` to ensure all dependencies are up to date, as they may have been updated since the template was created.

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
| `design/cards.md`      | `card.html` - link card with optional image         |
| `design/badges.md`     | Status badges, count chips, category tags           |
| `design/pagination.md` | `paginate.html` - Previous/Next with HTMX           |
| `design/typography.md` | `markdown.html`, prose, heading scale, link style   |
| `design/layout.md`     | Base templates, two-column layout, HTMX indicator   |

**Before writing new UI markup**, check `design/` first — the component you need likely already exists.

### JSON Serialization and Validation

Use **Pydantic** for JSON serialization and validation — both for parsing third-party/external API responses and for internal API payloads. Do not use Django REST Framework serializers.

When adding Pydantic (`uv add pydantic`), add this to `pyproject.toml` to prevent ruff from moving Pydantic base class imports into `TYPE_CHECKING` blocks:

```toml
[tool.ruff.lint.flake8-type-checking]
runtime-evaluated-base-classes = ["pydantic.BaseModel"]
```

### Image Processing and Thumbnails

Use **sorl-thumbnail** for image thumbnails (`uv add sorl-thumbnail`). Add `"sorl.thumbnail"` to `INSTALLED_APPS`. Uses the Redis cache backend (already configured).

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

Hierarchy — use the first that fits:

{% raw %}1. `{{ form.title.as_field_group }}` — explicit field-by-field control over order
2. `{% for field in form %} {{ field.as_field_group }} {% endfor %}` — all fields, default order
3. `{{ form }}` — renders all fields using the configured template renderer

Never use `{{ form.as_div }}` — it bypasses the configured renderer. Never use `{% include "form/field.html" %}`.{% endraw %}

See `design/forms.md` for full field template documentation.

## Testing Conventions

- Tests use `factory-boy` and `faker` for test data
- Fixtures organized as pytest plugins in `*/tests/fixtures.py`
- Coverage source: `{{cookiecutter.package_name}}/`, omits migrations and test files
- E2E tests marked with `@pytest.mark.e2e` and excluded from default test runs

## Working Conventions

### Required reading before implementation

| What you are about to implement | Read first                                                  |
| ------------------------------- | ----------------------------------------------------------- |
| Any template or UI component    | `docs/UI-Design-Patterns.md` + all of `design/`             |
| Background task                 | `docs/Django-Tasks.md`                                      |
| HTMX interaction                | `docs/HTMX.md`                                              |
| AlpineJS component              | `docs/Alpine.md`                                            |
| Tailwind / CSS                  | `docs/Tailwind.md`                                          |
| Authentication / allauth        | `docs/Authentication.md`                                    |
| Deployment / infrastructure     | `docs/Helm-Terraform.md`, `docs/k3s-Hetzner-Cloudflare.md` |
| Testing patterns                | `docs/Testing.md`                                           |
| Any of the above                | `docs/Project-Structure.md` (once per session)              |

If a doc contradicts what you see in existing code, flag it — do not silently pick one.

- **Search before implementing** — Before writing new code, search the codebase with `rg` or `ast-grep` for existing utilities, mixins, and patterns. Check `{{cookiecutter.package_name}}/admin.py` for admin mixins, `{{cookiecutter.package_name}}/db/search.py` for full-text search, `{{cookiecutter.package_name}}/http/` for request/response utilities.
- **Scope discipline** — Only change what was explicitly requested.
- **Diagnose before changing** — Read the code and state your diagnosis with a file:line reference before editing.
- **Verify runtime behaviour** — Passing tests is necessary but not sufficient.

## Template Feedback

This project was generated from [django-studio](https://github.com/danjac/django-studio). When you encounter something that should be fixed or improved in the template itself — a broken default, a missing utility, an antipattern — log it immediately using the `/django-studio` command:

```
/django-studio issue cookiecutter <what to fix or improve and why>
```

The justfile also has equivalent targets for use outside an agent session:

```bash
just studio "Fix post_gen hook" "service-worker.js is not removed when use_pwa=n"
```

Do not wait until the end of a session. Log it when you notice it.
