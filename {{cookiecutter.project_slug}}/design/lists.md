# Lists

Template: `templates/browse.html`

## Overview

`browse.html` is a divided list layout — items separated by horizontal rules. Use it for data-first content where items are read row by row (names, dates, statuses, actions).

The template defines three partials:

| Partial | Rendered as | Use for |
|---------|-------------|---------|
| _(outer)_ | `<ul class="divide-y">` | Container |
| `#item` | `<li class="py-3 first:pt-0 last:pb-0">` | One list item |
| `#empty` | `<li class="text-center prose">` | Empty state |

`grid.html` follows the same `#item` / `#empty` interface — swap one for the other to change the layout without touching item markup.

## Usage

### Paginated list

```python
# views.py
def user_list(request):
    return render_paginated_response(request, "users/list.html", User.objects.all())
```

```html
{# users/list.html #}
{% partialdef pagination inline %}
  {% fragment "paginate.html" %}
    {% fragment "browse.html" %}
      {% for user in page %}
        {% fragment "browse.html#item" %}
          <div class="flex items-center justify-between">
            <span class="font-medium">{{ user.get_full_name }}</span>
            <a href="{{ user.get_absolute_url }}" class="btn btn-secondary">View</a>
          </div>
        {% endfragment %}
      {% empty %}
        {% fragment "browse.html#empty" %}No users yet.{% endfragment %}
      {% endfor %}
    {% endfragment %}
  {% endfragment %}
{% endpartialdef pagination %}
```

### Standalone (no pagination)

Pass `target` to add an id for HTMX targeting:

```html
{% fragment "browse.html" target="notifications" %}
  {% for notification in notifications %}
    {% fragment "browse.html#item" %}
      {{ notification.message }}
    {% endfragment %}
  {% empty %}
    {% fragment "browse.html#empty" %}No notifications.{% endfragment %}
  {% endfor %}
{% endfragment %}
```

## Grid vs List

| Use `grid.html` + `card.html` | Use `browse.html` |
|-------------------------------|-------------------|
| Media-first content (photos, articles) | Data-first content (users, orders) |
| Visual browsing | Scanning rows |
| Items benefit from images | Items have structured fields |
