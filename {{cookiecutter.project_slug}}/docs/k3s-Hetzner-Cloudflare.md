# k3s + Hetzner + Cloudflare

This project deploys to a self-hosted K3s cluster on Hetzner Cloud with Cloudflare for DNS and CDN.

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

### Application (Ansible)

```bash
just apb site
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

1. **Set `concurrencyPolicy: Forbid`** — Prevents overlapping jobs
2. **Configure history limits** — Keep 3 successful and 3 failed jobs for debugging
3. **Use timezones** — CronJobs use the node's timezone; set `spec.timezone` if supported
4. **Handle partial failures** — Exit with non-zero code on failure for retry behavior
5. **Resource limits** — Set requests/limits to prevent resource exhaustion

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

### Integration with Ansible

Add CronJob manifests to your Ansible deploy templates:

```yaml
# ansible/templates/cronjob.yml.j2
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ app_name }}-{{ task_name }}
  namespace: {{ namespace }}
spec:
  schedule: {{ schedule }}
  ...
```

Then include in your playbook:

```yaml
- name: Deploy CronJobs
  kubernetes.core.k8s:
    state: present
    definition: "{{ lookup('template', 'cronjob.yml.j2') }}"
```

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

### Secrets
- Environment variables in K3s secrets
- Ansible vault for sensitive values
- Never commit secrets to git

### SSL/TLS
- Cloudflare origin certificates
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
just apb observability
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

1. Add server in Terraform
2. Run Terraform apply
3. Run Ansible to join cluster

## Backup

PostgreSQL backups via:
- K3s volume snapshots
- Cron job with pg_dump

## Cost

- 3x CPX11 servers: ~€15/month
- Volume: ~€4/month
- DNS: Free
- Total: ~€20/month
