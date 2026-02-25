# UI Design Patterns

This project uses Tailwind CSS with a dark mode implementation and responsive design patterns.

## Dark Mode

This project uses Tailwind's `dark:` prefix with system preference (via CSS media query):

```css
/* base.css */
@variant dark {
    color-scheme: dark;
    --color-bg: var(--color-zinc-950);
    --color-surface: var(--color-zinc-900);
    --color-border: var(--color-zinc-800);
    --color-text: var(--color-zinc-100);
}
```

### Common Dark Mode Classes

```html
<!-- Backgrounds -->
<div class="bg-white dark:bg-zinc-900">
<div class="bg-zinc-50 dark:bg-zinc-950">

<!-- Borders -->
<div class="border-zinc-200 dark:border-zinc-700">

<!-- Text -->
<p class="text-zinc-700 dark:text-zinc-300">
<p class="text-zinc-500 dark:text-zinc-400">

<!-- Links/Interactive -->
<a class="hover:text-indigo-600 dark:hover:text-indigo-400">
```

### Typography Dark Mode

```html
<!-- Use prose-invert for markdown content -->
<div class="prose dark:prose-invert">
    <!-- Markdown content -->
</div>
```

## Responsive Design

Mobile-first approach with `sm:`, `md:`, `lg:`, `xl:` prefixes:

```html
<!-- Mobile: stacked, Desktop: side-by-side -->
<div class="flex flex-col sm:flex-row">

<!-- Hide on mobile, show on desktop -->
<div class="hidden md:block">

<!-- Mobile: full width, Desktop: constrained -->
<div class="w-full md:w-3/4">
```

### Common Breakpoints

- `sm:` - 640px (small tablets)
- `md:` - 768px (tablets)
- `lg:` - 1024px (laptops)
- `xl:` - 1280px (desktops)

## Component Patterns

### Cards

```html
<article class="border rounded-xl p-4 hover:shadow-lg transition">
    <img src="..." class="rounded-t-xl">
    <h3 class="font-bold">{{ title }}</h3>
</article>
```

### Buttons

```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
```

### Forms

```html
<input class="form-input">
<textarea class="form-textarea">
<select class="form-select">
```

### Navigation

```html
<nav class="sticky top-0 z-10 bg-white/80 backdrop-blur-lg dark:bg-zinc-950/80">
```

## Spacing Patterns

```html
<!-- Vertical spacing between items -->
<div class="space-y-4">

<!-- Horizontal spacing -->
<div class="space-x-4">

<!-- Padding -->
<div class="p-4">

<!-- Margins -->
<div class="mb-4">
```

## Color Palette

This project uses Zinc for neutral colors:

- `zinc-50` to `zinc-950` - Neutral scale
- `indigo-500`, `indigo-600` - Primary accent
- `rose-500`, `rose-600` - Error states
- `zinc-500`, `zinc-400` - Muted text

## Accessibility

Target WCAG 2.1 AA as the baseline.

### Semantic HTML

Use the right element for the job — don't use `<div>` where a semantic element exists:

```html
<nav>        <!-- site/section navigation -->
<main>       <!-- primary page content (one per page) -->
<article>    <!-- self-contained content (post, card) -->
<section>    <!-- thematic group with a heading -->
<aside>      <!-- complementary content / sidebar -->
<header>     <!-- page or section header -->
<footer>     <!-- page or section footer -->
<h1>–<h6>   <!-- headings in document order, never skip levels -->
<button>     <!-- any clickable action (not <div @click>) -->
<a href="…"> <!-- navigation to a URL -->
```

### Focus Management

Every interactive element must have a visible focus ring. Tailwind removes outlines by default — always restore them:

```html
<button class="focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
<a class="focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded">
```

Use `focus-visible:` instead of `focus:` when you only want the ring for keyboard users (not mouse clicks):

```html
<button class="focus-visible:ring-2 focus-visible:ring-indigo-500">
```

### Screen Reader Text

Use `sr-only` to provide text for screen readers that is hidden visually:

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

### Icons and ARIA

