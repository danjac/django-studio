# HTMX

HTMX provides dynamic page behavior without writing JavaScript. This project uses `django-htmx` for seamless integration.

## Configuration

HTMX is configured via `HTMX_CONFIG` in settings, rendered as a `<meta>` tag by `{% meta_tags %}` in the base template:

```python
# config/settings.py
HTMX_CONFIG = {
    "globalViewTransitions": False,
    "scrollBehavior": "instant",
    "scrollIntoViewOnBoost": False,
    "useTemplateFragments": True,
}
```

## CSRF

All HTMX POST/PUT/DELETE requests must include the CSRF token via `hx-headers`. The `{{ csrf_header }}` context variable holds the correct header name (from `settings.CSRF_HEADER_NAME`):

```html
<form hx-post="{% url 'submit' %}"
      hx-headers='{"{{ csrf_header }}": "{{ csrf_token }}"}'
      hx-target="#result"
      hx-swap="outerHTML">
```

Set `hx-headers` at the `<body>` level if most interactions on a page are HTMX-driven, rather than repeating it on every element.

## Template Switching

When using `hx-boost`, templates extend from the appropriate base depending on whether the request is an HTMX request:

```html
{% extends request.htmx|yesno:"hx_base.html,default_base.html" %}
```

`hx_base.html` is a minimal wrapper (title + content block, no chrome). Only use this pattern with `hx-boost` — for targeted partial updates, just return the partial directly from the view.

## View Detection

```python
def my_view(request):
    if request.htmx:
        return TemplateResponse(request, "partials/items.html", {"items": items})
    return TemplateResponse(request, "full_page.html", {"items": items})
```

`request.htmx` is provided by `django-htmx` middleware. Useful attributes:
- `request.htmx.boosted` — True if triggered by `hx-boost` navigation
- `request.htmx.target` — ID of the target element
- `request.htmx.trigger` — ID of the triggering element
- `request.htmx.trigger_name` — name of the triggering element

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

### Pagination

```python
def items_list(request):
    items = Item.objects.all()
    paginator = Paginator(items, 20)
    page = paginator.get_page(request.GET.get("page", 1))

    if request.htmx:
        return TemplateResponse(request, "partials/items_table.html", {"page": page})
    return TemplateResponse(request, "items_list.html", {"page": page})
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

## Loading Indicator CSS

```css
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: inline; }
.htmx-request.htmx-indicator { display: inline; }
```

## Best Practices

1. Always include `hx-headers` with `{{ csrf_header }}` and `{{ csrf_token }}` on POST/PUT/DELETE requests.
2. Use `hx-boost` + template switching only for full-page navigation. For element-level updates, return a partial directly.
3. Use `hx-disabled-elt="this"` on submit buttons to prevent double-submission.
4. Debounce search inputs: `hx-trigger="keyup changed delay:300ms"`.
5. Use `hx-swap="outerHTML"` to replace a form with its re-rendered self on validation errors.
6. Use `hx-swap="delete"` to dismiss banners or remove list items after a destructive action.
