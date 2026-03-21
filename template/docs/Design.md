# Design

This project uses DaisyUI (on Tailwind CSS v4) for component styling, AlpineJS for client-side interactivity, and HTMX for server-driven updates. All JS/CSS dependencies are vendored — no CDN, no npm. See `docs/Frontend-Dependencies.md` to add or update them.

## Component Library

DaisyUI provides the component library. See [daisyui.com/components](https://daisyui.com/components/) for the full reference, and `docs/Tailwind.md` for project-specific configuration and class reference.

## Dark Mode

DaisyUI themes handle dark mode automatically — see `docs/Tailwind.md`.

## Responsive Design

Mobile-first. Use `sm:` (640 px), `md:` (768 px), `lg:` (1024 px), `xl:` (1280 px) prefixes to layer up from the smallest viewport.

## Icons

Use [`heroicons`](https://heroicons.com/) via `heroicons[django]` for all icons:

```html
{% load heroicons %} {% heroicon_outline "arrow-right" %} {# 24 px outline #} {%
heroicon_solid "check" %} {# 24 px filled #} {% heroicon_mini "x-mark"
class="size-4" %} {# 20 px compact #} {% heroicon_micro "chevron-down" %} {# 16
px tight spaces #} {# Extra attributes pass through directly: underscores are
converted to kebab-case #} {% heroicon_outline "magnifying-glass" class="size-5
opacity-50" aria_hidden="true" %}
```

- Use heroicons as the first choice for every icon.
- Use custom inline SVGs only when no heroicon covers the shape.
- Never use character entities (`&times;`, `&#9998;`) or emoji as icons.
- Decorative icons (next to visible text) get `aria-hidden="true"`.
- Standalone icons (icon-only buttons) need `aria-label` on the parent button.

## Forms

Form rendering uses `{{ field.as_field_group }}` (dispatches through `templates/form/field.html`
to widget-specific `{% partialdef %}` blocks), `django-widget-tweaks` for per-field attribute
overrides, and `{% fragment "form.html" %}` as the HTMX-aware `<form>` wrapper.

See `docs/Django-Templates.md` for the full reference: field rendering, widget type dispatch, custom
widget partials, the `form.html` wrapper variables, and the `{% partialdef %}` HTMX swap pattern.

## Accessibility

Target WCAG 2.1 AA. See `docs/Accessibility.md` for guidance on semantic HTML, focus styles,
ARIA, screen reader text, HTMX live regions, AlpineJS keyboard patterns, and colour contrast.
