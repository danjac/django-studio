# Design

This project uses DaisyUI (on Tailwind CSS v4) for component styling, AlpineJS for client-side interactivity, and HTMX for server-driven updates. All JS/CSS dependencies are vendored — no CDN, no npm. See `docs/frontend-dependencies.md` to add or update them.

## Contents

- [Component Library](#component-library)
- [Icons](#icons)
- [Forms](#forms)
- [Responsive Design](#responsive-design)
- [Accessibility](#accessibility)
- [Tailwind Configuration](#tailwind-configuration)

## Component Library

DaisyUI provides the component library. See [daisyui.com/components](https://daisyui.com/components/) for the full reference.

Use DaisyUI's semantic classes instead of hand-rolling component CSS:

| Component | Classes |
|-----------|---------|
| Buttons | `btn`, `btn-primary`, `btn-secondary`, `btn-error`, `btn-ghost`, `btn-outline` |
| Inputs | `input`, `select`, `textarea`, `checkbox` |
| Form fields | `fieldset`, `fieldset-legend`, `label` |
| Alerts | `alert`, `alert-info`, `alert-success`, `alert-warning`, `alert-error`, `alert-soft` |
| Toast | `toast`, `toast-end`, `toast-bottom` |
| Navbar | `navbar`, `navbar-start`, `navbar-center`, `navbar-end` |
| Menu | `menu`, `menu-title` |
| Join | `join`, `join-item` (pagination button groups) |
| Cards | `card`, `card-body`, `card-title` |
| Badges | `badge`, `badge-primary`, `badge-error` |

### Color utilities

DaisyUI provides semantic color classes that adapt to the active theme:

```html
<div class="bg-base-100 text-base-content">Surface</div>
<div class="bg-primary text-primary-content">Brand</div>
<div class="text-base-content/60">Muted text</div>
<div class="text-error">Error text</div>
<div class="border-base-300">Border</div>
```

Never use raw Tailwind colors (`indigo-600`, `zinc-900`, etc.) in templates — use DaisyUI semantic names so themes work correctly.

### Dark mode

DaisyUI handles dark mode via themes. The dark theme is activated automatically by `prefers-color-scheme: dark`. No `dark:` prefix needed for DaisyUI component classes. Use `dark:` only for custom Tailwind utilities outside DaisyUI components.

## Icons

Use [`heroicons`](https://heroicons.com/) via `heroicons[django]` for all icons:

```html
{% load heroicons %}
{% heroicon_outline "arrow-right" %}           {# 24 px outline #}
{% heroicon_solid "check" %}                   {# 24 px filled #}
{% heroicon_mini "x-mark" class="size-4" %}    {# 20 px compact #}
{% heroicon_micro "chevron-down" %}            {# 16 px tight spaces #}
{# Extra attributes pass through directly: underscores are converted to kebab-case #}
{% heroicon_outline "magnifying-glass" class="size-5 opacity-50" aria_hidden="true" %}
```

- Use heroicons as the first choice for every icon.
- Use custom inline SVGs only when no heroicon covers the shape.
- Never use character entities (`&times;`, `&#9998;`) or emoji as icons.
- Decorative icons (next to visible text) get `aria-hidden="true"`.
- Standalone icons (icon-only buttons) need `aria-label` on the parent button.

## Forms

Form rendering uses `{{ form }}` / `{{ field.as_field_group }}` (dispatches through
`templates/forms/partials.html` to widget-specific `{% partialdef %}` blocks),
`django-widget-tweaks` for per-field attribute overrides, and `{% fragment "form.html" %}`
as the HTMX-aware `<form>` wrapper.

See `docs/django-forms.md` for the full reference: field rendering levels, widget type
dispatch, custom widget partials, the `form.html` wrapper variables, and the
`{% partialdef %}` HTMX swap pattern.

## Responsive Design

Mobile-first. Use `sm:` (640 px), `md:` (768 px), `lg:` (1024 px), `xl:` (1280 px) prefixes to layer up from the smallest viewport.

## Accessibility

Target WCAG 2.1 AA. See `docs/accessibility.md` for guidance on semantic HTML, focus styles,
ARIA, screen reader text, HTMX live regions, AlpineJS keyboard patterns, and colour contrast.

## Tailwind Configuration

Tailwind CSS v4 with DaisyUI and `django-tailwind-cli` for compilation. No Node.js or npm required.

### Installation

```bash
uv add django-tailwind-cli
```

Add to `INSTALLED_APPS`:
```python
"django_tailwind_cli",
```

### Configuration

```python
# settings.py
TAILWIND_CLI_SRC_CSS = BASE_DIR / "tailwind" / "app.css"
TAILWIND_CLI_DIST_CSS = "app.css"
```

### CSS Structure

```css
/* tailwind/app.css */
@import "tailwindcss";

@plugin "@tailwindcss/typography";
@plugin "./daisyui.mjs";

@import "./theme.css";
@import "./tweaks.css";
@import "./htmx.css";
```

| File | Purpose |
|------|---------|
| `daisyui.mjs` | Component library (buttons, forms, alerts, navbar, etc.) |
| `daisyui-theme.mjs` | Custom theme definitions |
| `@tailwindcss/typography` | Prose styling for rendered markdown |
| `theme.css` | Custom DaisyUI themes for light and dark mode (oklch brand colors) |
| `tweaks.css` | Minimal global resets: scrollbar width and Alpine `[x-cloak]` rule |
| `htmx.css` | HTMX utilities: progress indicator bar and `htmx-added` custom variant |

DaisyUI is vendored as `.mjs` files in `tailwind/` — no npm needed. To update or add frontend dependencies, see `docs/frontend-dependencies.md`.

To rebrand, edit the oklch values in `tailwind/theme.css`. All DaisyUI components update automatically.

### Development

```bash
just dj tailwind build    # One-off CSS build (production / CI)
just serve                # Dev server with Tailwind watching for changes
```

### Linting

Use `rustywind` to sort Tailwind classes:

```bash
rustywind templates/ --write
```
