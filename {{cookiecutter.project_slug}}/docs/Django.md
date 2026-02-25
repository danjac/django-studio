# Django

This document covers Django patterns used in this project based on actual code.

## Django Version

Django 6.0+ with Python 3.14.

## Settings

Using `environs` for environment variables:

```python
# config/settings.py
from environs import Env

env = Env()
env.read_env()

DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY", default="...")
```

### Database with Connection Pooling

```python
DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL",
        default="postgresql://postgres:password@127.0.0.1:5432/postgres",
    )
}

if env.bool("USE_CONNECTION_POOL", default=True):
    DATABASES["default"]["CONN_MAX_AGE"] = 0
    DATABASES["default"]["OPTIONS"] = {
        "pool": (
            {
                "min_size": env.int("CONN_POOL_MIN_SIZE", 2),
                "max_size": env.int("CONN_POOL_MAX_SIZE", 10),
                "max_lifetime": env.int("CONN_POOL_MAX_LIFETIME", 1800),
                "max_idle": env.int("CONN_POOL_MAX_IDLE", 120),
                "max_waiting": env.int("CONN_POOL_MAX_WAITING", 200),
                "timeout": env.int("CONN_POOL_TIMEOUT", default=20),
            }
        ),
    }
```

### Cache

```python
CACHES = {
    "default": env.dj_cache_url("REDIS_URL", default="redis://127.0.0.1:6379/0")
    | {
        "TIMEOUT": env.int("DEFAULT_CACHE_TIMEOUT", 360),
    }
}
```

### Security Settings

Django 6 includes CSP (Content Security Policy) support built-in:

```python
# Content-Security-Policy (Django 6+)
from django.utils.csp import CSP

CSP_SCRIPT_WHITELIST = env.list("CSP_SCRIPT_WHITELIST", default=[])

SCRIPT_SRC = [
    CSP.SELF,
    CSP.UNSAFE_EVAL,
    CSP.UNSAFE_INLINE,
    *CSP_SCRIPT_WHITELIST,
]

CSP_DATA = f"data: {'https' if USE_HTTPS else 'http'}:"

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
    "script-src": SCRIPT_SRC,
    "script-src-elem": SCRIPT_SRC,
    "img-src": [CSP.SELF, CSP_DATA],
    "media-src": ["*"],
}

# HTTPS settings
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=USE_HTTPS)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)

# XSS and content type
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = USE_HTTPS
```

Add CSP middleware:

```python
MIDDLEWARE = [
    # ...
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    # ...
]
```

## Installed Apps

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.forms",
    # Third-party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_htmx",
    "django_http_compression",
    "django_linear_migrations",
    "django_tailwind_cli",
    "django_tasks_db",
    "health_check",
    "heroicons",
    "widget_tweaks",
    # Local apps
]
```

## Middleware Order

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django_http_compression.middleware.HttpCompressionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]
```

## Function-Based Views

This project uses **function-based views only**, not class-based views.

### View Decorators

```python
# myapp/http/decorators.py
from django.views.decorators.http import require_http_methods

require_form_methods = require_http_methods(["GET", "HEAD", "POST"])
require_DELETE = require_http_methods(["DELETE"])
```

Usage:

```python
from django.views.decorators.http import require_POST, require_safe

@require_safe
def index(request):
    return TemplateResponse(request, "index.html")

@require_POST
def create_item(request):
    return HttpResponseRedirect(reverse("items:list"))
```

### Custom Response Classes

```python
# myapp/http/response.py
import http
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

RenderOrRedirectResponse = TemplateResponse | HttpResponseRedirect

class TextResponse(HttpResponse):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("content_type", "text/plain")
        super().__init__(*args, **kwargs)

class HttpResponseNoContent(HttpResponse):
    status_code = http.HTTPStatus.NO_CONTENT

class HttpResponseConflict(HttpResponse):
    status_code = http.HTTPStatus.CONFLICT
```

### Extended HttpRequest

```python
# myapp/http/request.py
from django.http import HttpRequest as DjangoHttpRequest
from django_htmx.middleware import HtmxDetails

class HttpRequest(DjangoHttpRequest):
    if TYPE_CHECKING:
        htmx: HtmxDetails

class AuthenticatedHttpRequest(HttpRequest):
    if TYPE_CHECKING:
        user: User
```

### HTMX View Pattern

```python
def item_list(request):
    context = {"items": Item.objects.all()}

    if request.htmx:
        return TemplateResponse(request, "partials/items.html", context)

    return TemplateResponse(request, "full_page.html", context)
```

### Async Views

```python
from django.views.decorators.http import require_safe

@require_safe
async def search_items(request):
    client = get_client()
    results = await client.search(request.search.value)
    return TemplateResponse(request, "search_results.html", {"results": results})
```

## Async Patterns

