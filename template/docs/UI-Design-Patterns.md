# UI Design Patterns

This project uses Tailwind CSS v4 with AlpineJS and HTMX. The component library lives in `design/` - check there before writing new markup.

## Design System

See [`design/README.md`](../design/README.md) for the full component index. Quick reference:

| Component | Doc |
|-----------|-----|
| Buttons | [`design/Buttons.md`](../design/Buttons.md) |
| Forms | [`design/Forms.md`](../design/Forms.md) |
| Navbar / Sidebar | [`design/Navigation.md`](../design/Navigation.md) |
| Cards | [`design/Cards.md`](../design/Cards.md) |
| Badges | [`design/Badges.md`](../design/Badges.md) |
| Pagination | [`design/Pagination.md`](../design/Pagination.md) |
| Messages / Alerts | [`design/Messages.md`](../design/Messages.md) |
| Typography / Prose | [`design/Typography.md`](../design/Typography.md) |
| Layout | [`design/Layout.md`](../design/Layout.md) |

## Dark Mode

Uses Tailwind's `dark:` prefix driven by system preference via CSS media query. Design tokens are defined in `tailwind/theme.css`:

```css
@variant dark {
    color-scheme: dark;
    --color-bg: var(--color-zinc-950);
    --color-surface: var(--color-zinc-900);
    --color-border: var(--color-zinc-800);
    --color-text: var(--color-zinc-100);
}
```

Always pair light and dark values - never use a bare class like `bg-white` without a `dark:` counterpart.

## Color Palette

- `zinc-50` → `zinc-950` - neutral scale (backgrounds, borders, text)
- `indigo-500` / `indigo-600` - primary accent
- `rose-500` / `rose-600` - error / destructive states
- `zinc-500` / `zinc-400` - muted / secondary text

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
{% heroicon_outline "magnifying-glass" class="size-5 text-zinc-400" aria-hidden="true" %}
```

- Use heroicons as the first choice for every icon.
- Use custom inline SVGs only when no heroicon covers the shape.
- Never use character entities (`&times;`, `&#9998;`) or emoji as icons.
- Decorative icons (next to visible text) get `aria-hidden="true"`.
- Standalone icons (icon-only buttons) need `aria-label` on the parent button.

## Accessibility

Target WCAG 2.1 AA. Every component doc in `design/` includes component-specific accessibility notes. Cross-cutting rules follow.

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

Tailwind removes outlines by default - always restore them. Prefer `focus-visible:` to show the ring only for keyboard users:

```html
<button class="focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2">
```

### Screen Reader Text

```html
<!-- Icon-only button -->
<button aria-label="Close" class="...">
  {% heroicon_mini "x-mark" class="size-4" aria-hidden="true" %}
</button>

<!-- Supplementary context -->
<a href="/users/42/">
  View profile
  <span class="sr-only">for Alice Smith</span>
</a>
```

### Forms

Every input needs a `<label>`. Never rely on `placeholder` as a substitute.

```html
<label for="email">Email address</label>
<input id="email" type="email" ...>

<!-- Error state -->
<input id="email" aria-describedby="email-error" aria-invalid="true" ...>
<p id="email-error" class="text-rose-600 text-sm">Enter a valid email address.</p>
```

### HTMX Live Regions

When HTMX swaps content, announce changes to screen readers:

```html
<div aria-live="polite" aria-atomic="true" id="status"></div>   <!-- status messages -->
<div aria-live="assertive" aria-atomic="true" id="errors"></div> <!-- error messages -->
```

For fragment swaps, move focus explicitly after the swap:

```html
<div hx-get="/results/" hx-target="#results" hx-swap="innerHTML"
     hx-on::after-swap="document.getElementById('results').focus()">
```

### AlpineJS Widgets

Bind ARIA state to Alpine state:

```html
<!-- Disclosure -->
<button @click="open = !open" :aria-expanded="open.toString()">Toggle</button>
<div x-show="open" role="region">...</div>

<!-- Modal - use x-trap for focus lock (requires @alpinejs/focus) -->
<div x-show="open" role="dialog" aria-modal="true" aria-labelledby="dialog-title"
     x-trap.inert.noscroll="open">
  <h2 id="dialog-title">Confirm deletion</h2>
</div>
```

### Color Contrast

- Normal text: 4.5:1 minimum (WCAG AA)
- Large text (18 px+ or 14 px+ bold): 3:1 minimum
- UI components and focus indicators: 3:1 minimum

Standard pairings that meet AA:
- `text-zinc-900` on `bg-white` ✓
- `text-zinc-100` on `bg-zinc-950` ✓
- Avoid `text-zinc-400` on `bg-white` for body text - use `text-zinc-500` minimum

### Keyboard Navigation

- All interactive elements reachable by `Tab` in logical DOM order
- `Escape` closes modals, dropdowns, and overlays
- Arrow keys navigate within composite widgets (menus, tabs, radio groups)
- No keyboard traps except intentional modal focus traps (with `Escape` to close)
