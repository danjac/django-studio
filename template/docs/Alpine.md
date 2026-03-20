# Alpine.js

Alpine.js provides reactive JavaScript behavior without writing JavaScript files.

## Installation

Alpine.js is bundled locally in `static/vendor/`. To update it or add new JS dependencies, see `docs/Frontend-Dependencies.md`.

```html
<script src="{% static 'vendor/alpine.js' %}" defer></script>
```

## Basic Usage

### x-data

Declare component state:

```html
<div x-data="{show: false, count: 0}">
    <button @click="count++">Count: <span x-text="count"></span></button>
</div>
```

### Event Handlers

```html
<!-- Click -->
<button @click="show = true">Show</button>

<!-- Toggle -->
<button @click="show = !show">Toggle</button>

<!-- Outside click -->
<div @click.outside="show = false">...</div>

<!-- Keyboard -->
<input @keyup.escape="show = false">

<!-- Window events -->
<div @resize.window="handleResize()">
```

### Conditionals

```html
<!-- Show/hide -->
<div x-show="show">Visible when show is true</div>

<!-- With transition -->
<div x-show="show" x-transition>With fade</div>

<!-- x-if (needs template tag) -->
<template x-if="show">
    <div>Rendered only when show is true</div>
</template>
```

## Common Patterns

### Dropdown Menu

```html
<nav x-data="{showDropdown: false}" class="relative" id="dropdown">
    <button @click="showDropdown = !showDropdown"
            @click.outside="showDropdown=false"
            @keyup.escape.window="showDropdown=false">
        Toggle
    </button>

    <div x-show="showDropdown"
         x-transition.scale.origin.top
         x-cloak>
    </div>
</nav>
```

### Password Toggle

```html
<div x-data="{ show: false }">
    <input :type="show ? 'text' : 'password'">
    <button @click="show = !show">
        <span x-show="show">Hide</span>
        <span x-show="!show">Show</span>
    </button>
</div>
```

### Responsive Sidebar

```html
<div x-data="{showSidebar: false}">
    <button @click="showSidebar = !showSidebar">Menu</button>
    <div x-show="showSidebar" @click.outside="showSidebar = false">
    </div>
</div>
```

### Messages/Notifications

```html
<div x-data="{show: true}" x-show="show" x-transition>
    Message content
</div>
```

## Transitions

```html
<div x-show="show"
     x-transition:enter="transition ease-out duration-200"
     x-transition:enter-start="opacity-0"
     x-transition:enter-end="opacity-100"
     x-transition:leave="transition ease-in duration-150"
     x-transition:leave-start="opacity-100"
     x-transition:leave-end="opacity-0">
</div>
```

Or shorthand:
```html
<div x-show="show" x-transition>...</div>
```

## References (x-ref)

```html
<div x-data="{ adjustPositioning() {
    const el = this.$refs.dropdown;
}}" x-ref="dropdown">
</div>
```

## Init and Watch

```html
<div x-data="{count: 0}"
     x-init="count = 5"
     x-watch="count, () => console.log('changed')">
</div>
```

Or with $watch:
```html
<div x-data="{show: false}"
     x-init="$watch('show', () => $nextTick(() => adjust()))">
</div>
```

## Passing Server Data to Alpine

For simple scalar values, embed them directly in `x-data` or `x-init` using
`escapejs` for strings:

```html
<div x-data="{ username: '{{ request.user.username|escapejs }}' }">
```

For structured data (objects, arrays), use Django's `json_script` filter to
render a safe `<script type="application/json">` element and read it in
`x-init`:

```html
{{ object_list|json_script:"object-list-data" }}

<div x-data="{ items: [] }"
     x-init="items = JSON.parse(document.getElementById('object-list-data').textContent)">
```

Never interpolate raw template variables into JS expressions without escaping —
always use `escapejs` for strings or `json_script` for structured data.

## Icon-Only Buttons

Every button that contains only an SVG icon (no visible text) **must** have an
`aria-label`. Without it the button has no accessible name, which fails WCAG 2.1
SC 4.1.2 and makes Playwright selectors unreliable.

```html
<!-- BAD: no accessible name -->
<button @click="removeFile(file)" type="button">
  {% heroicon_mini "x-mark" class="size-4" aria_hidden="true" %}
</button>

<!-- GOOD: labelled and translatable -->
<button @click="removeFile(file)"
        type="button"
        aria-label="{% translate 'Remove file' %}">
  {% heroicon_mini "x-mark" class="size-4" aria_hidden="true" %}
</button>
```

This applies to all close, remove, toggle, and expand buttons generated inside
Alpine components. Always wrap the label text in `{% translate %}`.

## Component Root Identification

The `[x-data]` CSS selector matches the **first** Alpine component in DOM order,
which is usually the page-level layout wrapper — not the specific component you
intend. Give every interactive Alpine component a stable `id` or `data-component`
attribute so selectors and E2E tests can target it unambiguously:

```html
<!-- BAD: [x-data] matches the outermost Alpine component on the page -->
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open">...</div>
</div>

<!-- GOOD: stable root for scoped targeting -->
<div id="file-upload" x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open">...</div>
</div>

<!-- GOOD: data-component as an alternative -->
<div data-component="file-upload" x-data="{ open: false }">
  ...
</div>
```

