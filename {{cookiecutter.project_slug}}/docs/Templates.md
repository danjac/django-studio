# Templates

This project uses Django templates with HTMX, including the `partialdef` pattern for reusable template fragments.

## Template Structure

### Base Templates

```html
<!-- default_base.html - full page with all elements -->
{% partialdef head inline %}
    <head>...</head>
{% endpartialdef %}

{% partialdef sidebar inline %}
    <aside>...</aside>
{% endpartialdef %}

{% partialdef scripts inline %}
    <script src="..."></script>
{% endpartialdef %}
```

### Using Partials

```html
{% extends "default_base.html" %}

{% block content %}
    {% partial sidebar %}

    <main>
        {{ content }}
    </main>
{% endblock %}
```

## partialdef Pattern

The `partialdef` tag (from django-htmx) defines reusable template fragments:

```html
<!-- form.html -->
{% partialdef buttons %}
    <div class="flex">
        <button type="submit">Submit</button>
    </div>
{% endpartialdef %}
```

Use with `{% partial %}`:

```html
{% include "form.html" %}
{% partial buttons %}
```

### Inline Partials

Use `inline` to render immediately without separate template:

```html
{% partialdef form inline %}
    <form>...</form>
{% endpartialdef %}
```

This is useful for HTMX responses that need to swap content.

## Fragment Tag

The `fragment` tag (custom) includes a template with block content:

```html
<!-- Calling template -->
{% fragment "header.html" %}
title content here
{% endfragment %}

<!-- header.html -->
<h1>{{ content }}</h1>
```

This passes content between tags into the included template.

## Pagination Pattern

```html
<!-- paginate.html -->
{% with has_other_pages=page.has_other_pages %}
    {% fragment "browse.html" target=pagination_target %}
        {% if has_other_pages %}
            <li>{% partial links %}</li>
        {% endif %}
        {{ content }}
        {% if has_other_pages %}
            <li>{% partial links %}</li>
        {% endif %}
    {% endfragment %}
{% endwith %}

{% partialdef links %}
    <nav hx-swap="outerHTML show:window:top" hx-target="#{{ pagination_target }}">
        <ul class="flex">
            {% if page.has_previous %}
                <a href="?page={{ page.previous_page_number }}">Previous</a>
            {% endif %}
            {% if page.has_next %}
                <a href="?page={{ page.next_page_number }}">Next</a>
            {% endif %}
        </ul>
    </nav>
{% endpartialdef %}
```

## Forms with widget_tweaks

Forms define fields only - no CSS classes:

```python
# forms.py
class MyForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = ["field1", "field2"]
```

Classes added in template:

```html
{% load widget_tweaks %}

{% render_field form.field1 class="form-input" %}
{% render_field form.field2 class="form-textarea" %}
```

### Reusable Field Template

```html
<!-- form/field.html -->
{% load widget_tweaks %}

{% partialdef input %}
    {% partial label %}
    {% render_field field class="form-input" %}
{% endpartialdef %}

{% partialdef label %}
    <label for="{{ field.id_for_label }}">
        {{ field.label }}
    </label>
{% endpartialdef %}
```

## HTMX Form Template

```html
<!-- form.html -->
{% with action=action|default:request.path method="post" %}
<form method="{{ method }}"
      class="{{ class|default:'space-y-6' }}"
      {% if htmx %}
        hx-{{ method }}="{{ action }}"
        hx-disabled-elt="this"
        hx-swap="{{ hx_swap|default:'outerHTML' }}"
        hx-target="{{ hx_target|default:'this' }}"
      {% endif %}>
    {% csrf_token %}
    {{ content }}
</form>
{% endwith %}
```

## Best Practices

1. Use `partialdef` for reusable UI components
2. Use `fragment` for template composition with content
3. Keep forms simple - define fields in Python, styling in templates
4. Use `inline` partials for HTMX response content
5. Separate concerns - base templates define structure, partials define components
