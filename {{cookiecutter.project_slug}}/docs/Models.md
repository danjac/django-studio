# Models

## Custom QuerySet

Define a custom `QuerySet` for every model that needs filtering or annotation
methods. Attach it via `as_manager()`:

```python
from django.db import models


class ItemQuerySet(models.QuerySet):
    def published(self) -> "ItemQuerySet":
        return self.filter(pub_date__isnull=False)

    def by_user(self, user) -> "ItemQuerySet":
        return self.filter(user=user)


class Item(models.Model):
    objects: ItemQuerySet = ItemQuerySet.as_manager()
    pub_date = models.DateTimeField(null=True)
```

## Full-Text Search

Use the `Searchable` mixin from `myapp/db/search.py` for PostgreSQL full-text
search:

```python
from myapp.db.search import Searchable


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

Maintain `search_vector` via a database trigger rather than `post_save`:

```python
# migrations/0002_add_search_trigger.py
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("myapp", "0001_initial")]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE TRIGGER myapp_update_search_trigger
BEFORE INSERT OR UPDATE OF title, description ON myapp_item
FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger(
    search_vector, 'pg_catalog.english', title, description);
UPDATE myapp_item SET search_vector = NULL;""",
            reverse_sql=(
                "DROP TRIGGER IF EXISTS myapp_update_search_trigger ON myapp_item;"
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

## Forms

Forms define only fields, labels, and error messages — **no CSS classes**.
Styling is applied in templates via `widget_tweaks`:

```python
# myapp/<app_name>/forms.py
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name"]
        labels = {"name": "Name"}
        error_messages = {"name": {"unique": "This name is already taken"}}
```

See `design/forms.md` for template-side field rendering conventions, including
how to add a `{% partialdef %}` block in `form/field.html` for custom widgets.
