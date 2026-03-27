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

Each sub-step below is a separate question. Ask one, wait for the answer, then
proceed to the next. Do not bundle questions together.

#### 1a — Primary key

Read `DEFAULT_AUTO_FIELD` from the project's `settings.py`. Also check
`<package_name>/<app_name>/apps.py` for a `default_auto_field` override — the
app-level setting takes precedence.

Ask:

> Primary key: `id` (`<resolved_field_type>`) — use defaults?  [Y/n]

If **yes**, use the resolved default. Do not emit an explicit `id` field in the
model body (Django adds it automatically).

If **no**, ask:

1. Field name (e.g. `code`, `uid`) — use that name in the sketch and model body
2. Field type. If the user says **UUID** or **UUIDField**:
   - Ask: `Generator function?  [default: uuid.uuid4]`
   - Use `models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
     verbose_name="<name>")`
   - No further questions needed.
   - For any other non-default PK type, ask for options as needed.

Always show the PK in the model sketch, whether default or custom.

#### 1b — Timestamps

Ask alone and wait:

> Should `<model_name>` have timestamps?  [Y/n]

If **yes**, ask:

> Use default field names `created` / `updated`?  [Y/n]

If yes to defaults, use:

```python
created = models.DateTimeField(auto_now_add=True, verbose_name="created")
updated = models.DateTimeField(auto_now=True, verbose_name="updated")
```

If no, ask for the preferred names and use those.

#### 1c — Fields one at a time

Say:

> Add fields one at a time. For each, give the field name and type
> (e.g. "title char", "price decimal", "author FK"). Type **DONE** when finished.

For each field the user gives:

- If no type is given, ask: `What type is <field_name>?`
- Apply the type-specific follow-ups below, then confirm the resolved field
  definition before moving on to the next.

**Applied silently without asking** (Django best practices):
- `CharField` / `TextField`: `blank=True` (never `null=True`)
- `ManyToManyField`: `blank=True`
- `UUIDField` (non-PK): `editable=False`, `unique=True` — user can override either
- `verbose_name`: infer from field name (snake_case → space-separated lowercase),
  unless the user specifies otherwise

**Type-specific follow-ups:**

| Type | Ask |
|------|-----|
| `CharField` | `max_length`? |
| `DecimalField` | `max_digits`? `decimal_places`? |
| `ForeignKey` / `OneToOneField` | Target model (and app if ambiguous)? `on_delete`? (default `CASCADE`; use `SET_NULL` if nullable) `related_name`? (suggest `<model_lower>s`) |
| `ManyToManyField` | Target model (and app if ambiguous)? `related_name`? (suggest `<model_lower>s`) |
| `BooleanField` | `default`? |
| `DateField` / `DateTimeField` | `auto_now_add`, `auto_now`, or plain? |
| `FileField` | `upload_to`? |
| `ImageField` | `upload_to`? → then ask sorl-thumbnail (see below) |
| `UUIDField` (non-PK) | Generator function? (default `uuid.uuid4`). Defaults: `unique=True`, `editable=False` — confirm or override. |

**ImageField → sorl-thumbnail:**

When the user adds an `ImageField`, ask immediately after `upload_to`:

> Use sorl-thumbnail for on-the-fly resizing?  [Y/n]  (see `docs/images.md`)

If **yes**:
- Use `sorl.thumbnail.ImageField` instead of `models.ImageField`
- Import: `from sorl.thumbnail import ImageField`
- Flag to user: confirm sorl-thumbnail is in `INSTALLED_APPS`

If **no**, use `models.ImageField`.

Continue until the user types `DONE`.

#### 1d — Model-level options (ask after DONE)

Ask each of these separately, in order:

1. **Indexing** — `db_index=True` on any fields, or composite
   `indexes = [models.Index(fields=[...])]` in `Meta`?

2. **Uniqueness** — `unique=True` on any fields, or a
   `UniqueConstraint(fields=[...], name="...")` in `Meta`?

3. **Help text** — any fields needing `help_text` for the admin or forms?

4. **Non-editable fields** — any additional fields that should be
   `editable=False`? (UUID fields are already set automatically; no need to
   re-ask those.)

#### 1e — Model Meta

Infer `verbose_name` from the model name (lowercase, space-separated) and
`verbose_name_plural` by appending `s` (or ask if the plural looks irregular).
Confirm both with the user before proceeding.

**Never** add `ordering` unless the user explicitly requests it.

Use plain tuples for Meta sequences — no `ClassVar` annotation needed.

---

### Step 2 — Confirm the plan

Show the full model sketch and wait for the user to approve or request changes
before writing any code:

```
Model: <model_name>  →  <package_name>/<app_name>/models.py

  <pk_name>   <PKFieldType>(primary_key=True, ...)   ← always shown
  <field>     <FieldType>(<options>, verbose_name="...")
  …
  created     DateTimeField(auto_now_add=True, ...)   ← if timestamps
  updated     DateTimeField(auto_now=True, ...)

  Meta:
    verbose_name        = "<verbose_name>"
    verbose_name_plural = "<verbose_name_plural>"
    indexes             = [...]   ← only if requested
    constraints         = [...]   ← only if requested

  __str__: returns <description>
```

**Never** include `ordering` in the sketch unless the user explicitly asked for
it. Use plain tuples for Meta sequences — no `ClassVar` annotation needed:

```python
# Good
ordering = ("-created",)

# Bad — unnecessary annotation
ordering: ClassVar[list[str]] = ["-created"]
```

---

### Step 3 — Write the model

Append to `<package_name>/<app_name>/models.py`. Do not touch existing models.

Conventions:
- `from __future__ import annotations` at the top of the file
- Use `models.TextChoices` / `models.IntegerChoices` for enums, as inner classes
- Always define `__str__`; only reference fields on the model itself — never FK
  relations (e.g. use `self.event_id`, not `self.event`)
- FK `related_name` must always be explicit — never rely on the Django default
- Always include `class Meta` with `verbose_name` and `verbose_name_plural`
- Never add `ordering` to Meta unless the user explicitly requested it
- Use plain tuples for Meta sequences (e.g. `ordering = ("-created",)`) — no
  `ClassVar` annotation needed; see `docs/python-style-guide.md`

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
