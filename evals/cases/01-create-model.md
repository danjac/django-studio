# Create an app and a model

Covers `/djs-create-app` and `/djs-create-model`: a new app, a model with a unique
field, choices, a foreign key to the user model and timestamps, admin registration,
recipe, fixture, model tests and migration.

## Prompt

```text
/djs-create-model library Book

The `library` app does not exist yet. Create it first by following
.agents/skills/djs-create-app/SKILL.md, then continue with the model.

Answers for djs-create-model:

- Primary key: use the default.
- Timestamps: yes, with the default names `created` / `updated`.
- Fields, in this order:
  - `title`: CharField, max_length 200.
  - `isbn`: CharField, max_length 13, unique.
  - `status`: CharField with fixed choices `draft`, `published`, `archived`.
  - `owner`: ForeignKey to the user model (`settings.AUTH_USER_MODEL`),
    on_delete CASCADE (a book is owned by its user), related_name `books`.
  - `published_on`: DateField, plain, `null=True, blank=True`.
- No extra indexes, no extra uniqueness, no help text, no extra non-editable fields.
- verbose_name "book", verbose_name_plural "books".
- `__str__` returns the title.
- Approve the model sketch as shown.
- Register the model in the admin: yes.
- Run migrate: yes.
- Generate CRUD views: no.
```

## Check

```sh
just check-all
just dj makemigrations --check --dry-run
test -n "$(ls my_app/library/migrations/0001_*.py)"
uv run python manage.py shell -c '
from django.apps import apps
from django.contrib import admin
from django.db import models

Book = apps.get_model("library", "Book")
field = Book._meta.get_field

assert field("title").max_length == 200
assert field("isbn").unique
assert {v for v, _ in field("status").choices} == {"draft", "published", "archived"}
assert field("owner").remote_field.model._meta.label == "users.User"
assert field("owner").remote_field.on_delete is models.CASCADE
assert field("owner").remote_field.related_name == "books"
assert field("published_on").null
assert field("created").auto_now_add and field("updated").auto_now
assert not Book._meta.ordering
assert Book in admin.site._registry
print("model assertions passed")
'
grep -q "BookRecipe" my_app/library/tests/recipes.py
grep -q "def book" my_app/library/tests/fixtures.py
grep -q "my_app.library.tests.fixtures" conftest.py
```

## Review

```text
Review the `library` app in this Django project (package `my_app`).

Verify these facts:

1. `my_app/library/models.py` defines `Book` with fields `title`, `isbn`
   (unique), `status` (a `TextChoices` inner class with draft, published,
   archived), `owner` (ForeignKey to the user model, related_name `books`),
   `published_on`, `created` and `updated`.
2. `Book.__str__` uses only fields on the model itself, not the `owner` relation.
3. `Book` has no `Meta.ordering`.
4. `my_app/library/tests/recipes.py` has a `BookRecipe` that declares a unique
   value for `isbn` (for example with `seq`).
5. `my_app/library/tests/test_models.py` tests that a duplicate `isbn` raises
   `IntegrityError`.
6. The app is registered in `INSTALLED_APPS` in `config/settings.py`.
```
