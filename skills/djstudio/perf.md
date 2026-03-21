Audit the codebase for Django, Python, and database performance issues. Report
findings in three groups: **CRITICAL** (production-impacting), **WARNING** (likely
slow under real load), and **ADVISORY** (best-practice gap, lower urgency).

Work through each section below. Read every referenced file; do not skip sections.

---

## 1. ORM and database queries

### 1a. N+1 queries

Scan all `views.py` and `models.py` files under `<package_name>/`.

Flag as **CRITICAL** any queryset that:
- Iterates over a queryset in a template or view and accesses a related object
  without a `select_related` or `prefetch_related` call
- Calls `.count()`, `.exists()`, or `.all()` inside a loop

Flag as **WARNING** any queryset that:
- Returns all rows from a table with no `.values()`, `.only()`, or field limiting —
  especially if the model has large text/binary fields

Common patterns to flag:
```python
# CRITICAL: N+1
for order in Order.objects.all():
    print(order.user.email)  # hits DB once per order

# FIX: use select_related
Order.objects.select_related("user")

# CRITICAL: N+1 on M2M
for post in Post.objects.all():
    print(post.tags.all())  # hits DB once per post

# FIX: use prefetch_related
Post.objects.prefetch_related("tags")
```

### 1b. Missing database indexes

Scan all `models.py` files. Flag as **WARNING** any field that is:
- Used in a `filter()`, `order_by()`, `get()`, or `exclude()` call in views or
  managers, but has no `db_index=True`, is not a primary key, and is not a
  `ForeignKey` (which auto-indexes)
- A `ForeignKey` used in `order_by()` without a covering index on the FK column

Flag as **ADVISORY** any model with no explicit `class Meta: ordering` that is
paginated in a view — unordered pagination returns inconsistent results.

### 1c. Unbounded querysets

Flag as **WARNING** any queryset passed to a template or view that has no
`.limit()` / slice / pagination and could return an unbounded number of rows.
This includes `Model.objects.all()` with no limit in a list view.

### 1d. Aggregations and annotations

Flag as **WARNING** any Python-level aggregation that should be a database
aggregation:
```python
# WARNING: computing count in Python
total = len(Order.objects.filter(user=user))  # loads all rows
# FIX:
total = Order.objects.filter(user=user).count()
```

Flag as **ADVISORY** any `annotate()` with a subquery that could be replaced by
a `prefetch_related(Prefetch(...))` for batch fetching.

### 1e. Raw SQL

Flag as **WARNING** every `.raw()`, `.extra()`, or `cursor.execute()` call —
these bypass the ORM's optimisation hints and are harder to review. Verify they
are necessary and note what they do.

---

## 2. View performance

### 2a. Caching

See `docs/Caching.md` for the full caching strategy — when to cache, when not to,
and which mechanism to reach for first.

Flag as **ADVISORY** any view that:
- Makes the same DB query on every request for data that rarely changes (e.g.
  site-wide config, category lists, featured items) — consider low-level
  `cache.get/set` or `cache.get_or_set`
- Renders a public, user-agnostic page on every request — consider `@cache_page`
- Contains an expensive template fragment shared across users — consider
  `{% cache cache_timeout "key" %}` (pairs well with HTMX partial swaps)
- Makes a repeated cross-process call (third-party API, aggregated stat) that
  should be cached in Redis

Note: only flag views where caching would be safe. Never suggest `@cache_page` for
authenticated or user-personalised views — it will serve one user's data to another.

### 2b. Synchronous blocking in async views

If any views use `async def`, flag as **CRITICAL** any call to a synchronous ORM
method without `sync_to_async` or `database_sync_to_async`:
```python
# CRITICAL: blocking ORM in async view
async def my_view(request):
    posts = Post.objects.all()  # blocks the event loop
```

### 2c. Large response payloads

Flag as **WARNING** any view that:
- Returns a queryset without `.values()` or `.only()` where the model has fields
  that are not needed by the template (especially large `TextField` columns)
- Serialises entire model instances to JSON without field filtering

---

## 3. Python-level performance

### 3a. Repeated computation in loops

Flag as **WARNING** any loop that recomputes a constant value on each iteration:
```python
# WARNING: len() called every iteration
for i in range(len(items)):  # len() inside range is fine; avoid if called inside loop
    process(items[i])

# WARNING: DB call inside loop
for user in users:
    send_email(user, Config.objects.get(key="smtp_host"))  # hits DB every time
```

