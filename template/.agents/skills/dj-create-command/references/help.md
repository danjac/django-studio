**/dj-create-command <app_name> [description]**

Creates a Django management command for the given app, complete with tests.

Asks for a description if not provided and derives a `snake_case` command name.
Asks whether the command needs background tasks — if yes, delegates to
`/dj-create-task` first so the command enqueues work rather than doing it inline.
Creates `management/commands/` package structure if absent. Offers to schedule
via `/dj-deploy-cron` once tests pass.

Examples:
  /dj-create-command orders
  /dj-create-command orders "process pending refunds"
