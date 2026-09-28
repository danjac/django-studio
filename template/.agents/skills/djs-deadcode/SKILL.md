---
description: Remove unused Python code, templates, static assets and dependencies
---

Scan the project for unused code and assets. **Always present a summary of
everything to be removed for explicit user approval before making any changes.**

> **Warning:** This command permanently removes code. Run it only once the
> project is feature-complete. Deleted code cannot be recovered unless it is
> committed to version control.

---

## 1. Python dead code (vulture)

Run `vulture` to detect unused Python symbols:

```bash
uvx vulture <package_name>/ --min-confidence 80
```

Collect all reported items. For each one, verify by searching the codebase
before marking it dead — `vulture` has false-positive rates on:

- Django signal handlers and receivers
- `django-admin` management commands (the `handle` method)
- Model `Meta` classes and `__str__` methods
- Celery/django-tasks task functions decorated with `@task`
- Class-based view methods (`get`, `post`, `form_valid`, etc.)
- Template tag and filter functions registered via `@register`
- `pytest` fixtures and test helper functions
- **Pytest fixture arguments** — unused variables in test function signatures
  are pytest fixtures injected by name for their side effects (e.g.
  `transactional_db`, `django_db_setup`). They appear unused to vulture but
  are required for the fixture to run. **Never remove these.**
- **`TYPE_CHECKING` imports used in `cast()` string annotations** — imports
  guarded by `if TYPE_CHECKING:` are invisible to vulture at runtime. An
  import like `from myapp.types import GeopyLocation` used only in
  `cast("GeopyLocation | None", ...)` will be flagged as unused. Verify
  with `rg 'GeopyLocation'` before removing.

Exclude any item that is a framework hook unless you can confirm it is never
called. When in doubt, mark it **uncertain** and surface it to the user rather
than proposing deletion.

---

## 2. Unused URL patterns

Run the bundled scanner:

```bash
.agents/skills/djs-deadcode/scripts/find-unused-urls.py
```

It reads all `urls.py` files to collect named URL patterns, then scans every
`.py` and `.html` file (excluding `.venv`) for `{% url %}`, `reverse()`, and
`redirect()` references, stripping namespace prefixes before comparing. Any
pattern with no references is printed.

Flag each result as a candidate for removal together with its view and template
if those are also unreferenced.

---

## 3. Unreferenced templates

Run the bundled scanner:

```bash
.agents/skills/djs-deadcode/scripts/find-unused-templates.py
```

It walks every `.html` file under `templates/`, greps the path string across
all `.py` and `.html` files, and prints any with no hits. Catches all reference
forms: `TemplateResponse`, `render_to_string`, `{% extends %}`, `{% include %}`,
`{% fragment %}`, `{% partial "file#name" %}`. Skips `base*.html` and `_*.html`
automatically.

Flag any template printed by the script as potentially unused.

---

## 4. Unused static files

List every file under `static/` (or `<package_name>/static/`).

1. Search templates for `{% static "<path>" %}` references.
2. Search CSS files for `url(...)` references.
3. Search Python files for `staticfiles.finders` or explicit static URL paths.

Flag any file with zero references. Treat compiled output (`*.min.js`,
`*.min.css`, `app.css`) as derived — flag the source instead.

---

## 5. Dead migrations

List all migration files. Flag as candidates for squashing (not deletion) any
migration that:

- Is a `squashedmigrations` file whose `replaces` list is already applied
  (i.e. all replaced migrations are still present on disk after squash)

Do not flag individual intermediate migrations for deletion — squashing is the
correct tool. Mention `manage.py squashmigrations` if relevant.

---

## 6. Unused dependencies

Run `deptry` inside the project environment, so it can map distribution names
to import names (`django-allauth` → `allauth`), and report unused dependencies
only:

```bash
uv run --with deptry deptry . --ignore DEP001,DEP003,DEP004
```

deptry only sees `import` statements, so it reports every package that Django
loads from a string. On a new project, all of its results are false positives.
Treat each result as unverified until you have searched for its import name
(`rg -n '<import_name>' --glob '!uv.lock' --glob '!pyproject.toml'`)
and checked where Django loads packages by string:

- `config/settings.py`: `INSTALLED_APPS`, `MIDDLEWARE`, `STORAGES`,
  `EMAIL_BACKEND`, `TEMPLATES` builtins, and `TYPE_CHECKING` imports
- `{% load %}` tags in templates (`{% load heroicons %}`, `{% load widget_tweaks %}`)
- `Dockerfile`, `gunicorn.conf.py`, `*.sh`, `justfile` and `helm/` (`gunicorn`,
  `uvicorn`)
- URL-configured backends, where the scheme selects the driver and the package
  name never appears: `DATABASE_URL` needs `psycopg`, and `REDIS_URL` needs
  `redis`/`django-redis`

A package with any of these references is in use. Only packages with no
references go in the removal list. Mark a package **uncertain** if you can't
rule out that it's loaded indirectly.

Remove approved packages with `uv remove <package>` so that `uv.lock` stays in
sync, then delete any leftover settings for them.

---

## Approval step

After all sections are complete, present a single consolidated list grouped
by category:

```
PROPOSED REMOVALS
=================

Python symbols (vulture, confidence >= 80%, manually verified):
  - accounts/utils.py: format_initials() — no references found
  - reports/models.py: ReportDraft.generate_pdf() — no references found

Templates:
  - templates/reports/draft_preview.html — no render/include/extends found

Static files:
  - static/js/legacy-ie.js — no {% static %} or url() references found

Unused dependencies (deptry, manually verified):
  - markdown — no imports, settings, template or script references found

Uncertain (possible false positives — review manually):
  - accounts/signals.py: on_user_created() — decorated with @receiver;
    vulture flags as unused but Django signal dispatch is dynamic
  - django-redis — no references found, but REDIS_URL may select it as the
    cache backend
```

Then ask:

> I found N items to remove across M categories. Some are marked uncertain —
> these require your judgment. Should I proceed with the verified removals,
> review the uncertain ones with you first, or stop here?

Do not delete, edit, or move any file until the user confirms. Once confirmed,
apply only the approved removals and run:

```bash
just check-all
```

Fix any failures before presenting the final summary.
