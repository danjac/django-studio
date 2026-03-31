**/dj-create-task <app_name> <task_name>**

Adds an async background task to `<app_name>/tasks.py` using `django-tasks-db`.

Creates (or appends to) `tasks.py` with a `@task`-decorated async function and
writes a unit test. Uses the `ImmediateBackend` fixture already configured in
`tests/fixtures.py` so tasks run synchronously in tests.

Example:
  /dj-create-task orders send_confirmation_email
