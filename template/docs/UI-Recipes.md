# UI Recipes

Composite patterns combining Alpine.js, HTMX, Tailwind, and Django templates.

## Contents

- [Image Upload Preview](#image-upload-preview)
- [Photo Lightbox](#photo-lightbox)
- [Drag and Drop](#drag-and-drop)
- [Maps (OpenStreetMap)](#maps-openstreetmap)

## Image Upload Preview

For `ImageField` forms, use a `thumbnailwidget` partial that shows the current image
and an Alpine.js-powered preview of the newly selected file:

```html
{# form/partials.html #}

{% partialdef thumbnailwidget %}
  {% partial label %}
  {% with image=field.form.instance.image %}
    <div
      x-data="{ previewUrl: null }"
      @change="previewUrl = $event.target.files[0] ? URL.createObjectURL($event.target.files[0]) : null"
    >
      {% if image %}
        {% thumbnail image "340x240" crop="center" as im %}
          <img
            src="{{ im.url }}"
            :src="previewUrl ?? '{{ im.url }}'"
            alt="{% translate "Preview" %}"
            width="{{ im.width }}"
            height="{{ im.height }}"
            class="mb-2 rounded-lg"
          />
        {% empty %}
        {% endthumbnail %}
      {% else %}
        <template x-if="previewUrl">
          <img
            :src="previewUrl"
            alt="{% translate "Preview" %}"
            width="340"
            height="240"
            class="mb-2 rounded-lg"
          />
        </template>
      {% endif %}
      {% render_field field class="file-input" %}
    </div>
  {% endwith %}
{% endpartialdef thumbnailwidget %}
```

Replace `field.form.instance.image` with the actual field accessor for your model.
Use `widget_type` to dispatch to this partial automatically, or call `{% partial thumbnailwidget %}` directly.

**CSP note:** `URL.createObjectURL` generates a `blob:` URL. The default strict CSP
does not include it. In `config/settings.py`, define an upload variant of your base CSP
policy and pass it to `@csp_override` on views that serve upload forms:

```python
# config/settings.py
from django.utils.csp import CSP

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:"],
    # ... your full policy
}

# Extends SECURE_CSP to allow blob: URLs for file upload previews.
SECURE_CSP_UPLOAD = {**SECURE_CSP, "img-src": [CSP.SELF, "data:", "blob:"]}
```

```python
# views.py
from django.conf import settings
from django.views.decorators.csp import csp_override

@csp_override(settings.SECURE_CSP_UPLOAD)
def my_upload_view(request):
    ...
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
`{% url %}` in the template — never resolve URLs in JavaScript (see `docs/Alpine.md`):

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

## Maps (OpenStreetMap)

Free map embedding via [OpenStreetMap](https://www.openstreetmap.org/) and geocoding
via [geopy](https://geopy.readthedocs.io/) (Nominatim). No API key required for either.

### CSP

Add `frame-src` to `SECURE_CSP` in `config/settings.py` to allow the OSM iframe:

```python
SECURE_CSP = {
    ...
    "frame-src": ["https://www.openstreetmap.org"],
}
```

### Model fields

Store coordinates as `DecimalField` — `FloatField` loses precision at scale:

```python
from django.db import models

class Venue(models.Model):
    ...
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def get_osm_embed_url(self, osm_margin: float = 0.1) -> str | None:
        if self.latitude is not None and self.longitude is not None:
            lat, lon = float(self.latitude), float(self.longitude)
            bbox = f"{lon - osm_margin},{lat - osm_margin},{lon + osm_margin},{lat + osm_margin}"
            return (
                f"https://www.openstreetmap.org/export/embed.html"
                f"?bbox={bbox}&layer=mapnik&marker={lat},{lon}"
            )
        return None
```

### Geocoding task

Run geocoding in the background with `django-tasks` so it never blocks a request.
Use `filter().update()` rather than `instance.save()` to avoid re-triggering signals.

```python
import logging

from django.db import models
from django_tasks import task
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)


def _geocode(address: str) -> object:
    """Run Nominatim geocoding synchronously."""
    return Nominatim(user_agent="my-project").geocode(address)


@task
def geocode_venue(*, venue_pk: int) -> None:
    """Geocode a venue's address and store the lat/lng coordinates."""
    try:
        venue = Venue.objects.get(pk=venue_pk)
    except Venue.DoesNotExist:
        logger.warning("geocode_venue: venue %d not found", venue_pk)
        return

    address_parts = filter(
        None,
        [
            venue.street_address,
            venue.city,
            venue.region,
            venue.postal_code,
            str(venue.country.name) if venue.country else None,
        ],
    )
    address = ", ".join(address_parts)
    location = _geocode(address)

    if location is None:
        logger.warning("geocode_venue: no result for venue %d (%r)", venue_pk, address)
        return

    Venue.objects.filter(pk=venue_pk).update(
        latitude=location.latitude,  # type: ignore[attr-defined]
        longitude=location.longitude,  # type: ignore[attr-defined]
    )
```

### Triggering geocoding on save

Use a `post_save` signal to enqueue the task whenever the address changes. Check
for coordinate presence to avoid re-geocoding on every save:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Venue)
def enqueue_geocoding(
    sender: type[Venue],
    instance: Venue,
    created: bool,
    update_fields: frozenset[str] | None,
    **kwargs: object,
) -> None:
    address_fields = {"street_address", "city", "region", "postal_code", "country"}
    fields_changed = update_fields is None or bool(address_fields & set(update_fields))
    if fields_changed:
        geocode_venue.enqueue(venue_pk=instance.pk)
```

Connect the signal in `apps.py`:

```python
class VenuesConfig(AppConfig):
    ...
    def ready(self) -> None:
        import venues.signals  # noqa: F401
```

### Template embed

```html+django
{% with osm_embed_url=object.get_osm_embed_url %}
  {% if osm_embed_url %}
  <div>
    <iframe
      src="{{ osm_embed_url }}"
      title="{% translate "Map" %}"
      class="w-full rounded-lg border border-zinc-200 dark:border-zinc-700"
      height="300"
      loading="lazy"
      referrerpolicy="no-referrer"
      sandbox="allow-scripts allow-same-origin"
    ></iframe>
    <p class="mt-1 text-xs text-zinc-500">
      {% blocktranslate trimmed %}
        Map data &copy;
        <a
          href="https://www.openstreetmap.org/copyright"
          class="underline"
          target="_blank"
          rel="noopener noreferrer"
        >OpenStreetMap</a>
        contributors
      {% endblocktranslate %}
    </p>
  </div>
  {% endif %}
{% endwith %}
```
