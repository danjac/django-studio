Project assistant for this django-studio generated project.

Determine the main package name from the "Project Layout" section of `AGENTS.md`.

## Usage

```
/djstudio <subcommand> [args]
```

Dispatch on the first word of $ARGUMENTS. If no subcommand is given, print the
list of available subcommands and stop.

---

## Subcommands

### `create-app <app_name>`

Create a basic Django app with the standard file structure for this project.

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

### `create-view <app_name> <view_name>`

Add a view, template, and URL following HTMX and design system conventions.

Read `docs/Views.md` and `docs/HTMX.md`. Check `design/` before writing any
template markup — the component you need likely already exists.

**Steps:**

1. **Choose the response pattern:**

   Always add an explicit HTTP method decorator (see `docs/Views.md`).

   Full page (read-only):
   ```python
   from django.contrib.auth.decorators import login_required
   from django.template.response import TemplateResponse
   from django.views.decorators.http import require_safe

   from <package_name>.http.request import HttpRequest

   @require_safe
   @login_required
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

### `create-task <app_name> <task_name>`

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

### `create-model <app_name> <model_name>`

Design and write a Django model with factory, fixture, and model tests.

**Before writing anything**, read:
- `<package_name>/<app_name>/models.py` — existing models and patterns
- `<package_name>/<app_name>/tests/factories.py` — existing factories

---

#### Step 1 — Gather requirements

**STOP. Do not write any code yet.**

Unless the user has explicitly listed every field and relationship inline with
the command, ask now and wait for their reply before doing anything else:

> Describe `<model_name>`. For each field give: name, type, and options (e.g.
> `null`, `blank`, `choices`, `max_length`, `default`). For relationships
> (ForeignKey, ManyToMany, OneToOneField) also give: target model/app,
> `on_delete`, and `related_name`.

Also ask:

> Should `<model_name>` have timestamps? (created / updated)

If yes, add these fields automatically — do not ask the user to specify them:

```python
created = models.DateTimeField(auto_now_add=True)
updated = models.DateTimeField(auto_now=True)
```

Do not invent fields. Do not make assumptions about what the model "probably"
needs based on the app name or project context. Wait.

For any ambiguous relationship in the user's response, ask a follow-up before
proceeding:
- Which app and model is the target?
- `on_delete`: default to `CASCADE`; use `SET_NULL` if the field is nullable.
- `related_name`: suggest `<model_lower>s` if omitted; confirm with the user.

State every assumption explicitly.

---

#### Step 2 — Confirm the plan

Print a model sketch and wait for "yes" before writing any code:

```
Model: <model_name>  →  <package_name>/<app_name>/models.py
  id          BigAutoField (automatic)
  <field>     <FieldType>(<options>)
  …
  __str__:    returns <description>
  Meta:       ordering = [<fields>]
```

---

#### Step 3 — Write the model

Append to `<package_name>/<app_name>/models.py`. Do not touch existing models.

Conventions:
- `from __future__ import annotations` at the top of the file
- Use `models.TextChoices` / `models.IntegerChoices` for enums, as inner classes
- Always define `__str__`
- Add `class Meta` with `ordering` when there is a natural sort order
- FK `related_name` must always be explicit — never rely on the Django default

```python
from __future__ import annotations

from django.db import models


class <model_name>(models.Model):
    class <ChoiceName>(models.TextChoices):  # only if needed
        ...

    <field_name> = models.<FieldType>(...)

    class Meta:
        ordering = [...]

    def __str__(self) -> str:
        return ...
```

---

#### Step 4 — Register with admin (optional)

Ask the user:

> Register `<model_name>` in the Django admin? [y/n]

If yes, open `<package_name>/<app_name>/admin.py` and add:

```python
from django.contrib import admin

from <package_name>.<app_name>.models import <model_name>


@admin.register(<model_name>)
class <model_name>Admin(admin.ModelAdmin):
    list_display = [...]   # infer from model fields: prefer name/title, status, dates
    search_fields = [...]  # CharField and TextField fields
    list_filter = [...]    # choice fields, BooleanFields, date fields
