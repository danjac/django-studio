# Forms

This project uses Django forms for HTML form submissions, with
`form/partials.html` dispatching rendering per widget type and
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
  - [MoneyWidget](#moneywidget)
  - [django-countries LazySelect](#django-countries-lazyselect)

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

Use `{{ field.as_field_group }}` to render a form field with its label, errors, and
help text. The project ships `templates/form/partials.html` which dispatches to a
per-widget `partialdef` based on the field's widget type.

Use the first option that fits:

1. **`{{ form }}`** — all fields in default order via the configured renderer.
2. **`{{ form.title.as_field_group }}`** — explicit field order or subset.

```html
{# All fields, default order #}
{{ form }}

{# Explicit order #}
{{ form.title.as_field_group }}
{{ form.body.as_field_group }}
```

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

`form/partials.html` renders each field inside a DaisyUI `fieldset`:

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Email</legend>
  <input id="id_email" type="email" class="input w-full" ...>
  <ul class="text-sm font-semibold text-error">...</ul>
  <p class="label">Help text</p>
</fieldset>
```

## Widget Type Dispatch

`form/partials.html` dispatches to a `{% partialdef %}` block by lowercasing the
widget's class name via
`{% try_include "form/partials.html#"|add:widget_type "form/partials.html#input" %}`.
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
block to `templates/form/partials.html`. The partial name is the widget's class name,
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

For `ImageField` forms, use a `thumbnailwidget` partial that shows the current image
and an Alpine.js-powered preview of the newly selected file:

```html
{# form/partials.html #}

{% partialdef thumbnailwidget %}
  {% partial label %}
  {% with image=field.form.instance.image %}
    <div
      x-data="{ previewUrl: null }"
      @change="previewUrl = $event.target.files[0] ? URL.createObjectURL($event.target.files[0]) : null"
    >
      {% if image %}
        {% thumbnail image "340x240" crop="center" as im %}
          <img
            src="{{ im.url }}"
            :src="previewUrl ?? '{{ im.url }}'"
            alt="{% translate "Preview" %}"
            width="{{ im.width }}"
            height="{{ im.height }}"
            class="mb-2 rounded-lg"
          />
        {% empty %}
        {% endthumbnail %}
      {% else %}
        <template x-if="previewUrl">
          <img
            :src="previewUrl"
            alt="{% translate "Preview" %}"
            width="340"
            height="240"
            class="mb-2 rounded-lg"
          />
        </template>
      {% endif %}
      {% render_field field class="file-input" %}
    </div>
  {% endwith %}
{% endpartialdef thumbnailwidget %}
```

Replace `field.form.instance.image` with the actual field accessor for your model.
Use `widget_type` to dispatch to this partial automatically, or call
`{% partial thumbnailwidget %}` directly.

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

For forms that accept multiple files, use Alpine.js to manage a local file list with
drag-and-drop, previews, and individual removal. The `DataTransfer` API syncs Alpine's
state back to the native `<input>` so the form submission works normally.

```html
<div
  id="file-upload-zone"
  x-data="{
    files: [],
    previews: {},
    addFiles(event) {
      const incoming = Array.from(event.target?.files ?? event.dataTransfer?.files ?? []);
      this.files = [...this.files, ...incoming];
      incoming.forEach(f => { this.previews = {...this.previews, [f.name]: URL.createObjectURL(f)}; });
      this.syncInput();
    },
    removeFile(file) {
      URL.revokeObjectURL(this.previews[file.name]);
      const p = {...this.previews};
      delete p[file.name];
      this.previews = p;
      this.files = this.files.filter(f => f !== file);
      this.syncInput();
    },
    syncInput() {
      const dt = new DataTransfer();
      this.files.forEach(f => dt.items.add(f));
      this.$refs.fileInput.files = dt.files;
    },
  }"
  @dragover.prevent
  @drop.prevent="addFiles($event)"
>
  <label
    class="block p-8 text-center rounded-lg border-2 border-dashed cursor-pointer border-zinc-300 hover:border-primary-400"
    for="file-input"
  >
    {% heroicon_outline "arrow-up-tray" class="mx-auto size-8 text-zinc-400" aria_hidden="true" %}
    <span class="block mt-2 text-sm text-zinc-500">
      {% translate "Drag files here or click to browse" %}
    </span>
    <input
      id="file-input"
      name="files"
      type="file"
      multiple
      accept="image/*"
      class="sr-only"
      x-ref="fileInput"
      @change="addFiles($event)"
    >
  </label>

  <ul x-show="files.length" class="grid grid-cols-3 gap-3 mt-4">
    <template x-for="(file, index) in files" :key="file.name">
      <li class="overflow-hidden relative rounded-lg border border-zinc-200 dark:border-zinc-700">
        {# djlint:off H006 #}
        <img
          :src="previews[file.name]"
          :alt="'{% translate "Selected file" %} ' + (index + 1)"
          width="300"
          height="200"
          class="object-cover w-full aspect-video"
        >
        {# djlint:on #}
        <button
          type="button"
          class="absolute top-1 right-1 p-1 text-white rounded-full bg-black/50"
          aria-label="{% translate "Remove" %}"
          @click="removeFile(file)"
        >
          {% heroicon_mini "x-mark" class="size-4" aria_hidden="true" %}
        </button>
      </li>
    </template>
  </ul>
</div>
```

Use `multipart=True` on the form wrapper (see [HTMX Form Wrapper](#htmx-form-wrapper)).

**Key points:**

- `syncInput()` uses `DataTransfer` to keep the native `<input>` in sync — without
  this, the form submits an empty file list.
- Call `URL.revokeObjectURL` on remove to prevent memory leaks.
- Previews use `blob:` URLs — apply `@csp_override(settings.SECURE_CSP_UPLOAD)` to
  the view (see [Thumbnail Widget](#thumbnail-widget) for the settings pattern).
- The upload/delete workflow for existing server-side files is project-specific —
  implement via HTMX partial swaps.

### MoneyWidget

[django-money](https://github.com/django-money/django-money) pairs `MoneyField` with
`py-moneyed`. `MoneyWidget` renders an amount input and a currency select side-by-side.
Add a `{% partialdef moneywidget %}` block to `templates/form/partials.html`:

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
