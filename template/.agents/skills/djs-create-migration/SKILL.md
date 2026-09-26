---
description: Create an empty Django data migration (Python or SQL) for an app
---

Create a Django data migration for `<app>`.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/python-style-guide.md`

**Never write migration files by hand.** Always generate the empty file first:

```bash
just dj makemigrations --empty --name <name> <app>
```

Then fill in the operation — this keeps Django's dependency graph intact.

---

### Step 1 — Determine the migration name

If `<name>` was provided, use it as-is.

If not, ask the user:

> What does this migration do? (used to generate the migration name)

Derive a `snake_case` name from the answer (e.g. `backfill_user_display_names`).

---

### Step 2 — Generate the empty migration file

```bash
just dj makemigrations --empty --name <name> <app>
```

This creates the file at `<package_name>/<app>/migrations/<NNNN>_<name>.py` with
the correct dependency chain. Read the generated file to confirm the path and
dependencies before editing.

---

### Step 3 — Choose the operation type

Ask the user:

> Should this migration use Python (`RunPython`) or raw SQL (`RunSQL`)?

- **Python** — for ORM-based data transforms, row-by-row logic, or anything that
  needs the application layer.
- **SQL** — for bulk updates, index creation, triggers, or anything more efficient
  as a single statement.

---

### Step 4 — Ask for functionality

Ask the user:

> Describe what the migration should do, or type **skip** to leave the
> implementation empty (you'll fill it in manually).

If the user skips, write a `pass` body (or empty SQL string) and note that the
implementation is intentionally left blank. Do not invent logic.

---

### Step 5 — Ask about reversibility

Ask the user:

> Should this migration be reversible? [y/n]

- **Yes** — implement a `reverse_sql` string (SQL) or a `reverse_code` function (Python)
  that undoes the forward operation. Ask the user what the reverse should do if
  not obvious.
- **No** — use the appropriate noop:
  - Python: `reverse_code=migrations.RunPython.noop`
  - SQL: `reverse_sql=migrations.RunSQL.noop`

---

### Step 6 — Write the migration

Edit the generated file. Do not change `dependencies` or `initial`.

**Python template:**

```python
from django.db import migrations


def forward(apps, schema_editor):
    <model> = apps.get_model("<app>", "<ModelName>")
    # implementation


def reverse(apps, schema_editor):
    # reverse implementation (or omit if using noop)


class Migration(migrations.Migration):
    dependencies = [...]  # leave as generated

    operations = [
        migrations.RunPython(forward, reverse_code=migrations.RunPython.noop),
    ]
```

**SQL template:**

```python
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [...]  # leave as generated

    operations = [
        migrations.RunSQL(
            sql="<forward SQL>",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
```

Key rules:
- Always use `apps.get_model()` — never import models directly in `RunPython`
  functions (the historical model state may differ from the current model).
- For large tables, consider `atomic = False` on the `Migration` class and use
  `schema_editor.connection.cursor()` for batching — ask the user if the table
  is expected to have more than ~100k rows.

---

### Step 7 — Verify

Ask the user:

> Run `migrate` now to apply this migration? [y/n]

If yes:

```bash
just dj migrate
```

Then:

```bash
just check-all
```