```

Infer sensible defaults from the model fields defined in Step 3. If the model
has no obvious candidates for `search_fields` or `list_filter`, leave them as
empty lists rather than guessing.

---

#### Step 5 — Update the factory

Edit `<package_name>/<app_name>/tests/factories.py`. Use `factory.Faker` matched
to the field type:

| Django field | factory-boy declaration |
|---|---|
| `CharField` (name-like) | `factory.Faker("name")` |
| `CharField` (generic) | `factory.Faker("word")` |
| `TextField` | `factory.Faker("paragraph")` |
| `EmailField` | `factory.Faker("email")` |
| `URLField` | `factory.Faker("url")` |
| `SlugField` | `factory.Faker("slug")` |
| `IntegerField` | `factory.Faker("random_int")` |
| `BooleanField` | `factory.Faker("boolean")` |
| `DateField` | `factory.Faker("date_object")` |
| `DateTimeField` | `factory.Faker("date_time_this_decade")` |
| `DecimalField` | `factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)` |
| `FloatField` | `factory.Faker("pyfloat", positive=True)` |
| `ForeignKey` / `OneToOneField` | `factory.SubFactory(<TargetFactory>)` |
| `ManyToManyField` | `@factory.post_generation` (see below) |
| `FileField` / `ImageField` | omit from factory (leave at field default) |
| field with `choices` | `factory.Iterator([v for v, _ in <Model>.<Choices>.choices])` |

For nullable FK/O2O, still default to a `SubFactory` — tests that need `None`
can override. For M2M:

```python
@factory.post_generation
def <field_name>(self, create, extracted, **kwargs):
    if not create or not extracted:
        return
    self.<field_name>.set(extracted)
```

Full factory example:

```python
import factory
from factory.django import DjangoModelFactory

from <package_name>.<app_name>.models import <model_name>


class <model_name>Factory(DjangoModelFactory):
    class Meta:
        model = <model_name>

    <field_name> = <declaration>
```

---

#### Step 6 — Update fixtures

Add to `<package_name>/<app_name>/tests/fixtures.py`:

```python
@pytest.fixture
def <model_lower>() -> <model_name>:
    return <model_name>Factory()
```

Add the import for `<model_name>Factory` at the top if not already present.

---

#### Step 7 — Write model tests

Add to `<package_name>/<app_name>/tests/test_models.py`:

```python
import pytest

from <package_name>.<app_name>.tests.factories import <model_name>Factory


@pytest.mark.django_db
class Test<model_name>:
    def test_create(self):
        obj = <model_name>Factory()
        assert obj.pk is not None

    def test_str(self):
        obj = <model_name>Factory()
        assert str(obj)
```

Add extra methods for:
- Each `unique=True` field: create two instances with the same value and assert
  `django.db.IntegrityError` is raised.
- Each `unique_together` constraint: same pattern.
- Any `__str__` that returns a specific computed value: assert the exact string.

---

#### Step 8 — Verify

```bash
just dj makemigrations <app_name>
just dj check
just test
```

---

#### Step 9 — Offer to create CRUD views

Once tests pass, ask:

> `<model_name>` is ready. Would you like to generate CRUD views for it?
> (`/djstudio create-crud <app_name> <model_name>`)

Wait for the user's answer. Do not run `create-crud` automatically.

---

### `create-crud <app_name> <model_name>`

Generate a complete set of CRUD views for a model.

Read `docs/Views.md`, `docs/HTMX.md`, and `design/` before writing any template.

**Definitions:**
- `<model_lower>` = `<model_name>` lower-cased (e.g. `Photo` → `photo`)
- `<model_plural>` = pluralised `<model_lower>` (e.g. `photos`) — adjust for
  irregular plurals

**Step 0 — Check app and model exist**

1. Check whether `<package_name>/<app_name>/` exists as a directory.
   If not, tell the user:
   > The `<app_name>` app does not exist. Running `create-app` first.
   Then execute the `create-app` subcommand for `<app_name>` before continuing.

2. Read `<package_name>/<app_name>/models.py`. If `<model_name>` is not defined
   there, tell the user:
   > `<model_name>` does not exist yet. Starting `create-model` now.
   Then begin the `create-model` flow for `<app_name>` `<model_name>`.
   **`create-model` is interactive — it will ask the user for field definitions
   and wait for their response. Do not skip Step 1 of `create-model`. Do not
   invent fields.** Only resume CRUD generation after `create-model` has fully
   completed (model written, migration run, tests passing).

Do not proceed to the CRUD steps until both are in place.

---

#### 1. `forms.py`

Create `<package_name>/<app_name>/forms.py`:

```python
from __future__ import annotations

