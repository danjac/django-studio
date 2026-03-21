# Validation

This project validates input at three levels depending on the source and complexity.

## Django Forms

Use Django forms for HTML form submissions. The standard pattern uses
`render_partial_response` so that the form partial is returned on both initial
load and on validation failure, with the full page rendered only on first visit:

```python
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from my_package.http.decorators import require_form_methods
from my_package.http.request import AuthenticatedHttpRequest
from my_package.http.response import RenderOrRedirectResponse
from my_package.partials import render_partial_response


@login_required
@require_form_methods
def edit_item(
    request: AuthenticatedHttpRequest, pk: int
) -> RenderOrRedirectResponse:
    item = get_object_or_404(Item, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated.")
            return redirect(item)
    else:
        form = ItemForm(instance=item)
    return render_partial_response(
        request,
        "items/edit.html",
        {"form": form, "item": item},
        target="item-form",   # matches hx-target="#item-form" in the template
        partial="form",       # renders "items/edit.html#form" on HTMX requests
    )
```

The template defines a `{% partialdef form inline %}` block containing the form
markup. The `inline` keyword renders the block in place on a full-page load; on an
HTMX POST with a validation error, `render_partial_response` returns only that
partial so the form re-renders in place with error messages. On success, redirect
(Post/Redirect/Get) as normal.

Key rules:

- Always decorate with `@require_form_methods` (GET/HEAD/POST).
- Always redirect on success — never re-render after a valid POST.
- On invalid POST, return `render_partial_response` (not a plain `TemplateResponse`)
  so HTMX swaps the re-rendered form with inline error messages.

**Form rendering** — use `{{ field.as_field_group }}` for fields (renders via
`templates/form/field.html` with widget dispatch and DaisyUI classes), `django-widget-tweaks`
`render_field` to override individual field attributes, and `{% fragment "form.html" %}` as the
HTMX-aware form wrapper. See `docs/Django-Templates.md` for the full reference.

## Manual Query/POST Parameter Validation

When reading individual parameters directly from `request.GET` or `request.POST`
outside a Django form, always validate explicitly. Never assume a value is present
or the correct type.

**Bad:**
```python
page = int(request.GET["page"])    # KeyError if missing, ValueError if not an int
obj_id = request.POST["object_id"] # KeyError if missing
```

**Good:**
```python
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseBadRequest


def my_view(request: HttpRequest) -> HttpResponse:
    # Optional param — fall back to a safe default
    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    # Required param — two valid approaches depending on circumstances:

    # Option A: return 400 directly
    try:
        obj_id = int(request.POST["object_id"])
    except (KeyError, ValueError, TypeError):
        return HttpResponseBadRequest("Invalid object_id")

    # Option B: raise SuspiciousOperation (also 400, but logs a security WARNING)
    try:
        obj_id = int(request.POST["object_id"])
    except (KeyError, ValueError, TypeError) as exc:
        raise SuspiciousOperation("Invalid object_id") from exc
```

Rules:

- Use `.get()` with a default for optional parameters; use `[]` only for required ones.
- Wrap type conversions (`int()`, `uuid.UUID()`, etc.) in `try/except`.
- For optional params, use a safe default silently.
- For required params, both `HttpResponseBadRequest` (returns 400) and
  `SuspiciousOperation` (also 400, additionally logs a security WARNING) are valid.
  Use `SuspiciousOperation` when the malformed input warrants a security audit trail;
  use `HttpResponseBadRequest` for routine bad input.
- Use `Http404` only when the param identifies a resource that doesn't exist.

## Pydantic for Complex Validation

Use Pydantic when validating structured data from external sources: third-party API
responses, internal service payloads, webhook bodies, or any schema too complex for
manual parsing.

```python
from pydantic import BaseModel, ValidationError


class WeatherResponse(BaseModel):
    temperature: float
    condition: str
    humidity: int


async def fetch_weather(city: str) -> WeatherResponse:
    client = get_http_client()
    response = await client.get(f"/weather/{city}")
    response.raise_for_status()
    try:
        return WeatherResponse.model_validate(response.json())
    except ValidationError as exc:
        raise ValueError(f"Unexpected weather API response: {exc}") from exc
```

Rules:

- Define a `BaseModel` for every external schema you consume — do not key into raw
  dicts.
- Always wrap `.model_validate()` in `try/except ValidationError` and re-raise with
  context so callers know what operation failed.
- Do not use Pydantic for HTML form input — that is Django forms' job.
- See `docs/Packages.md` for the install command and basedpyright configuration.
