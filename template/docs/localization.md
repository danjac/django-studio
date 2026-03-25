# Localization

This project ships with Django's i18n framework enabled. This document covers the
i18n workflow, the language switcher component, and translation conventions for
models and forms.

---

## Workflow

### Extracting strings

Run `makemessages` to scan the project for translatable strings and update (or create)
the `.po` catalogue for a given locale:

```bash
just dj makemessages -l <locale> --no-wrap
```

Common locale codes: `fr`, `fr_CA`, `de`, `es`, `nl`, `pt`, `it`, `pl`, `sv`, `da`,
`fi`, `nb`.

This creates or updates `locale/<locale>/LC_MESSAGES/django.po`. Run it whenever you
add or change translatable strings in templates, views, or models.

### Compiling messages

After editing the `.po` file, compile it to a binary `.mo` catalogue:

```bash
just dj compilemessages
```

**Production:** `compilemessages` must be run inside the Dockerfile so the compiled
`.mo` files are available at runtime. The template Dockerfile already includes this
step — do not remove it.

---

## Language switcher

Use Django's built-in `set_language` view with a POST form and a `next` redirect.
Use `language_info_list` (available in the template context when
`django.template.context_processors.i18n` is enabled) to display native language names
(`lang.name_local`).

### Implementation

Use the dropdown component from `docs/ui-recipes.md#dropdown-menu` with the
hidden-form pattern. Render language options using `language_info_list` from the `i18n`
context processor — `lang.name_local` gives the native language name:

```html
{% for lang in language_info_list %}
  <li role="menuitem">
    <button type="submit" form="set-language-{{ lang.code }}" class="w-full">
      {{ lang.name_local }}
    </button>
  </li>
{% endfor %}
```

---

## Marking strings for translation

### Python

```python
from django.utils.translation import gettext as _, gettext_lazy as _l, ngettext

# Module-level (model fields, form labels): use gettext_lazy — evaluated lazily
class MyForm(forms.Form):
    title = forms.CharField(label=_l("Title"))

# Function/method body (views, signals): use gettext
def my_view(request):
    messages.success(request, _("Changes saved."))

# Plurals
msg = ngettext("%(n)s item", "%(n)s items", count) % {"n": count}
```

### Templates

Use `{% translate %}` (Django 4.0+), not the legacy `{% trans %}`:

```html
{% load i18n %}
<h1>{% translate "Welcome" %}</h1>
{% blocktranslate with name=user.name %}Hello, {{ name }}.{% endblocktranslate %}
```

You can use `_("string")` directly in tag arguments:

```html
{% include "header.html" with title=_("Dashboard") %}
```

---

## Models and forms

### Models

All model fields with a `verbose_name` must use `gettext_lazy` so the string is
translated at the point of use (not at import time):

```python
from django.utils.translation import gettext_lazy as _

class Article(models.Model):
    title = models.CharField(_("title"), max_length=255)
    body = models.TextField(_("body"))
```

### Forms

Form field labels defined explicitly must also use `gettext_lazy`:

```python
from django import forms
from django.utils.translation import gettext_lazy as _

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["title", "body"]
        labels = {
            "title": _("Article title"),
        }
```

Labels inferred from the model's `verbose_name` are already lazy — no extra wrapping
needed.

---

## Dates, numbers, and locale-aware formatting

Django's formatting system renders dates, times, and numbers according to the
active locale when `USE_L10N = True`. This is enabled by default.

`FORMAT_MODULE_PATH = ["config.formats"]` (already set in `config/settings.py`)
tells Django to look for locale-specific overrides in `config/formats/<locale>/formats.py`
before falling back to Django's built-in locale formats.

### Format file

Each locale can have a `config/formats/<locale>/formats.py` that overrides the
built-in defaults. The `en` locale already ships one:

```
config/formats/
    en/
        __init__.py
        formats.py        # DATE_FORMAT = "j M Y"
```

To add a new locale (e.g. `fr`):

```bash
mkdir -p config/formats/fr
touch config/formats/fr/__init__.py
```

Then create `config/formats/fr/formats.py` with any overrides:

```python
# Override Django's built-in French formats as needed.
# Available variables (see django/conf/locale/<locale>/formats.py for defaults):

DATE_FORMAT = "j F Y"          # 25 mars 2026
DATETIME_FORMAT = "j F Y H:i"
TIME_FORMAT = "H:i"
SHORT_DATE_FORMAT = "d/m/Y"

DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "\xa0"    # non-breaking space
NUMBER_GROUPING = 3
```

Leave out any variable you want Django's built-in locale default to apply.

### Templates

Use `{{ value|localize }}` to format a value using the active locale:

```html
{% load l10n %}
<p>{{ article.published_at|localize }}</p>
<p>{{ price|localize }}</p>
```

Wrap a block to force locale-aware output on/off:

```html
{% load l10n %}
{% localize on %}
  {{ price }}
{% endlocalize %}
```

### Python

```python
from django.utils import formats

formats.date_format(value, "DATE_FORMAT")       # uses active locale's DATE_FORMAT
formats.number_format(value, decimal_pos=2)     # locale-aware decimal/grouping
formats.localize(value)                         # auto-detects type
```

---

## dj-translate skill

Use `/dj-translate <locale>` to extract, translate, and compile a message catalogue in
one step. The skill handles `makemessages`, translates empty/fuzzy entries via Claude,
and runs `compilemessages`. See `docs/localization.md` (this file) for background on
the full i18n workflow.