from django import forms

from <package_name>.<app_name>.models import <model_name>


class <model_name>Form(forms.ModelForm):
    class Meta:
        model = <model_name>
        fields: list[str] = []  # fill in the fields
```

---

#### 2. Views

Add to `<package_name>/<app_name>/views.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_safe
from <package_name>.http.decorators import require_form_methods
from <package_name>.paginator import render_paginated_response
from <package_name>.partials import render_partial_response
from <package_name>.<app_name>.forms import <model_name>Form
from <package_name>.<app_name>.models import <model_name>

if TYPE_CHECKING:
    from <package_name>.http.request import HttpRequest


@require_safe
@login_required
def <model_lower>_list(request: HttpRequest) -> TemplateResponse:
    return render_paginated_response(
        request,
        "<app_name>/<model_lower>_list.html",
        <model_name>.objects.all(),
    )


@require_safe
@login_required
def <model_lower>_detail(request: HttpRequest, pk: int) -> TemplateResponse:
    <model_lower> = get_object_or_404(<model_name>, pk=pk)
    return TemplateResponse(
        request,
        "<app_name>/<model_lower>_detail.html",
        {"<model_lower>": <model_lower>},
    )


@login_required
@require_form_methods
def <model_lower>_create(request: HttpRequest) -> TemplateResponse | HttpResponseRedirect:
    form = <model_name>Form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "<model_name> created.")
        return redirect(reverse("<app_name>:<model_lower>_list"))
    return render_partial_response(
        request,
        "<app_name>/<model_lower>_form.html",
        {"form": form},
        target="<model_lower>-form",
        partial="<model_lower>-form",
    )


@login_required
@require_form_methods
def <model_lower>_edit(
    request: HttpRequest, pk: int
) -> TemplateResponse | HttpResponseRedirect:
    <model_lower> = get_object_or_404(<model_name>, pk=pk)
    form = <model_name>Form(request.POST or None, instance=<model_lower>)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "<model_name> updated.")
        return redirect(reverse("<app_name>:<model_lower>_list"))
    return render_partial_response(
        request,
        "<app_name>/<model_lower>_form.html",
        {"form": form, "<model_lower>": <model_lower>},
        target="<model_lower>-form",
        partial="<model_lower>-form",
    )


@require_http_methods(["GET", "HEAD", "DELETE"])
@login_required
def <model_lower>_delete(
    request: HttpRequest, pk: int
) -> TemplateResponse | HttpResponseRedirect:
    <model_lower> = get_object_or_404(<model_name>, pk=pk)
    if request.method == "DELETE":
        <model_lower>.delete()
        messages.success(request, "<model_name> deleted.")
        return redirect(reverse("<app_name>:<model_lower>_list"))
    return TemplateResponse(
        request,
        "<app_name>/<model_lower>_confirm_delete.html",
        {"<model_lower>": <model_lower>},
    )
```

---

#### 3. Templates

**`templates/<app_name>/<model_lower>_list.html`**

```html
{% extends "base.html" %}

{% block content %}
  {% include "header.html" with title="<model_name>s" %}
  <div class="mt-4">
    <a href="{% url '<app_name>:<model_lower>_create' %}" class="btn btn-primary">
      Add <model_name>
    </a>
  </div>
  {% with pagination_target="<model_lower>-list" %}
    {% fragment "paginate.html" %}
      {% for item in page.object_list %}
        <div>{{ item }}</div>
      {% empty %}
        <p class="text-zinc-500">No items yet.</p>
      {% endfor %}
    {% endfragment %}
  {% endwith %}
{% endblock content %}
```

**`templates/<app_name>/<model_lower>_detail.html`**

```html
{% extends "base.html" %}

{% block content %}
  {% include "header.html" with title="<model_name>" %}
  <div class="mt-4">
    <p>{{ <model_lower> }}</p>
    <div class="mt-6 flex gap-3">
      <a href="{% url '<app_name>:<model_lower>_edit' <model_lower>.pk %}"
         class="btn btn-secondary">Edit</a>
      <a href="{% url '<app_name>:<model_lower>_delete' <model_lower>.pk %}"
         class="btn btn-danger">Delete</a>
    </div>
  </div>
{% endblock content %}
```

**`templates/<app_name>/<model_lower>_form.html`** — shared by create and edit

```html
{% extends "base.html" %}

