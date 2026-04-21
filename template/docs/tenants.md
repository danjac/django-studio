# Multi-tenancy with django-tenants

This project uses [django-tenants](https://django-tenants.readthedocs.io/) for
PostgreSQL schema-based multi-tenancy. Each tenant gets an isolated PostgreSQL
schema; the public schema holds shared data (users, tenant registry, lookup
tables).

## Contents

- [How it works](#how-it-works)
- [SHARED\_APPS vs TENANT\_APPS](#shared_apps-vs-tenant_apps)
- [Required settings](#required-settings)
- [URL routing](#url-routing)
- [Accessing the current tenant](#accessing-the-current-tenant)
- [Tenant model](#tenant-model)
- [File uploads](#file-uploads)
- [Admin site customisation](#admin-site-customisation)
- [Management commands](#management-commands)
- [Testing](#testing)
- [Gotchas](#gotchas)

---

## How it works

`TenantMainMiddleware` (always the **first** middleware) inspects the request
hostname, looks up the matching `Domain` record, and sets:

- `request.tenant` — the `Tenant` instance
- `request.urlconf` — either `ROOT_URLCONF` (tenant subdomains) or
  `PUBLIC_SCHEMA_URLCONF` (the public domain)
- `connection.schema_name` — the active PostgreSQL schema for the request

All subsequent ORM queries in that request run against the resolved schema.

---

## SHARED\_APPS vs TENANT\_APPS

```python
# config/settings.py
SHARED_APPS = [
    "django_tenants",
    "modeltranslation",    # must come before django.contrib.admin
    "django.contrib.admin",
    # ... Django core + third-party apps
    "my_package.tenants",  # Tenant, Domain models
    "my_package.users",    # shared user identity
    # ... other apps with data shared across all tenants
]

TENANT_APPS = [
    "my_package.your_app",  # per-tenant data
    # ... other per-tenant apps
]

INSTALLED_APPS = SHARED_APPS + [app for app in TENANT_APPS if app not in SHARED_APPS]
```

**Rules:**

- `SHARED_APPS` — tables in the public schema only. Use for the tenant/domain
  registry, shared user identity, platform-wide lookup data, and infrastructure
  apps (background tasks, allauth, etc.).
- `TENANT_APPS` — each tenant gets its own copy of these tables. Use for
  per-organisation data.
- `TENANT_APPS` must contain at least one app or django-tenants raises
  `ImproperlyConfigured`.
- `django_tasks_db` (background tasks) belongs in `SHARED_APPS` — it is
  infrastructure, not tenant-specific data.
- `modeltranslation` must appear **before** `django.contrib.admin` in
  `SHARED_APPS`.

---

## Required settings

```python
DATABASE_ENGINE = "django_tenants.postgresql_backend"
DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"   # NOTE: not DOMAIN_MODEL
PUBLIC_SCHEMA_NAME = "public"
PUBLIC_SCHEMA_URLCONF = "config.urls.public"
ROOT_URLCONF = "config.urls.tenant"      # tenant subdomains
```

> **Gotcha:** The setting is `TENANT_DOMAIN_MODEL`, not `DOMAIN_MODEL`.
> Using `DOMAIN_MODEL` causes `AttributeError: 'Settings' object has no
> attribute 'TENANT_DOMAIN_MODEL'` at startup or on the first request.

---

## URL routing

Two URL confs serve different audiences:

| URL conf | Domain | Serves |
|---|---|---|
| `config.urls.public` | Public domain (`PUBLIC_SCHEMA_URLCONF`) | Landing page, auth, admin, infra endpoints |
| `config.urls.tenant` | Tenant subdomains (`ROOT_URLCONF`) | Application UI |

django-tenants has no built-in concept of shared URL patterns (unlike `SHARED_APPS` /
`TENANT_APPS`). The two URL confs are fully independent. To avoid duplicating patterns
that must be reachable on every domain (admin, allauth, health checks, infrastructure
endpoints, debug tools), define them once in `config/urls/shared.py` and import into
both confs:

```
config/urls/
    __init__.py   # empty
    shared.py     # admin, allauth, health checks, robots.txt, i18n, debug tools
    public.py     # index/about/privacy + shared_urlpatterns
    tenant.py     # tenant index + shared_urlpatterns
```

```python
# config/urls/shared.py
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("robots.txt", views.robots, name="robots"),
    path("account/", include("allauth.urls")),
    # health checks, debug toolbar, browser reload ...
]

# config/urls/tenant.py
from config.urls.shared import urlpatterns as shared_urlpatterns

urlpatterns = [
    path("", views.tenant_home, name="index"),
] + shared_urlpatterns

# config/urls/public.py
from config.urls.shared import urlpatterns as shared_urlpatterns

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
] + shared_urlpatterns
```

Both URL confs expose `name="index"` so shared templates (e.g. the navbar logo link)
can call `{% url 'index' %}` on any domain.

---

## Accessing the current tenant

django-tenants sets the tenant on the **request object**, not on the connection:

```python
# CORRECT
def my_view(request):
    tenant = request.tenant   # Tenant instance

# WRONG — connection.tenant is not set by TenantMainMiddleware
def my_view(request):
    from django.db import connection
    tenant = connection.tenant  # AttributeError
```

The `tenant` attribute is typed on `my_package.http.request.HttpRequest` via a
`TYPE_CHECKING` block, so views that use the typed request get full type inference:

```python
from my_package.http.request import HttpRequest

def my_view(request: HttpRequest) -> ...:
    tenant = request.tenant  # inferred as Tenant
```

In templates, pass the tenant explicitly from the view context:

```python
return TemplateResponse(request, "tenants/home.html", {"tenant": request.tenant})
```

---

## Tenant model

The `Tenant` model extends `TenantMixin`. `Domain` extends `DomainMixin`:

```python
from django_tenants.models import DomainMixin, TenantMixin
from sorl.thumbnail import ImageField
from my_package.uploads import UploadHandler

class Tenant(TenantMixin):
    name = models.CharField(_("name"), max_length=255)
    logo = ImageField(_("logo"), upload_to=UploadHandler("tenants/logos"), blank=True)
    auto_create_schema = True

class Domain(DomainMixin):
    pass
```

`auto_create_schema = True` causes django-tenants to create the tenant's
PostgreSQL schema when the `Tenant` record is first saved.

---

## File uploads

Tenant logos live in the **public schema** and use standard shared storage
(S3 / local). No tenant-scoped storage is needed for `Tenant.logo`.

For files uploaded *within* a tenant context (e.g. project attachments):
django-tenants provides `TenantFileSystemStorage` which scopes files per tenant
schema directory via `MULTITENANT_RELATIVE_MEDIA_ROOT`. In production with S3
this is less relevant since S3 uses path prefixes — the `UploadHandler`
UUID-based paths are sufficient for isolation.

Always use `sorl.thumbnail.ImageField` (not `django.db.models.ImageField`) for
image fields. It fires a `post_delete` signal that cleans up thumbnail cache
entries from storage automatically. Add an explicit `post_delete` signal to
delete the **original** file, since Django does not do this automatically:

```python
from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=Tenant)
def _delete_tenant_logo(sender, instance, **kwargs) -> None:
    instance.logo.delete(save=False)
```

---

## Admin site customisation

`TenantAwareAdminSite` overrides `each_context` to set `site_header` and
`site_title` to `"{tenant.name} Admin"` on tenant subdomains and
`"{site.name} Admin"` on the public domain.

It is wired in via a custom `AdminConfig` subclass:

```python
# my_package/tenants/admin_config.py
import django.contrib.admin.apps

class TenantAdminConfig(django.contrib.admin.apps.AdminConfig):
    default_site = "my_package.tenants.admin.TenantAwareAdminSite"
```

```python
# config/settings.py  SHARED_APPS
"my_package.tenants.admin_config.TenantAdminConfig",   # replaces "django.contrib.admin"
```

**Why a separate `admin_config.py` and not `admin.py` or `apps.py`?**

`TenantAdminConfig` must live in a module that can be safely imported *before*
the app registry is ready (Django imports the `AppConfig` class listed in
`INSTALLED_APPS` during startup, before any models are available).

- `admin.py` imports models at module level → `AppRegistryNotReady` at startup.
- `apps.py` already defines `TenantsConfig`. Django auto-scans `<module>.apps`
  for all `AppConfig` subclasses when resolving the `my_package.tenants` entry;
  finding two configs with `name = "django.contrib.admin"` raises
  `ImproperlyConfigured: Application labels aren't unique, duplicates: admin`.
- A dedicated `admin_config.py` that imports only `AdminConfig` (no models)
  avoids both problems.

---

## Management commands

### tenant_command

`tenant_command` wraps any Django management command so it runs within a specific
tenant's schema context. Use it whenever you need to run a command (e.g.
`migrate`, `shell`, `dbshell`, a custom management command) against a single
tenant's data rather than the public schema.

```bash
# Run against a specific tenant schema
python manage.py tenant_command --schema=acme migrate

# Pass options to the subcommand
python manage.py tenant_command --schema=acme shell --no-startup

# Interactive — prompts for tenant if --schema is omitted
python manage.py tenant_command migrate
```

When `--schema` is omitted, the command lists all available tenants and prompts
you to pick one. Enter `?` at the prompt to display schemas and their primary
domains.

#### Writing subcommands that run inside a tenant context

If you need a custom management command that always targets a specific tenant,
inherit from `BaseTenantCommand` and set `COMMAND_NAME`:

```python
from django_tenants.management.commands import BaseTenantCommand

class Command(BaseTenantCommand):
    COMMAND_NAME = "your_existing_command"
```

`BaseTenantCommand` iterates over all tenant schemas by default, or targets a
single schema when `--schema` is supplied. Use it for batch operations like
re-indexing search, sending per-tenant notifications, or running data migrations
across every tenant.

---

## Testing

### The public tenant fixture

`TenantMainMiddleware` runs on every request — including test client requests.
It looks up a `Domain` record matching the request hostname. Without a matching
record, every view test fails with `Domain.DoesNotExist` for `"testserver"`.

Add an **autouse** fixture that creates the public tenant and its test domains:

```python
# my_package/tests/fixtures.py
import pytest
from my_package.tenants.models import Domain, Tenant


@pytest.fixture(autouse=True)
def _public_tenant(db) -> None:
    """Create the public tenant and test-server domains for TenantMainMiddleware."""
    tenant, _ = Tenant.objects.get_or_create(
        schema_name="public",
        defaults={"name": "Public"},
    )
    for hostname in ("testserver", "localhost"):
        Domain.objects.get_or_create(
            domain=hostname,
            defaults={"tenant": tenant, "is_primary": hostname == "testserver"},
        )
```

Creating a `Tenant` with `schema_name="public"` is safe — django-tenants uses
`CREATE SCHEMA IF NOT EXISTS`, so it is a no-op when the schema already exists.

### ROOT\_URLCONF override

`reverse()` calls outside a request context use `ROOT_URLCONF` (the tenant URL
conf). If your test assertions call `reverse("index")` or other public-only
URL names, they will raise `NoReverseMatch` because those names only exist in
`PUBLIC_SCHEMA_URLCONF`.

Override `ROOT_URLCONF` in your settings fixture so that `reverse()` resolves
against the public URL conf:

```python
@pytest.fixture(autouse=True)
def _settings_overrides(settings, tmp_path) -> None:
    # ... other overrides ...
    settings.ROOT_URLCONF = "config.urls.public"
```

### Schema creation is expensive — avoid per-test creation

When `Tenant.save()` runs with `auto_create_schema = True`, django-tenants
creates a new PostgreSQL schema and runs **all tenant migrations**. This takes
3–5 seconds per call. With function-scoped fixtures, that cost multiplies by
every test that needs a tenant.

**Solution: session-scoped schema, function-scoped rows.**

1. A **session-scoped** `_tenant_schema` fixture creates the tenant schema
   once (with `--reuse-db`, it persists across runs).
2. Function-scoped fixtures create lightweight `Tenant` rows with
   `auto_create_schema = False` — no migrations run.

```python
TENANT_SCHEMA_NAME = "test_tenant"

# Session-scoped: creates schema + runs migrations once
@pytest.fixture(scope="session")
def _tenant_schema(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # Skip if schema already exists (--reuse-db)
        ...
        tenant = Tenant(schema_name=TENANT_SCHEMA_NAME, name="Test Tenant")
        tenant.save()  # creates schema + migrations (~5s, once)
        Tenant.objects.filter(pk=tenant.pk).delete()  # row only; schema stays

# Function-scoped: cheap row creation, no schema work
@pytest.fixture
def current_tenant(db, settings, _tenant_schema):
    tenant = Tenant(schema_name=TENANT_SCHEMA_NAME, name="Test Tenant")
    tenant.auto_create_schema = False  # schema already exists
    tenant.save()
    ...
```

### TenantFactory defaults to no schema creation

`TenantFactory` overrides `_create` to set `auto_create_schema = False` by
default. Pass `with_schema=True` when you genuinely need a new schema (e.g.
`transactional_db` tests):

```python
TenantFactory()                      # fast — no schema creation
TenantFactory(with_schema=True)      # slow — creates schema + runs migrations
```

### Cross-schema FK constraints and transactional\_db

Django's `TransactionTestCase` flushes tables with `TRUNCATE` **without
CASCADE** on PostgreSQL. If a tenant schema has FK constraints pointing to
shared-schema tables, the flush fails with:

```
cannot truncate a table referenced in a foreign key constraint
```

**Solution:** Drop cross-schema FK constraints after creating the schema.
Django validates FKs at the application level, so removing DB-level
cross-schema FKs doesn't affect test correctness.

Tests using `transactional_db` must also truncate tenant-schema tables in
their teardown, since `transactional_db`'s flush only covers the public
schema. Without this, committed data leaks to subsequent tests or runs.

```python
@pytest.fixture
def tenant_fixture(transactional_db, settings, _tenant_schema):
    tenant = Tenant(schema_name=TENANT_SCHEMA_NAME, ...)
    tenant.auto_create_schema = False
    tenant.save()
    ...
    yield tenant
    # Truncate tenant tables — transactional_db only flushes public schema
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = %s",
            [TENANT_SCHEMA_NAME],
        )
        tables = [row[0] for row in cursor.fetchall()]
        if tables:
            qualified = ", ".join(f'"{TENANT_SCHEMA_NAME}"."{t}"' for t in tables)
            cursor.execute(f"TRUNCATE {qualified} CASCADE")
```

---

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| `AttributeError: 'Settings' object has no attribute 'TENANT_DOMAIN_MODEL'` | Setting named `DOMAIN_MODEL` instead of `TENANT_DOMAIN_MODEL` | Rename the setting |
| `ImproperlyConfigured: TENANT_APPS is empty` | `TENANT_APPS = []` | Add at least one app to `TENANT_APPS` |
| `Domain.DoesNotExist` in tests | No `Domain` record for `"testserver"` | Add the `_public_tenant` autouse fixture |
| `NoReverseMatch` for public URL names in tests | `ROOT_URLCONF` points to tenant URL conf | Override to `PUBLIC_SCHEMA_URLCONF` in test settings |
| `connection.tenant` raises `AttributeError` | `TenantMainMiddleware` sets `request.tenant`, not `connection.tenant` | Use `request.tenant` |
| `No tenant for hostname "localhost"` when hitting `localhost:8000` | `Domain` record stored as `localhost:8000` but django-tenants strips the port before lookup | Store `Domain.domain` without the port — `localhost`, not `localhost:8000` |
| Admin shows "not available for this type of schema" for a `SHARED_APPS` entry | App listed by module name but registers under a different `AppConfig.label` | Use the full `AppConfig` dotted path (e.g. `"django_tasks_db.apps.TasksAppConfig"`) in `SHARED_APPS` |
| Tenant subdomain returns 404 in development | `ALLOWED_HOSTS` explicitly set without the `.localhost` wildcard | In `.env` set `ALLOWED_HOSTS=.localhost,127.0.0.1`. The leading dot is Django's wildcard and matches all `*.localhost` subdomains |
| `AppRegistryNotReady` or `ImproperlyConfigured: duplicates: admin` when wiring a custom `AdminSite` | Putting the `AdminConfig` subclass in `admin.py` (imports models) or `apps.py` (Django auto-scans and finds two configs with the same label) | Put the `AdminConfig` subclass in its own module (e.g. `admin_config.py`) that imports only `AdminConfig` and no models — see [Admin site customisation](#admin-site-customisation) |
