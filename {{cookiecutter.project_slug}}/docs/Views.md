# Views

This project uses **function-based views only** — no class-based views.

## View Decorators

```python
from myapp.http.decorators import login_required, require_form_methods
from django.views.decorators.http import require_safe, require_POST
```

The project provides two custom decorators:

```python
# myapp/http/decorators.py
from django.views.decorators.http import require_http_methods

require_form_methods = require_http_methods(["GET", "HEAD", "POST"])
require_DELETE = require_http_methods(["DELETE"])
```

Always use `myapp.http.decorators.login_required`, not
`django.contrib.auth.decorators.login_required`.

## Custom Response Classes

```python
# myapp/http/response.py
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
# myapp/http/request.py
from django.http import HttpRequest as DjangoHttpRequest
from django_htmx.middleware import HtmxDetails

class HttpRequest(DjangoHttpRequest):
    if TYPE_CHECKING:
        htmx: HtmxDetails

class AuthenticatedHttpRequest(HttpRequest):
    if TYPE_CHECKING:
        user: User
```

Always type-annotate request parameters with `myapp.http.request.HttpRequest`.
Use `AuthenticatedHttpRequest` in views protected by `@login_required`.

## Basic View Pattern

```python
from django.template.response import TemplateResponse
from django.views.decorators.http import require_safe

from myapp.http.request import HttpRequest


@require_safe
def index(request: HttpRequest) -> TemplateResponse:
    return TemplateResponse(request, "index.html", {})
```

## HTMX View Pattern

Use `render_partial_response` for views with HTMX inline swaps — returns the
full page on first load and the named partial block on subsequent HTMX requests:

```python
from myapp.partials import render_partial_response


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

See `docs/HTMX.md` for full HTMX conventions.

## Paginated Views

```python
from myapp.paginator import render_paginated_response


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

## HTTP Client

Always use `aiohttp` for outbound HTTP — never the `requests` library:

```python
import aiohttp

async with aiohttp.ClientSession() as session:
    async with session.get("https://api.example.com/data") as response:
        data = await response.json()
```

`aiohttp` is not in the default stack. Add it when needed: `uv add aiohttp`.

## URL Configuration

```python
# myapp/<app_name>/urls.py
from django.urls import path

from myapp.<app_name> import views

app_name = "<app_name>"

urlpatterns = [
    path("items/", views.item_list, name="item_list"),
    path("items/<int:pk>/", views.item_detail, name="item_detail"),
]
```

Register in `config/urls.py`:

```python
path("<app_name>/", include("myapp.<app_name>.urls")),
```
