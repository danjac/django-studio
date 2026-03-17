# File Storage

This project uses **Hetzner Object Storage** for user-uploaded media files in production.
Storage is always included in the project scaffold — activate it by setting `USE_S3_STORAGE=true`
and providing the Hetzner bucket credentials.

## Overview

| Environment | Backend | How media is served |
|-------------|---------|---------------------|
| Local dev | Django filesystem (`MEDIA_ROOT`) | Django dev server at `/media/` |
| Production | Hetzner Object Storage (S3-compatible) | Direct public URLs from the bucket |

The switch between backends is controlled by the `USE_S3_STORAGE` environment variable.
When `false` (the default), media files are written to the local `media/` directory.
When `true`, files go to Hetzner Object Storage via `django-storages`.

## Local Development

No extra configuration is needed. The default `.env` file leaves `USE_S3_STORAGE` unset,
so Django uses the local filesystem backend:

```
MEDIA_URL=/media/
MEDIA_ROOT=<project-root>/media/
```

The dev server automatically serves uploaded files at `/media/` (wired up in `config/urls.py`
via `django.conf.urls.static.static` when `DEBUG=True`).

The `media/` directory is gitignored. It is created automatically on first upload.

## Provisioning the Bucket (Terraform)

The `terraform/storage/` module provisions an S3-compatible bucket on Hetzner Object Storage
using the [MinIO Terraform provider](https://registry.terraform.io/providers/aminueza/minio).

### Prerequisites

Create S3 credentials in the Hetzner console before running Terraform:

> **Hetzner console** > Cloud > Security > S3 credentials > Generate credentials

### Steps

```bash
cd terraform/storage
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars  # set access_key, secret_key, and location
terraform init
terraform plan
terraform apply
```

Terraform outputs the bucket name and endpoint URL after apply:

```
bucket_name = "{{ project_slug }}-media"
endpoint_url = "https://fsn1.your-objectstorage.com"
```

The endpoint URL is always `https://<location>.your-objectstorage.com` — this is
a real Hetzner domain, not a placeholder.

### Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `access_key` | (required) | S3 access key from Hetzner console |
| `secret_key` | (required) | S3 secret key from Hetzner console |
| `bucket_name` | `{{ project_slug }}-media` | Bucket name (must be globally unique in region) |
| `location` | `fsn1` | Hetzner datacenter: `fsn1`, `nbg1`, `hel1`, `ash`, `hil` |

The bucket is created with `acl = "public-read"` — uploaded files are publicly accessible
via direct URL without signed URLs.

## Production Configuration

### Environment Variables

Once the bucket is provisioned, set these in the production environment:

| Variable | Description | Example |
|----------|-------------|---------|
| `USE_S3_STORAGE` | Enable S3 backend | `true` |
| `HETZNER_STORAGE_ACCESS_KEY` | S3 access key | from Hetzner console |
| `HETZNER_STORAGE_SECRET_KEY` | S3 secret key | from Hetzner console |
| `HETZNER_STORAGE_BUCKET` | Bucket name | `{{ project_slug }}-media` |
| `HETZNER_STORAGE_ENDPOINT` | S3 endpoint URL | `https://fsn1.your-objectstorage.com` |
| `HETZNER_STORAGE_REGION` | Region name (default: `fsn1`) | `fsn1` |

### Wiring into Helm

The Helm chart includes all storage env vars with `"false"`/empty defaults.
Fill in `helm/site/values.secret.yaml` after provisioning the bucket:

```yaml
secrets:
  useS3Storage: "true"
  hetznerStorageAccessKey: "<access-key>"
  hetznerStorageSecretKey: "<secret-key>"
  hetznerStorageBucket: "{{ project_slug }}-media"
  hetznerStorageEndpoint: "https://fsn1.your-objectstorage.com"
  hetznerStorageRegion: "fsn1"
```

Then redeploy:

```bash
just helm site
```

## Settings Reference

Relevant block in `config/settings.py`:

```python
# Media files / Object Storage
MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = BASE_DIR / "media"

if env.bool("USE_S3_STORAGE", default=False):
    STORAGES = {
        **STORAGES,
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
    }
    AWS_ACCESS_KEY_ID = env("HETZNER_STORAGE_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = env("HETZNER_STORAGE_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = env("HETZNER_STORAGE_BUCKET")
    AWS_S3_ENDPOINT_URL = env("HETZNER_STORAGE_ENDPOINT")
    AWS_S3_REGION_NAME = env("HETZNER_STORAGE_REGION", default="fsn1")
    AWS_DEFAULT_ACL = "public-read"
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL.rstrip('/')}/{AWS_STORAGE_BUCKET_NAME}/"
```

`django-storages` uses the `AWS_*` variable names regardless of provider — Hetzner Object
Storage is S3-compatible, so the same library works without modification.

## Dependency

`django-storages[s3]` is included in `pyproject.toml`. It brings in `boto3` as a transitive
dependency. No manual `uv add` is needed.

## sorl-thumbnail and S3

If you use [sorl-thumbnail](https://sorl-thumbnail.readthedocs.io/) with S3 storage,
there are several important behaviours to be aware of:

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
