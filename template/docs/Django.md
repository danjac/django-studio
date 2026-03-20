# Django

**Read this document before starting any implementation work.** It documents
how the project is configured and the conventions that apply everywhere. For
implementation patterns, see the focused docs:

| Topic                                                       | Doc                    |
| ----------------------------------------------------------- | ---------------------- |
| Views, decorators, response classes, async, URL config      | `docs/Django-Views.md`        |
| Models, querysets, full-text search, choices, relationships | `docs/Django-Models.md`       |
| Templates, partials, fragments, pagination                  | `docs/Django-Templates.md`    |
| Forms and validation                                        | `docs/Validation.md`   |
| Adding a new package                                        | `docs/Packages.md`     |
| Migrations and linear-migrations                            | `docs/Django-Models.md`       |
| Background tasks                                            | `docs/Django-Tasks.md` |
| Scheduled cron jobs                                         | `docs/CronJobs.md`     |

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

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=USE_HTTPS)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = USE_HTTPS
```

Add CSP middleware (see Middleware Order below).

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

All tags in `templatetags.py` are registered as builtins — no `{% load %}` required.

| Tag                                              | Description                                                   |
| ------------------------------------------------ | ------------------------------------------------------------- |
| `{% title_tag "Page" %}`                         | Renders `<title>Site Name \| Page</title>`                    |
| `{% meta_tags %}`                                | Renders META tags including HTMX config                       |
| `{% cookie_banner %}`                            | Renders the GDPR cookie consent banner                        |
| `{% absolute_uri site path %}`                   | Returns an absolute URI for a path                            |
| `{% fragment "tmpl.html" %}...{% endfragment %}` | Includes a template with block content as `{{ content }}`     |
| `{% active_app 'app' %}`                         | Returns active/inactive nav CSS classes matched on `app_name` |
| `{% active_url 'name' %}`                        | Returns active/inactive nav CSS classes matched on `url_name` |

New tags which are not specific to a single app should be added here.

App-specific tags should be added to `<app_name>/templatetags/<app_name>.py` unless the user specifies otherwise.

See `docs/Django-Templates.md` for `active_app` / `active_url` usage.

## Admin

```python
# myapp/<app_name>/admin.py
from django.contrib import admin

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name"]
    date_hierarchy = "created_at"
```

## Internationalisation

All user-visible strings must be wrapped in translation functions.

**In Python:**

```python
from django.utils.translation import gettext as _, gettext_lazy as _l, ngettext

# Module-level: use gettext_lazy (evaluated lazily)
class MyForm(forms.Form):
    title = forms.CharField(label=_l("Title"))

# Function/method body: use gettext
def my_view(request):
    messages.success(request, _("Changes saved."))

# Plurals
msg = ngettext("%(n)s item", "%(n)s items", count) % {"n": count}
```

**In templates** — use `{% translate %}` (Django 4.0+), not the legacy `{% trans %}`:

```html
{% load i18n %}
<h1>{% translate "Welcome" %}</h1>
{% blocktranslate with name=user.name %}Hello, {{ name }}.{% endblocktranslate %}
```

You can use `_("string")` directly in tag arguments:

```html
{% include "header.html" with title=_("Dashboard") %}
```

Use `/djstudio translate <locale>` to extract, translate, and compile catalogues.
