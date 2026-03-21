# Views

This project uses **function-based views only** — no class-based views.

## View Decorators

**Always restrict HTTP methods explicitly** — every view must be decorated with
an appropriate method guard. Never leave a view accepting any method by default.

```python
from django.contrib.auth.decorators import login_required
from my_package.http.decorators import require_form_methods, require_DELETE
from django.views.decorators.http import require_safe, require_POST
```

| Decorator               | Allowed methods | Use for                             |
| ----------------------- | --------------- | ----------------------------------- |
| `@require_safe`         | GET, HEAD       | Read-only views                     |
| `@require_POST`         | POST            | Single-action POST endpoints        |
| `@require_form_methods` | GET, HEAD, POST | Views that render and handle a form |
| `@require_DELETE`       | DELETE          | HTMX delete actions                 |

The project provides two custom decorators:

```python
# my_package/http/decorators.py
from django.views.decorators.http import require_http_methods

require_form_methods = require_http_methods(["GET", "HEAD", "POST"])
require_DELETE = require_http_methods(["DELETE"])
```

## Custom Response Classes

```python
# my_package/http/response.py
import http
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

RenderOrRedirectResponse = TemplateResponse | HttpResponseRedirect

class TextResponse(HttpResponse):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("content_type", "text/plain")
        super().__init__(*args, **kwargs)

class HttpResponseNoContent(HttpResponse):
    status_code = http.HTTPStatus.NO_CONTENT

class HttpResponseConflict(HttpResponse):
    status_code = http.HTTPStatus.CONFLICT
```

## Extended HttpRequest

```python
# my_package/http/request.py
from django.http import HttpRequest as DjangoHttpRequest
from django_htmx.middleware import HtmxDetails

class HttpRequest(DjangoHttpRequest):
    if TYPE_CHECKING:
        htmx: HtmxDetails

class AuthenticatedHttpRequest(HttpRequest):
    if TYPE_CHECKING:
        user: User
```

Always type-annotate request parameters with `my_package.http.request.HttpRequest`.
Use `AuthenticatedHttpRequest` in views protected by
`@login_required` (from `django.contrib.auth.decorators`).

## Basic View Pattern

```python
from django.template.response import TemplateResponse
from django.views.decorators.http import require_safe

from my_package.http.request import HttpRequest


@require_safe
def index(request: HttpRequest) -> TemplateResponse:
    return TemplateResponse(request, "index.html", {})
```

## Redirects

Use the `redirect` shortcut for redirects:

```python
from django.shortcuts import redirect

def my_view(request: HttpRequest) -> HttpResponseRedirect:
    # ... some logic ...
    return redirect("some_view_name")

```

Note that you don't need to use `reverse` when using `redirect` with a view name — it handles that for you. If redirecting to a model instance, ensure the model has a `get_absolute_url` method defined so that `redirect` can resolve the URL correctly to the detail view:

```python

from django.shortcuts import redirect, get_object_or_404
from mysite.app.models import Item

def redirect_to_item(request: HttpRequest, item_id: int) -> HttpResponseRedirect:
    item = get_object_or_404(Item, pk=item_id)
    return redirect(item)  # Assumes Item has get_absolute_url defined

```

## HTMX View Pattern

Use `render_partial_response` for views with HTMX inline swaps — returns the
full page on first load and the named partial block on subsequent HTMX requests:

```python
from my_package.partials import render_partial_response


def item_list(request: HttpRequest) -> TemplateResponse:
    context = {"items": Item.objects.all()}
    return render_partial_response(
        request,
        "items/list.html",
        context=context,
        target="item-list",
        partial="item-list",
    )
```

See `docs/HTMX.md` for full HTMX conventions and `docs/Django-Templates.md` for
template authoring conventions.

## Paginated Views

```python
from my_package.paginator import render_paginated_response


def item_list(request: HttpRequest) -> TemplateResponse:
    return render_paginated_response(
        request,
        "items/list.html",
        Item.objects.all(),
    )
```

## Async Views

**Prefer synchronous views. Use async only for I/O-bound work** (third-party
API calls, WebSockets). Do not use async for ordinary CRUD views.

```python
from django.views.decorators.http import require_safe


@require_safe
async def search_items(request: HttpRequest) -> TemplateResponse:
    client = get_client()
    results = await client.search(request.GET.get("q", ""))
    return TemplateResponse(request, "search_results.html", {"results": results})
```

**Do not use async for:**

- Simple CRUD views
- Database queries (use the sync ORM)
- Template rendering
- Most typical Django views

For the preferred HTTP client library, see `docs/Packages.md`.

## Internationalisation in Views

Import only what you use. The choice between `gettext` and `gettext_lazy` depends
on *where* the string is evaluated:

- **Function bodies** — use `gettext` (aliased `_`). The string is translated at
  call time when the request language is active.
- **Module-level constants** — use `gettext_lazy` (aliased `_l`). The string is
  translated lazily on first access, which is required outside the request cycle.

```python
# Only import what you need in each file
from django.utils.translation import gettext as _          # for function bodies
from django.utils.translation import gettext_lazy as _l    # for module-level strings

# Module-level — must use _l
PAGE_TITLE = _l("Dashboard")

# Function body — use _
def my_view(request: HttpRequest) -> TemplateResponse:
    messages.success(request, _("Changes saved."))
    ...
```

Never import both when you only need one — that triggers an unused-import linter
error. Add `gettext_lazy as _l` to your imports only when you have a module-level
string that needs it.

## URL Configuration

```python
# my_package/my_app/urls.py
from django.urls import path

from my_package.my_app import views

app_name = "my_app"

urlpatterns = [
    path("items/", views.item_list, name="item_list"),
    path("items/<int:pk>/", views.item_detail, name="item_detail"),
]
```

Register in `config/urls.py`:

```python
path("my_app/", include("my_package.my_app.urls")),
```
