# Kick off a project from its overview

Covers the project's `/dj-kickoff`: it reads the overview `/dj-bootstrap` writes to
`docs/this-project.md`, then follows the project's `dj-create-app`,
`dj-create-model`, `dj-create-crud`, `dj-localize` (without a TranslateBot key) and
`dj-doc` skills, runs `just check-all` and commits.

## Setup

```sh
cat > docs/this-project.md <<'EOF'
# This Project

This page describes **this project specifically** — what it does, who it is for, and
how its apps fit together. The other pages in `docs/` describe the generic stack and
conventions and are maintained by the template.

Each app has its own `README.md` next to its code with business rules, lifecycles,
APIs and integrations. This page is the map; the app READMEs are the detail.

## Contents

- [Purpose](#purpose)
- [Users and Roles](#users-and-roles)
- [Glossary](#glossary)
- [Apps](#apps)
- [Key Flows](#key-flows)
- [Integrations](#integrations)
- [Key Decisions](#key-decisions)

## Purpose

A recipe sharing site for home cooks: cooks publish their recipes, and anyone can
browse them.

## Users and Roles

| Role | Description |
| ---- | ----------- |
| Visitor | Browses and reads recipes without signing in |
| Cook | A signed-in user; creates and edits their own recipes |
| Staff | Moderates all recipes in the admin |

## Glossary

- **Recipe** — a dish a cook publishes: title, description and instructions.
- **Ingredient** — one line of a recipe's ingredient list: a name and a quantity.

## Apps

_One row per Django app under the project package. Keep responsibilities one line —
detail belongs in the app README._

| App | Responsibility | Depends on | Docs |
| --- | -------------- | ---------- | ---- |
| `users` | _User accounts and profiles_ | — | `my_package/users/README.md` |

## Key Flows

_TODO: the main end-to-end journeys_

## Integrations

_Third-party services the project calls or receives webhooks from. Generic patterns
are in `docs/integrating-apis.md` and `docs/webhooks.md`._

| Provider | Direction | Used for | App | Settings |
| -------- | --------- | -------- | --- | -------- |
| _e.g. Mailgun_ | _API out / webhook in_ | _Transactional email_ | _—_ | _`MAILGUN_API_KEY`_ |

## Key Decisions

| Date | Decision | Why |
| ---- | -------- | --- |
| 2026-09-26 | Public site; login needed only to post recipes | _TODO: why_ |
| 2026-09-26 | UI languages: English (default) and Finnish | _TODO: why_ |
| 2026-09-26 | Public API: not needed | _TODO: why_ |
| 2026-09-26 | Incoming webhooks: not needed | _TODO: why_ |
| 2026-09-26 | Background tasks: planned, for a weekly email digest of new recipes | _TODO: why_ |
EOF
```

## Prompt

```text
/dj-kickoff

Answers:

- Steps: run all of them.
- User model: no changes.
- App and model breakdown: approve this one.
  - One app, `recipes`.
  - `Recipe`: `title` CharField max_length 200; `description` TextField,
    blank; `instructions` TextField; `owner` ForeignKey to the user model,
    on_delete CASCADE, related_name `recipes`; timestamps `created` / `updated`.
    `__str__` returns the title. Register in the admin.
  - `Ingredient`: `recipe` ForeignKey to `Recipe`, on_delete CASCADE,
    related_name `ingredients`; `name` CharField max_length 100; `quantity`
    CharField max_length 50, blank. No timestamps. `__str__` returns the name.
    Register in the admin.
  - Default primary keys, no extra indexes or constraints, no help text,
    verbose names from the model names.
  - CRUD views for `Recipe` only.
- Languages: set up Finnish (`fi`). There is no TranslateBot key.
- Project docs: fill in what the code and this breakdown say; leave `_TODO_`
  markers for the rest.
- Push: there is no remote.
```

## Check

```sh
test "$(git rev-list --count eval-baseline..HEAD)" = 1
test -z "$(git status --porcelain)"
test "$(ls my_app/users/migrations/0*.py | wc -l)" = 1
test -n "$(ls my_app/recipes/migrations/0001_*.py)"
test -f my_app/recipes/forms.py
test -f my_app/recipes/README.md
test -f locale/fi/LC_MESSAGES/django.po
test -f locale/fi/LC_MESSAGES/django.mo
test -f config/formats/fi/formats.py
grep -q "recipes" docs/this-project.md
just dj makemigrations --check --dry-run
just check-all
uv run python manage.py shell -c '
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.db import models

Recipe = apps.get_model("recipes", "Recipe")
Ingredient = apps.get_model("recipes", "Ingredient")

owner = Recipe._meta.get_field("owner")
assert owner.remote_field.model._meta.label == "users.User"
assert owner.remote_field.related_name == "recipes"
recipe = Ingredient._meta.get_field("recipe")
assert recipe.remote_field.model is Recipe
assert recipe.remote_field.on_delete is models.CASCADE
assert recipe.remote_field.related_name == "ingredients"
assert Recipe._meta.get_field("title").max_length == 200
assert Ingredient._meta.get_field("quantity").blank
assert Recipe in admin.site._registry and Ingredient in admin.site._registry
assert "fi" in dict(settings.LANGUAGES)
print("kickoff assertions passed")
'
```

## Review

```text
Review a project that was just given its first app, languages and docs.

Verify these facts:

1. `docs/this-project.md` still has the Purpose, Users and Roles, Glossary and
   Key Decisions content about a recipe sharing site (visitors, cooks, staff;
   English and Finnish; a planned weekly digest), and its Apps section now lists
   the `recipes` app.
2. `my_app/recipes/README.md` describes the `Recipe` and `Ingredient` models.
3. `my_app/recipes/models.py` defines `Recipe` and `Ingredient` as described in
   fact 4 and 5, and `Ingredient.__str__` uses only its own fields.
4. `Recipe` has `title`, `description`, `instructions`, `owner` (ForeignKey to
   the user model) and timestamps `created` and `updated`.
5. `Ingredient` has `recipe` (ForeignKey to `Recipe`, related_name
   `ingredients`), `name` and `quantity`.
6. `locale/fi/LC_MESSAGES/django.po` has a Finnish `Plural-Forms` header, not the
   `nplurals=INTEGER` placeholder.
7. No `tasks.py`, `api/` or `webhooks/` package was added: the optional features
   were not built.
```