Decorative icons (accompanied by visible text) must be hidden from screen readers. Standalone icons need a label.

```html
<!-- Decorative — hidden from AT -->
{% heroicon_outline "arrow-right" class="size-5" aria-hidden="true" %}

<!-- Standalone — labelled via parent button -->
<button aria-label="Delete item">
  {% heroicon_outline "trash" class="size-5" aria-hidden="true" %}
</button>
```

### Forms

Every input needs a `<label>`. Never rely on `placeholder` as a substitute — it disappears on focus and has poor contrast.

```html
<label for="email">Email address</label>
<input id="email" type="email" ...>

<!-- Error messages -->
<input id="email" aria-describedby="email-error" aria-invalid="true" ...>
<p id="email-error" class="text-rose-600 text-sm">Enter a valid email address.</p>
```

With `widget_tweaks`, add ARIA attributes directly in the template:

```html
{% render_field form.email class="form-input" aria-describedby="email-error" %}
```

### HTMX Dynamic Content

When HTMX swaps content, screen readers won't announce the change unless you use a live region:

```html
<!-- Announce status messages (e.g. "Saved") -->
<div aria-live="polite" aria-atomic="true" id="status"></div>

<!-- Announce errors urgently -->
<div aria-live="assertive" aria-atomic="true" id="errors"></div>
```

For full-page fragment swaps, move focus explicitly:

```html
<div hx-get="/results/" hx-target="#results" hx-swap="innerHTML" hx-on::after-swap="document.getElementById('results').focus()">
```

### AlpineJS Interactive Widgets

Use ARIA state attributes alongside Alpine state:

```html
<!-- Disclosure / accordion -->
<button @click="open = !open" :aria-expanded="open.toString()">Toggle</button>
<div x-show="open" role="region">...</div>

<!-- Modal — trap focus while open -->
<div
  x-show="open"
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  x-trap.inert.noscroll="open"
>
  <h2 id="dialog-title">Confirm deletion</h2>
</div>
```

`x-trap` requires the `@alpinejs/focus` plugin — ensure it is registered.

### Color Contrast

- Normal text: minimum 4.5:1 contrast ratio against background (WCAG AA)
- Large text (18px+ or 14px+ bold): minimum 3:1
- UI components and focus indicators: minimum 3:1

The Zinc + Indigo palette meets AA at standard pairings:
- `text-zinc-900` on `bg-white` ✓
- `text-zinc-100` on `bg-zinc-950` ✓
- Avoid `text-zinc-400` on `bg-white` for body text — use `text-zinc-500` minimum

### Keyboard Navigation

- All interactive elements reachable by `Tab` in logical order
- `Escape` closes modals, dropdowns, and overlays
- Arrow keys navigate within composite widgets (menus, tabs, radio groups)
- No keyboard traps except intentional modal focus traps (with escape to close)

## Icons

Use [`heroicons`](https://heroicons.com/) for all icons via the `heroicons[django]` package. Load the template tag and prefer the built-in icon set over custom SVGs.

```html
{% load heroicons %}

<!-- Outline (24px) — default for most UI icons -->
{% heroicon_outline "arrow-right" %}

<!-- Solid (24px) — filled variant -->
{% heroicon_solid "check" %}

<!-- Mini (20px) — for compact UI, inline with text -->
{% heroicon_mini "x-mark" class="size-4" %}

<!-- Micro (16px) — smallest, for tight spaces -->
{% heroicon_micro "chevron-down" %}
```

Pass extra attributes (e.g. `class`, `aria-hidden`) directly to the tag:

```html
{% heroicon_outline "magnifying-glass" class="size-5 text-zinc-400" aria-hidden="true" %}
```

**Rules:**
- Use `heroicons` as the first choice for every icon.
- Use custom inline SVGs only when no heroicon exists for the shape you need.
- Never use character entities (`&times;`, `&#9998;`) or emoji as icons.

## Best Practices

1. Use semantic HTML elements
2. Ensure color contrast meets WCAG AA
3. Test at multiple viewport sizes
4. Use `dark:` variants consistently
5. Use `transition` for interactive elements
