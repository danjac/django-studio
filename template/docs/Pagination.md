# Pagination

This project ships a custom `ZeroCountPaginator` that avoids `COUNT(*)` queries by fetching one
extra row to detect whether a next page exists. Choose the right approach for your use
case:

| Use case | Approach |
|---|---|
| Simple browse/search lists | Previous/Next (default) |
| User needs to jump to a specific page | Numbered pages |
| Feed-style content | Infinite scroll |
| Django admin on large tables | `FastCountAdminMixin` |

---

## Contents

- [Previous/Next (default)](#previousnext-default)
- [Numbered Pagination](#numbered-pagination)
- [Infinite Scroll](#infinite-scroll)
- [Django Admin: FastCountAdminMixin](#django-admin-fastcountadminmixin)

## Previous/Next (default)

Use `render_paginated_response`. No `COUNT(*)` query — scales well on large tables.

```python
from my_package.paginator import render_paginated_response


def item_list(request: HttpRequest) -> TemplateResponse:
    return render_paginated_response(
        request,
        "my_app/items_list.html",
        Item.objects.order_by("-created_at"),
    )
```

In the template, include `paginate.html` via `{% fragment %}` inside a
`{% partialdef pagination inline %}` block:

```html
<!-- my_app/items_list.html -->
{% extends "base.html" %}

{% block content %}
  {% partialdef pagination inline %}
    {% fragment "paginate.html" %}
      {% for item in page.object_list %}
        <p>{{ item.name }}</p>
      {% endfor %}
    {% endfragment %}
  {% endpartialdef %}
{% endblock content %}
```

`paginate.html` renders Previous/Next navigation around `{{ content }}`.
On an HTMX page request only the `pagination` partial is returned.

To override the page size, pass a `ZeroCountPaginator` instance directly:

```python
from my_package.paginator import ZeroCountPaginator, PaginationConfig, render_paginated_response

def item_list(request: HttpRequest) -> TemplateResponse:
    qs = Item.objects.order_by("-created_at")
    return render_paginated_response(
        request,
        "my_app/items_list.html",
        qs,
        config=PaginationConfig(paginator=ZeroCountPaginator(qs, 50)),
    )
```

---

## Numbered Pagination

When users need to jump to a specific page you need a total count. Use Django's
built-in `Paginator` — the `COUNT(*)` query is fast on indexed, filtered querysets and
fine for most tables. Pass it via `PaginationConfig`:

```python
from django.core.paginator import Paginator

from my_package.paginator import PaginationConfig, render_paginated_response


def item_list(request: HttpRequest) -> TemplateResponse:
    qs = Item.objects.order_by("-created_at")
    return render_paginated_response(
        request,
        "my_app/items_list.html",
        qs,
        config=PaginationConfig(paginator=Paginator(qs, 20)),
    )
```

### Template

Create `templates/paginate_numbered.html` following `paginate.html`'s structure —
`{% partialdef links %}` defines the nav once and `{% partial links %}` renders it
above and below the list without duplication:

```html
<!-- templates/paginate_numbered.html -->
{% load i18n %}
{% with has_other_pages=page.has_other_pages %}
  <div id="{{ pagination_config.target }}" aria-live="polite" aria-atomic="true">
    {% if has_other_pages %}
      <div class="pb-3">{% partial links %}</div>
    {% endif %}
    {{ content }}
    {% if has_other_pages %}
      <div class="pt-3">{% partial links %}</div>
    {% endif %}
  </div>
{% endwith %}

{% partialdef links %}
  <nav role="navigation"
       aria-label="{% translate "Pagination" %}"
       hx-target="#{{ pagination_config.target }}"
       hx-swap="outerHTML show:window:top">
    <div class="join">
      {% if page.has_previous %}
        <a href="{{ request.path }}{% querystring page=1 %}"
           class="btn btn-ghost join-item"
           aria-label="{% translate "First page" %}">«</a>
        <a href="{{ request.path }}{% querystring page=page.previous_page_number %}"
           class="btn btn-ghost join-item"
           aria-label="{% translate "Previous page" %}">‹</a>
      {% else %}
        <span class="btn btn-ghost btn-disabled join-item" aria-hidden="true">«</span>
        <span class="btn btn-ghost btn-disabled join-item" aria-hidden="true">‹</span>
      {% endif %}

      {% for num in page.paginator.page_range %}
        {% if num == page.number %}
          <span class="btn btn-active join-item" aria-current="page">{{ num }}</span>
        {% elif num >= page.number|add:"-3" and num <= page.number|add:"3" %}
          <a href="{{ request.path }}{% querystring page=num %}"
             class="btn btn-ghost join-item">{{ num }}</a>
        {% endif %}
      {% endfor %}

      {% if page.has_next %}
        <a href="{{ request.path }}{% querystring page=page.next_page_number %}"
           class="btn btn-ghost join-item"
           aria-label="{% translate "Next page" %}">›</a>
        <a href="{{ request.path }}{% querystring page=page.paginator.num_pages %}"
           class="btn btn-ghost join-item"
           aria-label="{% translate "Last page" %}">»</a>
      {% else %}
        <span class="btn btn-ghost btn-disabled join-item" aria-hidden="true">›</span>
        <span class="btn btn-ghost btn-disabled join-item" aria-hidden="true">»</span>
      {% endif %}
    </div>
  </nav>
{% endpartialdef links %}
```

Use it in the page template the same way as `paginate.html`:

```html
<!-- my_app/items_list.html -->
{% extends "base.html" %}

{% block content %}
  {% partialdef pagination inline %}
    {% fragment "paginate_numbered.html" %}
      {% for item in page.object_list %}
        <p>{{ item.name }}</p>
      {% endfor %}
    {% endfragment %}
  {% endpartialdef %}
{% endblock content %}
```

The ±3 window in `paginate_numbered.html` keeps the page range short on large datasets.
Adjust `add:"-3"` / `add:"3"` to taste.

### FastCountPaginator (large unfiltered tables)

For tables with millions of rows where `COUNT(*)` is too slow, use
`FastCountPaginator` instead. It reads PostgreSQL's `pg_class.reltuples` statistic —
essentially free — for unfiltered querysets, falling back to `COUNT(*)` when filters
are applied.

Add to `my_package/paginator.py`:

```python
from django.core.paginator import Paginator as DjangoPaginator
from django.db import connection
from django.db.models import QuerySet
from django.utils.functional import cached_property


def count_reltuples(table_name: str) -> int:
    """Return estimated row count from pg_class for the given table."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT reltuples::bigint FROM pg_class WHERE oid = %s::regclass",
            [table_name],
        )
        try:
            return int(cursor.fetchone()[0])
        except IndexError, TypeError, ValueError:
            return 0


class FastCountPaginator(DjangoPaginator):
    """Django paginator with fast unfiltered counts via pg_class.reltuples.

    Falls back to a standard COUNT(*) when the queryset has filters applied.
    """

    @cached_property
    def count(self) -> int:
        """Return estimated count for unfiltered querysets, else exact count."""
        if (
            isinstance(self.object_list, QuerySet)
            and not self.object_list.query.where.children
        ):
            result = count_reltuples(self.object_list.model._meta.db_table)
            if result > 0:
                return result
        return super().count
```

Pass it via `PaginationConfig` the same way as the standard `Paginator`:

```python
qs = Item.objects.order_by("-created_at")
return render_paginated_response(
    request,
    "my_app/items_list.html",
    qs,
    config=PaginationConfig(paginator=FastCountPaginator(qs, 20)),
)
```

> `reltuples` is updated by `ANALYZE` (runs automatically via autovacuum). The estimate
> can be slightly off on very active tables — acceptable for pagination display.

---

## Infinite Scroll

Feed-style content that loads automatically as the user scrolls. Uses HTMX's
`revealed` trigger on a sentinel element at the end of each page.

```python
from my_package.paginator import PaginationConfig, render_paginated_response


def item_list(request: HttpRequest) -> TemplateResponse:
    return render_paginated_response(
        request,
        "my_app/items_list.html",
        Item.objects.order_by("-created_at"),
        config=PaginationConfig(target="scroll-sentinel", partial="items"),
    )
```

```html
<!-- my_app/items_list.html -->
{% extends "base.html" %}

{% block content %}
  <div id="item-feed">
    {% partialdef items inline %}
      {% for item in page.object_list %}
        <p>{{ item.name }}</p>
      {% endfor %}

      {% if page.has_next %}
        <div id="scroll-sentinel"
             hx-get="{{ request.path }}{% querystring page=page.next_page_number %}"
             hx-trigger="revealed"
             hx-swap="outerHTML"
             aria-hidden="true"></div>
      {% endif %}
    {% endpartialdef %}
  </div>
{% endblock content %}
```

On the first load the full page renders. When the sentinel scrolls into view, HTMX
sends `HX-Target: scroll-sentinel`. `render_paginated_response` matches on `target` and
returns only the `items` partial — new items plus a fresh sentinel (or nothing on the
last page). `hx-swap="outerHTML"` replaces the sentinel with the new content, appending
items in place.

See the [HTMX infinite scroll example](https://htmx.org/examples/infinite-scroll/).

---

## Django Admin: FastCountAdminMixin

Django's admin list view runs `COUNT(*)` on every page load. `FastCountAdminMixin`
swaps in `FastCountPaginator` and suppresses the second count query used for the
"X results (Y total)" display.

First add `FastCountPaginator` to `my_package/paginator.py` (see above), then add
to the app's `admin.py`:

```python
from django.contrib import admin
from django.contrib.admin import ModelAdmin

from my_package.paginator import FastCountPaginator  # add FastCountPaginator first


class FastCountAdminMixin:
    """ModelAdmin mixin for fast pagination on large tables."""

    show_full_result_count = False
    paginator = FastCountPaginator


@admin.register(Item)
class ItemAdmin(FastCountAdminMixin, ModelAdmin):
    ...
```
