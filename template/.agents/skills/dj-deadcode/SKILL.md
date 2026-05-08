---
description: Remove unused Python code, Django templates and static assets
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
scripts/find-unused-urls.py
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
scripts/find-unused-templates.py
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

Run:

```bash
uvx deptry .
```

Flag any package reported as unused. Cross-check against `config/settings.py`
`INSTALLED_APPS` and any `TYPE_CHECKING` imports before confirming it is truly
unused.

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

Unused dependencies (deptry):
  - boto3 — not imported outside settings; remove from pyproject.toml if
    USE_STORAGE is disabled

Uncertain (possible false positives — review manually):
  - accounts/signals.py: on_user_created() — decorated with @receiver;
    vulture flags as unused but Django signal dispatch is dynamic
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
