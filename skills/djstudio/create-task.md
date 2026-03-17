Add a background task using `django-tasks-db`. See `docs/Django-Tasks.md`.

**Steps:**

1. Create or open `<package_name>/<app_name>/tasks.py`.

2. Write the task — must be `async`, decorated with `@task`, and use
   keyword-only arguments:
   ```python
   from django.tasks import task

   @task
   async def <task_name>(*, <arg>: <type>) -> str:
       """<description>"""
       # implementation
       return "completed"
   ```

   Enqueue it with: `<task_name>.enqueue(<arg>=<value>)`

3. **Write a test** — the fixtures in `<package_name>/tests/fixtures.py`
   already override `TASKS` to use `ImmediateBackend`, which runs tasks
   synchronously. Do not add another override.
   ```python
   @pytest.mark.django_db
   def test_<task_name>():
       result = <task_name>.enqueue(<arg>=<value>)
       assert result.status == "complete"
   ```

4. If adding a management command for cron scheduling, create
   `<package_name>/<app_name>/management/commands/<name>.py` and add a test.

5. Verify: `just check-all`

---

## Help

**djstudio create-task <app_name> <task_name>**

Adds an async background task to `<app_name>/tasks.py` using `django-tasks-db`.

Creates (or appends to) `tasks.py` with a `@task`-decorated async function and
writes a unit test. Uses the `ImmediateBackend` fixture already configured in
`tests/fixtures.py` so tasks run synchronously in tests.

Example:
  /djstudio create-task orders send_confirmation_email
