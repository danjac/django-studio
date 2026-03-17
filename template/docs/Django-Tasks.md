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

Tasks are triggered by Kubernetes cron jobs defined in `helm/site/values.yaml`. The cron
job runs a management command that enqueues tasks; the worker processes them in parallel.

```python
# myapp/management/commands/process_items.py
from django.core.management import BaseCommand
from myapp import tasks

class Command(BaseCommand):
    help = "Enqueue pending items for processing"

    def handle(self, **options) -> None:
        for item in Item.objects.filter(status="pending"):
            tasks.process_item.enqueue(item_id=item.pk)
```

```yaml
# helm/site/values.yaml
cronjobs:
  process-items:
    schedule: "*/15 * * * *"
    command: "./manage.sh process_items"
```

See `docs/CronJobs.md` for the full cron job reference.

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
