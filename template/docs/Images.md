# Images

This project uses [sorl-thumbnail](https://sorl-thumbnail.readthedocs.io/) for image
resizing and thumbnail generation. See `docs/Packages.md` for installation notes.

## Thumbnail widget with instant preview

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
        <img
          src="{{ image.url }}"
          :src="previewUrl ?? '{{ image.url }}'"
          alt="{% translate "Preview" %}"
          width="320"
          height="160"
          class="mb-2 rounded-lg max-w-xs max-h-40 object-contain"
        />
      {% else %}
        <template x-if="previewUrl">
          <img
            :src="previewUrl"
            alt="{% translate "Preview" %}"
            width="320"
            height="160"
            class="mb-2 rounded-lg max-w-xs max-h-40 object-contain"
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
does not include it. Only add it to views that serve upload forms — use `@csp_update`
to apply it per-view rather than globally:

```python
from django.utils.csp import csp_update

@csp_update(IMG_SRC=["blob:"])
def my_upload_view(request):
    ...
```

## sorl-thumbnail and S3

If you use sorl-thumbnail with S3 storage (see `docs/File-Storage.md`), there are
several important behaviours to be aware of:

### Management commands are unreliable with S3

The `thumbnail cleanup`, `thumbnail clear`, `thumbnail clear_delete_all`, and
`thumbnail clear_delete_referenced` management commands use `storage.listdir()`
internally. This does not work correctly with all S3-compatible backends, including
Hetzner Object Storage. These commands will complete without errors but will **not**
delete thumbnail files from S3.

Do not rely on management commands for thumbnail cleanup in production S3 setups.

### Thumbnail cleanup on model deletion works via signal

sorl-thumbnail's `ImageField` fires a `post_delete` signal that deletes associated
thumbnail cache files from S3 when a model instance is deleted. This is the reliable
cleanup path and works correctly.

### Original files are not auto-deleted

Django does not delete `ImageField`/`FileField` files from storage when a model
instance is deleted. This is standard Django behaviour. Add an explicit `post_delete`
signal to handle it:

```python
from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=Photo)
def delete_photo_file(sender, instance, **kwargs):
    instance.photo.delete(save=False)
```

Without this, deleted model instances will leave orphaned files in your S3 bucket.
