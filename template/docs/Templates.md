# Templates

This project uses Django templates with HTMX, including the `partialdef` pattern for reusable template fragments.

> **Design System** - Before writing new templates, check `design/` for ready-made components (navbar, sidebar, forms, cards, pagination, markdown, buttons, messages). See `design/README.md` for the full index.

## Base Templates

`base.html` uses Django `{% block %}` tags. It renders the full page: `<head>`, HTMX indicator, messages, cookie banner, navbar, and a centred `<main>` wrapper. Page templates extend it:

```html
{% extends "base.html" %}

{% block content %}
  <h1>My Page</h1>
{% endblock content %}
```

To add a global sidebar or other page-level partials, add them to `base.html`. See `design/Layout.md` for layout patterns.

The `{% block scripts %}` block is rendered just before `</body>` — use it for per-page JavaScript:

```html
{% block scripts %}
  {{ block.super }}
  <script>
    document.addEventListener('alpine:init', () => {
      Alpine.data('myComponent', () => ({ ... }));
    });
  </script>
{% endblock scripts %}
```

## partialdef / partial

`partialdef` ([built into Django 6](https://docs.djangoproject.com/en/6.0/ref/templates/language/#template-partials)) defines a named fragment inside a template. `partial` renders it. This is the primary mechanism for HTMX partial swaps.

```html
<!-- myapp/items_list.html -->
{% extends "base.html" %}

{% block content %}
  <div id="item-list">
    {% partial item-list %}
  </div>
{% endblock content %}

{% partialdef item-list %}
  {% for item in items %}
    <p>{{ item.name }}</p>
  {% endfor %}
{% endpartialdef %}
```

On an HTMX request targeting `#item-list`, `render_partial_response` returns only the `item-list` partial. On a full-page load the whole template renders. See `docs/HTMX.md` for the view-side pattern.

## fragment Tag

`{% fragment "template.html#partial" %}...{% endfragment %}` includes a template and passes the enclosed content as `{{ content }}`. Used internally by `form/field.html` and `paginate.html`:

```html
{% fragment "form.html" htmx=True target="my-form" %}
  {{ form }}
{% endfragment %}
```

## Forms

### Rendering fields

Use `{{ field.as_field_group }}` to render a form field with its label, errors, and help text. The project ships `templates/form/field.html` which dispatches to a per-widget `partialdef` based on the field's widget type:

```html
{% for field in form %}
  {{ field.as_field_group }}
{% endfor %}
```

For explicit field order:

```html
{{ form.title.as_field_group }}
{{ form.body.as_field_group }}
```

See `design/Forms.md` for the full form wrapper and field conventions.

### HTMX form wrapper

`form.html` renders a `<form>` element. Include it via `{% fragment %}`, passing the form fields as `{{ content }}`:

```html
{% fragment "form.html" htmx=True target="my-form" %}
  {{ form.title.as_field_group }}
  {{ form.body.as_field_group }}
  <button type="submit" class="btn btn-primary">Save</button>
{% endfragment %}
```

Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `action` | `request.path` | Form action URL |
| `method` | `"post"` | HTTP method |
| `htmx` | — | Enable HTMX attributes |
| `hx_swap` | `"outerHTML"` | HTMX swap strategy |
| `hx_target` | `"this"` | HTMX target selector |
| `multipart` | — | Enable file upload encoding |

## Pagination

`paginate.html` renders a paginated list with previous/next links. Include it via `{% fragment %}`:

```html
{% fragment "paginate.html" target=pagination_target %}
  {% for item in page %}
    <p>{{ item.name }}</p>
  {% endfor %}
{% endfragment %}
```

The `links` partial inside `paginate.html` renders HTMX-enabled prev/next links targeting `#{{ pagination_target }}`. The view uses `render_paginated_response` which sets `page`, `pagination_target`, and related context automatically — see `docs/HTMX.md`.

## Browse List

`browse.html` renders a `<ul>` list with dividers. Use its `item` and `empty` partials:

```html
{% fragment "browse.html" target="item-list" %}
  {% for item in items %}
    {% fragment "browse.html#item" %}
      <a href="{{ item.get_absolute_url }}">{{ item.name }}</a>
    {% endfragment %}
  {% empty %}
    {% fragment "browse.html#empty" %}
      No items found.
    {% endfragment %}
  {% endfor %}
{% endfragment %}
```
