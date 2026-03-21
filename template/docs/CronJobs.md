# Cron Jobs

Scheduled tasks run as Kubernetes `CronJob` objects, defined in `helm/site/values.yaml`.
The Helm chart (`helm/site/templates/cronjobs.yaml`) iterates over the `cronjobs:` map
and creates one `CronJob` per entry.

## Adding a Cron Job

Add an entry under `cronjobs:` in `helm/site/values.yaml`:

```yaml
cronjobs:
  my-job:
    schedule: "0 3 * * *"        # daily at 03:00 UTC
    command: "./manage.sh my_app_my_command"
```

- **Key** (`my-job`) becomes the Kubernetes resource name — use lowercase kebab-case.
- **`schedule`** — standard cron syntax (UTC). Use [crontab.guru](https://crontab.guru) to verify expressions.
- **`command`** — passed to `/bin/bash -c`; use `./manage.sh` to invoke management commands.

Secrets and environment variables are injected automatically from the cluster `ConfigMap`
and `Secret`, so management commands have full Django settings available.

## Writing the Management Command

```python
# my_app/management/commands/my_command.py
from django.core.management import BaseCommand

class Command(BaseCommand):
    help = "Brief description shown in --help"

    def handle(self, **options) -> None:
        # do work here
        ...
```

Run locally with:

```bash
just dj my_command
```

## Long-Running or Parallel Work: Use django-tasks

Cron jobs are thin triggers — they run single-threaded, have no retry on failure, and
will be killed if they exceed the job deadline. For anything non-trivial, the management
command should enqueue tasks and return immediately; the worker processes them in parallel.

```python
# my_app/management/commands/process_items.py
from django.core.management import BaseCommand
from my_app import tasks

class Command(BaseCommand):
    help = "Enqueue pending items for processing"

    def handle(self, **options) -> None:
        for item in Item.objects.filter(status="pending"):
            tasks.process_item.enqueue(item_id=item.pk)
        self.stdout.write(f"Enqueued {Item.objects.filter(status='pending').count()} items")
```

The corresponding task does the real work:

```python
# my_app/tasks.py
from django.tasks import task

@task
async def process_item(*, item_id: int) -> None:
    item = await Item.objects.aget(pk=item_id)
    await item.process()
```

See `docs/Django-Tasks.md` for full task documentation.

**When to do work inline** (directly in `handle`): short, low-risk operations that finish
in seconds and don't need retry — e.g. `clearsessions`, `prune_db_task_results`.

**When to enqueue tasks**: anything that touches external APIs, processes many records,
or must retry on failure.

## Built-in Cron Jobs

Two cron jobs ship by default:

| Name | Schedule | Command |
|---|---|---|
| `clear-sessions` | `20 5 * * *` | `clearsessions` — purges expired Django sessions |
| `prune-db-task-results` | `25 9 * * *` | `prune_db_task_results --min-age-days=1` — removes old task records |

## Resource Limits

Cron jobs use the `resources.cronjob` profile from `values.yaml` (default: 512 Mi / 200m
request, 1024 Mi / 800m limit). Override per-job in `values.secret.yaml` if a job is
memory-intensive.

## Concurrency Policy

All cron jobs use `concurrencyPolicy: Replace` — if a previous run is still executing
when the next schedule fires, the old job is terminated and replaced. Design commands to
be safe to interrupt (idempotent enqueue calls, no long transactions).

## Node Scheduling

All batch workloads — CronJobs, one-off restore pods, and Helm release jobs — must run
on the `jobrunner` node. This is enforced via `nodeSelector` in every pod spec:

```yaml
nodeSelector:
  role: jobrunner
```

This is already set in all chart templates (`cronjobs.yaml`, `postgres-backup-cronjob.yaml`,
`release-job.yaml`) and in the `db-restore` pod created by `just rdb-restore`. When adding
any new one-off job or CronJob, always include this selector.

## Observing Jobs

```bash
# List cron jobs and their last schedule time
kubectl get cronjobs -n <namespace>

# List recent job runs
kubectl get jobs -n <namespace>

# Stream logs from the most recent run of a job
kubectl logs -n <namespace> -l job-name=<job-name> --tail=100
```
