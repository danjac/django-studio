# Pagination

Template: `templates/paginate.html`

## Overview

`paginate.html` wraps a paginated list with Previous / Next links above and below the content. It uses the `fragment` tag to render inside a named container, and the links use HTMX to swap the container in-place.

## Context Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `page` | yes | Django `Page` object from `Paginator` |
| `pagination_target` | yes | HTML `id` of the container element to swap |
| `content` | yes | Rendered list content (passed via `{% fragment %}`) |

## Usage

```html
{# In your list template: #}
{% with pagination_target="results" %}
  {% fragment "paginate.html" %}
    {% for item in page.object_list %}
      <li>{% include "card.html" with url=item.get_absolute_url title=item.name %}</li>
    {% endfor %}
  {% endfragment %}
{% endwith %}
```

The `#results` element is created by the paginate template itself - you do not need a wrapping div.

## View Setup

```python
from django.core.paginator import Paginator
from django.template.response import TemplateResponse

def my_list_view(request):
    qs = MyModel.objects.all()
    paginator = Paginator(qs, per_page=20)
    page = paginator.get_page(request.GET.get("page"))
    return TemplateResponse(request, "my_list.html", {"page": page})
```

## HTMX Behaviour

When a page link is clicked, HTMX swaps the entire `#results` container (including the pagination links) with the new page's content. The `show:window:top` modifier scrolls to the top of the page on swap.

```html
{# Inside paginate.html - set automatically #}
<nav
  hx-swap="outerHTML show:window:top"
  hx-target="#{{ pagination_target }}"
>
```

The page URL includes `?page=N` via `{% querystring %}` (from `django-querystring-tag`), which preserves other query string parameters (search, filters, etc.).

## Styling the Links

Previous/Next links use the `link` utility class (defined in `tailwind/links.css`). Disabled states (first/last page) render as non-interactive `<span>` elements with muted styling.

## Combining with Search / Filters

Because `{% querystring page=N %}` merges into the existing query string, pagination works automatically with filter parameters:

```
/items/?q=django&category=web&page=2
```

No extra setup is needed - just ensure filters are submitted as `GET` parameters.
