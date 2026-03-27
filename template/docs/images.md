# Images

This project uses [sorl-thumbnail](https://sorl-thumbnail.readthedocs.io/) for image
resizing and thumbnail generation. See `docs/packages.md` for installation notes.

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

### `thumbnail cleanup` is safe with S3

The `thumbnail cleanup` command only prunes stale entries from the cache index (the
key-value store). It does not delete any files from storage, so it works correctly
with S3 backends.

### `clear_delete_all` and `clear_delete_referenced` are unreliable with S3

The `thumbnail clear_delete_all` and `thumbnail clear_delete_referenced` management
commands delete actual thumbnail files from storage using `storage.listdir()`. This
does not work correctly with all S3-compatible backends, including Hetzner Object
Storage. These commands will complete without errors but will **not** delete thumbnail
files from S3.

Do not rely on these commands for file deletion in production S3 setups.

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
