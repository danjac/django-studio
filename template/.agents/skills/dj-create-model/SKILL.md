---
description: Design and write a Django model with factory, fixture, and model tests
---

Design and write a Django model with factory, fixture, and model tests.

**Before writing anything**, read:
- `<package_name>/<app_name>/models.py` — existing models and patterns
- `<package_name>/<app_name>/tests/factories.py` — existing factories

---

### Step 1 — Gather requirements

**STOP. Do not write any code yet.**

Unless the user has explicitly listed every field and relationship inline with
the command, ask now and wait for their reply before doing anything else:

> Describe `<model_name>`. For each field give: name, type, and options (e.g.
> `null`, `blank`, `choices`, `max_length`, `default`). For relationships
> (ForeignKey, ManyToMany, OneToOneField) also give: target model/app,
> `on_delete`, and `related_name`.

Also ask:

> Should `<model_name>` have timestamps? (created / updated)

If yes, add these fields automatically — do not ask the user to specify them:

```python
created = models.DateTimeField(auto_now_add=True)
updated = models.DateTimeField(auto_now=True)
```

Do not invent fields. Do not make assumptions about what the model "probably"
needs based on the app name or project context. Wait.

For any ambiguous relationship in the user's response, ask a follow-up before
proceeding:
- Which app and model is the target?
- `on_delete`: default to `CASCADE`; use `SET_NULL` if the field is nullable.
- `related_name`: suggest `<model_lower>s` if omitted; confirm with the user.

State every assumption explicitly.

---

### Step 2 — Confirm the plan

Print a model sketch and wait for "yes" before writing any code:

```
Model: <model_name>  →  <package_name>/<app_name>/models.py
  id          BigAutoField (automatic)
  <field>     <FieldType>(<options>)
  …
  __str__:    returns <description>
```

Only include `Meta: ordering = [...]` in the sketch if the user has explicitly
requested a default ordering. Never infer ordering from the model name or fields.

---

### Step 3 — Write the model

Append to `<package_name>/<app_name>/models.py`. Do not touch existing models.

Conventions:
- `from __future__ import annotations` at the top of the file
- Use `models.TextChoices` / `models.IntegerChoices` for enums, as inner classes
- Always define `__str__`; only reference fields on the model itself — never FK
  relations (e.g. use `self.event_id`, not `self.event`)
- Only add `class Meta` with `ordering` if the user explicitly requested it
- FK `related_name` must always be explicit — never rely on the Django default

```python
from __future__ import annotations

from django.db import models


class <model_name>(models.Model):
    class <ChoiceName>(models.TextChoices):  # only if needed
        ...

    <field_name> = models.<FieldType>(...)

    # class Meta:
    #     ordering = [...]  # only if user explicitly requested it

    def __str__(self) -> str:
        return ...  # use self fields only, never FK relations
```

---

### Step 4 — Register with admin (optional)

Ask the user:

> Register `<model_name>` in the Django admin? [y/n]

If yes, open `<package_name>/<app_name>/admin.py` and add:

```python
from django.contrib import admin

from <package_name>.<app_name>.models import <model_name>


@admin.register(<model_name>)
class <model_name>Admin(admin.ModelAdmin):
    list_display = [...]   # infer from model fields: prefer name/title, status, dates
    search_fields = [...]  # CharField and TextField fields
    list_filter = [...]    # choice fields, BooleanFields, date fields
```

Infer sensible defaults from the model fields defined in Step 3. If the model
has no obvious candidates for `search_fields` or `list_filter`, leave them as
empty lists rather than guessing.

---

### Step 5 — Update the factory

Edit `<package_name>/<app_name>/tests/factories.py`. Use `factory.Faker` matched
to the field type — see `resources/factory-reference.md` for the full mapping
table and M2M pattern.

Full factory example:

```python
import factory
from factory.django import DjangoModelFactory

from <package_name>.<app_name>.models import <model_name>


class <model_name>Factory(DjangoModelFactory):
    class Meta:
        model = <model_name>

    <field_name> = <declaration>
```

---

### Step 6 — Update fixtures

Add to `<package_name>/<app_name>/tests/fixtures.py`:

```python
@pytest.fixture
def <model_lower>() -> <model_name>:
    return <model_name>Factory()
```

Add the import for `<model_name>Factory` at the top if not already present.

---

### Step 7 — Write model tests

Add to `<package_name>/<app_name>/tests/test_models.py`:

```python
import pytest

from <package_name>.<app_name>.tests.factories import <model_name>Factory


@pytest.mark.django_db
class Test<model_name>:
    def test_create(self):
        obj = <model_name>Factory()
        assert obj.pk is not None

    def test_str(self):
        obj = <model_name>Factory()
        assert str(obj)
```

Add extra methods for:
- Each `unique=True` field: create two instances with the same value and assert
  `django.db.IntegrityError` is raised.
- Each `unique_together` constraint: same pattern.
- Any `__str__` that returns a specific computed value: assert the exact string.

---

### Step 8 — Verify

```bash
just dj makemigrations <app_name>
just check-all
```

---

### Step 9 — Offer to create CRUD views

Once tests pass, ask:

> `<model_name>` is ready. Would you like to generate CRUD views for it?
> (`/dj-create-crud <app_name> <model_name>`)

Wait for the user's answer. Do not run `dj-create-crud` automatically.
