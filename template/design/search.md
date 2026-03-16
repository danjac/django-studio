# Search

Template: `templates/search.html` (build per project — no shipped template)
CSS: none required beyond `form-input`

## Overview

The project ships a `SearchMiddleware` that adds `request.search` (a
`SearchDetails` instance) to every request. Use it in views and templates to
drive debounced, HTMX-powered search that updates the URL bar without a full
page reload.

## `request.search` API

| Expression | Type | Description |
|---|---|---|
| `request.search.value` | `str` | The current search query (stripped, max 200 chars) |
| `request.search.qs` | `str` | `?search=<value>` or `""` if empty |
| `bool(request.search)` | `bool` | `True` if a non-empty search query is present |
| `str(request.search)` | `str` | Same as `.value` |

The middleware reads from `GET["search"]`. Override `param` if you need a
different query-string key.

## View

Pass `request.search` to the queryset filter and into context:

```python
from myapp.db.search import Searchable  # if model uses FTS

@require_safe
@login_required
def item_list(request: HttpRequest) -> TemplateResponse:
    qs = Item.objects.all()
    if request.search:
        qs = qs.search(request.search.value)
    return render_paginated_response(
        request,
        "myapp/item_list.html",
        qs,
        target="pagination",
        partial="pagination",
    )
```

## Template

The search input uses HTMX to fire on every keystroke (debounced 300 ms) and
pushes the new URL into the browser history. The pagination `<div>` is the swap
target so only the list updates — the header and search bar stay in place.

```html
{% load i18n %}

{% include "header.html" with title=_("Items") %}

<div class="mt-4 flex items-center gap-3">
  <div class="relative flex-1 sm:max-w-xs">
    <input
      type="search"
      name="search"
      value="{{ request.search.value }}"
      placeholder="{% translate "Search…" %}"
      autocomplete="off"
      class="form-input w-full"
      hx-get="{{ request.path }}"
      hx-trigger="input changed delay:300ms, search"
      hx-target="#pagination"
      hx-push-url="true"
      hx-include="[name='search']"
    >
    {% if request.search %}
      <a
        href="{{ request.path }}"
        class="absolute inset-y-0 right-0 flex items-center px-3 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
        aria-label="{% translate "Clear search" %}"
        hx-get="{{ request.path }}"
        hx-target="#pagination"
        hx-push-url="{{ request.path }}"
      >
        {% heroicon_mini "x-mark" class="size-4" aria_hidden="true" %}
      </a>
    {% endif %}
  </div>
</div>

{% partialdef pagination inline %}
  {% fragment "paginate.html" %}
    ...
  {% endfragment %}
{% endpartialdef pagination %}
```

### Notes

- `hx-trigger="input changed delay:300ms, search"` debounces typing and also
  fires immediately when the browser's built-in search clear button is clicked.
- `hx-push-url="true"` keeps the URL bar in sync so users can share or bookmark
  search results.
- The clear button (`x-mark`) links back to `request.path` (no query string).
  Its `hx-push-url` attribute uses `request.path` directly so the URL bar clears.
- `hx-include="[name='search']"` is not needed when the input is the trigger
  element — HTMX includes it automatically — but is required if the clear
  button fires the request from a sibling element.

## Integration with `render_paginated_response`

`render_paginated_response` sets `pagination_target` in context and matches the
`HX-Target` header to decide whether to render the full page or the named
partial. The search input targets `#pagination`, which is the `<div id="pagination">`
that `paginate.html` renders inside `{% partialdef pagination %}`.

No additional view logic is needed: on the first load HTMX is not involved,
on subsequent searches only the pagination partial is re-rendered.
