**/djs-doc [app_name]**

Creates or updates documentation about this project itself — its purpose, domain
terms, apps, business rules, lifecycles, APIs, webhooks and integrations.

Generic stack docs (`docs/htmx.md`, `docs/django-models.md`, ...) describe *how* to
build with the template. `/djs-doc` documents *what* this project built:

- `docs/this-project.md` — project overview, glossary, app map, integrations, decisions
- `<package>/<app>/README.md` — one per app: business rules, lifecycles, API, reference

Scans the code for what it can derive, then asks you (one question at a time) for
what the code cannot say — why rules exist, what terms mean, edge cases. Re-running
updates existing docs: refreshes code-derived sections, flags stale references and
conflicts, asks only about new or changed items, and never overwrites your answers
without asking. Shows a summary of changes for approval before writing.

Arguments:
  app_name — optional; document a single app instead of the whole project

Examples:
  /djs-doc
  /djs-doc billing
