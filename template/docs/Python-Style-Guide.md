# Python Style Guide

Code style is enforced automatically by pre-commit (ruff, pyupgrade, django-upgrade,
absolufy-imports). See `docs/Precommit-Linting.md` for toolchain configuration.
This doc covers conventions and gotchas that tools cannot enforce.

## PEP 758 — `except` Without Parentheses

`pyupgrade --py314` rewrites multi-exception handlers to the Python 3.14 syntax:

```python
# Before (pyupgrade rewrites this automatically)
except (ValueError, TypeError):

# After — correct Python 3.14 syntax (PEP 758)
except ValueError, TypeError:
```

**Do not revert this.** AI assistants commonly flag it as invalid syntax and revert
it to the parenthesised form — that is wrong. The parenthesised form is the
pre-3.14 style; the unparenthesised form is now correct.
See [pyright#10546](https://github.com/microsoft/pyright/issues/10546) for upstream tracking.

## Function and Method Ordering

Private functions and methods must always be defined **after** public ones and prefixed with an underscore:

```python
class MyClass:
    def public_method(self):
        self._helper()

    def _helper(self):  # private — after public, underscore prefix
        ...

def public_function():
    _do_work()

def _do_work():  # private — after public, underscore prefix
    ...
```

This applies to both module-level functions and class methods.

## Module Naming

Avoid generic module or package names like `utils.py`, `helpers.py`, or `services.py`. Instead use specific names that describe what the module or package does:

```
# Bad
my_package/utils.py
my_package/helpers.py
my_package/services.py

# Good — modules
my_package/geocoding.py
my_package/notifications.py
my_package/pdf_export.py

# Good — packages (when functionality is large enough to split)
my_package/geocoding/
my_package/notifications/
my_package/payments/
```

## Caching

Use `cached_property` and `functools.cache` to avoid redundant computation:

- **`@cached_property`** — for instance properties that are expensive to compute. Use `django.utils.functional.cached_property` on Django model/view classes; use `functools.cached_property` elsewhere.
- **`@functools.cache`** — for module-level functions whose result depends only on their arguments (pure functions).

Prefer a cached function over a module-level variable for anything that may be slow to initialise (file I/O, DB queries, network calls) — module-level code runs at import time and slows startup:

```python
import functools

# Bad — runs at import time, slows startup
COUNTRIES = load_countries_from_file()

# Good — deferred until first call, then cached
@functools.cache
def get_countries():
    return load_countries_from_file()
```

## Function Arguments

Use `*` to force keyword-only arguments on functions and methods with multiple parameters:

```python
# Bad — positional, easy to pass in the wrong order
def do_something(name: str, num: int, active: bool = True): ...

# Good — explicit naming required at call site
def do_something(*, name: str, num: int, active: bool = True): ...
```

Only defaults belong on optional parameters; required parameters have no default. The
default value for an optional parameter should be defined **once** — at the outermost
entry point (e.g. `add_arguments` for management commands, the public API for libraries)
— and passed explicitly through internal helpers:

```python
# Bad — default duplicated on every internal function
def _helper(*, timeout: int = 30): ...

# Good — default lives once at the entry point
def handle(self, *, timeout: int, **options): ...
def _helper(self, *, timeout: int): ...
```

If a function accumulates many arguments (especially ones shared across several
functions), consider encapsulating them in a `dataclass`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class DownloadOptions:
    timeout: int
    retries: int
    verify_ssl: bool = True
```

## Imports

- **Absolute imports only** — `absolufy-imports` enforces this; no relative imports.
- **isort** — profile `black`, run automatically by ruff. No manual sorting needed.

## Internationalisation

See `docs/Django.md` for internationalisation conventions (`gettext`, `gettext_lazy`, templates).

## Class Attributes

For class-level constants that are fixed sequences, prefer plain tuples over annotated
`ClassVar` lists. This applies everywhere — Django model `Meta`, form `Meta`, admin classes, and any
other class that declares sequence attributes:

```python
# Bad — annotation adds noise, list is mutable
class Meta:
    ordering: ClassVar[list[str]] = ["-created"]

class MyAdmin(ModelAdmin):
    list_display: ClassVar[list[str]] = ["name", "created"]

# Good — tuple is immutable and needs no annotation
class Meta:
    ordering = ("-created",)

class MyAdmin(ModelAdmin):
    list_display = ("name", "created")
```

Use a tuple unless the framework explicitly requires a mutable list.

## Type Annotations

- Type checking is done by `basedpyright` (`just typecheck`). Configuration is in `pyproject.toml` under `[tool.pyright]`.
- Use typed request/response classes from `http/` — see `docs/Django-Views.md`.
- Migrations and test files are excluded from type checking.
