# UI Design Patterns

This project uses DaisyUI (on Tailwind CSS v4) for component styling, AlpineJS for client-side interactivity, and HTMX for server-driven updates. All JS/CSS dependencies are vendored — no CDN, no npm. See `docs/Frontend-Dependencies.md` to add or update them.

## Component Library

DaisyUI provides the component library. See [daisyui.com/components](https://daisyui.com/components/) for the full reference, and `docs/Tailwind.md` for project-specific configuration.

## Dark Mode

DaisyUI themes handle dark mode automatically via `prefers-color-scheme`. Component classes (`btn`, `alert`, `input`, etc.) adapt without `dark:` prefixes. Use `dark:` only for custom Tailwind utilities outside DaisyUI components.

## Responsive Design

Mobile-first. Use `sm:` (640 px), `md:` (768 px), `lg:` (1024 px), `xl:` (1280 px) prefixes to layer up from the smallest viewport.

## Icons

Use [`heroicons`](https://heroicons.com/) via `heroicons[django]` for all icons:

```html
{% load heroicons %}

{% heroicon_outline "arrow-right" %}                              {# 24 px outline #}
{% heroicon_solid "check" %}                                      {# 24 px filled #}
{% heroicon_mini "x-mark" class="size-4" %}                      {# 20 px compact #}
{% heroicon_micro "chevron-down" %}                               {# 16 px tight spaces #}

{# Extra attributes pass through directly #}
{% heroicon_outline "magnifying-glass" class="size-5 opacity-50" aria-hidden="true" %}
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

See `docs/Templates.md` for the full reference: field rendering, widget type dispatch, custom
widget partials, the `form.html` wrapper variables, and the `{% partialdef %}` HTMX swap pattern.

## Accessibility

Target WCAG 2.1 AA.

### Semantic HTML

Use the right element for the job:

```html
<nav>        <!-- site/section navigation -->
<main>       <!-- primary page content (one per page) -->
<article>    <!-- self-contained content (post, card) -->
<section>    <!-- thematic group with a heading -->
<aside>      <!-- complementary content / sidebar -->
<button>     <!-- any clickable action (not <div @click>) -->
<a href="…"> <!-- navigation to a URL -->
```

### Focus Rings

DaisyUI components include focus styles. For custom elements, use `focus-visible:` to show the ring only for keyboard users:

```html
<button class="focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2">
```

### Screen Reader Text

```html
<!-- Icon-only button -->
<button aria-label="Close" class="btn btn-ghost btn-circle">
  {% heroicon_mini "x-mark" class="size-4" aria-hidden="true" %}
</button>

<!-- Supplementary context -->
<a href="/users/42/">
  View profile
  <span class="sr-only">for Alice Smith</span>
</a>
```

### Forms

Every input needs a `<label>`. Never rely on `placeholder` as a substitute. The `fieldset` +
`fieldset-legend` DaisyUI pattern used by `{{ field.as_field_group }}` handles this automatically
— see `docs/Templates.md` for rendering details.

### HTMX Live Regions

When HTMX swaps content, announce changes to screen readers:

```html
<div aria-live="polite" aria-atomic="true" id="status"></div>
<div aria-live="assertive" aria-atomic="true" id="errors"></div>
```

### AlpineJS Widgets

Bind ARIA state to Alpine state:

```html
<button @click="open = !open" :aria-expanded="open.toString()">Toggle</button>
<div x-show="open" role="region">...</div>
```

### Color Contrast

- Normal text: 4.5:1 minimum (WCAG AA)
- Large text (18 px+ or 14 px+ bold): 3:1 minimum
- UI components and focus indicators: 3:1 minimum

### Keyboard Navigation

- All interactive elements reachable by `Tab` in logical DOM order
- `Escape` closes modals, dropdowns, and overlays
- Arrow keys navigate within composite widgets (menus, tabs, radio groups)
- No keyboard traps except intentional modal focus traps (with `Escape` to close)
