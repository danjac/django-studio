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
    {% include "form/field.html" with field=field %}
  {% endfor %}
  <button type="submit" class="btn btn-primary">Save</button>
{% endfragment %}
```

### HTMX Form

```html
{% fragment "form.html" action=url htmx=True hx_target="#my-form" %}
  {% for field in form %}
    {% include "form/field.html" with field=field %}
  {% endfor %}
  <button type="submit" class="btn btn-primary" hx-disabled-elt="this">Save</button>
{% endfragment %}
```

## Field Template

`form/field.html` renders a single form field with label, input widget, errors, and help text. It dispatches on the widget type (e.g. `textinput`, `checkboxinput`, `passwordinput`).

### Usage

```html
{% for field in form %}
  {% include "form/field.html" with field=field %}
{% endfor %}
```

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

| Widget | Partial | Notes |
|--------|---------|-------|
| `TextInput` | `textinput` | Standard text field |
| `URLInput` | `urlinput` | Same as textinput |
| `FileInput` | `fileinput` | Same as textinput |
| `CheckboxInput` | `checkboxinput` | Label to the right of the checkbox |
| `PasswordInput` | `passwordinput` | Show/hide toggle via AlpineJS |

## CSS Classes

| Class | Element |
|-------|---------|
| `form-input` | `<input>`, single-line text |
| `form-textarea` | `<textarea>` |
| `form-select` | `<select>` |
| `form-multiselect` | `<select multiple>` |
| `form-checkbox` | `<input type="checkbox">` |

All form inputs share: rounded corners, surface background, indigo focus ring, rose error state.

## Adding Widget Attributes

Use `django-widget-tweaks` to add classes or attributes from the template:

```html
{% load widget_tweaks %}
{% render_field form.email class="form-input w-full" placeholder="you@example.com" %}
{% render_field form.bio class="form-textarea" rows="4" %}
```

## Validation Error Display

The `form/field.html` template applies `has-errors` to the fieldset and renders an error list automatically. In views, re-render the form on invalid POST:

```python
def my_view(request):
    form = MyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saved.")
        return redirect("index")
    return TemplateResponse(request, "my_page.html", {"form": form})
```

## Accessibility

- Every field has an associated `<label>` via `field.id_for_label` — never omit it.
- Error messages are linked to the input via `aria-describedby` automatically.
- The `form-control.has-errors` class changes input border to rose — do not rely on color alone; the error list provides the text.
