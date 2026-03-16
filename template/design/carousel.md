# Carousel / Lightbox

Pattern built inline per project — no shipped template.

## Overview

An Alpine.js photo carousel with a full-screen lightbox overlay. Thumbnail
images are rendered server-side with `sorl-thumbnail`; the lightbox receives
photo URLs via `json_script` to avoid inline data interpolation.

## View

Serialise photo data in the view — never interpolate raw model data into
Alpine `x-data` attributes:

```python
photos = list(obj.photos.order_by("-is_cover", "created"))
photos_data = [{"url": photo.image.url, "pk": photo.pk} for photo in photos]
context = {"photos": photos, "photos_data": photos_data, ...}
```

## Template

```html
{% load heroicons i18n thumbnail %}

{% if photos %}
  {{ photos_data|json_script:"photos-data" }}

  <div id="photo-gallery"
       x-data="{
         open: false,
         current: 0,
         photos: [],
         init() { this.photos = JSON.parse(document.getElementById('photos-data').textContent); },
         openAt(index) { this.current = index; this.open = true; },
         prev() { this.current = (this.current - 1 + this.photos.length) % this.photos.length; },
         next() { this.current = (this.current + 1) % this.photos.length; },
       }">

    {# Thumbnail grid #}
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {% for photo in photos %}
        <button
          type="button"
          class="overflow-hidden rounded-lg border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:border-zinc-700"
          aria-label="{% translate "View photo" %}"
          @click="openAt({{ forloop.counter0 }})"
        >
          {% thumbnail photo.image "300x200" crop="center" as thumb %}
            <img
              src="{{ thumb.url }}"
              alt=""
              width="{{ thumb.width }}"
              height="{{ thumb.height }}"
              class="w-full object-cover transition-opacity hover:opacity-90"
              loading="lazy"
            >
          {% empty %}
            <div class="aspect-video bg-zinc-100 dark:bg-zinc-800"></div>
          {% endthumbnail %}
        </button>
      {% endfor %}
    </div>

    {# Lightbox overlay #}
    <div
      x-show="open"
      x-cloak
      x-transition
      role="dialog"
      aria-modal="true"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      @keyup.escape.window="open = false"
    >
      <button
        type="button"
        class="absolute top-4 right-4 text-white"
        aria-label="{% translate "Close" %}"
        @click="open = false"
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

      {# djlint:off H006 — dynamic Alpine src, no thumbnail object available #}
      <img
        :src="photos[current]?.url"
        alt=""
        class="max-h-[85vh] max-w-[85vw] rounded-lg object-contain shadow-xl"
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

## Notes

- `json_script` is required — never interpolate `photo.image.url` directly into
  `x-data`. Django's `json_script` filter escapes the data safely.
- Always use `{{ thumb.width }}` and `{{ thumb.height }}` from the
  `sorl-thumbnail` object for the grid thumbnails — never hardcode dimensions.
- The `{% empty %}` block inside `{% thumbnail %}` handles the case where no
  image file is set on the model instance.
- The lightbox `<img>` uses a dynamic Alpine `:src` binding, so no
  `{% thumbnail %}` object is available. `djlint:off H006` suppresses the
  missing-width/height lint warning for that element only.
- Keyboard navigation: `@keyup.escape.window` closes the overlay; prev/next
  buttons handle arrow-key navigation via `@click`. Add `@keyup.arrowleft.window`
  and `@keyup.arrowright.window` if keyboard navigation of photos is required.
- Accessibility: all buttons have `aria-label`, the overlay has `role="dialog"`
  and `aria-modal="true"`, thumbnail images use `alt=""` (decorative).
- `x-cloak` requires the Tailwind `x-cloak { display: none }` rule. This is
  already present in the generated project's base CSS.
