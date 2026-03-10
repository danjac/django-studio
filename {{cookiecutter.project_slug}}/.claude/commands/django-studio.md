Project assistant for this django-studio generated project.

Determine the main package name from the "Project Layout" section of `AGENTS.md`.

## Usage

```
/django-studio <subcommand> [args]
```

Dispatch on the first word of $ARGUMENTS. If no subcommand is given, print the
list of available subcommands and stop.

---

## Subcommands

### `new-app <app_name>`

Scaffold a complete Django app following this project's conventions.

**Steps:**

1. Create the directory structure under `<package_name>/<app_name>/`:

   ```
   __init__.py          (empty)
   apps.py
   models.py
   views.py
   urls.py
   admin.py
   tests/
       __init__.py      (empty)
       factories.py
       fixtures.py
       test_models.py
       test_views.py
   ```

   Do not create `forms.py`, `tasks.py`, or other files speculatively.

2. **apps.py**
   ```python
   from django.apps import AppConfig

   class <AppName>Config(AppConfig):
       default_auto_field = "django.db.models.BigAutoField"
       name = "<package_name>.<app_name>"
   ```

3. **models.py** — empty module, just `from __future__ import annotations`

4. **views.py** — typed request import only:
   ```python
   from __future__ import annotations
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from <package_name>.http.request import HttpRequest
   ```

5. **urls.py**
   ```python
   from __future__ import annotations
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from django.urls import URLPattern, URLResolver

   app_name = "<app_name>"
   urlpatterns: list[URLPattern | URLResolver] = []
   ```

6. **admin.py** — `from django.contrib import admin`

7. **tests/factories.py** — import stub only (no placeholder factories)

8. **tests/fixtures.py** — `import pytest` stub

9. **tests/test_models.py** and **tests/test_views.py** — `from __future__ import annotations`
   (empty stubs; coverage passes because source files are also empty)

10. Add to `config/settings.py` under `# Local apps`:
    ```python
    "<package_name>.<app_name>",
    ```

11. Add to `config/urls.py`:
    ```python
    path("<app_name>/", include("<package_name>.<app_name>.urls")),
    ```

12. Register fixtures in root `conftest.py`:
    ```python
    "<package_name>.<app_name>.tests.fixtures",
    ```

13. Verify: `just dj check` then `just test`

---

### `new-view <app_name> <view_name>`

Add a view, template, and URL following HTMX and design system conventions.

Read `docs/HTMX.md`. Check `design/` before writing any template markup — the
component you need likely already exists.

**Steps:**

1. **Choose the response pattern:**

   Full page (no HTMX partial):
   ```python
   from django.template.response import TemplateResponse
   from <package_name>.http.request import HttpRequest

   def <view_name>(request: HttpRequest) -> TemplateResponse:
       return TemplateResponse(request, "<app_name>/<view_name>.html", {})
   ```

   With an HTMX-swappable partial (e.g. a list that refreshes inline):
   ```python
   from <package_name>.http.request import HttpRequest
   from <package_name>.partials import render_partial_response
   from django.template.response import TemplateResponse

   def <view_name>(request: HttpRequest) -> TemplateResponse:
       return render_partial_response(
           request,
           "<app_name>/<view_name>.html",
           context={},
           target="<htmx-target-id>",
           partial="<partial-block-name>",
       )
   ```

   `render_partial_response` renders the full template on first load and
   switches to the named partial block when `HX-Target` matches `target`.

   Use `<package_name>.http.decorators.login_required`, not
   `django.contrib.auth.decorators.login_required`.

2. **Create the template** at `templates/<app_name>/<view_name>.html`.
   Start from a base template (see `design/layout.md`). For HTMX partials,
   use Django 6 named partial blocks. Consult `design/` for all components.

3. **Wire the URL** in `<package_name>/<app_name>/urls.py`:
   ```python
   path("<path>/", views.<view_name>, name="<view_name>"),
   ```

4. **Write tests** — minimum:
   - Happy path
   - HTMX partial path (headers `HX-Request: true`, `HX-Target: <target-id>`)
   - Any auth/permission branch
   100% coverage is required.

5. Verify: `just dj check` then `just test`

---

### `new-task <app_name> <task_name>`

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

5. Verify: `just dj check` then `just test`

---

### `prelaunch`

