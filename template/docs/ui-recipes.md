# UI Recipes

Composite patterns combining Alpine.js, HTMX, Tailwind, and Django templates.

## Contents

- [Dropdown menu](#dropdown-menu)
- [Photo Lightbox](#photo-lightbox)
- [Drag and Drop](#drag-and-drop)
- [Multiple File Upload](#multiple-file-upload)

## Dropdown menu

A reusable Alpine `dropdown()` component for action menus and navigation dropdowns.
Register it once in your base template's `{% block scripts %}` block:

```html
{% block scripts %}
  {{ block.super }}
  <script>
    document.addEventListener('alpine:init', () => {
      Alpine.data('dropdown', () => ({
        open: false,
        toggle() { this.open = !this.open; },
        close() { this.open = false; },
      }));
    });
  </script>
{% endblock scripts %}
```

### Basic usage

```html
<div
  class="relative"
  x-data="dropdown()"
  @click.outside="close()"
  @keyup.escape.window="close()"
>
  <button
    type="button"
    class="btn btn-ghost"
    :aria-expanded="open.toString()"
    @click="toggle()"
  >
    Options
    {% heroicon_mini "chevron-down" class="size-4" aria_hidden="true" %}
  </button>
  <ul
    class="absolute right-0 z-20 p-2 mt-1 w-48 border shadow-xl menu bg-base-100 rounded-box border-base-300"
    x-cloak
    x-show="open"
    x-transition.scale.origin.top
    role="menu"
  >
    <li role="menuitem"><a href="#">Action</a></li>
  </ul>
</div>
```

### Form actions inside a dropdown

When a dropdown item needs to submit a POST form (e.g. logout, language switch), do
not nest the `<form>` inside the `x-show` list — place it with `hidden` outside the
list and reference it from the button via `form="..."`. Add `hx-disable="true"` so
HTMX does not intercept these full-page POSTs.

```html
{# Form lives outside x-show, referenced by id #}
<form id="my-action-form" method="post" action="{% url 'my:action' %}" hx-disable="true" hidden>
  {% csrf_token %}
  {# any hidden inputs #}
</form>

<div
  class="relative"
  x-data="dropdown()"
  @click.outside="close()"
  @keyup.escape.window="close()"
>
  <button type="button" :aria-expanded="open.toString()" @click="toggle()" class="btn btn-ghost">
    Label
  </button>
  <ul class="absolute right-0 z-20 p-2 mt-1 w-48 border shadow-xl menu bg-base-100 rounded-box border-base-300"
      x-cloak x-show="open" x-transition.scale.origin.top role="menu">
    <li role="menuitem">
      <button type="submit" form="my-action-form">{% translate "Do action" %}</button>
    </li>
  </ul>
</div>
```

---

## Photo Lightbox

A full-screen photo viewer with keyboard navigation and focus trapping. Uses
`Alpine.data` because the logic is too involved for inline `x-data`. Pass the
photo list from Django via `json_script`.

### JS component

Place in `{% block scripts %}` (no `defer`):

```html
{% block scripts %}
  {{ block.super }}
  <script>
    document.addEventListener('alpine:init', () => {
      Alpine.data('lightbox', (photos) => ({
        open: false,
        current: 0,
        photos,

        openLightbox(index) {
          this.current = index;
          this.open = true;
          this.$nextTick(() => this.$refs.closeButton.focus());
        },

        closeLightbox() {
          this.open = false;
        },

        prev() {
          this.current = (this.current - 1 + this.photos.length) % this.photos.length;
        },

        next() {
          this.current = (this.current + 1) % this.photos.length;
        },

        trapFocus(event) {
          const focusable = this.$el.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (event.shiftKey) {
            if (document.activeElement === first) {
              event.preventDefault();
              last.focus();
            }
          } else {
            if (document.activeElement === last) {
              event.preventDefault();
              first.focus();
            }
          }
        },
      }));
    });
  </script>
{% endblock scripts %}
```

### Template

Pass photos via `json_script` to avoid XSS. The `photos` array must contain
objects with at least a `url` key:

```python
# views.py
photos_json = [{"url": photo.image.url} for photo in photos]
```

```html
{# In template #}
{{ photos_json|json_script:"photos-data" }}

{% if photos %}
  <div
    id="photo-gallery"
    x-data="lightbox(JSON.parse(document.getElementById('photos-data').textContent))"
  >
    {# Thumbnail grid #}
    <ul class="grid grid-cols-3 gap-2">
      {% for photo in photos %}
        {# djlint:off H006 #}
        <li>
          {% thumbnail photo.image "200x200" crop="center" as im %}
            <img
              src="{{ im.url }}"
              alt="{% translate "Photo" %} {{ forloop.counter }}"
              width="{{ im.width }}"
              height="{{ im.height }}"
              class="rounded-lg cursor-pointer"
              @click="openLightbox({{ forloop.counter0 }})"
            >
          {% endthumbnail %}
        </li>
        {# djlint:on #}
      {% endfor %}
    </ul>

    {# Lightbox #}
    <div
      x-show="open"
      x-cloak
      x-transition
      role="dialog"
      aria-modal="true"
      aria-label="{% translate "Photo viewer" %}"
      class="flex fixed inset-0 z-50 justify-center items-center bg-black/80"
      @keyup.escape.window="closeLightbox()"
      @keydown.left.window="open && prev()"
      @keydown.right.window="open && next()"
      @keydown.tab="trapFocus($event)"
    >
      <button
        type="button"
        x-ref="closeButton"
        class="absolute top-4 right-4 text-white"
        aria-label="{% translate "Close" %}"
        @click="closeLightbox()"
      >
        {% heroicon_outline "x-mark" class="size-8" aria_hidden="true" %}
      </button>

      <button
        type="button"
        class="absolute left-4 text-white disabled:opacity-30"
        aria-label="{% translate "Previous photo" %}"
        :disabled="photos.length <= 1"
        @click="prev()"
      >
        {% heroicon_outline "chevron-left" class="size-10" aria_hidden="true" %}
      </button>

      {# djlint:off H006 #}
      <img
        :src="photos[current]?.url"
        :alt="'{% translate "Photo" %} ' + (current + 1) + ' {% translate "of" %} ' + photos.length"
        class="object-contain rounded-lg shadow-xl max-h-[85vh] max-w-[85vw]"
      >
      {# djlint:on #}

      <button
        type="button"
        class="absolute right-4 text-white disabled:opacity-30"
        aria-label="{% translate "Next photo" %}"
        :disabled="photos.length <= 1"
        @click="next()"
      >
        {% heroicon_outline "chevron-right" class="size-10" aria_hidden="true" %}
      </button>

      <span class="absolute bottom-4 text-sm text-white/70">
        <span x-text="current + 1"></span> / <span x-text="photos.length"></span>
      </span>
    </div>
  </div>
{% endif %}
```

---

## Drag and Drop

A palette-to-grid drag-and-drop pattern: items in a sidebar are dragged onto
drop targets, triggering an HTMX POST via `htmx.ajax`. CSRF credentials and the
action URL are passed as constructor arguments so the component stays reusable.

### JS component

```html
{% block scripts %}
  {{ block.super }}
  <script>
    document.addEventListener('alpine:init', () => {
      Alpine.data('dragDrop', (csrfHeader, csrfToken, actionUrl) => ({
        dragging: null,

        onDragStart(item) {
          this.dragging = item;
        },

        onDragEnd() {
          this.dragging = null;
        },

        onDrop(target) {
          if (!this.dragging) return;
          htmx.ajax('POST', actionUrl, {
            values: { ...this.dragging, ...target },
            headers: { [csrfHeader]: csrfToken },
            target: '#drop-area',
            swap: 'outerHTML',
          });
          this.dragging = null;
        },
      }));
    });
  </script>
{% endblock scripts %}
```

### Template

Pass CSRF credentials and the resolved URL as constructor arguments. Use
`{% url %}` in the template — never resolve URLs in JavaScript (see `docs/alpine.md`):

```html
<div
  id="drag-drop"
  x-data="dragDrop('{{ csrf_header }}', '{{ csrf_token }}', '{% url "app:action" object.pk %}')"
>
  {# Palette: draggable items #}
  <ul>
    {% for item in palette %}
      <li
        draggable="true"
        @dragstart="onDragStart({ type: '{{ item.type }}' })"
        @dragend="onDragEnd()"
        class="cursor-grab active:cursor-grabbing"
      >
        {{ item.label }}
      </li>
    {% endfor %}
  </ul>

  {# Drop area: swap target for HTMX #}
  <div id="drop-area">
    {% partialdef drop-area inline %}
      <div class="grid grid-cols-5 gap-2">
        {% for cell in grid %}
          <div
            @dragover.prevent
            @drop.prevent="onDrop({ row: {{ cell.row }}, col: {{ cell.col }} })"
            class="flex justify-center items-center w-16 h-16 rounded border border-zinc-200 dark:border-zinc-700"
          >
            {% if cell.item %}{{ cell.item }}{% endif %}
          </div>
        {% endfor %}
      </div>
    {% endpartialdef drop-area %}
  </div>
</div>
```

The HTMX response should re-render only the `#drop-area` div contents (use the
`drop-area` partial as the view's response template).

---

## Multiple File Upload

A multi-file picker with drag-and-drop, instant previews, and per-file removal.
Alpine.js manages the file list; the `DataTransfer` API syncs it back to the
native `<input>` so the Django form submission works normally.

For the Django form side (CSP, `multipart=True`, HTMX integration), see
`docs/django-forms.md#multiple-file-upload`.

### JS component

Place in `{% block scripts %}` (no `defer`), or extract to `static/` if reused
across pages:

```html
{% block scripts %}
  {{ block.super }}
  <script>
    document.addEventListener('alpine:init', () => {
      Alpine.data('fileUpload', () => ({
        files: [],
        previews: {},

        addFiles(event) {
          const incoming = Array.from(event.target?.files ?? event.dataTransfer?.files ?? []);
          this.files = [...this.files, ...incoming];
          incoming.forEach(f => { this.previews = {...this.previews, [f.name]: URL.createObjectURL(f)}; });
          this.syncInput();
        },

        removeFile(file) {
          URL.revokeObjectURL(this.previews[file.name]);
          const p = {...this.previews};
          delete p[file.name];
          this.previews = p;
          this.files = this.files.filter(f => f !== file);
          this.syncInput();
        },

        syncInput() {
          const dt = new DataTransfer();
          this.files.forEach(f => dt.items.add(f));
          this.$refs.fileInput.files = dt.files;
        },
      }));
    });
  </script>
{% endblock scripts %}
```

### Template

```html
<div
  id="file-upload-zone"
  x-data="fileUpload()"
  @dragover.prevent
  @drop.prevent="addFiles($event)"
>
  <label
    class="block p-8 text-center rounded-lg border-2 border-dashed cursor-pointer border-zinc-300 hover:border-primary-400"
    for="file-input"
  >
    {% heroicon_outline "arrow-up-tray" class="mx-auto size-8 text-zinc-400" aria_hidden="true" %}
    <span class="block mt-2 text-sm text-zinc-500">
      {% translate "Drag files here or click to browse" %}
    </span>
    <input
      id="file-input"
      name="files"
      type="file"
      multiple
      accept="image/*"
      class="sr-only"
      x-ref="fileInput"
      @change="addFiles($event)"
    >
  </label>

  <ul x-show="files.length" class="grid grid-cols-3 gap-3 mt-4">
    <template x-for="(file, index) in files" :key="file.name">
      <li class="overflow-hidden relative rounded-lg border border-zinc-200 dark:border-zinc-700">
        {# djlint:off H006 #}
        <img
          :src="previews[file.name]"
          :alt="'{% translate "Selected file" %} ' + (index + 1)"
          width="300"
          height="200"
          class="object-cover w-full aspect-video"
        >
        {# djlint:on #}
        <button
          type="button"
          class="absolute top-1 right-1 p-1 text-white rounded-full bg-black/50"
          aria-label="{% translate "Remove" %}"
          @click="removeFile(file)"
        >
          {% heroicon_mini "x-mark" class="size-4" aria_hidden="true" %}
        </button>
      </li>
    </template>
  </ul>
</div>
```

**Key points:**

- `syncInput()` uses `DataTransfer` to keep the native `<input>` in sync — without
  this, the form submits an empty file list.
- Call `URL.revokeObjectURL` on remove to prevent memory leaks.
- The upload/delete workflow for existing server-side files is project-specific —
  implement via HTMX partial swaps.