{% block content %}
  {% include "header.html" with title="<model_name>" %}
  {% partial "<model_lower>-form" %}
    <div id="<model_lower>-form">
      {% fragment "form.html" htmx=True hx_target="#<model_lower>-form" %}
        {% for field in form %}
          {{ field.as_field_group }}
        {% endfor %}
        <button type="submit" class="btn btn-primary" hx-disabled-elt="this">Save</button>
        <a href="{% url '<app_name>:<model_lower>_list' %}" class="btn btn-secondary">
          Cancel
        </a>
      {% endfragment %}
    </div>
  {% endpartial %}
{% endblock content %}
```

**`templates/<app_name>/<model_lower>_confirm_delete.html`**

```html
{% extends "base.html" %}

{% block content %}
  {% include "header.html" with title="Delete <model_name>" %}
  <div class="mt-4">
    <p>Are you sure you want to delete <strong>{{ <model_lower> }}</strong>?</p>
    <div class="mt-6 flex gap-3">
      <button
        class="btn btn-danger"
        hx-delete="{% url '<app_name>:<model_lower>_delete' <model_lower>.pk %}"
        hx-confirm="This cannot be undone."
        hx-target="body"
        hx-push-url="{% url '<app_name>:<model_lower>_list' %}"
      >Delete</button>
      <a href="{% url '<app_name>:<model_lower>_detail' <model_lower>.pk %}"
         class="btn btn-secondary">Cancel</a>
    </div>
  </div>
{% endblock content %}
```

---

#### 4. URLs

Add to `<package_name>/<app_name>/urls.py`:

```python
from <package_name>.<app_name> import views

urlpatterns = [
    path("<model_plural>/", views.<model_lower>_list, name="<model_lower>_list"),
    path("<model_plural>/create/", views.<model_lower>_create, name="<model_lower>_create"),
    path("<model_plural>/<int:pk>/", views.<model_lower>_detail, name="<model_lower>_detail"),
    path("<model_plural>/<int:pk>/edit/", views.<model_lower>_edit, name="<model_lower>_edit"),
    path(
        "<model_plural>/<int:pk>/delete/",
        views.<model_lower>_delete,
        name="<model_lower>_delete",
    ),
]
```

---

#### 5. Tests

Add to `<package_name>/<app_name>/tests/test_views.py`:

```python
import pytest
from django.urls import reverse

from <package_name>.<app_name>.tests.factories import <model_name>Factory


@pytest.mark.django_db
class Test<model_name>List:
    def test_get(self, client, auth_user):
        <model_name>Factory.create_batch(3)
        response = client.get(reverse("<app_name>:<model_lower>_list"))
        assert response.status_code == 200

    def test_htmx_partial(self, client, auth_user):
        response = client.get(
            reverse("<app_name>:<model_lower>_list"),
            headers={"HX-Request": "true", "HX-Target": "<model_lower>-list"},
        )
        assert response.status_code == 200

    def test_redirect_if_not_logged_in(self, client):
        response = client.get(reverse("<app_name>:<model_lower>_list"))
        assert response.status_code == 302


@pytest.mark.django_db
class Test<model_name>Detail:
    def test_get(self, client, auth_user):
        obj = <model_name>Factory()
        response = client.get(reverse("<app_name>:<model_lower>_detail", args=[obj.pk]))
        assert response.status_code == 200

    def test_404(self, client, auth_user):
        response = client.get(reverse("<app_name>:<model_lower>_detail", args=[0]))
        assert response.status_code == 404

    def test_redirect_if_not_logged_in(self, client):
        obj = <model_name>Factory()
        response = client.get(reverse("<app_name>:<model_lower>_detail", args=[obj.pk]))
        assert response.status_code == 302


