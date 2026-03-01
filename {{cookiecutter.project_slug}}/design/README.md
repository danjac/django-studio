# Design System

This project ships with a ready-made set of UI components built on Tailwind CSS, HTMX, and AlpineJS. All components are sourced from and battle-tested in production.

**IMPORTANT** any individual project will have modifications to the original design system, for example branding requirements. If the modification has project scope i.e. the styling of all buttons instead of a one-off change for a specific case, then you should also update this design system documentation to reflect the change.

## Component Index

| Component         | Template file                                      | CSS layer               | Doc                            |
| ----------------- | -------------------------------------------------- | ----------------------- | ------------------------------ |
| Buttons           | _(utility classes only)_                           | `tailwind/buttons.css`  | [buttons.md](buttons.md)       |
| Messages / Alerts | `templates/messages.html`                          | `tailwind/messages.css` | [messages.md](messages.md)     |
| Forms             | `templates/form/field.html`, `templates/form.html` | `tailwind/forms.css`    | [forms.md](forms.md)           |
| Navbar            | `templates/navbar.html`                            | -                       | [navigation.md](navigation.md) |
| Sidebar           | `templates/sidebar.html`                           | -                       | [navigation.md](navigation.md) |
| User Dropdown     | _(inside navbar.html)_                             | -                       | [navigation.md](navigation.md) |
| Page Header       | `templates/header.html`                            | -                       | [headers.md](headers.md)       |
| Cards             | `templates/card.html`                              | -                       | [cards.md](cards.md)           |
| Badges / Tags     | _(inline classes)_                                 | -                       | [badges.md](badges.md)         |
| Pagination        | `templates/paginate.html`                          | -                       | [pagination.md](pagination.md) |
| Markdown / Prose  | `templates/markdown.html`                          | -                       | [typography.md](typography.md) |
| Layout patterns   | _(in base templates)_                              | -                       | [layout.md](layout.md)         |

## Stack

- **Tailwind CSS v4** - utility-first CSS, compiled by `django-tailwind-cli`
- **AlpineJS v3** - lightweight reactivity for interactive components
- **HTMX v2** - server-driven partial page updates
- **Heroicons** - SVG icon set via `heroicons[django]`

## Design Tokens

CSS custom properties defined in `tailwind/base.css`:

```css
--color-bg          /* page background */
--color-surface     /* card / panel background */
--color-border      /* default border */
--color-text        /* primary text */
--color-text-muted  /* secondary / placeholder text */
```

Light and dark variants are set automatically via the `@variant dark` media query.

## Global Rules

- Use `heroicons` for all icons - see [Icons](../docs/UI-Design-Patterns.md#icons)
- Use `btn`, `btn-primary`, `btn-secondary`, `btn-danger` for all buttons
- Use `form-input`, `form-select`, `form-textarea` for all inputs
- Prefer `{% include %}` with context variables over copy-pasting markup
- All interactive elements must have visible focus rings (see accessibility section in each doc)
