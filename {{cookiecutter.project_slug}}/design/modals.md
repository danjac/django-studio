# Modals

Template: `templates/modal.html`

## Overview

`modal.html` is an accessible dialog powered by AlpineJS. It requires a parent element with an `open` boolean in its Alpine scope, and the `@alpinejs/focus` plugin for keyboard focus trapping.

## Requirements

### Focus Plugin

Download and add the Alpine Focus plugin to your static vendor directory:

```html
{# In default_base.html, after alpine.min.js: #}
<script src="{% static 'vendor/alpine-focus-3.15.2.min.js' %}" defer></script>
```

Without this plugin, `x-trap` silently does nothing — the modal will open and close correctly but focus will not be trapped, which breaks keyboard accessibility.

## Context Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `modal_id` | yes | Unique `id` for the `<dialog>` element; also prefixes `aria-labelledby` |
| `modal_title` | yes | Visible heading inside the dialog |
| `content` | yes | Dialog body HTML, passed via `{% fragment %}` |

## Usage

### Confirmation Dialog

```html
<div x-data="{ open: false }">
  <button type="button" class="btn btn-danger" @click="open = true">
    Delete account
  </button>

  {% fragment "modal.html" modal_id="confirm-delete" modal_title="Delete your account?" %}
    <p class="text-zinc-600 dark:text-zinc-400">
      This action is permanent and cannot be undone.
    </p>
    <div class="mt-6 flex justify-end gap-3">
      <button type="button" class="btn btn-secondary" @click="open = false">
        Cancel
      </button>
      <form method="post" action="{% url 'users:delete' %}">
        {% csrf_token %}
        <button type="submit" class="btn btn-danger">Delete account</button>
      </form>
    </div>
  {% endfragment %}
</div>
```

### Form in a Modal

```html
<div x-data="{ open: false }">
  <button type="button" class="btn btn-primary" @click="open = true">
    Edit profile
  </button>

  {% fragment "modal.html" modal_id="edit-profile" modal_title="Edit profile" %}
    <form
      method="post"
      action="{% url 'users:update' %}"
      hx-post="{% url 'users:update' %}"
      hx-target="#edit-profile"
      hx-swap="outerHTML"
    >
      {% csrf_token %}
      {% for field in form %}
        {% include "form/field.html" with field=field %}
      {% endfor %}
      <div class="mt-6 flex justify-end gap-3">
        <button type="button" class="btn btn-secondary" @click="open = false">
          Cancel
        </button>
        <button type="submit" class="btn btn-primary" hx-disabled-elt="this">
          Save
        </button>
      </div>
    </form>
  {% endfragment %}
</div>
```

After a successful HTMX save, close the modal from the server response:

```html
{# In the HTMX success partial: #}
<div id="edit-profile" hx-swap-oob="true">
  {# Empty swap removes modal content; set open=false via Alpine event #}
</div>
<script>
  document.getElementById('edit-profile').dispatchEvent(new CustomEvent('close-modal'));
</script>
```

Or simpler: redirect and let HTMX handle the navigation.

## Keyboard Behaviour

| Key | Action |
|-----|--------|
| `Escape` | Closes the dialog |
| `Tab` / `Shift+Tab` | Cycles focus within the dialog (via `x-trap`) |
| Click backdrop | Closes the dialog |

## Multiple Modals on One Page

Each modal needs its own `x-data="{ open: false }"` scope. Do not share a single `open` variable across multiple modals:

```html
{# Correct — separate scopes #}
<div x-data="{ open: false }">
  <button @click="open = true">Edit</button>
  {% fragment "modal.html" modal_id="edit-modal" modal_title="Edit" %}...{% endfragment %}
</div>

<div x-data="{ open: false }">
  <button @click="open = true">Delete</button>
  {% fragment "modal.html" modal_id="delete-modal" modal_title="Delete" %}...{% endfragment %}
</div>
```

## Sizing

The default width is `max-w-md` (28rem). Override by passing a class via context — or copy the template and adjust `max-w-*` for wider dialogs (e.g. `max-w-2xl` for forms with many fields).

## Accessibility Checklist

- `role="dialog"` and `aria-modal="true"` are set automatically.
- `aria-labelledby` points to `{{ modal_id }}-title` — always provide `modal_title`.
- Focus is trapped inside the dialog while open (`x-trap.inert.noscroll`).
- `Escape` closes the dialog.
- The close button has `aria-label="Close dialog"`.
- The backdrop overlay has `aria-hidden="true"` so it's invisible to screen readers.