@pytest.mark.django_db
class Test<model_name>Create:
    def test_get(self, client, auth_user):
        response = client.get(reverse("<app_name>:<model_lower>_create"))
        assert response.status_code == 200

    def test_htmx_partial(self, client, auth_user):
        response = client.get(
            reverse("<app_name>:<model_lower>_create"),
            headers={"HX-Request": "true", "HX-Target": "<model_lower>-form"},
        )
        assert response.status_code == 200

    def test_post_valid(self, client, auth_user):
        response = client.post(
            reverse("<app_name>:<model_lower>_create"),
            data={},  # fill in valid form data
        )
        assert response.status_code == 302

    def test_post_invalid(self, client, auth_user):
        response = client.post(reverse("<app_name>:<model_lower>_create"), data={})
        assert response.status_code == 200

    def test_redirect_if_not_logged_in(self, client):
        response = client.get(reverse("<app_name>:<model_lower>_create"))
        assert response.status_code == 302


@pytest.mark.django_db
class Test<model_name>Edit:
    def test_get(self, client, auth_user):
        obj = <model_name>Factory()
        response = client.get(reverse("<app_name>:<model_lower>_edit", args=[obj.pk]))
        assert response.status_code == 200

    def test_htmx_partial(self, client, auth_user):
        obj = <model_name>Factory()
        response = client.get(
            reverse("<app_name>:<model_lower>_edit", args=[obj.pk]),
            headers={"HX-Request": "true", "HX-Target": "<model_lower>-form"},
        )
        assert response.status_code == 200

    def test_post_valid(self, client, auth_user):
        obj = <model_name>Factory()
        response = client.post(
            reverse("<app_name>:<model_lower>_edit", args=[obj.pk]),
            data={},  # fill in valid form data
        )
        assert response.status_code == 302

    def test_post_invalid(self, client, auth_user):
        obj = <model_name>Factory()
        response = client.post(
            reverse("<app_name>:<model_lower>_edit", args=[obj.pk]),
            data={},
        )
        assert response.status_code == 200

    def test_404(self, client, auth_user):
        response = client.get(reverse("<app_name>:<model_lower>_edit", args=[0]))
        assert response.status_code == 404

    def test_redirect_if_not_logged_in(self, client):
        obj = <model_name>Factory()
        response = client.get(reverse("<app_name>:<model_lower>_edit", args=[obj.pk]))
        assert response.status_code == 302


@pytest.mark.django_db
class Test<model_name>Delete:
    def test_get(self, client, auth_user):
        obj = <model_name>Factory()
        response = client.get(reverse("<app_name>:<model_lower>_delete", args=[obj.pk]))
        assert response.status_code == 200

    def test_delete(self, client, auth_user):
        obj = <model_name>Factory()
        response = client.delete(reverse("<app_name>:<model_lower>_delete", args=[obj.pk]))
        assert response.status_code == 302
        assert not <model_name>.objects.filter(pk=obj.pk).exists()

    def test_404(self, client, auth_user):
        response = client.delete(reverse("<app_name>:<model_lower>_delete", args=[0]))
        assert response.status_code == 404

    def test_redirect_if_not_logged_in(self, client):
        obj = <model_name>Factory()
        response = client.get(reverse("<app_name>:<model_lower>_delete", args=[obj.pk]))
        assert response.status_code == 302
```

If `<model_name>Factory` does not already exist in
`<package_name>/<app_name>/tests/factories.py` (e.g. because `create-model`
was not run), add a minimal one now:

```python
import factory
from factory.django import DjangoModelFactory

from <package_name>.<app_name>.models import <model_name>


class <model_name>Factory(DjangoModelFactory):
    class Meta:
        model = <model_name>
