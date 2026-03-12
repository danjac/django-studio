# k3s + Hetzner + Cloudflare

This project deploys to a self-hosted K3s cluster on Hetzner Cloud with Cloudflare for DNS and CDN.

## Why This Stack

### Cost predictability

PaaS providers (Railway, Fly.io, Render, Heroku) are convenient but build on top of AWS or GCP, which means costs scale with usage in ways that are hard to cap. A solo developer running multiple side projects can easily accumulate unexpected bills — this is a well-documented failure mode, not a theoretical one.

Hetzner has fixed, published pricing. A 3-node k3s cluster costs roughly €20/month regardless of traffic. There are no egress surprise charges, no per-request fees, no auto-scaling that runs away. The cost is predictable and budgetable.

### Why not Docker + systemd

The obvious simpler alternative — Docker Compose or plain containers managed by systemd — gets you most of the way there, but leaves you writing your own solutions for rolling deploys, health checks, service restarts, secret management, and scheduled jobs. After a few iterations you end up with an ad-hoc orchestration layer that has all the operational complexity of Kubernetes without any of its tooling. This is the "inner platform effect": you reinvent the scheduler badly.

k3s avoids this by providing a real scheduler, service discovery, rolling deploys, CronJobs, and Secrets management in a single ~70MB binary. The overhead over Docker Compose is low; the ceiling is much higher.

### Why k3s specifically

Full Kubernetes (kubeadm, EKS, GKE) is operationally heavy for a single developer. k3s is a CNCF-certified Kubernetes distribution that:
- Installs via a single shell command (bootstrapped from Terraform cloud-init)
- Uses SQLite instead of etcd for the control plane (no HA etcd cluster to manage)
- Ships with Traefik as the ingress controller
- Is binary-compatible with standard Kubernetes tooling (`kubectl`, Helm)

The result is a setup that behaves like production Kubernetes but fits on a €5/month VPS.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Cloudflare                              │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐    │
│  │    DNS      │  │    CDN      │  │    SSL/TLS    │    │
│  └──────┬──────┘  └──────┬──────┘  └───────┬───────┘    │
└──────────┼────────────────┼────────────────┼──────────────┘
           │                │                │
           ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                   Hetzner Cloud                            │
│  ┌─────────────────────────────────────────────────┐     │
│  │                  K3s Cluster                      │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │     │
│  │  │  Server 1 │  │  Server 2 │  │  Server 3 │   │     │
│  │  │ (control) │  │  (worker) │  │  (worker) │   │     │
│  │  └──────────┘  └──────────┘  └──────────┘   │     │
│  └─────────────────────────────────────────────────┘     │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐                      │
│  │ PostgreSQL  │  │    Redis    │                      │
│  │  (volume)   │  │             │                      │
│  └─────────────┘  └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

## Components

### Hetzner Cloud

- **Servers**: K3s cluster nodes
- **Volumes**: PostgreSQL data volume
- **Firewall**: Security rules
- **Network**: Private network for cluster

### Cloudflare

- **DNS**: Domain management
- **CDN**: Static asset caching
- **SSL/TLS**: Free certificates via Origin Server
- **Security Headers**: CSP, HSTS, etc.

### K3s

- Lightweight Kubernetes
- Single binary installation
- Built-in SQLite (no etcd needed)
- Traefik for ingress

## Deployment

### Infrastructure (Terraform)

```bash
cd terraform/hetzner
terraform init
terraform plan
terraform apply
```

### DNS (Cloudflare Terraform)

```bash
cd terraform/cloudflare
terraform init
terraform plan
terraform apply
```

### Application (Helm)

```bash
just helm site
```

## Services

### Traefik Ingress

Traefik handles routing:
- HTTP/HTTPS termination
- Path-based routing
- Let's Encrypt certificates

### PostgreSQL

Managed via K3s with:
- Persistent volume
- Automated backups (optional)

### Redis

Used for:
- Cache
- Session storage
- Django cache backend

## CronJobs

Use Kubernetes CronJobs for scheduled tasks instead of traditional cron. CronJobs run pods on a schedule and are ideal for Django management commands, data cleanup, batch processing, and periodic syncs.

### Basic CronJob Structure

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: my-django-command
  namespace: default
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: django
              image: your-registry/your-app:latest
              command:
                - python
                - manage.py
              args:
                - your_command
                - --arg1
                - value1
              env:
                - name: DJANGO_SETTINGS_MODULE
                  value: config.settings
```

### Common Schedule Patterns

| Schedule | Description |
|----------|-------------|
| `0 2 * * *` | Daily at 2 AM |
| `0 3 * * 0` | Weekly on Sunday at 3 AM |
| `0 0 1 * *` | Monthly on 1st at midnight |
| `*/15 * * * *` | Every 15 minutes |
| `0 4 * * *` | Daily at 4 AM |

### Django Management Command Examples

```yaml
# Database cleanup
args: ["shell", "--command", "from myapp.models import OldRecord; OldRecord.objects.filter(created__lt=now()-timedelta(days=90).delete()"]

# RSS feed refresh
args: ["refresh_feeds", "--workers=4"]

