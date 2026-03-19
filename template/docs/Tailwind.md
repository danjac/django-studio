# Tailwind CSS

This project uses Tailwind CSS v4 with DaisyUI and `django-tailwind-cli` for compilation. No Node.js or npm required.

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

## CSS Structure

```css
/* tailwind/app.css */
@import "tailwindcss";

@plugin "@tailwindcss/typography";
@plugin "./daisyui.mjs";

@import "./theme.css";
@import "./tweaks.css";
@import "./htmx.css";
```

### Plugins

| Plugin | Purpose |
|--------|---------|
| `daisyui.mjs` | Component library (buttons, forms, alerts, navbar, etc.) |
| `daisyui-theme.mjs` | Custom theme definitions |
| `@tailwindcss/typography` | Prose styling for rendered markdown |

DaisyUI is vendored as `.mjs` files in `tailwind/` — no npm needed. To update, download new releases from [daisyui.com](https://daisyui.com/pages/tailwind-css-without-node/).

### theme.css

Custom DaisyUI themes for light and dark mode. Each theme defines brand colors in oklch:

```css
@plugin "./daisyui-theme.mjs" {
  name: "light";
  default: true;
  color-scheme: light;
  --color-primary: oklch(0.50 0.18 264);
  --color-secondary: oklch(0.55 0.20 293);
  --color-error: oklch(0.58 0.22 18);
  /* ... */
}
```

To rebrand, edit the oklch values in `theme.css`. All DaisyUI components update automatically.

### tweaks.css

Minimal global resets: scrollbar width and Alpine `[x-cloak]` rule.

### htmx.css

HTMX utilities: progress indicator bar and `htmx-added` custom variant.

## DaisyUI Component Reference

Use DaisyUI's semantic classes instead of hand-rolling component CSS. Full docs at [daisyui.com/components](https://daisyui.com/components/).

Common classes used in this project:

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

## Development

```bash
just dj tailwind build    # One-off CSS build (production / CI)
just serve                # Dev server with Tailwind watching for changes
```

## Linting

Use `rustywind` to sort Tailwind classes:

```bash
rustywind templates/ --write
```
