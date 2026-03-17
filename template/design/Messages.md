# Messages / Alerts

Template: `templates/messages.html`
CSS source: `tailwind/messages.css`

## How It Works

The Django messages framework is rendered via `messages.html`, which is included in `base.html`. Messages appear as a fixed toast stack in the bottom-right corner and auto-dismiss after 4 seconds using AlpineJS.

```html
{% if messages %}
  {% include "messages.html" %}
{% endif %}
```

## CSS Classes by Tag

The CSS class `message-{{ message.tags }}` is set automatically from the Django message level:

| Django level | Tags string | CSS class | Token |
|-------------|-------------|-----------|-------|
| `messages.DEBUG` | `debug` | `message-debug` | _(unstyled)_ |
| `messages.INFO` | `info` | `message-info` | `--color-info-*` (default: sky) |
| `messages.SUCCESS` | `success` | `message-success` | `--color-success-*` (default: emerald) |
| `messages.WARNING` | `warning` | `message-warning` | `--color-warning-*` (default: amber) |
| `messages.ERROR` | `error` | `message-error` | `--color-error-*` (default: rose) |

To restyle all message toasts at once, override the semantic tokens in `tailwind/theme.css`:

```css
--color-success-400: var(--color-teal-400);
--color-success-600: var(--color-teal-600);
```

## Usage in Views

```python
from django.contrib import messages

def my_view(request):
    messages.success(request, "Profile saved.")
    messages.error(request, "Something went wrong.")
    messages.warning(request, "Your session will expire soon.")
    return redirect("index")
```

## HTMX Out-of-Band Swap

For HTMX requests that don't do a full page reload, re-render the messages partial as an out-of-band swap:

```python
# views.py
from django_htmx.http import HttpResponseClientRefresh
from django.template.response import TemplateResponse

def my_htmx_view(request):
    messages.success(request, "Saved.")
    return TemplateResponse(request, "my_partial.html", {
        "hx_oob": True,  # signals messages.html to add hx-swap-oob="true"
    })
```

```html
<!-- my_partial.html -->
{% include "messages.html" with hx_oob=True %}
<!-- ... rest of your partial ... -->
```

The `hx-swap-oob="true"` attribute on `#messages` tells HTMX to update the toast container from any response.

## Template Source

```html
<div
  id="messages"
  class="fixed inset-x-0 bottom-4 z-50 flex justify-center md:justify-end md:pr-4"
  {% if hx_oob %}hx-swap-oob="true"{% endif %}
>
  {% if messages %}
    <ul class="flex flex-col items-center gap-2 md:items-end">
      {% for message in messages %}
        <li
          class="message-{{ message.tags }} flex flex-wrap items-center justify-center rounded-xl px-4 py-3 text-center font-semibold shadow-lg"
          role="alert"
          x-data="{ show: true }"
          x-show="show"
          x-init="setTimeout(() => show = false, 4000)"
          x-transition:enter="transition ease-out duration-200"
          x-transition:enter-start="translate-y-2 opacity-0"
          x-transition:enter-end="translate-y-0 opacity-100"
          x-transition:leave="transition ease-in duration-300"
          x-transition:leave-start="translate-y-0 opacity-100"
          x-transition:leave-end="translate-y-2 opacity-0"
        >{{ message.message }}</li>
      {% endfor %}
    </ul>
  {% endif %}
</div>
```
