**/dj-create-migration <app> [name]**

Creates a Django data migration for the given app.

Generates an empty migration file via `makemigrations --empty` (never writes
the file manually), then fills in a `RunPython` or `RunSQL` operation based on
your choice. Prompts for reversibility — adds `noop` if not reversible. You can
type **skip** to leave the implementation empty and fill it in yourself.

Arguments:
  `<app>`   — the Django app to create the migration in (required)
  `[name]`  — snake_case name for the migration (optional; prompted if omitted)

Examples:
  /dj-create-migration orders
  /dj-create-migration orders backfill_order_totals
