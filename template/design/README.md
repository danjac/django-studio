# Design System

This project ships with a ready-made set of UI components built on Tailwind CSS, HTMX, and AlpineJS. All components are sourced from and battle-tested in production.

**IMPORTANT** any individual project will have modifications to the original design system, for example branding requirements. If the modification has project scope i.e. the styling of all buttons instead of a one-off change for a specific case, then you should also update this design system documentation to reflect the change.

## Component Index

| Component         | Template file                                         | CSS layer               | Doc                            |
| ----------------- | ----------------------------------------------------- | ----------------------- | ------------------------------ |
| Buttons           | _(utility classes only)_                              | `tailwind/buttons.css`  | [Buttons.md](Buttons.md)       |
| Messages / Alerts | `templates/messages.html`                             | `tailwind/messages.css` | [Messages.md](Messages.md)     |
| Forms             | `templates/form.html` _(fields via `as_field_group`)_ | `tailwind/forms.css`    | [Forms.md](Forms.md)           |
| Navbar            | `templates/navbar.html`                               | -                       | [Navigation.md](Navigation.md) |
| Sidebar           | `templates/sidebar.html`                              | -                       | [Navigation.md](Navigation.md) |
| User Dropdown     | _(inside navbar.html)_                                | -                       | [Navigation.md](Navigation.md) |
| Page Header       | `templates/header.html`                               | -                       | [Headers.md](Headers.md)       |
| Cards (pattern)   | _(inline markup — see doc)_                           | -                       | [Cards.md](Cards.md)           |
| Grid layout       | `templates/grid.html`                                 | -                       | [Cards.md](Cards.md)           |
| List layout       | `templates/browse.html`                               | -                       | [Lists.md](Lists.md)           |
| Badges / Tags     | _(inline classes)_                                    | -                       | [Badges.md](Badges.md)         |
| Pagination        | `templates/paginate.html`                             | -                       | [Pagination.md](Pagination.md) |
| Markdown / Prose  | `templates/markdown.html`                             | -                       | [Typography.md](Typography.md) |
| Layout patterns   | _(in base templates)_                                 | -                       | [Layout.md](Layout.md)         |
| File upload       | _(inline markup — see doc)_                           | -                       | [Upload.md](Upload.md)         |

## Stack

- **Tailwind CSS v4** - utility-first CSS, compiled by `django-tailwind-cli`
- **AlpineJS v3** - lightweight reactivity for interactive components
- **HTMX v2** - server-driven partial page updates
- **Heroicons** - SVG icon set via `heroicons[django]`

## Design Tokens

All tokens live in `tailwind/theme.css`. Two sections, both safe to change:

### Layout tokens (`:root`)

```css
--color-bg          /* page background */
--color-surface     /* card / panel background */
--color-border      /* default border */
--color-text        /* primary text */
--color-text-muted  /* secondary / placeholder text */
```

Light and dark variants are set automatically via the `@variant dark` media query.

### Brand color tokens (`@theme`)

```css
--color-primary-*   /* brand color, default: indigo - buttons, focus rings, links */
--color-secondary-* /* secondary color, default: violet - btn-secondary */
--color-danger-*    /* destructive color, default: rose - btn-danger, error states */
```

These are defined as `@theme` aliases in `tailwind/theme.css` and generate Tailwind utilities (`text-primary-600`, `bg-danger-50`, etc.). **Never use named Tailwind colors such as `indigo-*`, `violet-*`, or `rose-*` directly in templates or CSS** - use the semantic token names so rebranding stays in one place.

Additional semantic token scales available in templates:

```css
--color-muted-*     /* neutral chrome, default: zinc */
--color-success-*   /* success states, default: emerald */
--color-warning-*   /* warning indicators, default: amber */
--color-error-*     /* validation errors, default: rose */
--color-info-*      /* informational banners, default: sky */
```

### Token usage in templates vs CSS

The **layout CSS variables** (`--color-text`, `--color-text-muted`, `--color-bg`, `--color-surface`, `--color-border`) are designed for use in **CSS files** via `var()` (e.g. `color: var(--color-text)`). Do not use CSS variable syntax in HTML class attributes.

In templates, always use the **`@theme`-generated utility classes** instead:

| Instead of                  | Use                                      |
| --------------------------- | ---------------------------------------- |
| `text-(--color-text)`       | `text-muted-900 dark:text-muted-100`     |
| `text-(--color-text-muted)` | `text-muted-500 dark:text-muted-400`     |
| `border-(--color-border)`   | `border-muted-200 dark:border-muted-800` |
| `bg-(--color-bg)`           | `bg-white dark:bg-muted-950`             |

### Rebranding

To change the primary brand color from indigo to (e.g.) teal, update the `--color-primary-*` block in `tailwind/theme.css`:

```css
@theme {
  --color-primary-50: var(--color-teal-50);
  --color-primary-100: var(--color-teal-100);
  /* ... through 950 */
}
```

All buttons, focus rings, active states, and error colors update automatically.

## Global Rules

- Use `heroicons` for all icons - see [Icons](../docs/UI-Design-Patterns.md#icons)
- Use `btn`, `btn-primary`, `btn-secondary`, `btn-danger` for all buttons
- Use `form-input`, `form-select`, `form-textarea` for all inputs
- Never use raw Tailwind colors (`indigo-*`, `violet-*`, `rose-*`, `zinc-*`, `sky-*`, `amber-*`, etc.) directly in templates or CSS — always use semantic tokens
- Use `text-primary-*` / `bg-primary-*` for brand color
- Use `text-muted-*` / `bg-muted-*` for neutral/inactive UI chrome (replaces `zinc-*`)
- Use `text-danger-*` / `bg-danger-*` for error, destructive, and warning states
- Use `text-success-*` / `bg-success-*` for success/verified states
- Use `text-info-*` / `bg-info-*` for informational banners and notices
- Use `text-warning-*` / `bg-warning-*` for caution/advisory states
- Do not use CSS variable syntax (`text-(--color-text)`) in template class attributes — use `@theme`-generated utility classes (see Design Tokens section above)
- Prefer `{% include %}` with context variables over copy-pasting markup
- All interactive elements must have visible focus rings (see accessibility section in each doc)
