# Buttons

CSS source: `tailwind/buttons.css`

## Variants

| Class | Use case |
|-------|----------|
| `btn btn-primary` | Primary action (indigo) |
| `btn btn-secondary` | Secondary / neutral action (violet) |
| `btn btn-danger` | Destructive action (rose) |
| `btn btn-primary btn-outline` | Outlined primary |
| `btn btn-secondary btn-outline` | Outlined neutral |
| `btn btn-danger btn-outline` | Outlined destructive |

All buttons require **both** the base `btn` class and a variant class.

## Usage

```html
<!-- Primary action -->
<button type="submit" class="btn btn-primary">Save changes</button>

<!-- Secondary action -->
<a href="{% url 'index' %}" class="btn btn-secondary">Cancel</a>

<!-- Destructive action -->
<button type="submit" class="btn btn-danger">Delete account</button>

<!-- Outlined variants -->
<button type="button" class="btn btn-primary btn-outline">Export</button>
<button type="button" class="btn btn-danger btn-outline">Remove</button>
```

## With Icons

The `.btn` class automatically spaces an `svg` child to the left:

```html
{% load heroicons %}
<button type="submit" class="btn btn-primary">
  {% heroicon_mini "check" class="size-4" aria-hidden="true" %}
  Save
</button>
```

## In Forms

Use `hx-disabled-elt="this"` to disable the button during HTMX requests:

```html
<button
  type="submit"
  class="btn btn-primary"
  hx-disabled-elt="this"
  hx-indicator="this"
>
  Save
</button>
```

The `.btn[disabled]` style applies automatically when the element is disabled.

## Accessibility

- Use `<button type="button">` for non-submit actions to prevent accidental form submission.
- Always provide a text label or `aria-label` - icon-only buttons need `aria-label`.
- For destructive actions, consider a confirmation step (modal or `confirm()`) before submitting.

```html
<!-- Icon-only button needs aria-label -->
<button type="button" class="btn btn-danger" aria-label="Delete item">
  {% heroicon_mini "trash" class="size-4" aria-hidden="true" %}
</button>
```
