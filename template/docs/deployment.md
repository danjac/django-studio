# Deployment

This project uses Terraform for infrastructure provisioning and Helm for Kubernetes deployment.

## Contents

- [Overview](#overview)
- [Terraform](#terraform)
- [Helm](#helm)
- [CI/CD Pipeline](#cicd-pipeline)
- [Production Commands](#production-commands)

## Overview

| Layer | Tool | What it does |
|-------|------|--------------|
| Infrastructure | Terraform (hetzner) | Servers, network, firewall, Postgres volume; K3s via cloud-init |
| DNS / CDN / SSL | Terraform (cloudflare) | DNS A record, CDN caching, TLS settings |
| Kubernetes objects | Helm (`helm/site/`) | App, workers, cron jobs, Postgres, Redis, ingress |
| Observability | Helm (`helm/observability/`) | Prometheus, Grafana, Loki, Tempo, OTel |

## Terraform

### Structure

```
terraform/
├── hetzner/        # Hetzner Cloud infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars.example
│   └── templates/
│       ├── cloud_init_server.tftpl
│       ├── cloud_init_database.tftpl
│       └── cloud_init_agent.tftpl
├── cloudflare/     # Cloudflare DNS/CDN
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars.example
├── storage/        # Hetzner Object Storage bucket for media uploads
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
└── backups/        # Hetzner Object Storage bucket for database backups (private)
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    └── terraform.tfvars.example
```

The `storage/` and `backups/` modules are independent of the other two — each can be
applied at any time after the bucket credentials are created.

- See `docs/file-storage.md` for the media storage workflow.
- See `docs/database-backups.md` for the database backup workflow, or run `/dj-enable-db-backups`.

### Commands

```bash
cd terraform/hetzner && cp terraform.tfvars.example terraform.tfvars
just terraform hetzner init
just terraform hetzner plan
just terraform hetzner apply

cd terraform/cloudflare && cp terraform.tfvars.example terraform.tfvars
just terraform cloudflare apply
```

After applying, create a Cloudflare origin certificate so TLS terminates at your server:

> Cloudflare Dashboard → SSL/TLS → Origin Server → Create Certificate (15-year validity)

Paste the certificate and key into `helm/site/values.secret.yaml` before deploying.

### Variables

Copy the example file and fill in required values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Never commit `terraform.tfvars` - it's gitignored.

## Helm

### Structure

```
helm/
├── {{ project_slug }}/   # Application chart
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values.secret.yaml.example
│   └── templates/
│       ├── configmap.yaml
│       ├── secret.yaml
│       ├── django-deployment.yaml
│       ├── django-worker-deployment.yaml
│       ├── django-service.yaml
│       ├── ingress-route.yaml
│       ├── postgres-statefulset.yaml
│       ├── postgres-pv.yaml
│       ├── postgres-pvc.yaml
│       ├── postgres-service.yaml
│       ├── redis-deployment.yaml
│       ├── redis-service.yaml
│       └── cronjobs.yaml
└── observability/  # Optional monitoring chart
    ├── Chart.yaml
    ├── values.yaml
    └── values.secret.yaml.example
```

### Commands

```bash
# Deploy or update the application
# Runs helm dependency build automatically, then helm upgrade --install
just helm site

# Deploy or update the observability stack
# Also runs helm dependency build — required on first install (fetches kube-prometheus-stack, loki, etc.)
just helm observability
```

### Secrets

Copy and fill in the secrets file:

```bash
cp helm/site/values.secret.yaml.example helm/site/values.secret.yaml
```

`values.secret.yaml` is gitignored — never commit it.

The `postgres.volumePath` value must match the Hetzner volume mount path provisioned by
Terraform:

```bash
terraform -chdir=terraform/hetzner output -raw postgres_volume_mount_path
# e.g. /mnt/HC_Volume_12345678
```

Both charts ship resource defaults tuned for the Terraform default server type (`cx23`:
2 vCPU, 4 GB RAM). If you change `server_type` in `terraform.tfvars`, override the
corresponding resource values in `values.secret.yaml`.

## CI/CD Pipeline

The `deploy` GitHub Actions workflow:

1. Runs tests (`checks.yml`)
2. Builds and pushes Docker image (`docker.yml`)
3. Runs `helm upgrade --rollback-on-failure` with the new image

### GitHub Actions secrets

Two secrets must be set in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | What it is | Where it comes from |
|--------|-----------|---------------------|
| `KUBECONFIG_BASE64` | Base64-encoded K3s kubeconfig | `just get-kubeconfig`, then base64-encoded (see below) |
| `HELM_VALUES_SECRET` | Full contents of `helm/site/values.secret.yaml` | The file you fill in before deploying |

**Prerequisites before setting secrets:**

1. Hetzner infra must be provisioned (`just terraform hetzner apply`)
2. Kubeconfig must be fetched (`just get-kubeconfig` → writes `~/.kube/<project>.yaml`)
3. `helm/site/values.secret.yaml` must be fully filled in

**Push both secrets in one command:**

```bash
just gh-set-secrets
```

`gh secret set` cannot accept multi-line values interactively — `just gh-set-secrets` pipes
both values correctly via stdin. Running it again overwrites the existing secrets.

To set them individually:

```bash
# Kubeconfig: base64-encode (no line wrapping) and pipe to gh
base64 -w 0 ~/.kube/<project>.yaml | gh secret set KUBECONFIG_BASE64

# Helm values: pipe the file directly
gh secret set HELM_VALUES_SECRET < helm/site/values.secret.yaml
```

Verify with:

```bash
gh secret list
```

### Build workflows

Two workflows build the Docker image:

| Workflow | Trigger | Does |
|----------|---------|------|
| `build.yml` | Manual (`just gh build`) | Checks + build only, no deploy |
| `deploy.yml` | Manual (`just gh deploy`) | Checks + build + deploy |

Use `just gh build` to pre-build the image before the first deploy, or
go straight to `just gh deploy` which builds and deploys in one run.
`just helm` does **not** build — only use it when an image already exists in the registry.

### Private repositories and image pulling

ghcr.io packages are **private by default** when the repository is private. The K3s cluster
has no credentials to pull private images, so pods will fail with `ImagePullBackOff`.

**Simplest fix: make the package public**

> GitHub → Your profile → Packages → `{{ project_slug }}` → Package settings → Change visibility → Public

This is fine for open-source or personal projects where the image itself contains no secrets
(secrets are injected at runtime via Kubernetes secrets / Helm values).

**Alternative: image pull secret (for private images)**

Create a GitHub PAT with `read:packages` scope, then add it to the cluster:

```bash
just rkube create secret docker-registry ghcr-pull-secret \
  --docker-server=ghcr.io \
  --docker-username=<github-username> \
  --docker-password=<your-pat>
```

Then reference it in `helm/site/values.yaml`:

```yaml
imagePullSecrets:
  - name: ghcr-pull-secret
```

### Build attestation and private repositories

The `docker.yml` workflow includes `actions/attest-build-provenance` to sign the
image with a build provenance attestation. **This step fails for private repositories**
with the error:

```
Failed to persist attestation: Feature not available for user-owned private repositories.
```

This is a GitHub limitation — attestations require a public repository or GitHub Enterprise.
The step is configured with `continue-on-error: true` so the build succeeds regardless.
Attestation will work automatically if the repository is ever made public.

## Production Commands

```bash
# Django management commands
just rdj migrate
just rdj createsuperuser

# Database access
just rpsql

# Kubernetes
just rkube get pods
just rkube logs -f deployment/django-app

# Fetch kubeconfig
just get-kubeconfig
```

### Upgrade PostgreSQL major version

Set the upgrade flags in `helm/site/values.secret.yaml` before running `just helm site`:

```yaml
pgUpgrade:
  enabled: true
  newImage: postgres:17
  newVolumePath: /mnt/HC_Volume_<new-volume-id>
```
