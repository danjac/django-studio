# Forms

This project uses Django forms for HTML form submissions, with
`forms/partials.html` dispatching rendering per widget type and
`django-widget-tweaks` for attribute overrides.

## Contents

- [Form View Pattern](#form-view-pattern)
- [Rendering Fields](#rendering-fields)
- [HTMX Form Wrapper](#htmx-form-wrapper)
- [Field Template Structure](#field-template-structure)
- [Widget Type Dispatch](#widget-type-dispatch)
- [Custom Widget Partials](#custom-widget-partials)
- [Adding Widget Attributes](#adding-widget-attributes)
- [Common Custom Widgets](#common-custom-widgets)
  - [Thumbnail Widget](#thumbnail-widget)
  - [Multiple File Upload](#multiple-file-upload)
  - [Tag Widget](#tag-widget)
  - [MoneyWidget](#moneywidget)
  - [django-countries LazySelect](#django-countries-lazyselect)
- [Alpine Widget JS and class Media](#alpine-widget-js-and-class-media)

## Form View Pattern

Use Django forms for HTML form submissions. The standard pattern uses
`render_partial_response` so that the form partial is returned on both initial
load and on validation failure, with the full page rendered only on first visit:

```python
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from my_package.http.decorators import require_form_methods
from my_package.http.request import AuthenticatedHttpRequest
from my_package.http.response import RenderOrRedirectResponse
from my_package.partials import render_partial_response


@login_required
@require_form_methods
def edit_item(
    request: AuthenticatedHttpRequest, pk: int
) -> RenderOrRedirectResponse:
    item = get_object_or_404(Item, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated.")
            return redirect(item)
    else:
        form = ItemForm(instance=item)
    return render_partial_response(
        request,
        "items/edit.html",
        {"form": form, "item": item},
        target="item-form",   # matches hx-target="#item-form" in the template
        partial="form",       # renders "items/edit.html#form" on HTMX requests
    )
```

The template defines a `{% partialdef form inline %}` block containing the form
markup. The `inline` keyword renders the block in place on a full-page load; on an
HTMX POST with a validation error, `render_partial_response` returns only that
partial so the form re-renders in place with error messages. On success, redirect
(Post/Redirect/Get) as normal.

Key rules:

- Always decorate with `@require_form_methods` (GET/HEAD/POST).
- Always redirect on success — never re-render after a valid POST.
- On invalid POST, return `render_partial_response` (not a plain `TemplateResponse`)
  so HTMX swaps the re-rendered form with inline error messages.

## Rendering Fields

`templates/forms/partials.html` dispatches each field to a per-widget `partialdef`
based on the field's widget type, rendering label, input, errors, and help text.

Use the first level that fits:

**Level 1 — default rendering, default order:**

```html
{{ form }}
```

**Level 2 — custom field order or subset:**

```html
{{ form.title.as_field_group }}
{{ form.body.as_field_group }}
```

**Level 3 — custom attributes on one field, default rendering for the rest:**

Use `django-widget-tweaks` to override attributes on a single field. Wrap it in
the `fieldset` fragment to keep the DaisyUI structure, errors, and help text:

```html
{% load widget_tweaks %}
{{ form.title.as_field_group }}
{% fragment "forms/partials.html#fieldset" with field=form.body %}
  {% partial label %}
  {% render_field form.body class="textarea w-full" rows="8" %}
{% endfragment %}
```

For anything beyond attribute tweaks — custom layout, composite inputs, or
reusable widget behaviour — add a `{% partialdef %}` block to
`templates/forms/partials.html` or write a custom Django widget class.
See [Custom Widget Partials](#custom-widget-partials) and
[Common Custom Widgets](#common-custom-widgets).

## HTMX Form Wrapper

`form.html` renders a `<form>` element. Include it via `{% fragment %}`, passing the
form fields as `{{ content }}`:

```html
{% fragment "form.html" htmx=True target="my-form" %}
  {{ form.title.as_field_group }}
  {{ form.body.as_field_group }}
  {% fragment "form.html#buttons" %}
    <button type="submit" class="btn btn-primary">Save</button>
  {% endfragment %}
{% endfragment %}
```

Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `action` | `request.path` | Form action URL |
| `method` | `"post"` | HTTP method |
| `htmx` | — | Enable HTMX attributes |
| `hx_swap` | `"outerHTML"` | HTMX swap strategy |
| `hx_target` | `"this"` | HTMX target selector |
| `multipart` | — | Enable file upload encoding |

For file upload forms, pass `multipart=True`:

```html
{% fragment "form.html" htmx=True target="my-form" multipart=True %}
  ...
{% endfragment %}
```

## Field Template Structure

`forms/partials.html` renders each field inside a DaisyUI `fieldset`. The
following sub-partials are available for use in custom widget partials or
level-3 rendering (see [Rendering Fields](#rendering-fields)):

| Partial | Renders |
|---------|---------|
| `{% partial label %}` | `<legend>` with label text, optional marker, error colour |
| `{% partial errors %}` | `<ul>` of validation errors |
| `{% partial help_text %}` | `<p>` of help text |
| `{% fragment "forms/partials.html#fieldset" with field=... %}` | Full `<fieldset>` wrapper — `{{ content }}` + errors + help text |

The rendered output for a standard field:

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Email</legend>
  <input id="id_email" type="email" class="input w-full" ...>
  <ul class="text-sm font-semibold text-error">...</ul>
  <p class="label">Help text</p>
</fieldset>
```

## Widget Type Dispatch

`forms/partials.html` dispatches to a `{% partialdef %}` block by lowercasing the
widget's class name via
`{% try_include "forms/partials.html#"|add:widget_type "forms/partials.html#input" %}`.
If no matching partial exists, it falls back to the `input` partial. Built-in widgets
with explicit partials:

| Widget | Partial | DaisyUI class |
|--------|---------|---------------|
| `Textarea` | `textarea` | `textarea` |
| `CheckboxInput` | `checkboxinput` | `checkbox` |
| `CheckboxSelectMultiple` | `checkboxselectmultiple` | — |
| `PasswordInput` | `passwordinput` | `input` |
| `Select` | `select` | `select` |
| `SelectMultiple` | `selectmultiple` | `select` |
| `DateInput` | `dateinput` | `input` (type="date") |
| `DateTimeInput` | `datetimeinput` | `input` (type="datetime-local") |

All other widgets (e.g. `TextInput`, `EmailInput`, `FileInput`, `URLInput`) fall back
to the `input` partial automatically.

## Custom Widget Partials

If you add a custom widget with non-default rendering, add a matching `{% partialdef %}`
block to `templates/forms/partials.html`. The partial name is the widget's class name,
lowercased. Use `{% partial label %}`, `{% partial errors %}`, and
`{% partial help_text %}` to keep rendering consistent. Widgets that render identically
to a plain `<input>` need no partial — the fallback handles them.

## Adding Widget Attributes

Use `django-widget-tweaks` to add classes or attributes from the template:

```html
{% load widget_tweaks %}
{% render_field form.email class="input w-full" placeholder="you@example.com" %}
{% render_field form.bio class="textarea w-full" rows="4" %}
```

## Common Custom Widgets

### Thumbnail Widget

`ThumbnailWidget` is a `FileInput` subclass that renders a sorl thumbnail preview
of the current image and an Alpine.js-powered preview of a newly selected file.
Create the widget class in your project:

```python
from django.forms.widgets import FileInput


class ThumbnailWidget(FileInput):
    """File input widget that renders a sorl thumbnail preview in forms/partials.html."""

    class Media:
        js = ("widgets/thumbnail.js",)
```

Use it via `Meta.widgets`:

```python
class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ("title", "description", "image")
        widgets: ClassVar[dict] = {"image": ThumbnailWidget}
```

Add the `thumbnailwidget` partialdef to `forms/partials.html`:

```html
{# Thumbnail widget — ImageField with sorl preview + Alpine new-file preview #}
{% partialdef thumbnailwidget %}
  {% load thumbnail %}
  {% partial label %}
  {% with image=field.field.widget.image %}
    {% if image %}
      {% thumbnail image "340x240" crop="center" as im %}
        <div x-data="thumbnailWidget()">
          <img
            :src="previewUrl ?? '{{ im.url }}'"
            alt="{% translate "Preview" %}"
            width="{{ im.width }}"
            height="{{ im.height }}"
            class="mb-2 rounded-lg"
          />
          {% render_field field class="file-input" "@change"="onFileChange" %}
        </div>
      {% endthumbnail %}
    {% else %}
      <div x-data="thumbnailWidget()">
        <template x-if="previewUrl">
          <img :src="previewUrl" alt="{% translate "Preview" %}" width="340" height="240" class="mb-2 rounded-lg" />
        </template>
        {% render_field field class="file-input" "@change"="onFileChange" %}
      </div>
    {% endif %}
  {% endwith %}
{% endpartialdef thumbnailwidget %}
```

Create `static/widgets/thumbnail.js`:

```js
document.addEventListener('alpine:init', () => {
  Alpine.data('thumbnailWidget', () => ({
    previewUrl: null,

    onFileChange(event) {
      const file = event.target.files[0];
      this.previewUrl = file ? URL.createObjectURL(file) : null;
    },
  }));
});
```

Then render normally:

```html
{{ form.image.as_field_group }}
```

**CSP note:** `URL.createObjectURL` generates a `blob:` URL. Views that serve upload
forms must use `@csp_override(settings.SECURE_CSP_UPLOAD)`. Define the upload CSP
variant in `config/settings.py`:

```python
# config/settings.py
from django.utils.csp import CSP

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:"],
    # ... your full policy
}

# Extends SECURE_CSP to allow blob: URLs for file upload previews.
SECURE_CSP_UPLOAD = {**SECURE_CSP, "img-src": [CSP.SELF, "data:", "blob:"]}
```

```python
# views.py
from django.conf import settings
from django.views.decorators.csp import csp_override

@csp_override(settings.SECURE_CSP_UPLOAD)
def my_upload_view(request):
    ...
```

### Multiple File Upload

Use the `fileUpload` Alpine.js component from `docs/ui-recipes.md#multiple-file-upload`
for multi-file pickers with drag-and-drop, instant previews, and per-file removal.
The `DataTransfer` API syncs Alpine's file list back to the native `<input>` so the
Django form submission works normally.

- Use `multipart=True` on the form wrapper (see [HTMX Form Wrapper](#htmx-form-wrapper)).
- Previews use `blob:` URLs — apply `@csp_override(settings.SECURE_CSP_UPLOAD)` to
  the view (see [Thumbnail Widget](#thumbnail-widget) for the settings pattern).
- The upload/delete workflow for existing server-side files is project-specific —
  implement via HTMX partial swaps.

### Tag Widget

`TagWidget` is a `TextInput` subclass that renders an Alpine.js pill/chip tag editor.
Tags are stored as a space-separated string in the database; the widget splits and
joins on spaces. Create the widget class in `widgets.py`:

```python
from django.forms.widgets import TextInput


class TagWidget(TextInput):
    """Text input that renders as an Alpine.js pill/chip tag editor in forms/partials.html."""

    class Media:
        js = ("widgets/tags.js",)
```

Add the `tagwidget` partialdef to `templates/forms/partials.html`:

```html
{# Tag chip widget — pill editor backed by a hidden text input #}
{% partialdef tagwidget %}
  {% partial label %}
  <div
    x-data="tagWidget('{{ field.value|default:''|escapejs }}')"
    class="space-y-2"
  >
    <div class="flex flex-wrap gap-2 items-center py-2 !h-auto input"
         @click="$refs.tagInput.focus()">
      <template x-for="tag in tags" :key="tag">
        <span class="gap-1 badge badge-outline">
          <span x-text="tag"></span>
          <button
            type="button"
            @click.stop="removeTag(tag)"
            aria-label="{% translate "Remove tag" %}"
          >
            {% heroicon_mini "x-mark" class="size-3" aria_hidden="true" %}
          </button>
        </span>
      </template>
      <input
        type="text"
        x-ref="tagInput"
        @input="onInput"
        @keydown.enter.prevent="addTag()"
        @keydown.backspace="$refs.tagInput.value === '' && removeLastTag()"
        placeholder="{% translate "Add tag…" %}"
        class="flex-1 text-sm bg-transparent outline-none min-w-20"
      >
    </div>
    <input type="hidden" name="{{ field.html_name }}" :value="tags.join(' ')">
  </div>
{% endpartialdef tagwidget %}
```

Create `static/widgets/tags.js`:

```js
document.addEventListener('alpine:init', () => {
  Alpine.data('tagWidget', (initial) => ({
    tags: initial ? initial.trim().split(/\s+/) : [],

    onInput(event) {
      const value = event.target.value;
      if (!value.endsWith(' ')) return;
      const tag = value.trim().toLowerCase();
      event.target.value = '';
      if (tag && !this.tags.includes(tag)) {
        this.tags = [...this.tags, tag];
      }
    },

    addTag() {
      const tag = this.$refs.tagInput.value.trim().toLowerCase();
      this.$refs.tagInput.value = '';
      if (tag && !this.tags.includes(tag)) {
        this.tags = [...this.tags, tag];
      }
    },

    removeTag(tag) {
      this.tags = this.tags.filter((t) => t !== tag);
    },

    removeLastTag() {
      if (this.tags.length > 0) {
        this.tags = this.tags.slice(0, -1);
      }
    },
  }));
});
```

The hidden input uses `:value="tags.join(' ')"` (reactive binding) so Alpine always
keeps it in sync with the displayed chips.

Then render normally:

```html
{{ form.tags.as_field_group }}
```

### MoneyWidget

[django-money](https://github.com/django-money/django-money) pairs `MoneyField` with
`py-moneyed`. `MoneyWidget` renders an amount input and a currency select side-by-side.
Add a `{% partialdef moneywidget %}` block to `templates/forms/partials.html`:

```html
{# django-money MoneyWidget (amount + currency select) #}
{% partialdef moneywidget %}
  {% partial label %}
  <div class="flex flex-col gap-2 sm:flex-row sm:items-stretch">
    {% render_field field %}
  </div>
{% endpartialdef moneywidget %}
```

### django-countries LazySelect

[django-countries](https://github.com/SmileyChris/django-countries) provides a
`CountryField` with a lazy-loading select widget (`LazySelect`). The widget renders
identically to a standard `<select>`, so no custom partial is needed — the existing
`select` partial handles it:

```html
{# django-countries LazySelect (same as a regular select) #}
{% partialdef lazyselect %}{% partial select %}{% endpartialdef %}
```

## Alpine Widget JS and class Media

Any custom widget that uses an Alpine.js component **must** load its JavaScript via
`class Media`, not as an inline `<script>` in the partial template:

```python
class ThumbnailWidget(FileInput):
    class Media:
        js = ("widgets/thumbnail.js",)


class TagWidget(TextInput):
    class Media:
        js = ("widgets/tags.js",)
```

The form template renders `{{ form.media }}` in `{% block scripts %}`, which collects
and deduplicates JS from every widget on the form automatically. Place static files
under `static/widgets/`.

**Do not** inline Alpine component definitions in `forms/partials.html`. Inline scripts
prevent browser caching, run before Alpine initialises, and make the widget
non-reusable across forms.
