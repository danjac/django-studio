---
description: Generate full CRUD views, templates, URLs, and tests for a model
---

Generate a complete set of CRUD views for a model.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/python-style-guide.md`

**Definitions:**
- `<model_lower>` = `<model_name>` lower-cased (e.g. `Photo` → `photo`)
- `<model_plural>` = pluralised `<model_lower>` (e.g. `photos`) — adjust for
  irregular plurals

**Step 0 — Check app and model exist**

1. Check whether `<package_name>/<app_name>/` exists as a directory.
   If not, tell the user:
   > The `<app_name>` app does not exist. Running `create-app` first.
   Then read `.agents/skills/dj-create-app/SKILL.md` and execute those steps
   for `<app_name>` before continuing.

2. Read `<package_name>/<app_name>/models.py`. If `<model_name>` is not defined
   there, tell the user:
   > `<model_name>` does not exist yet. Starting `dj-create-model` now.
   Then read `.agents/skills/dj-create-model/SKILL.md` and begin that flow.
   **`dj-create-model` is interactive — it will ask the user for field definitions
   and wait for their response. Do not skip Step 1 of `dj-create-model`. Do not
   invent fields.** Only resume CRUD generation after `dj-create-model` has fully
   completed (model written, migration run, tests passing).

Do not proceed to the CRUD steps until both are in place.

---

### 1. `forms.py`

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

### 2. Views

For numbered pagination, infinite scroll, or custom `PaginationConfig` options see
`docs/pagination.md`.

Add to `<package_name>/<app_name>/views.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

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
    if request.method == "POST":
        form = <model_name>Form(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("<model_name> created."))
            return redirect(reverse("<app_name>:<model_lower>_list"))
    else:
        form = <model_name>Form()
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
    if request.method == "POST":
        form = <model_name>Form(request.POST, instance=<model_lower>)
        if form.is_valid():
            form.save()
            messages.success(request, _("<model_name> updated."))
            return redirect(reverse("<app_name>:<model_lower>_list"))
    else:
        form = <model_name>Form(instance=<model_lower>)
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
        messages.success(request, _("<model_name> deleted."))
        return redirect(reverse("<app_name>:<model_lower>_list"))
    return TemplateResponse(
        request,
        "<app_name>/<model_lower>_confirm_delete.html",
        {"<model_lower>": <model_lower>},
    )
```

---

### 3. Templates

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
  {% partialdef pagination inline %}
    {% fragment "paginate.html" %}
      {% for item in page.object_list %}
        <div>{{ item }}</div>
      {% empty %}
        <p class="text-zinc-500">No items yet.</p>
      {% endfor %}
    {% endfragment %}
  {% endpartialdef %}
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

### 4. URLs

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

### 5. Tests

**Fixture convention:** `dj-create-model` Step 6 creates a `<model_lower>` pytest
fixture in `<package_name>/<app_name>/tests/fixtures.py`. Use it as a parameter
in tests that need a single instance — do not call `<model_name>Factory()`
directly for those cases. Only use `<model_name>Factory.create_batch()` (or
direct factory calls) when you need multiple objects or need to control specific
field values.

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
    def test_get(self, client, auth_user, <model_lower>):
        response = client.get(reverse("<app_name>:<model_lower>_detail", args=[<model_lower>.pk]))
        assert response.status_code == 200

    def test_404(self, client, auth_user):
        response = client.get(reverse("<app_name>:<model_lower>_detail", args=[0]))
        assert response.status_code == 404

    def test_redirect_if_not_logged_in(self, client, <model_lower>):
        response = client.get(reverse("<app_name>:<model_lower>_detail", args=[<model_lower>.pk]))
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
    def test_get(self, client, auth_user, <model_lower>):
        response = client.get(reverse("<app_name>:<model_lower>_edit", args=[<model_lower>.pk]))
        assert response.status_code == 200

    def test_htmx_partial(self, client, auth_user, <model_lower>):
        response = client.get(
            reverse("<app_name>:<model_lower>_edit", args=[<model_lower>.pk]),
            headers={"HX-Request": "true", "HX-Target": "<model_lower>-form"},
        )
        assert response.status_code == 200

    def test_post_valid(self, client, auth_user, <model_lower>):
        response = client.post(
            reverse("<app_name>:<model_lower>_edit", args=[<model_lower>.pk]),
            data={},  # fill in valid form data
        )
        assert response.status_code == 302

    def test_post_invalid(self, client, auth_user, <model_lower>):
        response = client.post(
            reverse("<app_name>:<model_lower>_edit", args=[<model_lower>.pk]),
            data={},
        )
        assert response.status_code == 200

    def test_404(self, client, auth_user):
        response = client.get(reverse("<app_name>:<model_lower>_edit", args=[0]))
        assert response.status_code == 404

    def test_redirect_if_not_logged_in(self, client, <model_lower>):
        response = client.get(reverse("<app_name>:<model_lower>_edit", args=[<model_lower>.pk]))
        assert response.status_code == 302


@pytest.mark.django_db
class Test<model_name>Delete:
    def test_get(self, client, auth_user, <model_lower>):
        response = client.get(reverse("<app_name>:<model_lower>_delete", args=[<model_lower>.pk]))
        assert response.status_code == 200

    def test_delete(self, client, auth_user, <model_lower>):
        pk = <model_lower>.pk
        response = client.delete(reverse("<app_name>:<model_lower>_delete", args=[pk]))
        assert response.status_code == 302
        assert not <model_name>.objects.filter(pk=pk).exists()

    def test_404(self, client, auth_user):
        response = client.delete(reverse("<app_name>:<model_lower>_delete", args=[0]))
        assert response.status_code == 404

    def test_redirect_if_not_logged_in(self, client, <model_lower>):
        response = client.get(reverse("<app_name>:<model_lower>_delete", args=[<model_lower>.pk]))
        assert response.status_code == 302
```

If `<model_name>Factory` does not already exist in
`<package_name>/<app_name>/tests/factories.py` (e.g. because `dj-create-model`
was not run), add a minimal one now:

```python
import factory
from factory.django import DjangoModelFactory

from <package_name>.<app_name>.models import <model_name>


class <model_name>Factory(DjangoModelFactory):
    class Meta:
        model = <model_name>
```

If `dj-create-model` already created a factory with field declarations, use that
— do not replace it with this stub.

---

### 6. Verify

```bash
just check-all
```
