# Forms

Templates: `templates/form.html`, `templates/form/field.html`
CSS source: `tailwind/forms.css`

## Form Wrapper

`form.html` renders a `<form>` element that works for both standard and HTMX submissions.

### Context Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `content` | _(required)_ | Block content rendered inside the form |
| `action` | `request.path` | Form action URL |
| `method` | `"post"` | HTTP method |
| `class` | `"space-y-6"` | CSS classes on the form element |
| `htmx` | `False` | Enable HTMX attributes |
| `hx_swap` | `"outerHTML"` | HTMX swap mode (when `htmx=True`) |
| `hx_target` | `"this"` | HTMX target selector (when `htmx=True`) |

### Standard Form

```html
{% fragment "form.html" %}
  {% for field in form %}
    {{ field.as_field_group }}
  {% endfor %}
  <button type="submit" class="btn btn-primary">Save</button>
{% endfragment %}
```

### HTMX Form

```html
{% fragment "form.html" action=url htmx=True hx_target="#my-form" %}
  {% for field in form %}
    {{ field.as_field_group }}
  {% endfor %}
  <button type="submit" class="btn btn-primary" hx-disabled-elt="this">Save</button>
{% endfragment %}
```

## Field Template

`form/field.html` renders a single form field with label, input widget, errors, and help text. It dispatches on the widget type (e.g. `textinput`, `checkboxinput`, `passwordinput`).

### Usage

Use Django's `as_field_group` method rather than including `form/field.html` directly. This is the preferred approach - `as_field_group` delegates to `form/field.html` internally, so all label, error, and help-text handling is identical.

```html
{# Render all fields in form order #}
{% for field in form %}
  {{ field.as_field_group }}
{% endfor %}
```

### Field Ordering

Prefer Django 5+'s `as_field_group` for fine-grained control over which fields appear and in what order, rather than rendering `{{ form }}` wholesale or always iterating every field:

```html
{# Render specific fields in a chosen order #}
{{ form.title.as_field_group }}
{{ form.body.as_field_group }}
{{ form.published.as_field_group }}
```

`as_field_group` delegates to `django/forms/field.html`, which in turn renders via `form/field.html`, so all label, error, and help-text handling is identical to the loop pattern.

### Rendered Structure

Each field outputs a `<fieldset>` with the `form-control` class:

```html
<fieldset class="form-control space-y-3 [has-errors]">
  <label for="id_email" class="block font-semibold ...">Email</label>
  <input id="id_email" type="email" class="form-input" ...>
  <!-- Error messages if any -->
  <ul class="text-rose-600 ...">...</ul>
  <!-- Help text if any -->
  <div class="text-sm text-zinc-500 ...">...</div>
</fieldset>
```

### Widget Types and Their Partials

`form/field.html` dispatches to a `{% partialdef %}` block by lowercasing the
widget's class name:

```html
{% with widget_type=field|widget_type %}
  {% include "form/field.html#"|add:widget_type %}
{% endwith %}
```

Built-in widgets and their partials:

| Widget | Partial name |
|--------|-------------|
| `TextInput` | `textinput` |
| `EmailInput` | `emailinput` |
| `URLInput` | `urlinput` |
| `FileInput` | `fileinput` |
| `ClearableFileInput` | `clearablefileinput` |
| `DateInput` | `dateinput` |
| `DateTimeInput` | `datetimeinput` |
| `Textarea` | `textarea` |
| `CheckboxInput` | `checkboxinput` |
| `CheckboxSelectMultiple` | `checkboxselectmultiple` |
| `PasswordInput` | `passwordinput` |
| `Select` | `select` |
| `SelectMultiple` | `selectmultiple` |

### Custom Widget Partials

If you add a custom widget — from a third-party package or from within this
project — **you must add a matching `{% partialdef %}` block to
`templates/form/field.html`**. Without it the field renders nothing, with no
error.

The partial name is the widget's class name, lowercased.

Steps for any custom widget:

1. Find the widget class name: check the field's `widget` attribute or the
   package source (`field.field.widget.__class__.__name__`).
2. Add `{% partialdef <classname_lowercased> %}...{% endpartialdef %}` to
   `templates/form/field.html`.
3. Use `{% partial label %}`, `{% partial errors %}`, and `{% partial help_text %}`
   to keep label/error/help-text rendering consistent with built-in widgets.
4. Test by rendering the field with `{{ field.as_field_group }}` and verifying
   the output is not empty.

#### Example: `django-money` `MoneyWidget`

`MoneyWidget` is a `MultiWidget` that combines an amount `TextInput` and a
currency `Select`. The partial and CSS are pre-built in the template:

```html
{# templates/form/field.html — already present #}
{% partialdef moneywidget %}
  {% partial label %}
  <div class="money-widget">
    {% render_field field %}
  </div>
{% endpartialdef %}
```

The `.money-widget` class in `tailwind/forms.css` stacks the two sub-widgets
vertically on mobile and side-by-side on `sm+`, giving both the same styling as
`form-input`/`form-select`. No additional configuration is needed beyond
installing `django-money` and using `MoneyField` in the model.

## CSS Classes

| Class | Element |
|-------|---------|
| `form-input` | `<input>`, single-line text |
| `form-textarea` | `<textarea>` |
| `form-select` | `<select>` |
| `form-multiselect` | `<select multiple>` |
| `form-checkbox` | `<input type="checkbox">` |

All form inputs share: rounded corners, surface background, `primary` focus ring, `danger` error state.

## Adding Widget Attributes

Use `django-widget-tweaks` to add classes or attributes from the template:

```html
{% load widget_tweaks %}
{% render_field form.email class="form-input w-full" placeholder="you@example.com" %}
{% render_field form.bio class="form-textarea" rows="4" %}
```

## Accessibility

- Every field has an associated `<label>` via `field.id_for_label` - never omit it.
- Error messages are linked to the input via `aria-describedby` automatically.
- The `form-control.has-errors` class changes input border to rose - do not rely on color alone; the error list provides the text.
