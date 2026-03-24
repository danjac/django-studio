# Pagination

Use `render_paginated_response` for all paginated views. Choose the right approach for
your use case:

| Use case | Approach |
|---|---|
| Simple browse/search lists | Previous/Next (default) |
| User needs to jump to a specific page | Numbered pages |
| Feed-style content | Infinite scroll |
| Django admin on large tables | `FastCountAdminMixin` |
| Large tables where COUNT(*) is too slow | [Performance Optimizations](#performance-optimizations) |

---

## Contents

- [Previous/Next (default)](#previousnext-default)
- [Numbered Pagination](#numbered-pagination)
- [Infinite Scroll](#infinite-scroll)
- [Performance Optimizations](#performance-optimizations)
- [Django Admin: FastCountAdminMixin](#django-admin-fastcountadminmixin)

## Previous/Next (default)

Use `render_paginated_response` with no custom paginator — Django's built-in `Paginator`
is used by default.

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

To override the page size, pass a `Paginator` instance directly:

```python
from django.core.paginator import Paginator

from my_package.paginator import PaginationConfig, render_paginated_response


def item_list(request: HttpRequest) -> TemplateResponse:
    qs = Item.objects.order_by("-created_at")
    return render_paginated_response(
        request,
        "my_app/items_list.html",
        qs,
        config=PaginationConfig(paginator=Paginator(qs, 50)),
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

For very large unfiltered tables where `COUNT(*)` is slow, see
[FastCountPaginator](#fastcountpaginator--estimated-counts-for-numbered-pagination).

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

## Performance Optimizations

For large tables, add one of these custom paginators to `my_package/paginator.py` and
pass via `PaginationConfig`.

### ZeroCountPaginator — skip COUNT(*) for previous/next pagination

Avoids `COUNT(*)` entirely by fetching one extra row to detect whether a next page
exists. Best for large tables used with previous/next or infinite scroll.

```python
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.utils.functional import cached_property


class ZeroCountPage:
    """Pagination page without COUNT(*) queries."""

    def __init__(self, *, paginator: "ZeroCountPaginator", number: int) -> None:
        self.paginator = paginator
        self.page_size = paginator.per_page
        self.number = number

    def __len__(self) -> int:
        return len(self.object_list)

    def __getitem__(self, index):
        return self.object_list[index]

    def has_next(self) -> bool:
        return self._has_next

    def has_previous(self) -> bool:
        return self._has_previous

    def has_other_pages(self) -> bool:
        return self._has_previous or self._has_next

    def next_page_number(self) -> int:
        if self._has_next:
            return self.number + 1
        raise EmptyPage("Next page does not exist")

    def previous_page_number(self) -> int:
        if self._has_previous:
            return self.number - 1
        raise EmptyPage("Previous page does not exist")

    @cached_property
    def object_list(self):
        return self._object_list_with_next_item[: self.page_size]

    @cached_property
    def _has_next(self) -> bool:
        return len(self._object_list_with_next_item) > self.page_size

    @cached_property
    def _has_previous(self) -> bool:
        return self.number > 1

    @cached_property
    def _object_list_with_next_item(self) -> list:
        start = (self.number - 1) * self.page_size
        end = start + self.page_size + 1
        return list(self.paginator.object_list[start:end])


class ZeroCountPaginator:
    """Paginator that avoids COUNT(*) queries."""

    def __init__(self, object_list, per_page: int) -> None:
        self.object_list = object_list
        self.per_page = per_page

    def get_page(self, number) -> ZeroCountPage:
        try:
            number = int(number)
            if number < 1:
                raise EmptyPage
        except TypeError, ValueError:
            number = 1
        except EmptyPage:
            number = 1
        return ZeroCountPage(paginator=self, number=number)
```

Use it via `PaginationConfig`:

```python
from my_package.paginator import PaginationConfig, render_paginated_response


def item_list(request: HttpRequest) -> TemplateResponse:
    qs = Item.objects.order_by("-created_at")
    return render_paginated_response(
        request,
        "my_app/items_list.html",
        qs,
        config=PaginationConfig(paginator=ZeroCountPaginator(qs, 50)),
    )
```

### FastCountPaginator — estimated counts for numbered pagination

Reads PostgreSQL's `pg_class.reltuples` statistic — essentially free — for unfiltered
querysets, falling back to `COUNT(*)` when filters are applied. Use with numbered
pagination on tables with millions of rows.

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

## Django Admin: FastCountAdminMixin

Django's admin list view runs `COUNT(*)` on every page load. `FastCountAdminMixin`
swaps in `FastCountPaginator` and suppresses the second count query used for the
"X results (Y total)" display.

First add `FastCountPaginator` to `my_package/paginator.py` (see
[Performance Optimizations](#performance-optimizations)), then add to the app's `admin.py`:

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
