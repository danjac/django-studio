# Layout

## Base Templates

| Template | Purpose |
|----------|---------|
| `default_base.html` | Full HTML page: head, HTMX indicator, messages, navbar, main content |
| `base.html` | Extends `default_base.html` - entry point for page templates |
| `hx_base.html` | HTMX partial: title block + content block, no surrounding HTML |
| `error_base.html` | Error pages (4xx, 5xx) - standalone, no nav |

### Full Page (`base.html`)

```html
{% extends "base.html" %}

{% block content %}
  <h1 class="text-2xl font-bold">My Page</h1>
  <p>Content goes here.</p>
{% endblock content %}
```

### HTMX Partial (`hx_base.html`)

Use for views that are called by HTMX and need to update the page title alongside the content:

```html
{% extends "hx_base.html" %}

{% block title %}My Page - {{ request.site.name }}{% endblock title %}

{% block content %}
  <p>Partial content returned by HTMX.</p>
{% endblock content %}
```

---

## Page Layouts

### Centred Content (Default)

`default_base.html` wraps `{% block content %}` in a centred max-width container:

```html
<main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
  {% block content %}{% endblock content %}
</main>
```

Use this for most pages. No extra wrapper needed in your template.

### Two-Column with Sidebar

Add a sidebar layout inside your content block:

```html
{% block content %}
  <div class="flex gap-8">
    <aside class="hidden w-64 shrink-0 xl:block">
      <nav class="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900">
        {% include "sidebar.html" %}
      </nav>
    </aside>
    <main class="min-w-0 flex-1">
      {{ content }}
    </main>
  </div>
{% endblock content %}
```

The sidebar is hidden on `< xl` screens - the mobile navbar menu (from `navbar.html`) provides navigation on smaller screens.

### Full-Width / Hero

For marketing pages or landing pages without the centred constraint, override the main tag by wrapping in `{% block content %}` directly:

```html
{# Override the narrow container with a full-bleed section #}
{% block content %}
  <section class="-mx-4 -mt-8 bg-indigo-600 px-4 py-24 text-white sm:-mx-6 lg:-mx-8">
    <h1 class="text-4xl font-bold">Welcome</h1>
  </section>
  <div class="mt-12">
    <!-- normal content -->
  </div>
{% endblock content %}
```

---

## Responsive Utilities

Mobile-first breakpoints:

| Prefix | Width | Use |
|--------|-------|-----|
| _(none)_ | All screens | Mobile default |
| `sm:` | ≥ 640px | Large phones |
| `md:` | ≥ 768px | Tablets |
| `lg:` | ≥ 1024px | Laptops |
| `xl:` | ≥ 1280px | Desktops |

### Common Patterns

```html
<!-- Stack on mobile, side-by-side on tablet -->
<div class="flex flex-col gap-4 md:flex-row">

<!-- Hide on mobile, show on desktop -->
<aside class="hidden xl:block">

<!-- Full width on mobile, auto on desktop -->
<button class="w-full btn btn-primary sm:w-auto">Submit</button>
```

---

## HTMX Progress Indicator

`default_base.html` renders an `#hx-indicator` element at the top of the page. It displays a thin indigo progress bar during any HTMX request - no per-request setup needed.

The indicator is driven purely by CSS classes that HTMX adds (`htmx-request`), with a small AlpineJS animation for the growing-bar effect:

```html
<div
  id="hx-indicator"
  x-data="{ width: 0 }"
  x-init="setInterval(() => { ... }, 36)"
></div>
```

To attach the indicator to a specific element instead of the global one, use `hx-indicator="#my-element"`.

---

## Cookie Banner

`{% cookie_banner %}` is rendered by a template tag in `default_base.html`. It requires a `accept_cookies` URL and uses HTMX to dismiss itself without a page reload.

To disable the cookie banner, remove `{% cookie_banner %}` from `default_base.html`.
