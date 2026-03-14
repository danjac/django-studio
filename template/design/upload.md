# File Upload

## When to use

**Default: use `{{ field.as_field_group }}`** for any `FileField` or `ImageField`.
The standard widget handles single-file selection and is accessible by default.
Do not reach for this component unless you have a specific UX requirement that
the standard widget cannot meet.

Use this custom widget when you need:
- Drag-and-drop file selection
- Multi-file selection with per-file preview and removal before submit
- A styled drop zone (e.g. image gallery uploads, attachment pickers)

Do **not** use it for simple single-file fields — the extra Alpine complexity is
not worth it.

---

## Markup

```html
{% load i18n heroicons %}

<div id="file-upload"
     x-data="{
       files: [],
       addFiles(event) {
         const incoming = Array.from(event.target.files ?? event.dataTransfer.files);
         this.files = [...this.files, ...incoming];
       },
       removeFile(file) {
         this.files = this.files.filter(f => f !== file);
       },
     }"
     @dragover.prevent
     @drop.prevent="addFiles($event)">

  {# Drop zone #}
  <label class="block cursor-pointer rounded-lg border-2 border-dashed
                 border-border p-8 text-center hover:border-primary-400"
         for="file-input">
    {% heroicon_outline "arrow-up-tray" class="mx-auto size-8 text-text-muted" aria_hidden="true" %}
    <span class="mt-2 block text-sm text-text-muted">
      {% translate "Drag files here or click to browse" %}
    </span>
    <input id="file-input"
           type="file"
           multiple
           accept="image/*"
           class="sr-only"
           @change="addFiles($event)">
  </label>

  {# File preview grid #}
  <ul x-show="files.length" class="mt-4 grid grid-cols-3 gap-3" data-file-list>
    <template x-for="file in files" :key="file.name">
      <li class="relative rounded border border-border p-2 text-sm">
        <span x-text="file.name" class="block truncate"></span>
        <button type="button"
                class="absolute right-1 top-1"
                :aria-label="`{% translate 'Remove' %} ${file.name}`"
                @click="removeFile(file)">
          {% heroicon_mini "x-mark" class="size-4" aria_hidden="true" %}
        </button>
      </li>
    </template>
  </ul>
</div>
```

---

## Alpine conventions

| Rule | Reason |
|------|--------|
| Use `filter()` to remove items, not `splice()` | Assignment triggers reactivity; in-place mutation may not |
| Use spread `[...files, ...incoming]` to add items, not `push()` | Same reason |
| Pass **item value** to `removeFile`, not loop index | Index-based removal breaks after list reorder |
| Always give the root element a stable `id` | Needed to scope E2E selectors unambiguously |

---

## Accessibility

- The `<label>` wrapping the drop zone makes the entire area keyboard-activatable
  via the hidden `<input>`.
- The hidden input must have `id` matching the `for` attribute on the label.
- `multiple` and `accept` are required attributes — adjust `accept` to the allowed
  MIME types for your use case.
- Every remove button must have an `aria-label` that includes the filename so
  screen reader users know which file they are removing.
- Icons inside buttons must carry `aria_hidden="true"`.

---

## HTMX integration

Submit the file list to the server via a standard form `enctype="multipart/form-data"`.
HTMX does not natively handle `FormData` with file inputs — use a normal form
submit or a small Alpine helper that constructs a `FormData` and posts it with
`fetch`:

```html
<form method="post"
      enctype="multipart/form-data"
      hx-post="{% url 'upload' %}"
      hx-encoding="multipart/form-data"
      hx-target="#upload-result">
  ...
</form>
```

For drag-and-drop with HTMX, bind the `hx-vals` attribute dynamically or use
`htmx.ajax()` with a manually constructed `FormData`.

---

## Testing

Playwright cannot programmatically trigger drag-and-drop for file uploads.
Use `page.set_input_files()` on the hidden input instead:

```python
upload = page.locator("#file-upload")
upload.locator("#file-input").set_input_files([
    {"name": "photo.jpg", "mimeType": "image/jpeg", "buffer": b"..."},
])
# Verify the file appears in the preview list
expect(upload.locator("[data-file-list]")).to_contain_text("photo.jpg")
# Verify the remove button has an accessible label
remove_btn = upload.get_by_role("button", name="Remove photo.jpg")
expect(remove_btn).to_be_visible()
```
