# Models

## Contents

- [Custom QuerySet](#custom-queryset)
- [`__str__` convention](#__str__-convention)
- [Linting bypass comments](#linting-bypass-comments)
- [Full-Text Search](#full-text-search)
- [Choices](#choices)
- [Relationships](#relationships)
- [Migrations](#migrations)

## Custom QuerySet

Define a custom `QuerySet` for every model that needs filtering or annotation
methods. Attach it via `as_manager()`:

```python
from typing import Self

from django.db import models


class ItemQuerySet(models.QuerySet["Item"]):
    def published(self) -> Self:
        return self.filter(pub_date__isnull=False)

    def by_user(self, user: "User") -> Self:
        return self.filter(user=user)


class Item(models.Model):
    objects: ItemQuerySet = ItemQuerySet.as_manager()  # type: ignore[assignment]
    pub_date = models.DateTimeField(null=True)
```

**Typing notes:**

- `QuerySet["Item"]` — parameterise the base class so `.get()`, `.first()`,
  and other single-object methods return `Item`, not `Any`.
- `Self` (from `typing`) — use on all chaining methods instead of the class
  name as a string. Correct on subclasses and avoids forward-reference strings.
- `# type: ignore[assignment]` — `as_manager()` returns `Manager[Item]`, not
  `ItemQuerySet`; the annotation is intentionally wider for full type inference
  on chained calls (e.g. `Item.objects.published().by_user(u)`).

**Never use `@classmethod` on the model for query logic.** QuerySet methods are
the correct place — they chain correctly and receive `self` as a `QuerySet`,
not the model class.

**No `Meta.ordering` by default.** Do not add `ordering` to `Meta` unless the
user explicitly requests it. Default ordering adds an `ORDER BY` clause to
every query, including ones that don't need it, and can mask missing indexes.
Add an explicit `.order_by()` at the call site instead.

## `__str__` convention

`__str__` must only reference fields on the model itself — never FK relations:

```python
# Good — only reads the model's own column
def __str__(self) -> str:
    return self.name

# Good — FK id column is on this table, no extra query
def __str__(self) -> str:
    return f"Item {self.pk} (event {self.event_id})"

# Bad — accessing self.event triggers an extra SQL query if not select_related
def __str__(self) -> str:
    return f"Item {self.pk} - {self.event}"
```

FK access in `__str__` causes N+1 queries in list views, admin changelistss, and
logging — any place that calls `str()` on a queryset without `select_related`.

## Linting bypass comments

Do not add `# noqa: ...`, `# type: ignore`, or similar inline bypass comments
without first asking the user. In most cases a code change avoids the bypass
entirely. If there is truly no alternative, state the reason and ask before
adding the comment.

## Full-Text Search

Use the `Searchable` mixin from `my_package/db/search.py` for PostgreSQL full-text
search:

```python
from my_package.db.search import Searchable


class ItemQuerySet(Searchable, models.QuerySet):
    default_search_fields = ("search_vector",)


class Item(models.Model):
    objects = ItemQuerySet.as_manager()
    search_vector = SearchVectorField(null=True)
```

Usage:

```python
Item.objects.search("django")
Item.objects.search("django", "title", "description")  # override fields
```

### Search Vector Updates via Triggers

Maintain `search_vector` via a database trigger rather than `post_save`.

**Important:** the trigger config and the `Searchable.search()` config must
match. The mixin defaults to `config='simple'`, so the trigger must also use
`pg_catalog.simple`. Using `pg_catalog.english` in the trigger would apply
English stemming when building the vector (`"alice"` → `"alic"`) but the query
would search for the literal token `"alice"`, silently breaking search for many
common words.

```python
# migrations/0002_add_search_trigger.py
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("my_app", "0001_initial")]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE TRIGGER my_app_update_search_trigger
BEFORE INSERT OR UPDATE OF title, description ON my_app_item
FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger(
    search_vector, 'pg_catalog.simple', title, description);
UPDATE my_app_item SET title = title;""",
            reverse_sql=(
                "DROP TRIGGER IF EXISTS my_app_update_search_trigger ON my_app_item;"
            ),
        ),
    ]
```

## Choices

Use `models.TextChoices` / `models.IntegerChoices` as inner classes:

```python
class Item(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
```

## Relationships

Always define `related_name` explicitly on every `ForeignKey` and
`ManyToManyField`. Django's default reverse accessor (`<model>_set`) is fragile
— it breaks on model renames and is unclear at the call site:

```python
class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    podcast = models.ForeignKey(
        "podcasts.Podcast",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )

class Post(models.Model):
    tags = models.ManyToManyField(
        "Tag",
        related_name="posts",
        blank=True,
    )
```

Use `related_name="+"` only when the reverse relation is genuinely never needed:

```python
created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    related_name="+",  # reverse not needed
)
```

## Migrations

This project uses `django-linear-migrations` to enforce a linear migration
history.

### Normal workflow

Always give migrations a descriptive name:

```bash
just dj makemigrations <app_name> --name <description>
just dj migrate
just test
```

`makemigrations` automatically updates `max_migration.txt` in the affected
app's migrations directory. Never edit `max_migration.txt` by hand.

### Resolving max_migration.txt conflicts

A git conflict in `max_migration.txt` means two branches each created a
migration for the same app simultaneously. This is intentional — the conflict
forces you to resolve the ordering explicitly.

Resolution steps:

1. Keep both migration files. Update the second migration's `dependencies` to
   point to the first.
2. If Django reports two heads, create a merge migration:

   ```bash
   just dj makemigrations --merge --name merge_<branch_a>_<branch_b>
   ```

3. Regenerate `max_migration.txt` to point to the new tip:

   ```bash
   just dj create_max_migration
   ```

4. Validate the graph is linear:

   ```bash
   just dj validate_migration_graph
   ```

5. Apply and verify: `just dj migrate` then `just test`

### Squashing

```bash
just dj squashmigrations <app_name> <from> <to>
just dj create_max_migration
just dj validate_migration_graph
just test
```
