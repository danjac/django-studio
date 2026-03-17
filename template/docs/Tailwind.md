# Tailwind CSS

This project uses Tailwind CSS v4 with `django-tailwind-cli` for compilation.

## Installation

```bash
uv add django-tailwind-cli
```

Add to `INSTALLED_APPS`:
```python
"django_tailwind_cli",
```

## Configuration

```python
# settings.py
TAILWIND_CLI_SRC_CSS = BASE_DIR / "tailwind" / "app.css"
TAILWIND_CLI_DIST_CSS = "app.css"
```

## CSS Structure (Tailwind v4)

This project organizes Tailwind CSS into multiple files:

```css
/* tailwind/app.css */
@import "tailwindcss";

/* Plugins */
@plugin "@tailwindcss/forms";
@plugin "@tailwindcss/typography";

@import "./theme.css";
@import "./tweaks.css";
@import "./htmx.css";
@import "./buttons.css";
@import "./forms.css";
@import "./messages.css";
```

### theme.css

Brand palette and semantic layout tokens. The two sections serve different roles
but are edited together when rebranding:

- **`@theme` block** — Tailwind palette aliases that generate utility classes
  (`text-primary-600`, `bg-danger-50`, etc.). Change these to rebrand. Never use
  `indigo-*`, `violet-*`, or `rose-*` directly in templates.
- **`:root` block** — Runtime CSS custom properties used with `var()` throughout
  the project. Change these to retheme the layout or dark mode palette. Do not
  rename them — they are referenced across all component files.

### tweaks.css

Global resets, body defaults, Alpine utilities, and dark mode border corrections.

### htmx.css

HTMX utilities:

```css
@custom-variant htmx-added (& .htmx-added,.htmx-added &);

@layer base {
    #hx-indicator {
        display: none;
        position: fixed;
        top: 0; left: 0;
        height: 3px;
        background: var(--color-primary-500);
        z-index: 9999;
    }

    #hx-indicator.htmx-request {
        display: block !important;
    }
}
```

### Component CSS

Define component styles in separate files:

```css
/* tailwind/buttons.css */
@layer components {
    .btn {
        @apply px-4 py-2 rounded-lg font-semibold transition-colors;
    }
    .btn-primary {
        @apply bg-indigo-600 text-white hover:bg-indigo-700;
    }
}
```

```css
/* tailwind/forms.css */
@layer components {
    .form-input {
        @apply w-full px-3 py-2 border rounded-lg;
    }
    .form-checkbox {
        @apply rounded border-zinc-300;
    }
}
```

## Development

```bash
just dj tailwind build    # One-off CSS build (production / CI)
just serve                # Dev server with Tailwind watching for changes
```

## Common Classes

### Layout
```html
<div class="flex">flexbox</div>
<div class="grid grid-cols-3">grid</div>
<div class="space-y-4">vertical spacing</div>
```

### Responsive
```html
<div class="flex flex-col sm:flex-row">mobile-first responsive</div>
```

### Dark Mode
```html
<div class="bg-white dark:bg-zinc-900">dark mode support</div>
<div class="text-zinc-700 dark:text-zinc-300">adaptive text</div>
```

## Linting

Use `rustywind` to sort Tailwind classes:

```bash
rustywind templates/ --write
```

## Key Differences from Tailwind v3

- Uses `@import "tailwindcss"` instead of `@tailwind` directives
- Uses `@plugin` for plugins instead of `plugins: []` in config
- No `tailwind.config.js` required - use CSS for configuration
- Uses `@variant dark` for dark mode instead of `darkMode: 'class'`