```

If `create-model` already created a factory with field declarations, use that
— do not replace it with this stub.

---

#### 6. Verify

```bash
just dj check
just test
```

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

If `terraform/storage/main.tf` exists (i.e. the project was generated with `use_storage=y`),
also check — regardless of the current value of `useS3Storage`:

| Key | Severity | Condition |
| --- | --- | --- |
| `secrets.useS3Storage` | BLOCKING | `"false"` — object storage was included at project generation but has not been enabled |
| `secrets.hetznerStorageAccessKey` | BLOCKING | empty string |
| `secrets.hetznerStorageSecretKey` | BLOCKING | empty string |
| `secrets.hetznerStorageBucket` | ADVISORY | still the default value — confirm it matches the bucket provisioned by `terraform/storage` |
| `secrets.hetznerStorageEndpoint` | ADVISORY | still the default endpoint — confirm the region matches your Hetzner datacenter |

If any storage credential is missing or `useS3Storage` is still `"false"`, give
the user the following provisioning steps:

1. Create S3 credentials in the Hetzner console: Cloud → Security → S3 credentials
2. Run:
   ```
   export TF_VAR_access_key=<access-key>
   export TF_VAR_secret_key=<secret-key>
   terraform -chdir=terraform/storage init
   terraform -chdir=terraform/storage apply
   ```
3. Copy the terraform outputs into `helm/site/values.secret.yaml`:
   - `secrets.hetznerStorageAccessKey` ← the access key used above
   - `secrets.hetznerStorageSecretKey` ← the secret key used above
   - `secrets.hetznerStorageBucket` ← `terraform -chdir=terraform/storage output -raw bucket_name`
   - `secrets.hetznerStorageEndpoint` ← `terraform -chdir=terraform/storage output -raw endpoint_url`
   - `secrets.useS3Storage` ← set to `"true"`
4. See `docs/File-Storage.md` for the full provisioning guide.

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

### `gdpr`

Audit the project for GDPR compliance issues. Read `docs/GDPR.md` first.
Report findings in two groups: **REQUIRED** (likely non-compliant) and
**ADVISORY** (worth reviewing).

---

#### 1. Personal data in models

Scan all `models.py` files under `<package_name>/`. For each model, identify
fields that likely contain personal data (names containing: `email`, `name`,
`phone`, `address`, `ip`, `location`, `birth`, `gender`, `username`).

For each model with PII fields, check:

| Check | REQUIRED if failing |
|---|---|
| An anonymisation function exists for this model (or the User model covers it) | No anonymisation found |
| Anonymisation covers all identified PII fields | Field missing from anonymisation |
| ForeignKeys to the User model have appropriate `on_delete` | Unclear cascade behaviour on user deletion |

#### 2. Right to erasure

Check for a view or utility function that anonymises or deletes a user account:

| Check | REQUIRED if failing |
|---|---|
| An `anonymise_user` function (or equivalent) exists | Missing |
| It sets `is_active = False` | Missing |
| It replaces email with a placeholder | Missing |
| It calls `set_unusable_password()` | Missing |
| It handles related PII models | No cascade to related models |

#### 3. Data export (right of access)

Check for a view that exports user data:

| Check | ADVISORY if failing |
|---|---|
| A data export view exists | Missing — implement when the project goes live |
| It requires authentication | Unauthenticated access |
| It covers all models containing user PII | Incomplete export |

#### 4. Consent

Check the User model (and any related models) for consent fields:

| Check | ADVISORY if failing |
|---|---|
| Marketing/communication consent field exists | Missing |
| Consent timestamp recorded | Missing |
| Privacy policy version recorded | Missing |

#### 5. Logging

Scan `config/settings.py` and any `LOGGING` configuration for handlers that
might log personal data:

| Check | REQUIRED if failing |
|---|---|
| No email addresses in log format strings | PII in log format |
| `send_default_pii = False` in Sentry config (if Sentry enabled) | Sentry sending PII |

#### 6. Third-party services

Check `config/settings.py` and installed apps for third-party integrations
that receive user data (email providers, analytics, error tracking):

For each integration found, flag as ADVISORY:
> `<service>` receives user data — verify a Data Processing Agreement is in
> place and data transfer outside EU/EEA is covered.

---

#### Report format

```
REQUIRED (likely non-compliant — address before going live):
  [models] User.email has no anonymisation coverage
  [erasure] anonymise_user() does not call set_unusable_password()
  ...

ADVISORY (review before go-live):
  [export] No data export view found
  [consent] No marketing consent field on User model
  [third-party] Mailgun receives user data — verify DPA is in place
  ...

OK:
  [erasure] anonymise_user() found and covers email, username, first_name, last_name
  ...
