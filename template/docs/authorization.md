# Authorization

This project uses [`django-rules`](https://github.com/dfunckt/django-rules) for object-level authorization. Rules are predicate functions composed from smaller, reusable building blocks.

## Contents

- [How it works](#how-it-works)
- [Defining predicates](#defining-predicates)
- [Registering permissions](#registering-permissions)
- [Loading rules at startup](#loading-rules-at-startup)
- [Checking permissions in views](#checking-permissions-in-views)
- [Checking permissions in templates](#checking-permissions-in-templates)
- [The rules backend](#the-rules-backend)
- [Where to check permissions](#where-to-check-permissions)
- [Fine-grained permissions](#fine-grained-permissions)
- [Access control via querysets](#access-control-via-querysets)
- [Naming conventions](#naming-conventions)

## How it works

`django-rules` replaces database-stored permissions with code-defined predicates. A **predicate** is a plain Python function `(user, obj) -> bool`. Predicates compose with `&`, `|`, `~`. Permissions are named strings mapped to predicates via `add_perm`.

## Defining predicates

Predicates live in `<app>/rules.py`. Use `@predicate` from `rules.predicates`:

```python
from rules.permissions import add_perm
from rules.predicates import predicate

from myapp.models import Membership

@predicate
def is_member(user, obj) -> bool:
    """True if the user is a member of the given object."""
    if not user.is_authenticated:
        return False
    return Membership.objects.filter(user=user, obj=obj).exists()
```

Always check `user.is_authenticated` first — anonymous users should return `False` immediately without hitting the database.

## Registering permissions

Register permissions at the bottom of `<app>/rules.py` using `add_perm` from `rules.permissions`:

```python
from rules.permissions import add_perm

add_perm("myapp.do_something", is_member)
add_perm("myapp.do_something_else", is_member & is_admin)
```

**Import path:** use `from rules.permissions import add_perm`, not `from rules import add_perm`. The latter is not exported and causes a `reportPrivateImportUsage` error in basedpyright.

Permission names follow Django's convention: `"<app_label>.<action>"`.

## Loading rules at startup

Rules must be imported when Django starts so that `add_perm` calls run before any permission check. Do this in `AppConfig.ready()`:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "mypackage.myapp"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        import mypackage.myapp.rules  # noqa: F401
```

**This is required.** Without it, permissions registered via `add_perm` will not exist when views or templates try to check them.

## Checking permissions in views

Use `request.user.has_perm` directly:

```python
from django.core.exceptions import PermissionDenied

def my_view(request, pk):
    obj = get_object_or_404(MyModel, pk=pk)
    if not request.user.has_perm("myapp.do_something", obj):
        raise PermissionDenied
    ...
```

Do **not** pass permission booleans as template context variables — use the `{% has_perm %}` template tag instead (see below).

## Checking permissions in templates

Load the `rules` template tag library and use `{% has_perm %}`:

```html
{% load rules %}

{% has_perm 'myapp.do_something' request.user object as can_do_something %}
{% if can_do_something %}
  <a href="...">Do something</a>
{% endif %}
```

`{% has_perm %}` takes the permission name, the user, and the object (or no object for global permissions), and assigns the result to a context variable.

## The rules backend

For `has_perm` and the `{% has_perm %}` template tag to work, `rules.permissions.ObjectPermissionBackend` must be listed **first** in `AUTHENTICATION_BACKENDS`:

```python
AUTHENTICATION_BACKENDS = [
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
```

Placing it first ensures object-level rules are evaluated before the standard model backend's global permissions.

## Where to check permissions

Permissions belong in the layer that needs them. Do **not** compute a permission in the view just to pass it as a template context variable.

**View-level** — use `request.user.has_perm(...)` when the result drives view logic:
- gatekeeping (raise `PermissionDenied` / `Http404`)
- deciding which queryset to fetch
- building different context based on access

```python
can_manage = request.user.has_perm("projects.manage_project", project)
# used to decide what data to fetch:
applications = Applicant.objects.filter(project=project) if can_manage else Applicant.objects.none()
```

**Template-level** — use `{% has_perm %}` when the result only controls what is rendered. Call it once at the top of the template if referenced multiple times:

```html
{% load rules %}
{% has_perm 'projects.manage_project' request.user project as can_manage %}

{% if can_manage %}
  <a href="...">Edit</a>
{% endif %}
```

Never pass a permission boolean to the template from the view just to show or hide a UI element. If the view already computed it for view-level logic, it is fine to reuse it in the template — but it should not be computed *solely* for the template.

## Fine-grained permissions

Each permission name must describe a **specific action**, not a role or membership state. The predicate encodes *who* qualifies; the permission name describes *what they can do*.

**Wrong** — using a capability permission as a membership proxy:

```python
# In a view:
is_member = request.user.has_perm("organizations.create_project", org)
```

`create_project` means "can create a project in this org". Using it to check membership silently breaks the moment the underlying rule changes (e.g., restricting project creation to admins only). Every view that used it as a membership proxy now has the wrong gate — with no type error, no test failure, no warning.

**Right** — each check names exactly what it tests:

```python
# In rules.py — one predicate per concept:
add_perm("organizations.create_project", is_org_member)
add_perm("organizations.view_internals", is_org_member)
add_perm("organizations.manage_members", is_org_admin)

# In a view — read literally:
if not request.user.has_perm("organizations.view_internals", org):
    return redirect(org)
```

If the rule for `create_project` tightens to admins-only, `view_internals` is unaffected because they are separate permissions with separate predicates.

### Access logic belongs in rules.py, not views

Never reconstruct a permission predicate inside a view:

```python
# Wrong — view reimplements the rule:
is_org_member = request.user.has_perm("organizations.create_project", org)
is_team_member = TeamMember.objects.filter(user=request.user, project=project).exists()
can_see_internals = is_org_member or is_team_member
```

If "can see internals" is a meaningful concept, it belongs as a named permission whose predicate composes the required checks:

```python
# rules.py
add_perm(
    "projects.view_project_internals",
    is_project_owner | is_project_team_member | is_org_member,
)

# view
can_see_internals = request.user.has_perm("projects.view_project_internals", project)
```

The rule is defined once, tested once, and changed in one place.

## Access control via querysets

For list views and object fetches, prefer **queryset-as-gate** over explicit permission checks. `get_object_or_404` with a filtered queryset returns 404 for inaccessible objects — simpler and consistent with Django idiom:

```python
# Wrong — fetch then check:
org = get_object_or_404(Organization, pk=pk)
if not request.user.has_perm("organizations.view_internals", org):
    raise PermissionDenied  # 403, leaks existence

# Right — filter then fetch:
org = get_object_or_404(Organization.objects.for_member(request.user), pk=pk)
# 404 for non-members, no existence leak
```

Use `has_perm` (which may 403) only when the object's *existence* is already public and you are gatekeeping a specific action on it (e.g., an edit form on a publicly visible record).

## Naming conventions

| Permission name | Predicate | Meaning |
|----------------|-----------|---------|
| `organizations.create_project` | `is_org_member` | Any org member can create a project |
| `organizations.manage_members` | `is_org_admin` | Only org admins can manage membership |

Use the pattern `<app_label>.<verb>_<noun>` for action permissions, or `<app_label>.<verb>_<object>` when the object type is relevant.