# Generate reports
args: ["generate_reports", "--format=csv"]

# Send digests
args: ["send_digest_emails"]
```

### Best Practices

1. **Set `concurrencyPolicy: Forbid`** - Prevents overlapping jobs
2. **Configure history limits** - Keep 3 successful and 3 failed jobs for debugging
3. **Use timezones** - CronJobs use the node's timezone; set `spec.timezone` if supported
4. **Handle partial failures** - Exit with non-zero code on failure for retry behavior
5. **Resource limits** - Set requests/limits to prevent resource exhaustion

### With Custom Commands/Scripts

For complex tasks, mount a script or use a custom entrypoint:

```yaml
spec:
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: worker
              image: your-registry/your-app:latest
              command: ["/bin/sh", "-c"]
              args:
                - |
                  #!/bin/sh
                  set -e
                  echo "Starting task at $(date)"
                  python manage.py my_command
                  echo "Completed at $(date)"
              resources:
                requests:
                  memory: "256Mi"
                  cpu: "100m"
                limits:
                  memory: "512Mi"
                  cpu: "500m"
```

### Managing CronJobs

```bash
# List CronJobs
kubectl get cronjobs -n default

# View CronJob details
kubectl describe cronjob my-django-command

# Manually trigger a job
kubectl create job my-django-command-manual --from=cronjob/my-django-command

# View job logs
kubectl logs job/my-django-command-xxxxx

# Delete failed jobs
kubectl delete jobs $(kubectl get jobs -o jsonpath='{.items[?(@.status.failed>0)].metadata.name}')
```

### Defining CronJobs

Add entries to the `cronjobs` section in `helm/site/values.yaml`:

```yaml
cronjobs:
  my-command:
    schedule: "0 2 * * *"
    command: "./manage.sh my_command --arg value"
```

Then run `just helm site` to apply.

### Alternatives

- **Django-q** or **Celery Beat**: For tasks tied to application lifecycle
- **GitHub Actions scheduled workflows**: For maintenance tasks not requiring cluster access
- **External cron services** (e.g., EasyCron): For simple webhooks when K3s overhead isn't justified

## Production Commands

```bash
# Check pod status
just kube get pods

# View logs
just kube logs -f deployment/myapp

# Restart application
just kube rollout restart deployment/myapp

# Database migrations
just rdj migrate

# Create superuser
just rdj createsuperuser

# Connect to database
just rpsql
```

## Security

### Network
- Private network between servers
- Firewall restricts access
- Cloudflare proxies all traffic

### Firewall and SSH access

SSH (port 22) and the K3s API (port 6443) are controlled by the `admin_ips` variable in
`terraform/hetzner/terraform.tfvars`. The default is open (`["0.0.0.0/0", "::/0"]`),
which is fine — both ports are protected by strong credentials (SSH key, K3s token + TLS)
so open ports are not a meaningful risk in practice.

**Restricting `admin_ips` is optional.** If you do restrict it, note that the GitHub
Actions deploy workflow needs to reach port 6443, and GitHub-hosted runner IPs are
unpredictable — so you would also need a self-hosted runner or to leave 6443 open.

If you want to restrict anyway (e.g. you have a static IP or VPN dedicated IP):

```hcl
# terraform/hetzner/terraform.tfvars
admin_ips = ["203.0.113.42/32"]   # find your current IP with: curl -s ifconfig.me
```

**If you use a VPN with rotating exit IPs (e.g. Proton VPN):** a static `/32` entry will
lock you out when you switch servers. Either use a dedicated IP add-on for a stable exit
IP, or leave `admin_ips` at the default.

### Secrets
- Environment variables stored in Kubernetes secrets via Helm
- `values.secret.yaml` is gitignored — never commit it
- Use GitHub Actions secrets for CI/CD (`KUBECONFIG_BASE64`, `HELM_VALUES_SECRET`)

### SSL/TLS
- Cloudflare origin certificates with `full_strict` mode (validates origin cert chain)
- Full TLS encryption end-to-end

## Monitoring and Observability

Optional observability stack via OpenTelemetry, Prometheus, Grafana, Loki, and Tempo.

### Components

- **OpenTelemetry (OTel)**: Collects metrics, traces, and logs
- **Prometheus**: Time-series database for metrics
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation
- **Tempo**: Distributed tracing

### Deployment

```bash
just helm observability
```

### Access

Grafana at `https://grafana.yourdomain.com` (configured in Terraform).

### Application Integration

To instrument Django with OpenTelemetry:

```bash
uv add opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

```python
# settings.py
OTEL_SERVICE_NAME = "myapp"
OTEL_EXPORTER_OTLP_ENDPOINT = "http://otel-collector:4317"
```

## Scaling

1. Edit `terraform/hetzner/terraform.tfvars` (e.g. increase `webapp_count`)
2. Run `terraform apply` — new nodes join the cluster automatically via cloud-init
3. Run `just helm site` to apply the updated replica count

## Backup

PostgreSQL backups via:
- K3s volume snapshots
- Cron job with pg_dump

## Cost

- 3x CPX11 servers: ~€15/month
- Volume: ~€4/month
- DNS: Free
- Total: ~€20/month
