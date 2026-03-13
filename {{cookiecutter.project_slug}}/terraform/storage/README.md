# terraform/storage

Provisions a Hetzner Object Storage bucket for Django media uploads.
Hetzner Object Storage is S3-compatible; this module uses the MinIO Terraform
provider since Hetzner does not expose a bucket API through the hcloud provider.

## What This Configures

- **S3 bucket** with public-read ACL for serving media files

## Prerequisites

1. **Hetzner Cloud account** with a project already created
2. **S3 credentials** — generate these in the Hetzner Cloud Console:
   - Cloud Console → `<your project>` → Security → S3 credentials → Generate credentials
   - Note both the **Access Key** and **Secret Key** — the secret is only shown once

## Setup

```bash
cd terraform/storage
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars   # set access_key, secret_key
terraform init
terraform plan
terraform apply
```

## Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `access_key` | yes | - | S3 access key from Hetzner Console |
| `secret_key` | yes | - | S3 secret key from Hetzner Console |
| `bucket_name` | no | `{{cookiecutter.project_slug}}-media` | Bucket name (globally unique per region) |
| `location` | no | `fsn1` | Datacenter location — must match your cluster |

## Outputs

After `terraform apply`, get the values needed for your Helm secrets:

```bash
terraform output bucket_name    # → HETZNER_STORAGE_BUCKET
terraform output endpoint_url   # → HETZNER_STORAGE_ENDPOINT
```

Set these in `helm/site/values.secret.yaml` alongside the access key and secret key:

```yaml
secrets:
  storage:
    accessKey: "<access_key>"
    secretKey: "<secret_key>"
    bucket: "<bucket_name>"
    endpoint: "https://fsn1.your-objectstorage.com"
```

## Troubleshooting

**Authentication error on `terraform init`/`apply`** — double-check `access_key` and `secret_key`
in `terraform.tfvars`. The secret is only shown once when you generate credentials; if lost,
delete and regenerate in the Hetzner Console.

**Bucket name already taken** — bucket names are globally unique within a region. Change
`bucket_name` in `terraform.tfvars` to something unique (e.g. add a random suffix).

**Wrong region** — `location` in `terraform.tfvars` must match the datacenter where your
Hetzner cluster is deployed. A bucket in `fsn1` cannot be accessed via the `nbg1` endpoint.
