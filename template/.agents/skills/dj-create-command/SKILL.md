---
description: Add a management command with tests
---

Create a Django management command for the given app, with tests. Optionally
enqueues background tasks via `django-tasks-db` for long-running or parallel work.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/python-style-guide.md`

Parse `$ARGUMENTS` as: `<app_name> [description]`

---

## Step 1 — Gather requirements

If no description was provided in `$ARGUMENTS`, ask:

> Describe the management command for `<app_name>`. What should it do?

Then ask:

> Does this command need to run long-running or parallel background work?
> (If yes, tasks will be enqueued via `django-tasks-db` and processed by the worker.)

Wait for both answers before proceeding.

Derive a `snake_case` command name from the description (e.g. "process pending orders"
→ `process_pending_orders`). State the derived name and ask the user to confirm or
correct it before writing anything.

---

## Step 2 — Confirm the plan

Print a summary and wait for "yes":

```
Command: <command_name>
File:    <package_name>/<app_name>/management/commands/<command_name>.py
Test:    <package_name>/<app_name>/tests/test_commands.py
Tasks:   <yes — will call /dj-create-task | no>
```

---

## Step 3 — Create tasks (if needed)

If the user confirmed background tasks are needed, run:

```
/dj-create-task <app_name> <task_name>
```

Wait for that to complete before continuing. The management command will import
and enqueue the task(s) generated in that step.

---

## Step 4 — Create the management/commands/ package

Check whether `<package_name>/<app_name>/management/` exists. If not, create:

```
<package_name>/<app_name>/management/__init__.py        (empty)
<package_name>/<app_name>/management/commands/__init__.py  (empty)
```

If the directory already exists, leave existing files untouched.

---

## Step 5 — Write the management command

Create `<package_name>/<app_name>/management/commands/<command_name>.py`.

**Command that does work inline** (short, low-risk, no retry needed):

```python
from __future__ import annotations

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "<one-line description>"

    def handle(self, **options) -> None:
        # implementation
        self.stdout.write("Done.")
```

**Command that enqueues tasks** (long-running or parallel):

```python
from __future__ import annotations

from django.core.management import BaseCommand

from <package_name>.<app_name> import tasks


class Command(BaseCommand):
    help = "<one-line description>"

    def handle(self, **options) -> None:
        enqueued = 0
        for <item> in <queryset>:
            tasks.<task_name>.enqueue(<arg>=<item>.<field>)
            enqueued += 1
        self.stdout.write(f"Enqueued {enqueued} <items>.")
```

Add `def add_arguments(self, parser)` only if the command genuinely needs CLI
flags. Do not add arguments speculatively.

---

## Step 6 — Write tests

Create or append to `<package_name>/<app_name>/tests/test_commands.py`.

**Inline command** (assert side effects):

```python
from __future__ import annotations

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_<command_name>() -> None:
    call_command("<command_name>")
    # assert expected side effect, e.g. objects created/updated
```

**Enqueuing command** (verify tasks are enqueued; `ImmediateBackend` fixture
already active — task runs synchronously, so assert its effects):

```python
from __future__ import annotations

import pytest
from django.core.management import call_command

from <package_name>.<app_name>.tests.factories import <ItemFactory>


@pytest.mark.django_db
def test_<command_name>_enqueues_tasks() -> None:
    <ItemFactory>.create_batch(3)
    call_command("<command_name>")
    # assert the task's side effect on all 3 items
```

---

## Step 7 — Verify

```bash
just check-all
```

---

## Step 8 — Offer to schedule via cron

Once tests pass, ask:

> `<command_name>` is ready. Would you like to schedule it as a Kubernetes cron job?
> (`/dj-deploy-cron <app_name> <command_name>`)

Wait for the user's answer. Do not run `dj-deploy-cron` automatically.