### 3b. Inefficient string building

Flag as **WARNING** any string built with `+` concatenation inside a loop —
prefer `"".join(parts)` or f-strings outside loops.

### 3c. Missing in-process memoization

Flag as **ADVISORY** any:
- Model or service property that recomputes the same expensive derived value
  multiple times per instance — prefer `@cached_property` (computed once, stored
  on the instance for its lifetime)
- Pure module-level function called repeatedly with the same arguments across
  requests — prefer `@functools.cache` (process-level memoization, no Redis needed)

```python
# ADVISORY: recomputed on every access
class Article(models.Model):
    @property
    def reading_time(self):
        return estimate_reading_time(self.body)  # expensive, called many times

# FIX: cache on the instance
from django.utils.functional import cached_property

class Article(models.Model):
    @cached_property
    def reading_time(self):
        return estimate_reading_time(self.body)
```

Reach for `@cached_property` or `functools.cache` before Redis — they have no
network overhead and no invalidation complexity. Use Redis only when the value
must be shared across processes or server instances. See `docs/Caching.md`.

### 3e. Unnecessary imports

Flag as **ADVISORY** any `import *` statements — they pollute the namespace and
make dependency analysis harder.

---

## 4. Static files and media

### 4a. Uncompressed static assets

Check `config/settings.py` for `STATICFILES_STORAGE` or `STORAGES["staticfiles"]`.

Flag as **ADVISORY** if:
- `ManifestStaticFilesStorage` (or equivalent) is not used in production — this
  enables cache-busting by content hash
- CSS/JS files are not minified (no Whitenoise, no Vite/Webpack build step found)

### 4b. Large media files served by Django

Flag as **WARNING** if `DEBUG=False` and media files are served via Django's
`static()` URL conf (only appropriate in development). Production should serve
media from S3 or a CDN.

---

## 5. Template performance

### 5a. Expensive template tags

Flag as **WARNING** any custom template tag that makes a database call —
these run on every render and bypass Django's queryset caching. Prefer passing
data from the view instead.

### 5b. Deep template inheritance

Flag as **ADVISORY** if templates extend more than 4 levels deep — Django
re-parses the entire inheritance chain on every render (without caching).

---

## 6. Background tasks

If `django-tasks` or Celery is configured, scan all task files.

Flag as **WARNING** any task that:
- Makes unbounded DB queries (no limit, no pagination)
- Is called synchronously inside a view when it should be deferred

Flag as **ADVISORY** any task with no retry logic for transient failures
(network calls, external APIs).

---

## 7. Settings

Check `config/settings.py` for production-relevant performance settings:

| Setting | Recommended value | Severity if missing |
|---|---|---|
| `CONN_MAX_AGE` | `600` or `None` (persistent connections) | WARNING |
| `ATOMIC_REQUESTS` | `True` (wraps each request in a transaction) | ADVISORY |
| `SESSION_ENGINE` | `django.contrib.sessions.backends.cache` (Redis) | ADVISORY |
| `CACHES` | Redis backend configured | ADVISORY |
| `DEBUG` | `False` in production | CRITICAL (security, also disables query caching) |

---

## Report format

```
CRITICAL:
  [orm] orders/views.py:order_list — iterates Order queryset and accesses
    order.user.email with no select_related; N+1 query on every request
  [async] payments/views.py:checkout — sync ORM call in async view blocks event loop
  ...

WARNING:
  [orm] products/models.py:Product — name field used in filter() but no db_index
  [orm] reports/views.py:summary — len(queryset) should be queryset.count()
  [settings] CONN_MAX_AGE not set; new DB connection on every request
  ...

ADVISORY:
  [caching] homepage/views.py:index — category list fetched on every request,
    consider cache_page or Redis
  [settings] SESSION_ENGINE not using cache backend
  ...

OK:
  No raw SQL found
  All list views are paginated
  select_related / prefetch_related used correctly in checked views
  ...
```

After listing all findings, print a one-line summary:

```
X critical · Y warnings · Z advisory
```

If there are CRITICAL findings, recommend addressing them before any public
deployment and offer to fix each one. Wait for the user to confirm before making
any changes.

---

## Help

**djstudio perf**

Audits the codebase for Django, Python, and database performance issues.

Scans views, models, tasks, templates, and settings. Reports findings as CRITICAL
(production-impacting), WARNING (likely slow under load), or ADVISORY (best-practice
gap). Offers to fix critical issues after presenting the report.

Example:
  /djstudio perf
