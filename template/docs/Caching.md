# Caching

This project uses Redis as the cache backend via `django-redis`.

References:
- [Django cache framework](https://docs.djangoproject.com/en/6.0/topics/cache/)
- [django-redis documentation](https://github.com/jazzband/django-redis)

---

## Caching Strategy

### When to cache

| Situation | Approach |
|-----------|----------|
| Expensive queryset, result changes infrequently | Low-level cache on the queryset result |
| Public page with no per-user content | `@cache_page` |
| Expensive template fragment shared across users | `{% cache %}` fragment |
| Third-party API call (weather, exchange rates, etc.) | Low-level cache on the response |
| Aggregated count or stat used in many requests | Low-level cache keyed on the aggregate |

### When NOT to cache

- **Per-user data** — never use `@cache_page` on a view that shows user-specific content; it will serve one user's data to another.
- **Write paths** — POST/PUT/DELETE views should never be cached.
- **Data that must be consistent** — financial calculations, inventory counts, anything where a stale read has real consequences.
- **Cheap queries** — indexed lookups by primary key or a small, filtered queryset are already fast. Adding a cache layer just adds complexity and a cache-invalidation problem.
- **Development shortcuts** — do not add caching to paper over an N+1 query or a missing index. Fix the root cause first.

### When in doubt, ask

If it is not obvious whether data is safe to cache, or how long the TTL should be,
**ask the user** before adding caching. The wrong answer introduces hard-to-debug
inconsistencies:

- Is it acceptable to show data that is up to N seconds old?
- Does any other part of the system write to this data? How often?
- Is this content per-user, per-session, or fully public?

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

## In-Process Caching

Before reaching for Redis, consider whether the cached value is needed **beyond a single
process or server instance**. If it only needs to survive for the lifetime of a request
or a Python object, use a Python-level mechanism instead:

### `@cached_property` — per-instance, per-request

Use `django.utils.functional.cached_property` for expensive properties on a model or
service object. The result is stored on the instance and computed at most once per
instance lifetime (typically one request):

```python
from django.utils.functional import cached_property

class Article(models.Model):
    ...

    @cached_property
    def reading_time_minutes(self) -> int:
        """Compute estimated reading time (expensive text analysis)."""
        return estimate_reading_time(self.body)
```

Do not use `@cached_property` on data that may become stale mid-request — it is never
invalidated. It is ideal for pure derivations of immutable instance state.

### `@functools.cache` — per-process, module-level

Use `functools.cache` (or `functools.lru_cache`) for pure functions whose result depends
only on their arguments and never changes (or changes infrequently enough that a process
restart is an acceptable reset):

```python
import functools

@functools.cache
def supported_locales() -> list[str]:
    """Load supported locales from disk once per process."""
    ...
```

**Use Redis (the low-level cache API) only when:**
- The cached value must be shared across multiple server instances or worker processes.
- The value needs to survive a process restart.
- TTL-based expiry or explicit invalidation across instances is required.

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
