# Helm and Terraform

This project uses Terraform for infrastructure provisioning and Helm for Kubernetes deployment.

## Overview

| Layer | Tool | What it does |
|-------|------|--------------|
| Infrastructure | Terraform (hetzner) | Servers, network, firewall, Postgres volume; K3s via cloud-init |
| DNS / CDN / SSL | Terraform (cloudflare) | DNS A record, CDN caching, TLS settings |
| Kubernetes objects | Helm (`helm/{{cookiecutter.project_slug}}/`) | App, workers, cron jobs, Postgres, Redis, ingress |
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
└── cloudflare/     # Cloudflare DNS/CDN
    ├── main.tf
    ├── variables.tf
    └── terraform.tfvars.example
```

### Commands

```bash
cd terraform/hetzner && cp terraform.tfvars.example terraform.tfvars
just terraform hetzner init
just terraform hetzner plan
just terraform hetzner apply

cd terraform/cloudflare && cp terraform.tfvars.example terraform.tfvars
just terraform cloudflare apply
```

### Variables

Copy the example file and fill in required values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Never commit `terraform.tfvars` — it's gitignored.

## Helm

### Structure

```
helm/
├── {{cookiecutter.project_slug}}/   # Application chart
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
# Deploy or update the application (preserves running image via --reuse-values)
just helm site

# Deploy or update the observability stack
just helm observability
```

### Secrets

Copy and fill in the secrets file:

```bash
cp helm/{{cookiecutter.project_slug}}/values.secret.yaml.example helm/{{cookiecutter.project_slug}}/values.secret.yaml
```

`values.secret.yaml` is gitignored — never commit it.

## CI/CD Pipeline

The `deploy` GitHub Actions workflow:

1. Runs tests (`checks.yml`)
2. Builds and pushes Docker image (`docker.yml`)
3. Runs `helm upgrade --rollback-on-failure` with the new image

Required repository secrets:
- `KUBECONFIG_BASE64` — base64-encoded kubeconfig
- `HELM_VALUES_SECRET` — full contents of `values.secret.yaml`

## Production Commands

```bash
# Django management commands
just rdj migrate
just rdj createsuperuser

# Database access
just rpsql

# Kubernetes
just kube get pods
just kube logs -f deployment/django-app

# Fetch kubeconfig
just get-kubeconfig
```
