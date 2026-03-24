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

Exclude any item that is a framework hook unless you can confirm it is never
called. When in doubt, mark it **uncertain** and surface it to the user rather
than proposing deletion.

---

## 2. Unused URL patterns

Read all `urls.py` files. For each `path()`/`re_path()` entry:

1. Note the `name=` argument.
2. Search the codebase for `{% url '<name>' %}` in templates and
   `reverse('<name>')` / `redirect('<name>')` in Python files.

Flag any named URL with no references in templates or Python as a candidate
for removal, along with its corresponding view and template if those are also
unreferenced.

---

## 3. Unreferenced templates

List every file under `templates/`. For each template:

1. Search Python files for `render(request, "<path>")`,
   `get_template("<path>")`, `loader.get_template("<path>")`.
2. Search templates for `{% include "<path>" %}` and `{% extends "<path>" %}`.

Flag any template not found by either search as potentially unused. Exclude
`base.html` and layout templates (files whose name starts with `_` or
`base`) — these are typically inherited, not referenced directly.

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
