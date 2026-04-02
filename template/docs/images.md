# Images

This project uses [sorl-thumbnail](https://sorl-thumbnail.readthedocs.io/) for image
resizing and thumbnail generation. See `docs/packages.md` for installation notes.

## Contents

- [Rendering thumbnails in templates](#rendering-thumbnails-in-templates)
- [Thumbnail widget with instant preview](#thumbnail-widget-with-instant-preview)
- [Thumbnail cache cleanup](#thumbnail-cache-cleanup)
- [sorl-thumbnail and S3](#sorl-thumbnail-and-s3)

## Rendering thumbnails in templates

Use the `{% thumbnail %}` tag to resize an image and render it with correct dimensions:

```html
{% load thumbnail %}

{% thumbnail photo.image "300x200" crop="center" as thumb %}
  <img src="{{ thumb.url }}" width="{{ thumb.width }}" height="{{ thumb.height }}" alt="...">
{% endthumbnail %}
```

- The geometry string (`"300x200"`) sets the bounding box. sorl-thumbnail preserves aspect
  ratio by default — use `crop="center"` (or another anchor) to fill the box exactly.
- Always set `width` and `height` on the `<img>` from `thumb.width`/`thumb.height` — these
  reflect the actual rendered dimensions after resizing, preventing layout shift.
- The block is skipped if the source image is missing or empty, so no `{% if %}` guard is needed.

Common geometry formats:

| Geometry | Behaviour |
|----------|-----------|
| `"300x200"` | Fit within 300×200, preserve aspect ratio |
| `"300x200"` + `crop="center"` | Fill 300×200, crop to center |
| `"300"` | Scale to width 300, height auto |
| `"x200"` | Scale to height 200, width auto |

## Thumbnail widget with instant preview

For upload form widgets with inline preview, see `docs/django-forms.md#thumbnail-widget`.

## Thumbnail cache cleanup

The thumbnail cache is **not** automatically cleared when the original image is deleted.
Add a daily cron job to remove stale cache entries:

```bash
./manage.sh thumbnail cleanup
```

See `docs/cron-jobs.md` for instructions on adding cron jobs.

## sorl-thumbnail and S3

If you use sorl-thumbnail with S3 storage (see `docs/file-storage.md`), there are
several important behaviours to be aware of:

### `thumbnail cleanup` removes stale cache entries from storage

`thumbnail cleanup` removes stale cache entries from storage. It does not remove
original images — that is handled by sorl-thumbnail's `post_delete` signal (see below).

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
