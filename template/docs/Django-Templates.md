# Templates

This project uses Django templates with HTMX, including the `partialdef` pattern for reusable template fragments. Components use DaisyUI classes — see `docs/Tailwind.md` for the class reference.

## Contents

- [Base Templates](#base-templates)
- [partialdef / partial](#partialdef--partial)
- [fragment Tag](#fragment-tag)
- [Forms](#forms)
- [Pagination](#pagination)
- [Browse List](#browse-list)
- [Messages](#messages)
- [Navigation](#navigation)
- [Layout Patterns](#layout-patterns)
- [Cookie Banner](#cookie-banner)
- [Custom Template Tags and Filters](#custom-template-tags-and-filters)

## Base Templates

`base.html` uses Django `{% block %}` tags. It renders the full page: `<head>`, HTMX indicator, messages, cookie banner, navbar, and a centred `<main>` wrapper. Page templates extend it:

```html
{% extends "base.html" %}

{% block content %}
  <h1>My Page</h1>
{% endblock content %}
```

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

`partialdef` ([built into Django 6](https://docs.djangoproject.com/en/6.0/ref/templates/language/#template-partials)) defines a named fragment inside a template. `partial` renders a previously defined fragment by name. This is the primary mechanism for HTMX partial swaps.

Use `inline` when the partial IS the content — i.e. the block should render in place on a full-page load AND be extractable by `render_partial_response` for HTMX swaps. Without `inline`, `{% partialdef %}` defines the fragment but does not render it — you need a separate `{% partial name %}` call to render it.

**Page-level template (use `inline`):**

```html
<!-- my_app/items_list.html -->
{% extends "base.html" %}

{% block content %}
  <div id="item-list">
    {% partialdef item-list inline %}
      {% for item in items %}
        <p>{{ item.name }}</p>
      {% endfor %}
    {% endpartialdef %}
  </div>
{% endblock content %}
```

On an HTMX request targeting `#item-list`, `render_partial_response` returns only the `item-list` partial. On a full-page load `inline` renders the block in place. See `docs/HTMX.md` for the view-side pattern.

**Component template (no `inline`):**

Component templates such as `browse.html`, `paginate.html`, and `sidebar.html` define partials without `inline` because they are always rendered via `{% fragment %}` or `{% partial %}` — never directly. The caller controls what gets rendered.

### Extracting shared partials into partials.html

When several templates share the same `{% partialdef %}` blocks (e.g. a card layout, a status badge, a shared action menu), extract them into a dedicated `partials.html` file. Callers include the partial via `{% fragment "partials.html#block-name" %}`.

Conventional locations:

| Scope | File |
|-------|------|
| Project-wide | `templates/partials.html` |
| Domain-specific | `templates/form/partials.html`, `templates/my_app/partials.html` |

`form/partials.html` follows this pattern — it holds all form-field widget partials and is included indirectly by Django's field renderer.

## fragment Tag

`{% fragment "template.html#partial" %}...{% endfragment %}` includes a template and passes the enclosed content as `{{ content }}`. Used internally by `form/partials.html` and `paginate.html`:

```html
{% fragment "form.html" htmx=True target="my-form" %}
  {{ form }}
{% endfragment %}
```

## Forms

### Rendering fields

Use `{{ field.as_field_group }}` to render a form field with its label, errors, and help text. The project ships `templates/form/partials.html` which dispatches to a per-widget `partialdef` based on the field's widget type:

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

### HTMX form wrapper

`form.html` renders a `<form>` element. Include it via `{% fragment %}`, passing the form fields as `{{ content }}`:

```html
{% fragment "form.html" htmx=True target="my-form" %}
  {{ form.title.as_field_group }}
  {{ form.body.as_field_group }}
  {% fragment "form.html#buttons" %}
    <button type="submit" class="btn btn-primary">Save</button>
  {% endfragment %}
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

### Field template structure

`form/partials.html` renders each field inside a DaisyUI `fieldset`:

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Email</legend>
  <input id="id_email" type="email" class="input w-full" ...>
  <ul class="text-sm font-semibold text-error">...</ul>
  <p class="label">Help text</p>
</fieldset>
```

### Widget type dispatch

`form/partials.html` dispatches to a `{% partialdef %}` block by lowercasing the widget's class name via `{% try_include "form/partials.html#"|add:widget_type "form/partials.html#input" %}`. If no matching partial exists, it falls back to the `input` partial. Built-in widgets with explicit partials:

| Widget | Partial | DaisyUI class |
|--------|---------|---------------|
| `Textarea` | `textarea` | `textarea` |
| `CheckboxInput` | `checkboxinput` | `checkbox` |
| `CheckboxSelectMultiple` | `checkboxselectmultiple` | — |
| `PasswordInput` | `passwordinput` | `input` |
| `Select` | `select` | `select` |
| `SelectMultiple` | `selectmultiple` | `select` |
| `DateInput` | `dateinput` | `input` (type="date") |
| `DateTimeInput` | `datetimeinput` | `input` (type="datetime-local") |

All other widgets (e.g. `TextInput`, `EmailInput`, `FileInput`, `URLInput`) fall back to the `input` partial automatically.

### Custom widget partials

If you add a custom widget with non-default rendering, add a matching `{% partialdef %}` block to `templates/form/partials.html`. The partial name is the widget's class name, lowercased. Use `{% partial label %}`, `{% partial errors %}`, and `{% partial help_text %}` to keep rendering consistent. Widgets that render identically to a plain `<input>` need no partial — the fallback handles them.

### Adding widget attributes

Use `django-widget-tweaks` to add classes or attributes from the template:

```html
{% load widget_tweaks %}
{% render_field form.email class="input w-full" placeholder="you@example.com" %}
{% render_field form.bio class="textarea w-full" rows="4" %}
```

## Pagination

`paginate.html` renders a paginated list with previous/next links using DaisyUI `join` buttons. Include it via `{% fragment %}`:

```html
{% fragment "paginate.html" %}
  {% for item in page %}
    <p>{{ item.name }}</p>
  {% endfor %}
{% endfragment %}
```

The `links` partial inside `paginate.html` renders HTMX-enabled prev/next links targeting `#{{ pagination_config.target }}`. The view uses `render_paginated_response` which sets `page`, `paginator`, and `pagination_config` in context automatically — see `docs/Pagination.md`.

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

## Messages

`messages.html` renders Django messages as a DaisyUI toast stack (bottom-right, `toast toast-end`). Messages auto-dismiss after 4 seconds via AlpineJS.

DaisyUI alert classes map directly to Django message tags:

| Django level | DaisyUI class |
|-------------|---------------|
| `messages.INFO` | `alert alert-soft alert-info` |
| `messages.SUCCESS` | `alert alert-soft alert-success` |
| `messages.WARNING` | `alert alert-soft alert-warning` |
| `messages.ERROR` | `alert alert-soft alert-error` |

For HTMX requests, re-render messages as an out-of-band swap:

```html
{% include "messages.html" with hx_oob=True %}
```

## Navigation

### Navbar

`navbar.html` is a DaisyUI navbar (`navbar` class) included in `base.html`. It provides:

- Site logo (links to `{% url 'index' %}`)
- User dropdown with Alpine state management
- Mobile menu toggle
- Auth links (sign in / sign up) when not authenticated

The component uses Alpine for the mobile menu and dropdown — DaisyUI provides the styling, Alpine provides the behaviour (close on escape, close on HTMX navigation, mutual exclusion).

### Sidebar

`sidebar.html` is a navigation list used in the mobile slide-in menu and optionally in a desktop sidebar. Items use the `{% partial item %}` shorthand:

```html
{% url 'podcasts:subscriptions' as subscriptions_url %}
{% with icon="rss" label="Subscriptions" url=subscriptions_url %}
  {% partial item %}
{% endwith %}
```

### Active item highlighting

Use `active_app` or `active_url` template tags for active state:

```html
<a href="{% url 'podcasts:subscriptions' %}"
   class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition-colors {% active_app 'podcasts' %}">
```

| Tag | Matches against | Use for |
|-----|----------------|---------|
| `{% active_app 'app' %}` | `request.resolver_match.app_name` | All pages within an app |
| `{% active_url 'name' %}` | `request.resolver_match.url_name` | A specific named view |

### Adding a sidebar layout

Replace the `<main>` block in `base.html` with a conditional driven by a `show_sidebar` context variable:

```html
{% if show_sidebar %}
  <div class="mx-auto flex max-w-7xl gap-8 px-4 py-8 sm:px-6 lg:px-8">
    <aside class="hidden w-56 shrink-0 md:block">
      <nav class="sticky top-20 rounded-box border border-base-300 bg-base-200 p-4">
        {% block sidebar %}{% include "sidebar.html" %}{% endblock %}
      </nav>
    </aside>
    <main class="min-w-0 flex-1">
{% else %}
  <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
{% endif %}
```

## Layout Patterns

### Centred content (default)

`base.html` wraps `{% block content %}` in a centred `max-w-7xl` container.

### Two-column with sidebar

See [Adding a sidebar layout](#adding-a-sidebar-layout) above.

### Full-width / hero

Override the container constraint with negative margins:

```html
{% block content %}
  <section class="-mx-4 -mt-8 bg-primary px-4 py-24 text-primary-content sm:-mx-6 lg:-mx-8">
    <h1 class="text-4xl font-bold">Welcome</h1>
  </section>
{% endblock content %}
```

## Cookie Banner

`{% cookie_banner %}` is a template tag rendered in `base.html`. It uses HTMX to dismiss itself. Remove the tag from `base.html` to disable it.

---

## Custom Template Tags and Filters

Use `/djstudio create-tag` and `/djstudio create-filter` to add new tags and filters.

### Where they live

| Scope | File |
|-------|------|
| Project-wide | `<package_name>/templatetags.py` (ships with every project) |
| App-specific | `<package_name>/<app_name>/templatetags/<app_name>.py` |

Always append to an existing file — never recreate it. App-level files need a
`templatetags/__init__.py` alongside them.

### Shipped tags

| Tag | Type | Purpose |
|-----|------|---------|
| `{% active_app 'name' %}` | `simple_tag` | CSS class when `request.resolver_match.app_name` matches |
| `{% active_url 'name' %}` | `simple_tag` | CSS class when `request.resolver_match.url_name` matches |
| `{% fragment "t.html" %}...{% endfragment %}` | `simple_block_tag` | Include a template with `{{ content }}` slot |
| `{% try_include "t.html" "fallback.html" key=val %}` | `simple_tag` | Include a template, falling back if not found; optional extra context |
| `{% cookie_banner %}` | `inclusion_tag` | GDPR cookie consent banner |
| `{% title_tag %}` | `simple_tag` | Composable `<title>` tag |

### Choosing a tag type

Pick the simplest type that fits:

| Type | Use when |
|------|----------|
| `@register.simple_tag` | Returns a value; no template rendering needed |
| `@register.simple_tag(takes_context=True)` | Needs `request` or context variables |
| `@register.simple_block_tag` | Wraps or transforms a block of template content (Django 6+) |
| `@register.inclusion_tag("t.html")` | Renders a sub-template and returns its output |
| `@register.filter` | Transforms a single value in a template expression |

Reach for `simple_block_tag` before a custom `Node` subclass — the built-in
`fragment` tag is a working example of `simple_block_tag`.

### Tags that produce HTML

Always use `format_html` — it escapes every interpolated value and returns a
`SafeString`. Never build HTML with f-strings or string concatenation on
user-supplied data:

```python
from django.utils.html import format_html

@register.simple_tag
def icon(name: str) -> "SafeString":
    return format_html('<svg class="icon icon-{}"></svg>', name)
```

For lists of HTML fragments, use `format_html_join` — it calls `format_html` on each
item and joins the results:

```python
from django.utils.html import format_html_join

@register.simple_tag
def badge_list(items: list[str]) -> "SafeString":
    return format_html_join("", '<span class="badge">{}</span>', ((i,) for i in items))
```

**IMPORTANT — XSS risk:** `mark_safe` (Python) and `{{ value|safe }}` (template
filter) both disable autoescaping entirely. They are equivalent and equally dangerous
on user-supplied data. Neither is needed on the output of `format_html`, which already
calls `mark_safe` internally. The only valid use is when you have pre-sanitized a
string externally (e.g. with a library like `nh3`) or via `conditional_escape` in a
`needs_autoescape` filter. **Never pass user-supplied data to `mark_safe` or `|safe`.**

### Testing

Test the function directly — do not instantiate `Template`/`Context` unless full
rendering is genuinely required:

```python
from my_package.templatetags import my_filter

def test_my_filter():
    assert my_filter("hello") == "HELLO"
```

For `inclusion_tag`, assert the returned context dict, not the rendered HTML.
