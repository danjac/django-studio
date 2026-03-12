# Accessibility

This project targets **WCAG 2.1 Level AA** compliance. This document covers
practical guidance for this stack. Check it before writing any template or UI
component.

## Key references

- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/) — full
  checklist filtered by level and technique
- [MDN ARIA Guide](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)
  — ARIA roles, states, and properties
- [HTMX Accessibility](https://htmx.org/docs/#accessibility) — HTMX-specific
  patterns (focus management, `aria-busy`, live regions)
- [AlpineJS Accessibility](https://alpinejs.dev/advanced/accessibility) —
  keyboard handling in Alpine components
- [axe-core rules](https://dequeuniversity.com/rules/axe/4.9) — the rule set
  used by automated testing tools
- [Inclusive Components](https://inclusive-components.design/) — pattern library
  with accessible component implementations

---

## Forms

Form fields rendered via `{{ field.as_field_group }}` or
`{% fragment "form.html" %}` are accessible by default:
- Every `<input>` has an associated `<label>` via `field.id_for_label`
- Error messages are linked via `aria-describedby`
- The `has-errors` class on the `<fieldset>` provides a visual indicator

Do not bypass this rendering — `{% render_field %}` without a label wrapper
breaks the label association. Always use `as_field_group`. See `design/forms.md`.

For groups of related inputs (radio buttons, checkboxes), use `<fieldset>` and
`<legend>` rather than a plain `<label>`.

---

## Icons

Heroicons are inline SVGs. Apply `aria-hidden="true"` when the icon is
decorative (adjacent text already communicates the meaning):

```html
{% heroicon_mini "trash" class="size-4" aria_hidden="true" %}
```

When the icon is the only content of an interactive element, provide a label:

```html
<button type="button" aria-label="Delete post">
  {% heroicon_mini "trash" class="size-4" aria_hidden="true" %}
</button>
```

Never use an unlabelled icon-only button.

---

## Interactive components (AlpineJS)

Alpine components must be keyboard-operable:

- Dropdowns/menus: open on `Enter`/`Space`, close on `Escape`, arrow-key
  navigation between items
- Modals/dialogs: trap focus while open, return focus to trigger on close,
  use `role="dialog"` and `aria-modal="true"`
- Toggles: use `aria-expanded` to reflect open/closed state
- Loading states: use `aria-busy="true"` on the container being updated

```html
<div x-data="{ open: false }">
  <button
    type="button"
    :aria-expanded="open"
    @click="open = !open"
    @keydown.escape="open = false"
  >
    Menu
  </button>
  <ul x-show="open" role="menu">...</ul>
</div>
```

---

## HTMX

HTMX swaps DOM content without a full page reload. Ensure:

- **Focus management**: after a swap, move focus to the updated region if the
  user's focus point was removed or replaced. Use `hx-on::after-request` or an
  Alpine directive.
- **Live regions**: wrap content that updates in response to user action in an
  `aria-live` region so screen readers announce the change:

  ```html
  <div aria-live="polite" aria-atomic="true" id="search-results">
    ...updated content...
  </div>
  ```

- **Loading indicators**: use `aria-busy="true"` on the target element during
  requests (set via `htmx:beforeRequest` / `htmx:afterRequest` events or
  `hx-indicator`).
- **Page title**: update `<title>` on full-page HTMX navigations
  (`hx-push-url`) so screen readers announce the new page.

---

## Semantic HTML

Use the correct element for the job — ARIA should supplement semantics, not
replace them:

- Use `<button>` for actions, `<a>` for navigation. Never use `<div>` or
  `<span>` with a click handler.
- Use `<nav>` for navigation landmarks, `<main>` for main content, `<header>`,
  `<footer>`, `<aside>` for regions.
- Heading hierarchy must be sequential (`h1` → `h2` → `h3`). Do not skip
  levels. See `design/typography.md` for the heading scale.
- Use `<table>` for tabular data, with `<th scope="col|row">` headers.
- Use `<ul>`/`<ol>` for lists. Do not use CSS `list-style: none` without
  keeping the list role visible to screen readers.

---

## Colour and contrast

- Text must meet a **4.5:1** contrast ratio against its background (AA normal
  text) or **3:1** for large text (18pt+ or 14pt bold).
- Do not convey information by colour alone — pair colour with a text label,
  icon, or pattern.
- Verify contrast using the Tailwind palette. The design system's semantic
  tokens (`primary`, `danger`, `success`, `error`, `info`, `warning`) are
  mapped to Tailwind shades chosen to meet AA at their standard usages, but
  always verify when combining custom values or overriding tokens in
  `tailwind/app.css`.

---

## Focus styles

Never remove focus outlines without replacing them. The design system uses
Tailwind's `focus-visible:ring` utilities — do not override these with
`outline: none` or `outline: 0` unless a custom focus style is in place.

---

## Images

Every `<img>` must have an `alt` attribute:
- Meaningful images: describe the content concisely
- Decorative images: `alt=""` (empty, not absent)
- Never use the filename or "image of" as alt text

---

## Testing

Automated tools catch roughly 30–40% of accessibility issues. Use them as a
floor, not a ceiling.

**Automated (recommended):**

`axe-playwright-python` integrates axe-core with the `page` fixture from
`pytest-playwright`. Check [PyPI](https://pypi.org/project/axe-playwright-python/)
and the repo for current maintenance status before adding (see `docs/Packages.md`).

```bash
uv add --dev axe-playwright-python
```

```python
# tests/e2e/test_accessibility.py
import pytest
from axe_playwright_python.sync_playwright import Axe

@pytest.mark.e2e
def test_home_page_accessibility(page):
    page.goto("/")
    results = Axe().run(page)
    assert results.violations_count == 0, results.generate_report()
```

The `page` fixture is provided by `pytest-playwright` — no additional setup
needed beyond what the project already has.

**Manual:**

- Keyboard-only navigation: tab through every interactive element, verify
  focus is always visible and logical
- Screen reader: test with NVDA (Windows), VoiceOver (macOS/iOS), or TalkBack
  (Android)
- Zoom to 200%: ensure no content is lost or overlapping
