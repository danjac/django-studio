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

- Use `focus:ring-2` for focus states
- Use `sr-only` for screen reader text
- Use semantic HTML (`nav`, `main`, `article`, `section`)
- Use `aria-label` for icon-only buttons

## Best Practices

1. Use semantic HTML elements
2. Ensure color contrast meets WCAG AA
3. Test at multiple viewport sizes
4. Use `dark:` variants consistently
5. Use `transition` for interactive elements
