# Pagination

Use `render_paginated_response` for all paginated views. Choose the right approach for
your use case:

| Use case | Approach |
|---|---|
| Standard browse/search lists | Numbered pages (default) |
| Simple prev/next only | [Previous/Next](#previousnext) |
| Feed-style content | Infinite scroll |
| Django admin on large tables | `FastCountAdminMixin` |
| Large tables where COUNT(*) is too slow | [Performance Optimizations](#performance-optimizations) |

---

## Contents

- [Numbered Pages (default)](#numbered-pages-default)
- [Previous/Next](#previousnext)
- [Infinite Scroll](#infinite-scroll)
- [Performance Optimizations](#performance-optimizations)
- [Django Admin: FastCountAdminMixin](#django-admin-fastcountadminmixin)

## Numbered Pages (default)

Use `render_paginated_response` with no extra configuration — Django's built-in
`Paginator` is used by default and `paginate.html` renders numbered navigation.

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

`paginate.html` renders first/previous, a ±3 window of numbered page links, and
next/last controls around `{{ content }}`. On an HTMX request only the `pagination`
partial is returned.

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

For very large unfiltered tables where `COUNT(*)` is slow, see
[FastCountPaginator](#fastcountpaginator--estimated-counts-for-numbered-pagination).

---

## Previous/Next

For simple lists where users don't need to jump to a specific page, create a minimal
`templates/paginate_prevnext.html` and reference it in the view template. The view
is identical to the default:

```python
from my_package.paginator import render_paginated_response


def item_list(request: HttpRequest) -> TemplateResponse:
    return render_paginated_response(
        request,
        "my_app/items_list.html",
        Item.objects.order_by("-created_at"),
    )
```

```html
<!-- templates/paginate_prevnext.html -->
{% load i18n %}
{% with has_other_pages=page.has_other_pages %}
  <div id="{{ pagination_config.target }}" aria-live="polite" aria-atomic="true">
    {{ content }}
    {% if has_other_pages %}
      <div class="flex justify-center pt-6">
        {% partial links %}
      </div>
    {% endif %}
  </div>
{% endwith %}

{% partialdef links %}
  <nav
    role="navigation"
    aria-label="{% translate "Pagination" %}"
    hx-swap="outerHTML show:window:top"
    hx-target="#{{ pagination_config.target }}"
  >
    <div class="join">
      {% if page.has_previous %}
        {% querystring page=1 as first_url %}
        <a
          href="{{ request.path }}{{ first_url }}"
          hx-get="{{ request.path }}{{ first_url }}"
          aria-label="{% translate "First page" %}"
          class="join-item btn btn-outline"
        >«</a>
        {% querystring page=page.previous_page_number as prev_url %}
        <a
          href="{{ request.path }}{{ prev_url }}"
          hx-get="{{ request.path }}{{ prev_url }}"
          aria-label="{% translate "Previous page" %}"
          class="join-item btn btn-outline"
        >‹</a>
      {% else %}
        <span class="join-item btn btn-outline btn-disabled" aria-hidden="true">«</span>
        <span class="join-item btn btn-outline btn-disabled" aria-hidden="true">‹</span>
      {% endif %}
      {% if page.has_next %}
        {% querystring page=page.next_page_number as next_url %}
        <a
          href="{{ request.path }}{{ next_url }}"
          hx-get="{{ request.path }}{{ next_url }}"
          aria-label="{% translate "Next page" %}"
          class="join-item btn btn-outline"
        >›</a>
        {% querystring page=page.paginator.num_pages as last_url %}
        <a
          href="{{ request.path }}{{ last_url }}"
          hx-get="{{ request.path }}{{ last_url }}"
          aria-label="{% translate "Last page" %}"
          class="join-item btn btn-outline"
        >»</a>
      {% else %}
        <span class="join-item btn btn-outline btn-disabled" aria-hidden="true">›</span>
        <span class="join-item btn btn-outline btn-disabled" aria-hidden="true">»</span>
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
    {% fragment "paginate_prevnext.html" %}
      {% for item in page.object_list %}
        <p>{{ item.name }}</p>
      {% endfor %}
    {% endfragment %}
  {% endpartialdef %}
{% endblock content %}
```

This avoids `COUNT(*)` when combined with `ZeroCountPaginator` — see
[ZeroCountPaginator](#zerocountpaginator--skip-count-for-previousnext-pagination).

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
