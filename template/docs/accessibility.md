# Accessibility

This project targets **WCAG 2.1 Level AA** compliance. This document covers
practical guidance for this stack. Check it before writing any template or UI
component.

## Contents

- [Key references](#key-references)
- [Forms](#forms)
- [Icons](#icons)
- [Interactive components (AlpineJS)](#interactive-components-alpinejs)
- [HTMX](#htmx)
- [Semantic HTML](#semantic-html)
- [Colour and contrast](#colour-and-contrast)
- [Focus styles](#focus-styles)
- [Images](#images)
- [Testing](#testing)
- [Common pitfalls](#common-pitfalls)

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
- Error states use `text-error` for visual indication

Do not bypass this rendering — `{% render_field %}` without a label wrapper
breaks the label association. Always use `as_field_group`. See `docs/django-forms.md`.

For groups of related inputs (radio buttons, checkboxes), use `<fieldset>` and
`<legend>` rather than a plain `<label>`.

---

## Icons

Heroicons are inline SVGs. Apply `aria-hidden="true"` when the icon is
decorative (adjacent text already communicates the meaning):

```html
{% heroicon_mini "trash" class="size-4" aria_hidden="true" %}
```

**Note:** heroicon template tags convert `aria_hidden` to `aria-hidden` in the output.

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
  <ul x-show="open" role="menu">
    ...
  </ul>
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
  levels.
- Use `<table>` for tabular data, with `<th scope="col|row">` headers.
- Use `<ul>`/`<ol>` for lists. Do not use CSS `list-style: none` without
  keeping the list role visible to screen readers.

---

## Colour and contrast

- Text must meet a **4.5:1** contrast ratio against its background (AA normal
  text) or **3:1** for large text (18pt+ or 14pt bold).
- Do not convey information by colour alone — pair colour with a text label,
  icon, or pattern.
- Verify contrast using the DaisyUI theme palette. The theme colors
  (`primary`, `secondary`, `error`, `success`, `info`, `warning`) are
  chosen to meet AA at their standard usages, but always verify when
  customising theme values in `tailwind/theme.css`.

---

## Focus styles

Never remove focus outlines without replacing them. DaisyUI components include
focus styles. For custom elements, use Tailwind's `focus-visible:ring`
utilities — do not override these with `outline: none` or `outline: 0`
unless a custom focus style is in place.

---

## Images

Every `<img>` must have an `alt` attribute, explicit `width`, and explicit
`height`. Missing dimensions cause layout shift (CLS); missing alt text fails
WCAG 1.1.1.

### alt text

- **Content images** (convey information): describe the content concisely.
  Never use the filename, "image of", or an empty string.
- **Decorative images** (purely visual, no informational value): `alt=""`
  (empty string — not absent). Only use `alt=""` when the image adds nothing
  for screen reader users.

### width and height

Always emit explicit `width` and `height` so the browser can reserve space
before the image loads:

```html
<!-- BAD: no dimensions, causes layout shift -->
<img src="{{ item.photo.url }}" alt="{{ item.title }}" />

<!-- GOOD: explicit dimensions -->
<img
  src="{{ item.photo.url }}"
  alt="{{ item.title }}"
  width="400"
  height="300"
/>
```

When using `sorl-thumbnail`, derive dimensions from the thumbnail object rather
than hard-coding:

```html
{% thumbnail item.photo "400x300" crop="center" as thumb %}
<img
  src="{{ thumb.url }}"
  alt="{{ item.title }}"
  width="{{ thumb.width }}"
  height="{{ thumb.height }}"
/>
{% endthumbnail %}
```

Hard-coded dimensions are acceptable when the image size is fixed by design (e.g.
an avatar always displayed at 48×48). Use the actual rendered size, not the
source file size.

---

## Testing

Automated tools catch roughly 30–40% of accessibility issues. Use them as a
floor, not a ceiling.

**Automated (recommended):**

`axe-playwright-python` integrates axe-core with the `page` fixture from
`pytest-playwright`. Check [PyPI](https://pypi.org/project/axe-playwright-python/)
and the repo for current maintenance status before adding (see `docs/packages.md`).

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

---

## Common pitfalls

### Heading hierarchy in card grids and lists

Do not skip heading levels. A common mistake is jumping from `<h1>` (page title) to
`<h3>` (card title) inside a grid or list, leaving no `<h2>` in between.

Card titles inside a list or grid should use `<h2>` if the section has no existing
`<h2>` heading, or `<h3>` if there is already a `<h2>` section heading above them.

```html
<!-- BAD: skips from h1 to h3 -->
<h1>Photos</h1>
<ul>
  <li>
    <h3>Sunset at the beach</h3>
  </li>
</ul>

<!-- GOOD: sequential hierarchy -->
<h1>Photos</h1>
<ul>
  <li>
    <h2>Sunset at the beach</h2>
  </li>
</ul>
```

### Screen-reader labels on icon-only inputs

A DaisyUI `<label class="input">` that contains only an `aria-hidden` icon and an
`<input>` has no accessible text — the label is empty to a screen reader.

Fix: add a visually-hidden `<span class="sr-only">` inside the label.

```html
<!-- BAD: label has no accessible text -->
<label class="input">
  {% heroicon_mini "magnifying-glass" class="opacity-50 size-4 shrink-0" aria_hidden="true" %}
  <input type="search" name="q" placeholder="{% translate "Search..." %}">
</label>

<!-- GOOD: sr-only span provides an accessible label -->
<label class="input">
  {% heroicon_mini "magnifying-glass" class="opacity-50 size-4 shrink-0" aria_hidden="true" %}
  <span class="sr-only">{% translate "Search photos" %}</span>
  <input type="search" name="q" placeholder="{% translate "Search..." %}">
</label>
```