Use `id` when the component appears exactly once on a page. Use `data-component`
for components that can appear multiple times (prefer scoping via the nearest
ancestor with a unique `id` in that case).

E2E selectors should always be scoped to this root:

```python
upload = page.locator("#file-upload")  # or [data-component="file-upload"]
upload.get_by_role("button", name="Add file").click()
```

## Array and Counter Mutations

Alpine's reactivity relies on assignment. In-place mutations (`splice`, `push`,
`++`, `--`) do not always trigger reactive updates and make logic harder to
follow. Always produce new values instead:

```html
<!-- BAD: in-place mutation -->
<div x-data="{ items: [], count: 0 }">
  <button @click="items.push(newItem)">Add</button>
  <button @click="items.splice(index, 1)">Remove</button>
  <button @click="count++">Up</button>
  <button @click="count--">Down</button>
</div>

<!-- GOOD: assignment -->
<div x-data="{ items: [], count: 0 }">
  <button @click="items = [...items, newItem]">Add</button>
  <button @click="items = items.filter(i => i !== item)">Remove</button>
  <button @click="count += 1">Up</button>
  <button @click="count -= 1">Down</button>
</div>
```

Inside `x-for`, pass the **item value** (not the loop index) to handlers so
removal works correctly after the list is reordered:

```html
<!-- BAD: index-based removal breaks after reorder -->
<template x-for="(item, index) in items" :key="item.id">
  <button @click="items.splice(index, 1)">Remove</button>
</template>

<!-- GOOD: value-based removal -->
<template x-for="item in items" :key="item.id">
  <button @click="items = items.filter(i => i !== item)">Remove</button>
</template>
```

## Best Practices

1. **Use `x-cloak`** to prevent flash of unstyled content:
```css
[x-cloak] { display: none !important; }
```

2. **Use `$nextTick`** when manipulating DOM after state changes:
```html
<button @click="show = true; $nextTick(() => input.focus())">
```

3. **Use `.window`** for global event listeners:
```html
<button @keyup.escape.window="close()">
```

4. **Combine with HTMX** - Alpine handles client-side state, HTMX handles server communication

### Alpine.data for Complex Components

Follow this progression based on component complexity:

**1. Simple state** — inline `x-data` is fine for small, self-contained components:

```html
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open">Content</div>
</div>
```

**2. Complex logic** — move to `Alpine.data()` in a `<script>` tag inside the
page's `{% block scripts %}` block (rendered in the footer, before `</body>`):

```html
{% block scripts %}
  {{ block.super }}
  <script>
    document.addEventListener('alpine:init', () => {
      Alpine.data('myComponent', (param) => ({
        value: param,
        doSomething() { ... },
      }));
    });
  </script>
{% endblock scripts %}
```

Then reference it in the template:

```html
<div x-data="myComponent('{{ django_var }}')">...</div>
```

**3. Reused across pages** — extract to a JS file under `static/` and include
it via a `<script src="...">` tag in `{% block scripts %}`. Do **not** add
`defer`:

```html
{% block scripts %}
  {{ block.super }}
  <script src="{% static 'my_component.js' %}"></script>
{% endblock scripts %}
```

See: https://alpinejs.dev/globals/alpine-data

## Script Loading Order

Alpine component scripts (`Alpine.data()`, `Alpine.store()`) must be placed in
`{% block scripts %}` at the bottom of `<body>` and must **not** use `defer`.

**Why:**

Alpine itself loads with `defer` in `<head>`. Scripts at the bottom of `<body>`
without `defer` execute before deferred scripts fire. This means by the time
Alpine's deferred script dispatches `alpine:init`, the `Alpine.data()`
registrations are already in place. If you add `defer` to component scripts in
`<head>`, their execution order relative to Alpine is ambiguous and registration
may fail silently.

```django
{# base.html <head> — Alpine itself uses defer #}
<script src="{% static 'vendor/alpine.js' %}" defer></script>

{# {% block scripts %} at bottom of <body> — NO defer on component scripts #}
{% block scripts %}
  <script src="{% static 'my-component.js' %}"></script>
{% endblock scripts %}
```

**Wrong — do not do this:**

```django
{# In <head> with defer — component registration may fail #}
<script src="{% static 'my-component.js' %}" defer></script>
```

### URL Resolution in Alpine Components

Backend API endpoints must **never** be resolved in JavaScript. Always resolve
them in the Django template or view using `{% url %}` or `reverse()`, then pass
them as arguments to the component.

**For a fixed URL** (no dynamic segments), pass it as a constructor argument:

```html
<div x-data="myComponent('{% url "app:some_action" object.pk %}')">
```

```js
Alpine.data('myComponent', (actionUrl) => ({
  doSomething() {
    htmx.ajax('POST', actionUrl, { ... });
  },
}));
```

**For a per-item URL** (e.g. each item in a loop has its own URL), pass it
alongside the item identifier in the event handler:

```html
{% for item in items %}
  <li @dragstart="onDragStart({{ item.pk }}, '{% url "app:item_action" item.pk %}')">
{% endfor %}
```

```js
onDragStart(id, actionUrl) {
  this.dragging = { id, actionUrl };
},
onDrop() {
  htmx.ajax('POST', this.dragging.actionUrl, { ... });
},
```

This keeps all URL knowledge in the template layer where Django's `{% url %}` tag
can reverse them correctly, and avoids breakage when URL patterns change.
