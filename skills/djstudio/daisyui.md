Fetch a DaisyUI component's documentation and show how to use it in this project.

**Arguments:** `<component_name>` — the DaisyUI component name (e.g. `modal`, `drawer`, `tabs`, `collapse`, `dropdown`, `tooltip`, `swap`, `loading`, `skeleton`, `diff`, `countdown`, `radial-progress`, `rating`, `steps`, `timeline`, etc.)

**Step 1 — Fetch the component docs**

Use WebFetch to retrieve the component page:

```
URL: https://daisyui.com/components/<component_name>/
Prompt: List ALL CSS classes for this component, their purpose, and show the complete HTML examples. Include all variants (sizes, colors, styles). Show the full class reference table.
```

**Step 2 — Show project-specific usage**

Present the component with:

1. **Class reference** — table of all classes and what they do
2. **Basic HTML example** — adapted for Django templates (use `{% translate %}` for text, `{% heroicon_* %}` for icons, `{% url %}` for links)
3. **With HTMX** — if the component involves user interaction, show how to integrate with HTMX (e.g. `hx-get`, `hx-swap`, `hx-target`)
4. **With Alpine** — if the component needs JS behaviour beyond DaisyUI's CSS-only approach (e.g. close on escape, dynamic state), show the Alpine pattern

**Step 3 — Note any project conventions**

Remind the user of relevant conventions:
- Use `{% heroicon_mini %}` / `{% heroicon_outline %}` for icons, not inline SVGs
- Use `{% translate %}` for all user-visible text
- Use semantic DaisyUI colors (`primary`, `secondary`, `error`, etc.) not raw Tailwind colors
- For forms, use the `{% fragment "form.html" %}` wrapper — see `docs/Templates.md`
- For HTMX partials, use `{% partialdef %}` / `{% partial %}` — see `docs/Templates.md`

## Help

```
/djstudio daisyui <component>
```

Fetches DaisyUI component documentation and shows how to use it with this project's Django/HTMX/Alpine conventions.

**Arguments:**
- `<component>` — DaisyUI component name (e.g. `modal`, `drawer`, `tabs`, `tooltip`)

**Examples:**
```
/djstudio daisyui modal
/djstudio daisyui tabs
/djstudio daisyui drawer
/djstudio daisyui collapse
```