Check that all deployment configuration is complete before the first production
deploy. Read each file listed below, scan for placeholder values, and report
results in two groups: **BLOCKING** (deploy will fail or be insecure) and
**ADVISORY** (worth reviewing, but won't necessarily break anything).

Placeholder patterns to flag: empty string `""`, `"CHANGE_ME"`, `"example.com"`,
`"grafana.example.com"`, literal `CHANGE_ME` inside cert/key PEM blocks.

---

#### 1. `terraform/hetzner/terraform.tfvars`

If the file does not exist: BLOCKING — copy from `.example` and fill in values.

Check these keys:
| Key | BLOCKING if |
| --- | --- |
| `hcloud_token` | empty string |
| `ssh_public_key` | empty string |
| `k3s_token` | `"CHANGE_ME"` |

#### 2. `terraform/cloudflare/terraform.tfvars`

If the file does not exist: BLOCKING.

| Key | BLOCKING if |
| --- | --- |
| `cloudflare_api_token` | empty string |
| `domain` | `"example.com"` or empty |
| `server_ip` | empty string — must be set after `terraform apply` in hetzner |

#### 3. `helm/<project-slug>/values.secret.yaml`

If the file does not exist: BLOCKING — copy from `.example` and fill in values.

| Key | Severity | Condition |
| --- | --- | --- |
| `postgres.volumePath` | BLOCKING | `"CHANGE_ME"` — set from `terraform output -raw postgres_volume_mount_path` |
| `domain` | BLOCKING | `"CHANGE_ME"` |
| `image` | BLOCKING | contains `CHANGE_ME` |
| `app.admins` | BLOCKING | `"CHANGE_ME"` |
| `app.contactEmail` | BLOCKING | `"CHANGE_ME"` |
| `app.mailgunSenderDomain` | BLOCKING | `"CHANGE_ME"` |
| `secrets.postgresPassword` | BLOCKING | `"CHANGE_ME"` |
| `secrets.djangoSecretKey` | BLOCKING | `"CHANGE_ME"` |
| `secrets.cloudflare.cert` | BLOCKING | contains `CHANGE_ME` |
| `secrets.cloudflare.key` | BLOCKING | contains `CHANGE_ME` |
| `app.adminUrl` | ADVISORY | still `"admin/"` — change for security |
| `app.metaAuthor` | ADVISORY | `"CHANGE_ME"` |
| `app.metaDescription` | ADVISORY | `"CHANGE_ME"` |

#### 4. `helm/observability/values.secret.yaml` (if it exists)

| Key | Severity | Condition |
| --- | --- | --- |
| `kube-prometheus-stack.grafana.adminPassword` | BLOCKING | `"CHANGE_ME"` |
| grafana ingress host | BLOCKING | `"grafana.example.com"` |

#### 5. GitHub Actions secrets

Run `gh secret list` and cross-reference against secrets referenced in
`.github/workflows/*.yml`. For each secret name found in workflows, flag as
BLOCKING if it is absent from `gh secret list` output.

#### 6. Kubeconfig

Check whether `~/.kube/<project-slug>.yaml` exists. If not: ADVISORY —
run `just get-kubeconfig` after Hetzner provisioning.

---

#### Report format

Print a summary like:

```
BLOCKING (must fix before deploy):
  [terraform/hetzner] hcloud_token is empty
  [helm/values.secret.yaml] secrets.djangoSecretKey is CHANGE_ME
  ...

ADVISORY (review before go-live):
  [helm/values.secret.yaml] app.adminUrl is still "admin/" — change for security
  ...

OK:
  terraform/hetzner/terraform.tfvars — all required values set
  ...
```

If there are no BLOCKING items, confirm the project looks ready to deploy and
suggest running `just helm-install` to proceed.

---

### `issue cookiecutter <title>`

File a GitHub issue against the django-studio template repo:

```bash
gh issue create --repo danjac/django-studio --title "<title>" --body "<description>"
```

Use this when the bug or improvement belongs in the template, not this project.

---

### `feedback <title>`

Alias for `issue cookiecutter`. Reports a bug or improvement suggestion against
the [django-studio](https://github.com/danjac/django-studio) template that
generated this project.

```bash
gh issue create --repo danjac/django-studio --title "<title>" --body "<description>"
```

Prompt for a description if not provided. Prefer `/django-studio feedback` over
filing issues manually — it keeps the feedback loop with the template intact.
