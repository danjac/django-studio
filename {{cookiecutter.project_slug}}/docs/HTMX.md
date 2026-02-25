# HTMX

HTMX provides dynamic page behavior without writing JavaScript. This project uses `django-htmx` for seamless integration.

## Installation

```bash
uv add django-htmx
```

Add to settings:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_htmx",
]

MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
]
```

## Configuration

Configure HTMX via settings (rendered via template tag):

```python
# config/settings.py

# HTMX configuration
# https://htmx.org/docs/#config
HTMX_CONFIG = {
    "globalViewTransitions": False,
    "scrollBehavior": "instant",
    "scrollIntoViewOnBoost": False,
    "useTemplateFragments": True,
}
```

```html
<!-- In base template -->
<head>
    {% meta_tags %}
</head>
```

The `meta_tags` template tag renders HTMX config as:
```html
<meta name="htmx-config" content='{"useTemplateFragments": true, ...}'>
```

## CSRF for HTMX Requests

This project uses `hx-headers` attribute with CSRF token from context processor:

```python
# myapp/context_processors.py
from django.conf import settings
from django.http import HttpHeaders
import functools

def csrf_header(_) -> dict[str, str | None]:
    """Returns CSRF header name"""
    return {"csrf_header": _csrf_header_name()}

@functools.cache
def _csrf_header_name() -> str | None:
    return HttpHeaders.parse_header_name(settings.CSRF_HEADER_NAME)
```

Add to context processors in settings:
```python
TEMPLATES = [
    {
        "OPTIONS": {
            "context_processors": [
                # ...
                "myapp.context_processors.csrf_header",
            ],
        },
    },
]
```

Then in templates use:
```html
<button hx-post="{% url 'submit' %}"
        hx-headers='{"{{ csrf_header }}": "{{ csrf_token }}"}'
        hx-target="#result">
    Submit
</button>
```

## Template Switching

Automatically switch between full page and partial templates based on HTMX request:

```html
<!-- base.html -->
{% extends request.htmx|yesno:"hx_base.html,default_base.html" %}
```

```html
<!-- hx_base.html - minimal template for HTMX responses -->
{% spaceless %}
    {% block title %}
        {% title_tag %}
    {% endblock title %}
    {% block content %}
    {% endblock content %}
{% endspaceless %}
```

> **Note:** This pattern is only useful when using `hx-boost="true"` for full-page swaps. For simple HTMX requests that update specific DOM elements (the common case), you don't need separate base templates - just return the appropriate partial from your view.

## HTMX Attributes

This project uses these HTMX attributes in templates:

```html
<!-- POST request with CSRF -->
<form hx-post="/endpoint/"
      hx-headers='{"{{ csrf_header }}": "{{ csrf_token }}"}'
      hx-target="#result"
      hx-swap="outerHTML">
    <!-- form fields -->
</form>

<!-- GET request -->
<a href="/page/"
   hx-get="/endpoint/"
   hx-target="#result"
   hx-push-url="true">Load</a>

<!-- Disable element during request -->
<button hx-get="/endpoint/"
        hx-disabled-elt="this">
    Loading...
</button>

<!-- Swap options -->
hx-swap="outerHTML"    <!-- Replace target element -->
hx-swap="innerHTML"    <!-- Insert inside target -->
hx-swap="delete"       <!-- Remove target element -->
hx-swap="beforebegin"  <!-- Insert before target -->
hx-swap="afterend"     <!-- Insert after target -->

<!-- Trigger on events -->
hx-trigger="click"
hx-trigger="revealed"                      <!-- When element scrolls into view -->
hx-trigger="intersect"                     <!-- When element enters viewport -->
hx-trigger="keyup changed delay:300ms"     <!-- Debounced input -->

<!-- Boost regular links -->
<a href="/page/" hx-boost="true">Link</a>

<!-- Confirmation -->
<button hx-delete="/item/1/"
        hx-confirm="Are you sure?">Delete</button>

<!-- Loading indicator -->
<button hx-get="/endpoint/"
        hx-indicator="#loading">Go</button>
<span id="loading" class="htmx-indicator">Loading...</span>
```

## View Detection

Check if request is HTMX-driven:

```python
from django.http import HttpRequest
from django.template.response import TemplateResponse

def my_view(request: HttpRequest) -> TemplateResponse:
    if request.htmx:
        # Return partial HTML
        return TemplateResponse(request, "partials/items.html", {"items": items})

    # Return full page
    return TemplateResponse(request, "full_page.html", {"items": items})
```

The `django-htmx` middleware adds `request.htmx` with these attributes:
- `request.htmx.boosted` - True if navigation is boosted
- `request.htmx.current_url` - Current URL
- `request.htmx.target` - Target element ID
- `request.htmx.trigger` - Trigger element ID
- `request.htmx.trigger_name` - Trigger element name

## Common Patterns

### Search with Debounce

```html
<input type="text"
       name="q"
       hx-get="{% url 'search' %}"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#results"
       hx-headers='{"{{ csrf_header }}": "{{ csrf_token }}"}'
       hx-indicator=".searching">

<div id="results"></div>
<span class="htmx-indicator searching">Searching...</span>
```

### Pagination

```python
def items_list(request):
    items = Item.objects.all()
    paginator = Paginator(items, 20)
    page = paginator.get_page(request.GET.get("page", 1))

    if request.htmx:
        return render(request, "partials/items_table.html", {"page": page})

    return render(request, "items_list.html", {"page": page})
```

```html
<!-- In items_table.html -->
<table>
    {% for item in page.object_list %}
    <tr><td>{{ item.name }}</td></tr>
    {% endfor %}
</table>

<!-- Pagination links -->
<div hx-get="{% url 'items_list' %}?page={{ page.next_page_number }}"
     hx-target="closest div"
     hx-swap="outerHTML">
    {% include "partials/pagination_links.html" %}
</div>
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
<div id="results"></div>
```

## Loading Indicator CSS

```css
.htmx-indicator {
    display: none;
}
.htmx-request .htmx-indicator {
    display: inline;
}
.htmx-request.htmx-indicator {
    display: inline;
}
```

## Best Practices

1. **Use `hx-headers`** with `{{ csrf_header }}` and `{{ csrf_token }}` for all HTMX POST/PUT/DELETE requests
2. **Use template switching** only when using `hx-boost` - otherwise just return partials from views
3. **Use `hx-disabled-elt`** to prevent double-submission
4. **Debounce search inputs** with `hx-trigger="keyup changed delay:300ms"`
5. **Use `hx-swap`** appropriately for the UI pattern (delete for banners, outerHTML for content replacement)
6. **Use loading indicators** with `hx-indicator` for better UX
