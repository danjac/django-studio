Fetch a DaisyUI component's documentation and show how to use it in this project.

**Arguments:** `<component_name>` — the DaisyUI component name (e.g. `modal`, `drawer`, `tabs`, `collapse`, `dropdown`, `tooltip`, `swap`, `loading`, `skeleton`, `diff`, `countdown`, `radial-progress`, `rating`, `steps`, `timeline`, etc.)

**Step 1 — Check local cache**

Look for `docs/daisyui/<component_name>.md` in this project.

- **Found** → read it and skip to Step 3.
- **Not found** → proceed to Step 2.

**Step 2 — Fetch from DaisyUI site**

Use WebFetch to retrieve the component page:

```
URL: https://daisyui.com/components/<component_name>/
Prompt: List ALL CSS classes for this component, their purpose, and show the complete HTML examples. Include all variants (sizes, colors, styles). Show the full class reference table.
```

After fetching, write the raw component reference to `docs/daisyui/<Component-Name>.md` so it is
available locally next time. Use Capital-Kebab-Case for the filename — e.g. `docs/daisyui/Modal.md`,
`docs/daisyui/Radial-Progress.md`.

**Step 3 — Show project-specific usage**

Present the component with:

1. **Class reference** — table of all classes and what they do
2. **Basic HTML example** — adapted for Django templates (use `{% translate %}` for text, `{% heroicon_* %}` for icons, `{% url %}` for links)
3. **With HTMX** — if the component involves user interaction, show how to integrate with HTMX (e.g. `hx-get`, `hx-swap`, `hx-target`)
4. **With Alpine** — if the component needs JS behaviour beyond DaisyUI's CSS-only approach (e.g. close on escape, dynamic state), show the Alpine pattern

**Step 4 — Note any project conventions**

Remind the user of relevant conventions:
- Use `{% heroicon_mini %}` / `{% heroicon_outline %}` for icons, not inline SVGs
- Use `{% translate %}` for all user-visible text
- Use semantic DaisyUI colors (`primary`, `secondary`, `error`, etc.) not raw Tailwind colors
- For forms, use the `{% fragment "form.html" %}` wrapper — see `docs/Django-Templates.md`
- For HTMX partials, use `{% partialdef %}` / `{% partial %}` — see `docs/Django-Templates.md`

## Help

```
/djstudio daisyui <component>
```

Fetches DaisyUI component documentation and shows how to use it with this project's Django/HTMX/Alpine conventions. Caches the result in `docs/daisyui/` so subsequent lookups are instant.

**Arguments:**
- `<component>` — DaisyUI component name (e.g. `modal`, `drawer`, `tabs`, `tooltip`)

**Examples:**
```
/djstudio daisyui modal
/djstudio daisyui tabs
/djstudio daisyui drawer
/djstudio daisyui collapse
```
