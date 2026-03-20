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

## Imports

- **Absolute imports only** — `absolufy-imports` enforces this; no relative imports.
- **isort** — profile `black`, run automatically by ruff. No manual sorting needed.

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

## Type Annotations

- Type checking is done by `basedpyright` (`just typecheck`). Configuration is in `pyproject.toml` under `[tool.pyright]`.
- Use typed request/response classes from `http/` — see `docs/Views.md`.
- Migrations and test files are excluded from type checking.
