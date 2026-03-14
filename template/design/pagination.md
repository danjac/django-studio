# Pagination

Template: `templates/paginate.html`

## Overview

`paginate.html` wraps any list or grid with Previous / Next navigation. It creates a `<div id="{{ pagination_target }}">` as the HTMX swap target, so page changes replace only the list - not the surrounding page.

It is layout-agnostic: the inner content can be a `browse.html` list, a `grid.html` grid, or any other markup.

## View Setup

Use `render_paginated_response` - it handles pagination, sets `pagination_target` in context, and returns only the named partial on HTMX requests:

```python
from {{ package_name }}.paginator import render_paginated_response

def photo_list(request):
    return render_paginated_response(
        request,
        "photos/list.html",
        Photo.objects.all(),
        target="pagination",   # matches pagination_target in template
        partial="pagination",  # matches {% partialdef pagination %} in template
    )
```

## Template Structure

Wrap the paginated content in a `{% partialdef pagination inline %}` block. On HTMX page requests, only this block is rendered and swapped in.

### Grid layout (cards)

```html
{% partialdef pagination inline %}
  {% fragment "paginate.html" %}
    {% fragment "grid.html" %}
      {% for photo in page %}
        {% fragment "grid.html#item" %}
          {% include "card.html" with url=photo.get_absolute_url title=photo.title image_url=photo.image_url %}
        {% endfragment %}
      {% empty %}
        {% fragment "grid.html#empty" %}No photos yet.{% endfragment %}
      {% endfor %}
    {% endfragment %}
  {% endfragment %}
{% endpartialdef pagination %}
```

### List layout (browse)

```html
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

## HTMX Behaviour

When a page link is clicked, HTMX swaps the `<div id="{{ pagination_target }}">` container (including nav links and list content) with the new page's response. `show:window:top` scrolls back to the top.

## Combining with Search / Filters

`{% querystring page=N %}` (from `django-querystring-tag`) merges into the existing query string, so pagination works automatically alongside filters:

```
/photos/?q=sunset&tag=nature&page=2
```

No extra setup needed - just ensure filters are submitted as `GET` parameters.

## Styling the Links

Previous/Next links use the `link` utility class (`tailwind/links.css`). Disabled states (first/last page) render as non-interactive `<span>` elements with muted styling.
