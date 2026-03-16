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
@import "./tokens.css";
@import "./base.css";
@import "./htmx.css";
@import "./buttons.css";
@import "./forms.css";
@import "./messages.css";
```

### theme.css

Tailwind `@theme` aliases that generate utility classes. Change these to rebrand
the entire project — `text-primary-600`, `bg-danger-50`, etc. map back to these:

```css
@theme {
  --color-primary-50:  var(--color-indigo-50);
  /* ... through 950 */

  --color-secondary-50: var(--color-violet-50);
  /* ... */

  --color-danger-50: var(--color-rose-50);
  /* ... */

  --color-success-400: var(--color-emerald-400);
  --color-error-400:   var(--color-rose-400);
  --color-info-400:    var(--color-sky-400);
  --color-warning-400: var(--color-amber-400);
}
```

### tokens.css

Semantic CSS custom properties for light and dark mode. Override these to retheme
the layout without touching brand colors:

```css
@layer base {
    :root {
        scrollbar-width: thin;
        --color-bg: var(--color-white);
        --color-surface: var(--color-zinc-50);
        --color-border: var(--color-zinc-200);
        --color-text: var(--color-zinc-900);
        --color-text-muted: var(--color-zinc-500);

        @variant dark {
            color-scheme: dark;
            --color-bg: var(--color-zinc-950);
            --color-surface: var(--color-zinc-900);
            --color-border: var(--color-zinc-800);
            --color-text: var(--color-zinc-100);
            --color-text-muted: var(--color-zinc-400);
        }
    }
}
```

### base.css

Global resets and framework utilities. Consumes tokens from `tokens.css`:

```css
@layer base {
    /* Tailwind v4 border-color reset */
    *, ::after, ::before, ::backdrop, ::file-selector-button {
        border-color: var(--color-zinc-200, currentColor);
    }

    body {
        background-color: var(--color-bg);
        color: var(--color-text);
    }

    /* AlpineJS */
    [x-cloak] {
        display: none !important;
    }
}
```

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
just dj tailwind build    # Build CSS
just serve               # Dev server + Tailwind watcher
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
