# Caching

This project uses Redis as the cache backend via `django-redis`.

References:
- [Django cache framework](https://docs.djangoproject.com/en/6.0/topics/cache/)
- [django-redis documentation](https://github.com/jazzband/django-redis)

---

## Configuration

```python
# config/settings.py
DEFAULT_CACHE_TIMEOUT = env.int("DEFAULT_CACHE_TIMEOUT", 360)  # seconds

CACHES = {
    "default": env.dj_cache_url("REDIS_URL", default="redis://127.0.0.1:6379/0")
    | {"TIMEOUT": DEFAULT_CACHE_TIMEOUT},
}
```

`DEFAULT_CACHE_TIMEOUT` (default 360 s / 6 minutes) is the fallback TTL used when
no explicit timeout is passed. It is also available in templates as
`{{ cache_timeout }}` via the `cache_timeout` context processor.

---

## Low-Level Cache API

```python
from django.core.cache import cache

# Store
cache.set("my_key", value, timeout=300)   # timeout in seconds; None = forever

# Retrieve
value = cache.get("my_key")               # returns None on miss
value = cache.get("my_key", default="fallback")

# Delete
cache.delete("my_key")

# Check existence
cache.has_key("my_key")

# Atomic get-or-set
value = cache.get_or_set("my_key", expensive_computation, timeout=300)
```

Use the low-level API when you need fine-grained control over keys and TTLs —
model data, aggregated counts, or expensive third-party API responses.

---

## Per-View Caching

Cache an entire view response for anonymous users with `@cache_page`:

```python
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_safe

from my_package.http.request import HttpRequest


@require_safe
@cache_page(60 * 15)  # 15 minutes
def public_list(request: HttpRequest) -> TemplateResponse:
    ...
```

`@cache_page` is only appropriate for public, anonymous views — it does not
vary by user. For authenticated views, cache at the queryset or object level
instead.

---

## Template Fragment Caching

Cache expensive template sections with `{% cache %}`:

```html
{% load cache %}

{% cache cache_timeout "sidebar" %}
  {# expensive sidebar content #}
{% endcache %}
```

`cache_timeout` is available in every template via the context processor.
Pass additional vary-keys after the fragment name to scope per-user or per-object:

```html
{% cache cache_timeout "user-profile" request.user.pk %}
  {{ request.user.get_full_name }}
{% endcache %}
```

---

## Cache Invalidation

**By key** — delete explicitly when data changes:

```python
from django.core.cache import cache

def update_item(item):
    item.save()
    cache.delete(f"item-{item.pk}")
```

**By versioning** — bump a version suffix to invalidate a group of keys without
iterating them:

```python
version = cache.get("items-version", 1)
cache.set("items-version", version + 1)
```

**By TTL** — for tolerably stale data, just let keys expire. Prefer this for
read-heavy, infrequently-changing data (e.g. public category lists).

---

## Sessions

Sessions use `cached_db` backend — stored in both Redis and the database:

```python
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
```

Fast reads hit Redis; the database provides durability if Redis is flushed.

---

## Testing

Override the cache backend in tests to avoid cross-test contamination:

```python
# my_package/tests/fixtures.py
@pytest.fixture(autouse=True)
def _settings_overrides(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    }
```

This is already set in the project's root `fixtures.py` — no additional setup
needed in most tests. For tests that explicitly exercise caching behaviour, use
`LocMemCache` instead of `DummyCache`:

```python
settings.CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}
```
