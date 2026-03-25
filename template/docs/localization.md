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

Use the dropdown component from `docs/ui-recipes.md#dropdown-menu`. That doc covers the
full language-switcher example, the hidden-form pattern (required to avoid Alpine
swallowing form submits), and the `hx-disable="true"` attribute needed to prevent HTMX
intercepting the full-page POST.

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

## dj-translate skill

Use `/dj-translate <locale>` to extract, translate, and compile a message catalogue in
one step. The skill handles `makemessages`, translates empty/fuzzy entries via Claude,
and runs `compilemessages`. See `docs/localization.md` (this file) for background on
the full i18n workflow.
