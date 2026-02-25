# Django Tasks

This project uses `django-tasks-db` for background tasks instead of Celery.

## Installation

```bash
uv add django-tasks-db
```

Add to `INSTALLED_APPS`:
```python
"django_tasks_db",
```

Configure in settings:
```python
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
    }
}
```

## Defining Tasks

```python
# myapp/tasks.py
from django.tasks import task

@task
async def my_task(*, item_id: int) -> str:
    """Task description."""
    # Async task logic
    await do_something(item_id)
    return "completed"
```

## Enqueuing Tasks

```python
# From views or management commands
from myapp.tasks import my_task

# Enqueue with kwargs
my_task.enqueue(item_id=123)
```

## Running the Task Worker

```bash
just dj db_worker
```

This runs the Django tasks database worker to process queued tasks.

## Task Scheduling

Tasks can be scheduled via cron (using management commands):

```python
# myapp/management/commands/myapp.py
from typing import Annotated
import typer
from django_typer.management import Typer
from myapp import tasks

app = Typer()

@app.command()
def process_items(
    limit: Annotated[int, typer.Option("--limit", "-l")] = 100,
) -> None:
    """Process items."""
    for item in Item.objects.all()[:limit]:
        tasks.process_item.enqueue(item_id=item.id)
```

Run via cron:
```bash
# /etc/cron.d/myapp
*/15 * * * * user /path/to/venv/bin/python manage.py myapp process-items --limit=100
```

## Testing

Use the dummy backend for tests:

```python
# conftest.py or test settings
@pytest.fixture(autouse=True)
def _immediate_task_backend(settings):
    settings.TASKS = {
        "default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend"}
    }
```

This runs tasks synchronously during tests.

## Benefits over Celery

- Simpler deployment (just Django + database)
- Tasks stored in database with status tracking
- Built-in retry support

## When to Use

- Background jobs that don't require precise timing
- Periodic tasks (via cron)
- Task chains where ordering matters

## When NOT to Use

- High-throughput message queues
- Real-time task processing
- Complex task routing/partitions

## Running the Task Worker

A separate process is required to process tasks:

```bash
just dj db_worker
```

This runs the Django tasks database worker to process queued tasks.
