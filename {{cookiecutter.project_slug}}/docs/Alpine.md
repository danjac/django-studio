# Alpine.js

Alpine.js provides reactive JavaScript behavior without writing JavaScript files.

## Installation

```html
<script src="https://cdn.jsdelivr.net/npm/alpinejs@{{ ALPINE_VERSION }}/dist/cdn.min.js" defer></script>
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

### Complex Functionality

For complex functionality that exceeds what Alpine's declarative approach can handle elegantly, create a reusable JavaScript component:

```javascript
// In a separate JS file
document.addEventListener('alpine:init', () => {
    Alpine.data('dropdown', () => ({
        open: false,
        toggle() {
            this.open = !this.open
        },
        close() {
            this.open = false
        }
    }))
})
```

Then use in HTML:
```html
<div x-data="dropdown">
    <button @click="toggle()">Toggle</button>
    <div x-show="open" @click.outside="close()">Content</div>
</div>
```

See: https://alpinejs.dev/essentials/state#re-usable-data
