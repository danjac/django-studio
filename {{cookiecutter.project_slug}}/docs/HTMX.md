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

## View Utilities

This project ships two utilities for the common HTMX view patterns. Prefer these over manual `if request.htmx` branching.

### `render_partial_response` — partial swap on target match

`{{cookiecutter.package_name}}.partials.render_partial_response` renders the full template normally, but when the `HX-Target` header matches `target` it appends `#partial` to the template name, triggering Django 6's named-partial rendering.

```python
from {{cookiecutter.package_name}}.partials import render_partial_response

def my_form_view(request):
    form = MyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saved.")
        return redirect("index")
    return render_partial_response(
        request,
        "myapp/my_form.html",
        {"form": form},
        target="my-form",   # matches hx-target="#my-form" in the template
        partial="form",     # renders "myapp/my_form.html#form" on HTMX requests
    )
```

The template defines a `{% partialdef form %}` block that contains just the form markup. On a full-page load the entire template renders; on an HTMX form submit only the `form` partial is returned and swapped in.

### `render_paginated_response` — paginated list with no COUNT query

`{{cookiecutter.package_name}}.paginator.render_paginated_response` wraps `render_partial_response` with pagination. It uses the project's custom `Paginator` which avoids `COUNT(*)` queries by fetching one extra row to detect whether a next page exists.

```python
from {{cookiecutter.package_name}}.paginator import render_paginated_response

def items_list(request):
    return render_paginated_response(
        request,
        "myapp/items_list.html",
        Item.objects.all(),
    )
```

The view always renders `myapp/items_list.html` on the first load. When HTMX requests the next page with `hx-target="#pagination"`, only the `pagination` partial is returned. Context automatically includes `page`, `page_size`, and `pagination_target`.

Default keyword arguments (override as needed):

| Argument | Default | Description |
|----------|---------|-------------|
| `param` | `"page"` | Query-string key for the page number |
| `target` | `"pagination"` | Expected `HX-Target` value |
| `partial` | `"pagination"` | Named partial to render on HTMX requests |
| `per_page` | `settings.DEFAULT_PAGE_SIZE` | Items per page |

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