**Prefer synchronous code unless async is specifically required.**

Use async when:
- Making API calls to third-party services
- Using Django Channels/WebSockets
- I/O-bound operations that benefit from concurrency

### HTTP Client

Always use `httpx` for HTTP requests - never `requests`:

```python
import httpx

# Sync (preferred unless async is needed)
response = httpx.get("https://api.example.com/data")

# Async
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/data")
```

### Running Async Code

Django runs in ASGI mode for async support:

```python
# config/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()
```

Gunicorn with Uvicorn worker:
```bash
gunicorn --worker-class uvicorn.workers.UvicornWorker config.asgi:application
```

### When NOT to Use Async

- Simple CRUD views
- Database operations (use Django's sync ORM)
- Template rendering
- Most typical Django views

## Models

### Custom QuerySet with Searchable Mixin

```python
# myapp/db/search.py
class Searchable(Base):
    default_search_fields: tuple[str, ...] = ()

    def search(self, value: str, *search_fields: str, annotation: str = "rank") -> QuerySet:
        if not value:
            return self.none()
        ...
```

```python
# myapp/models.py
from myapp.db.search import Searchable

class PodcastQuerySet(Searchable, models.QuerySet):
    default_search_fields = ("search_vector",)

    def published(self):
        return self.filter(pub_date__isnull=False)

    def subscribed(self, user):
        return self.filter(pk__in=user.subscriptions.values("podcast"))
```

### PostgreSQL Full-text Search

Use PostgreSQL full-text search. This project uses a `Searchable` mixin pattern:

```python
# myapp/db/search.py
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, QuerySet
import functools
import operator

class Searchable:
    default_search_fields: tuple[str, ...] = ()

    def search(self, value: str, *search_fields: str, annotation: str = "rank") -> QuerySet:
        if not value:
            return self.none()

        search_fields = search_fields if search_fields else self.default_search_fields
        query = SearchQuery(value, search_type="websearch", config="simple")

        rank = functools.reduce(
            operator.add,
            (SearchRank(F(field), query=query) for field in search_fields),
        )

        q = functools.reduce(
            operator.or_,
            (Q(**{field: query}) for field in search_fields),
        )

        return self.annotate(**{annotation: rank}).filter(q)
```

Use in models:

```python
# myapp/models.py
from myapp.db.search import Searchable

class ItemQuerySet(Searchable, models.QuerySet):
    default_search_fields = ("search_vector",)

class Item(models.Model):
    objects = ItemQuerySet()
    search_vector = SearchVectorField(null=True)
```

### Search Vector Updates via Triggers

Use database triggers to auto-update search vectors:

```python
# myapp/migrations/0002_add_search_trigger.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [("myapp", "0001_initial")]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE TRIGGER myapp_update_search_trigger
BEFORE INSERT OR UPDATE OF title, description ON myapp_item
FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger(
    search_vector, 'pg_catalog.english', title, description);
UPDATE myapp_item SET search_vector = NULL;""",
            reverse_sql="DROP TRIGGER IF EXISTS myapp_update_search_trigger ON myapp_item;",
        ),
    ]
```

### Model with Choices

```python
class Item(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
```

## Forms

Forms define only fields, labels, and error messages - **no CSS classes**:

```python
# myapp/forms.py
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name"]
        labels = {"name": "Name"}
        error_messages = {"name": {"unique": "This name is already taken"}}
```

Classes added in templates using `widget_tweaks`:

```html
{% load widget_tweaks %}
{% render_field form.name class="form-input" %}
```

### Form Template Pattern

```html
<!-- form/field.html -->
{% load heroicons widget_tweaks %}

{% partialdef input %}
    {% partial label %}
    {% render_field field class="form-input" %}
{% endpartialdef %}

{% partialdef label %}
    <label for="{{ field.id_for_label }}">
        {{ field.label }}
        {% if not field.field.required %}(optional){% endif %}
    </label>
{% endpartialdef %}
```

## Context Processors

```python
# myapp/context_processors.py
def csrf_header(_) -> dict[str, str | None]:
    return {"csrf_header": _csrf_header_name()}

@functools.cache
def _csrf_header_name() -> str | None:
    return HttpHeaders.parse_header_name(settings.CSRF_HEADER_NAME)
```

## Template Tags

```python
# myapp/templatetags.py
from django import template

register = template.Library()

@register.simple_tag
def meta_tags() -> str:
    """Renders meta tags including HTMX config."""
    ...

@register.simple_block_tag(takes_context=True)
def fragment(context, content: str, template_name: str, *, only: bool = False, **extra_context):
    """Include template with block content."""
    ...
```

## URL Configuration

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("myapp.users.urls")),
]
```

## Admin

```python
# myapp/admin.py
from django.contrib import admin

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name"]
    date_hierarchy = "created_at"
```