```

---

### `translate <locale>`

Extract all translatable strings, translate them using Claude, and compile the
message catalogue for the given locale (e.g. `fr`, `fr_CA`, `de`, `es`, `nl`).

**Prerequisites:**

`gettext` binaries (`xgettext`, `msgfmt`) must be installed.

```bash
# Debian/Ubuntu
sudo apt install gettext
# Fedora/RHEL
sudo dnf install gettext
# macOS
brew install gettext
```

If `gettext` is not available, stop and tell the user to install it first.

---

**Steps:**

#### 0 — Detect existing locale

Check whether `locale/<locale>/LC_MESSAGES/django.po` already exists.

- **New locale** — the file does not exist. Run all steps below (1 through 5).
- **Existing locale** — the file already exists. This is a re-run to pick up
  new or changed strings. Skip step 2 (LANGUAGES is already set). In step 3,
  only translate entries where `msgstr` is still empty **or** the entry is
  marked `#, fuzzy` — do not re-translate entries that already have a
  translation.

---

#### 1 — Run `makemessages`

```bash
just dj makemessages -l <locale> --no-wrap
```

This creates or updates `locale/<locale>/LC_MESSAGES/django.po`. Django marks
strings that were previously translated but whose source has since changed as
`#, fuzzy`; brand-new strings get an empty `msgstr`. If the directory does not
exist, Django creates it automatically.

---

#### 2 — Add locale to LANGUAGES *(new locale only — skip if re-running)*

Open `config/settings.py` and find the `LANGUAGES` list. If `<locale>` is not
already present, add it using the **native name** of the language:

```python
LANGUAGES = [
    ("en", "English"),
    ("<locale>", "<native name>"),  # e.g. ("fr", "Français")
]
```

Common native names: `fr` → Français, `fr_CA` → Français (Canada),
`de` → Deutsch, `es` → Español, `nl` → Nederlands, `pt` → Português,
`it` → Italiano, `pl` → Polski, `sv` → Svenska, `da` → Dansk,
`fi` → Suomi, `nb` → Norsk bokmål.

---

#### 3 — Translate the `.po` file

Read `locale/<locale>/LC_MESSAGES/django.po`.

**Check the `Plural-Forms` header.** If it is still the default
`nplurals=INTEGER; plural=EXPRESSION;` placeholder, replace it with the
correct rule for `<locale>`:

| Locale | Plural-Forms |
|--------|-------------|
| fr, fr_CA, es, pt, it | `nplurals=2; plural=(n > 1);` |
| de, nl, sv, da, fi, nb | `nplurals=2; plural=(n != 1);` |
| pl | `nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);` |
| ru, uk | `nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);` |

For any locale not listed, use the correct rule from the GNU gettext manual.

**Translate every entry where `msgstr` is empty** (and any marked `#, fuzzy`).
Use the project name and description (from `cookiecutter.json` or README) as
context so proper nouns and app-specific terminology are translated consistently.

For simple strings:
```
msgid "Save changes"
msgstr "Enregistrer les modifications"
```

For plural strings, fill in all `msgstr[n]` forms:
```
msgid "%(count)s item"
msgid_plural "%(count)s items"
msgstr[0] "%(count)s élément"
msgstr[1] "%(count)s éléments"
```

Remove the `#, fuzzy` flag after translating a fuzzy entry.

Write the updated `.po` file back.

---

#### 4 — Compile

```bash
just dj compilemessages
```

This generates `locale/<locale>/LC_MESSAGES/django.mo`.

---

#### 5 — Report

Print a summary:

```
Translated: <N> strings  (X new, Y fuzzy updated, Z already had translations)
Locale:     <locale>
Catalogue:  locale/<locale>/LC_MESSAGES/django.mo
```

For a re-run, if N is 0 (no new or fuzzy strings were found), say:

```
No new or changed strings found for <locale>. Catalogue is up to date.
```

If any `msgid` contained Python format specifiers (`%(var)s`, `{var}`), remind
the user to verify that the translated strings preserve them exactly.

---

### `feedback [description]`

File a GitHub issue against the django-studio template repo. Use this when the
bug or improvement belongs in the template, not this project.

**Steps:**

1. If a description was not provided inline, ask the user to describe the
   problem or improvement in plain text and wait for their reply.

2. From the description, draft a concise issue title (≤72 characters,
   imperative mood, e.g. "Add X", "Fix Y when Z").

3. Show the proposed title to the user:
   ```
   Proposed title: "<title>"
   Post this issue to danjac/django-studio? [y/n]
   ```
   Wait for confirmation. If the user suggests a different title, use theirs.

4. Once confirmed, file the issue:
   ```bash
   gh issue create --repo danjac/django-studio --title "<title>" --body "<description>"
   ```

5. Print the new issue URL.
