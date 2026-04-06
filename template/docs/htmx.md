# HTMX

HTMX provides dynamic page behavior without writing JavaScript. This project uses `django-htmx` for seamless integration.

HTMX is vendored into `static/vendor/`. To update it or add new JS dependencies, see `docs/frontend-dependencies.md`.

## Contents

- [Configuration](#configuration)
- [CSRF](#csrf)
- [Bootstrap hx-boost (opt-in)](#bootstrap-hx-boost-opt-in)
- [View Utilities](#view-utilities)
- [Middleware](#middleware)
- [Common Patterns](#common-patterns)
- [Loading Indicator CSS](#loading-indicator-css)
- [Extensions](#extensions)
- [Best Practices](#best-practices)
- [References](#references)

## Configuration

HTMX is configured via `HTMX_CONFIG` in settings, rendered as a `<meta>` tag by `{% meta_tags %}` in the base template:

```python
# config/settings.py
HTMX_CONFIG = {
    "globalViewTransitions": False,
    "scrollBehavior": "instant",
    "useTemplateFragments": True,
}
```

## CSRF

All HTMX POST/PUT/DELETE requests must include the CSRF token via `hx-headers`. The `{{ csrf_header }}` context variable holds the header name derived from `settings.CSRF_HEADER_NAME`. It is injected into every template by the `csrf_header` context processor in `my_package/context_processors.py`, which is registered in `config/settings.py` by default.

```html
<form hx-post="{% url 'submit' %}"
      hx-headers='{"{{ csrf_header }}": "{{ csrf_token }}"}'
      hx-target="#result"
      hx-swap="outerHTML">
```

Set `hx-headers` at the `<body>` level if most interactions on a page are HTMX-driven, rather than repeating it on every element.

## Bootstrap hx-boost (opt-in)

`hx-boost` converts standard `<a>` and `<form>` elements into AJAX requests, giving SPA-like navigation without a JavaScript framework. It is not enabled by default — use it only if you want full-page AJAX navigation.

### 1. Add `hx-boost` to the body tag

In `templates/base.html`, change the opening `<body>` tag:

```html
<body hx-boost="true">
```

### 2. Create `hx_base.html`

Add `templates/hx_base.html` — a minimal wrapper returned for boosted navigation requests (title + content only, no surrounding chrome):

```html
{% spaceless %}
  {% block title %}
    {% title_tag %}
  {% endblock title %}
  {% block content %}
  {% endblock content %}
{% endspaceless %}
```

### 3. Switch base template per request type

In each page template, extend from the appropriate base depending on whether the request is an HTMX request:

```html
{% extends request.htmx|yesno:"hx_base.html,base.html" %}
```

On a boosted navigation HTMX sends an XHR request with `HX-Request: true`, so `hx_base.html` is used (title + content, no chrome). On a full-page load `base.html` is used.

### 4. Add `scrollIntoViewOnBoost` to HTMX config

In `config/settings.py`, add the option to `HTMX_CONFIG` so boosted navigation scrolls to the top:

```python
HTMX_CONFIG = {
    ...
    "scrollIntoViewOnBoost": False,
}
```

> For targeted partial updates (search results, forms, pagination), return a partial directly from the view — no `hx_base.html` needed.

## View Utilities

This project ships two utilities for the common HTMX view patterns. Prefer these over manual `if request.htmx` branching.

### `render_partial_response` - partial swap on target match

`my_package.partials.render_partial_response` renders the full template normally, but when the `HX-Target` header matches `target` it appends `#partial` to the template name, triggering Django 6's named-partial rendering.

```python
from my_package.partials import render_partial_response

def my_form_view(request):
    form = MyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saved.")
        return redirect("index")
    return render_partial_response(
        request,
        "my_app/my_form.html",
        {"form": form},
        target="my-form",   # matches hx-target="#my-form" in the template
        partial="form",     # renders "my_app/my_form.html#form" on HTMX requests
    )
```

The template defines a `{% partialdef form inline %}` block containing the form markup. The `inline` keyword renders the block in place on a full-page load; on an HTMX submit `render_partial_response` returns only the `form` partial.

### `render_paginated_response` - paginated list with no COUNT query

`my_package.paginator.render_paginated_response` wraps `render_partial_response` with pagination. It uses the project's custom `ZeroCountPaginator` which avoids `COUNT(*)` queries by fetching one extra row to detect whether a next page exists.

```python
from my_package.paginator import render_paginated_response

def items_list(request):
    return render_paginated_response(
        request,
        "my_app/items_list.html",
        Item.objects.all(),
    )
```

The view always renders `my_app/items_list.html` on the first load. When HTMX requests the next page with `hx-target="#pagination"`, only the `pagination` partial is returned. Context automatically includes `page`, `paginator`, and `pagination_config`.

Pass a `PaginationConfig` to customise behaviour (target, partial name, page size, or
paginator class). For numbered pagination and infinite scroll patterns see
`docs/pagination.md`.

## Middleware

Three custom middleware classes in `my_package/middleware.py` handle HTMX-specific behaviour. They must be placed **after** `django_htmx.middleware.HtmxMiddleware` in `MIDDLEWARE`.

### `HtmxCacheMiddleware`

Sets `Vary: HX-Request` on HTMX responses so caches serve the correct variant to HTMX vs normal requests. See [HTMX caching docs](https://htmx.org/docs/#caching).

### `HtmxMessagesMiddleware`

Appends pending Django messages to HTMX HTML responses as an [out-of-band swap](https://htmx.org/attributes/hx-swap-oob/) (`hx-swap-oob="true"`) targeting the `#messages` container in `base.html`. This means any view that calls `messages.success(...)` before a partial response will automatically display the toast — no extra template code required.

The middleware skips responses that already carry an HTMX redirect header (`HX-Location`, `HX-Redirect`, `HX-Refresh`) because the browser is about to navigate away.

### `HtmxRedirectMiddleware`

Converts standard HTTP 3xx redirects into `HX-Location` responses when the request came from HTMX. Without this, HTMX would follow the redirect internally and swap the redirected page's HTML into the current target — usually not what you want.

With this middleware, a normal `return redirect(...)` in a view does the right thing for both full-page and HTMX requests:

```python
def my_form_view(request):
    form = MyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saved.")
        return redirect("index")  # becomes HX-Location for HTMX, full redirect otherwise
    ...
```

## Common Patterns

### Search with Debounce

```html
<input type="text"
       name="q"
       hx-get="{% url 'search' %}"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#results"
       hx-indicator=".searching">

<div id="results"></div>
<span class="htmx-indicator searching">Searching...</span>
```

### Infinite Scroll

```html
<div hx-get="{% url 'more_items' %}?offset=0"
     hx-trigger="revealed"
     hx-swap="afterend">
    {% include "partials/items.html" %}
</div>
```

### File Uploads

```html
<form hx-post="/upload/"
      hx-encoding="multipart/form-data"
      hx-target="#results"
      hx-headers='{"{{ csrf_header }}": "{{ csrf_token }}"}'>
    <input type="file" name="file">
    <button type="submit">Upload</button>
</form>
```

### hx-swap Patterns

HTMX supports several swap strategies beyond the default `innerHTML`. See [hx-swap docs](https://htmx.org/attributes/hx-swap/) for the full list.

#### Delete a list item in-place

```html
<button hx-delete="{% url 'item-delete' item.pk %}"
        hx-target="#item-{{ item.pk }}"
        hx-swap="delete"
        hx-headers='{"{{ csrf_header }}": "{{ csrf_token }}"}'>
  Delete
</button>
```

`hx-swap="delete"` removes the target element from the DOM after a successful response. No response body is required.

#### Fire-and-forget (suppress DOM update)

```html
<button hx-post="{% url 'track' %}"
        hx-swap="none"
        hx-headers='{"{{ csrf_header }}": "{{ csrf_token }}"}'>
  Track click
</button>
```

`hx-swap="none"` sends the request but performs no DOM swap. Use for analytics, logging, or side-effect-only actions.

#### Scroll and show modifiers

Modifiers appended to the swap strategy control scroll or viewport position after the swap:

```html
<!-- Scroll to the top of the page after replacing results -->
<form hx-post="{% url 'search' %}"
      hx-target="#results"
      hx-swap="outerHTML show:top">
</form>

<!-- Append messages and scroll to the bottom of the container -->
<div id="messages"
     hx-post="{% url 'send-message' %}"
     hx-swap="beforeend scroll:bottom">
</div>
```

## Loading Indicator CSS

```css
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: inline; }
.htmx-request.htmx-indicator { display: inline; }
```

## Extensions

HTMX extensions add optional capabilities (SSE, WebSockets, etc.) without
bloating the core library. Vendor them like any other frontend dependency.

### Adding an extension

1. Add an entry to `vendors.json` (see `docs/frontend-dependencies.md`):

   ```json
   "htmx-ext-sse": {
       "version": "2.2.4",
       "source": "https://cdn.jsdelivr.net/npm/htmx-ext-sse@{version}/sse.min.js",
       "dest": "static/vendor/htmx-ext-sse.js"
   }
   ```

2. Download it:

   ```bash
   just dj sync_vendors --no-input
   ```

3. Load it on the pages that need it via the `scripts` block. The extension
   must execute **after** `htmx.js` — placing it in `scripts` (bottom of
   `<body>`) guarantees this since `htmx.js` loads in `<head>` with `defer`:

   ```html
   {% block scripts %}
     {{ block.super }}
     <script src="{% static 'vendor/htmx-ext-sse.js' %}" defer></script>
   {% endblock scripts %}
   ```

4. Activate the extension on the elements that use it with `hx-ext`:

   ```html
   <div hx-ext="sse" sse-connect="/events/">
       ...
   </div>
   ```

Do not load extensions globally in `base.html` unless every page needs them.

### Available extensions

| Extension | Package | Use case | Docs |
| --------- | ------- | -------- | ---- |
| SSE | `htmx-ext-sse` | Server-Sent Events | `docs/sse.md` |
| WebSocket | `htmx-ext-ws` | Bidirectional WebSockets | `docs/channels.md` |

See [htmx.org/extensions](https://htmx.org/extensions/) for the full list.

## Best Practices

1. Always include `hx-headers` with `{{ csrf_header }}` and `{{ csrf_token }}` on POST/PUT/DELETE requests.
2. Use `hx-boost` + template switching only for full-page navigation (see "Bootstrap hx-boost" above). For element-level updates, return a partial directly.
3. Use `hx-disabled-elt="this"` on submit buttons to prevent double-submission.
4. Debounce search inputs: `hx-trigger="keyup changed delay:300ms"`.
5. Use `hx-swap="outerHTML"` to replace a form with its re-rendered self on validation errors.
6. Use `hx-swap="delete"` to dismiss banners or remove list items after a destructive action.

## References

- [HTMX Documentation](https://htmx.org/docs/)
- [hx-swap](https://htmx.org/attributes/hx-swap/)
- [hx-trigger](https://htmx.org/attributes/hx-trigger/)
- [hx-boost](https://htmx.org/attributes/hx-boost/)
- [django-htmx](https://django-htmx.readthedocs.io/)
