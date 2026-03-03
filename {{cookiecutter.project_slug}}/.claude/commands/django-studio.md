# Django Studio

@description Manage your Django project: file issues, scaffold new apps, and initialize your project roadmap.
@arguments $ARGUMENTS: Subcommand followed by arguments

## Subcommands

Parse the first word of `$ARGUMENTS` to determine the subcommand:

| Subcommand | Purpose |
|------------|---------|
| `issue`    | File a GitHub issue |
| `create`   | Scaffold a new Django app |
| `init`     | Run Session Zero |

If `$ARGUMENTS` is empty or the first word is not a recognised subcommand, print usage and stop.

---

## `issue` — File a GitHub Issue

Parse `$ARGUMENTS` after `issue`:

- **`issue cookiecutter <feedback>`** — target the django-studio template repo (`danjac/django-studio`). Feedback is everything after `cookiecutter`.
- **`issue <feedback>`** — target the current project.

**Steps:**

1. Draft a concise issue title (≤72 characters, imperative mood).
2. Write a one- or two-sentence body: what to change, where, and why.
3. Create the issue:

   **Current project** — run from the project root:
   ```bash
   gh issue create --title "<title>" --body "<body>"
   ```

   **Template repo** (`danjac/django-studio`):
   ```bash
   gh issue create --repo danjac/django-studio --title "<title>" --body "<body>"
   ```

4. Confirm the issue was created and show the URL.

Log feedback immediately when you notice it — do not wait until the end of a session.

---

## `create` — Scaffold a New Django App

`$ARGUMENTS` after `create` is the app name (snake_case, e.g. `blog`, `shop`).

### 1. Detect the package name

Read `conftest.py`. The first-party package is the prefix in `pytest_plugins` entries before
`.tests.fixtures` (e.g. `myproject.users.tests.fixtures` → `myproject`).

### 2. Create the app files

Create these files under `<package>/<app>/`:

**`__init__.py`** — empty

**`apps.py`**:
```python
from django.apps import AppConfig


class <AppName>Config(AppConfig):
    name = "<package>.<app>"
    default_auto_field = "django.db.models.BigAutoField"
```
(Convert the app name to CamelCase for the class name, e.g. `blog_posts` → `BlogPostsConfig`.)

**`models.py`** — empty

**`admin.py`** — empty

**`views.py`** — empty

**`urls.py`**:
```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

app_name = "<app>"

urlpatterns: list[URLPattern | URLResolver] = []
```

**`tests/__init__.py`** — empty

**`tests/factories.py`** — empty

**`tests/fixtures.py`** — empty

### 3. Update `config/settings.py`

Add `"<package>.<app>"` to `INSTALLED_APPS` after the last existing first-party app entry
(the block of entries beginning with the package name prefix).

### 4. Update `conftest.py`

Add `"<package>.<app>.tests.fixtures"` to the `pytest_plugins` list.

### 5. Update `config/urls.py`

Add an include for the new app immediately after the last first-party `include()`:

```python
path("", include("<package>.<app>.urls")),
```

### 6. Confirm

Report what was created and remind the user to:
- Define models in `models.py` then run `just dj makemigrations <app>`
- Add views in `views.py` and URL patterns in `urls.py`
- Add tests in `tests/`
- Run `/django-studio init` to set up the project roadmap if not already done

---

## `init` — Session Zero

Run Session Zero to establish the project's purpose and roadmap before any development work begins.

**Steps:**

1. Ask all of these questions in a single message:
   - What problem is this project solving?
   - Who are the users and stakeholders?
   - What are the key features and success criteria?
   - What should the project **not** do (out of scope)?
   - What is the intended license? (MIT, BSD-3, GPL-3, AGPL-3, or proprietary)

2. Update `README.md` with a project overview based on the answers.

3. Create `ROADMAP.md` with milestones and tasks. Each task gets a checkbox (`- [ ] Task`).
   Group related tasks into milestones.

4. Present the roadmap to the user for approval.

Do not start any implementation work until the user has explicitly approved the roadmap.

---

## Requirements

- `gh` CLI installed and authenticated (`gh auth status`)
- Working git repository with a remote (for `issue` on the current project)

## Installation

After editing this file in the django-studio repo, sync to your global Claude Code commands:

```bash
just sync-skills
```
