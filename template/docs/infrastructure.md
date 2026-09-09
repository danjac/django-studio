# Infrastructure

This project deploys to a self-hosted K3s cluster on Hetzner Cloud with Cloudflare for DNS and CDN.

## Contents

- [Why This Stack](#why-this-stack)
- [Architecture](#architecture)
- [Topology and scaling](#topology-and-scaling)
- [Components](#components)
- [Deployment](#deployment)
- [Services](#services)
- [CronJobs](#cronjobs)
- [Security](#security)
- [Monitoring and Observability](#monitoring-and-observability)
- [Scaling](#scaling)
- [Backup](#backup)
- [Cost](#cost)

## Why This Stack

### Cost predictability

PaaS providers (Railway, Fly.io, Render, Heroku) are convenient but build on top of AWS or GCP, which means costs scale with usage in ways that are hard to cap. A solo developer running multiple side projects can easily accumulate unexpected bills.

Hetzner has fixed, published pricing. You pay per server, so the bill is the same whether the app is idle or busy. There are no egress surprise charges, no per-request fees, no auto-scaling that runs away. The cost is predictable and budgetable.

### Why not Docker + systemd

The obvious simpler alternative - Docker Compose or plain containers managed by systemd - gets you most of the way there, but leaves you writing your own solutions for rolling deploys, health checks, service restarts, secret management, and scheduled jobs. After a few iterations you end up with an ad-hoc orchestration layer that has all the operational complexity of Kubernetes without any of its tooling. This is the "inner platform effect": you reinvent the scheduler badly.

k3s avoids this by providing a real scheduler, service discovery, rolling deploys, CronJobs, and Secrets management in a single ~70MB binary.

### Why k3s specifically

Full Kubernetes (kubeadm, EKS, GKE) is operationally heavy for a single developer. k3s is a CNCF-certified Kubernetes distribution that:

- Installs via a single shell command (bootstrapped from Terraform cloud-init)
- Uses SQLite instead of etcd for the control plane (no HA etcd cluster to manage)
- Ships with Traefik as the ingress controller
- Is binary-compatible with standard Kubernetes tooling (`kubectl`, Helm)

## Architecture

The default topology is a **single k3s node** running everything. Roles are split onto
dedicated nodes as you grow — see [Topology and scaling](#topology-and-scaling).

```
                       Cloudflare
              DNS  ·  CDN  ·  SSL/TLS
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│                  Hetzner Cloud                   │
│  ┌────────────────────────────────────────────┐  │
│  │  server node  (k3s control plane, cx33)    │  │
│  │                                            │  │
│  │   Traefik ingress                          │  │
│  │   django-app        [webapp=true]          │  │
│  │   django-worker     [jobrunner=true]       │  │
│  │   CronJobs          [jobrunner=true]       │  │
│  │   PostgreSQL        [database=true] ──┐    │  │
│  │   Redis             [database=true]   │    │  │
│  └───────────────────────────────────────┼────┘  │
│                                          ▼       │
│                                  ┌──────────────┐│
│                                  │ Hetzner vol. ││
│                                  │  (pg data)   ││
│                                  └──────────────┘│
└──────────────────────────────────────────────────┘
```

## Topology and scaling

### How placement works

Every app workload selects a node with a **boolean label** rather than a role name:

| Workload | `nodeSelector` |
| -------- | -------------- |
| `django-app` | `webapp: "true"` |
| `django-worker`, CronJobs, release job | `jobrunner: "true"` |
| PostgreSQL, Redis | `database: "true"` |

A node can only carry one `role=` value, but it can carry all three booleans. So the
single server node is labelled `webapp=true jobrunner=true database=true` and runs
everything, while a split cluster gives each node exactly one of those labels.

**The Helm chart is byte-for-byte identical in both cases.** Scaling is a Terraform
change plus a redeploy — you never edit the chart.

Terraform applies each label to the server node unless a dedicated node claims it:

| Variable | Default | When set |
| -------- | ------- | -------- |
| `webapp_count` | `0` | `N` dedicated webapp nodes take `webapp=true` |
| `create_jobrunner` | `false` | dedicated jobrunner node takes `jobrunner=true` |
| `create_database` | `false` | dedicated database node takes `database=true` |
| `create_monitor` | `false` | separate observability node (see `/dj-deploy-observe`) |

### The scaling path

Each step is independent — take them in any order, as load demands.

**Stage 1 — single node (default).** One `cx33`. Everything runs on it, and it is the
cheapest the cluster gets.

**Stage 2 — split the database.** PostgreSQL and Redis get their own node:

```hcl
create_database = true
```

⚠️ **This moves the Hetzner volume between servers.** Terraform will detach it from the
server node and reattach it to the new database node, so PostgreSQL is down for the
duration. Take a backup first (`/dj-db-backup`), and expect a short outage.

**Stage 3 — split the workers.** Background tasks and CronJobs stop competing with web
requests for CPU:

```hcl
create_jobrunner = true
```

**Stage 4 — split the webapps.** Dedicated gunicorn nodes:

```hcl
webapp_count = 2
```

Then raise `replicas` in `helm/site/values.secret.yaml` to match, and raise the `app`
resource requests — a dedicated node has the whole box to itself. Or just run `/dj-scale`.

After any stage: `just terraform hetzner apply`, then `just helm site`.

### Migrating an existing cluster

Clusters provisioned before boolean labels existed have nodes labelled only `role=<name>`,
so pods will not schedule after upgrading the chart. Relabel the existing nodes once:

```bash
kubectl label node <webapp-node>    webapp=true
kubectl label node <jobrunner-node> jobrunner=true
kubectl label node <database-node>  database=true
```

New nodes get the labels from cloud-init automatically.

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

See `docs/deployment.md` for all deployment commands (Terraform, Helm, CI/CD pipeline).

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
  schedule: "0 2 * * *" # Daily at 2 AM
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

| Schedule       | Description                |
| -------------- | -------------------------- |
| `0 2 * * *`    | Daily at 2 AM              |
| `0 3 * * 0`    | Weekly on Sunday at 3 AM   |
| `0 0 1 * *`    | Monthly on 1st at midnight |
| `*/15 * * * *` | Every 15 minutes           |
| `0 4 * * *`    | Daily at 4 AM              |

### Django Management Command Examples

```yaml
# Database cleanup
args: ["shell", "--command", "from my_package.models import OldRecord; OldRecord.objects.filter(created__lt=now()-timedelta(days=90).delete()"]

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

## Security

### Network

- Private network between servers
- Firewall restricts access
- Cloudflare proxies all traffic

### Firewall and SSH access

SSH (port 22) and the K3s API (port 6443) are controlled by the `admin_ips` variable in
`terraform/hetzner/terraform.tfvars`. The default is open (`["0.0.0.0/0", "::/0"]`),
which is fine - both ports are protected by strong credentials (SSH key, K3s token + TLS)
so open ports are not a meaningful risk in practice.

**Restricting `admin_ips` is optional.** If you do restrict it, note that the GitHub
Actions deploy workflow needs to reach port 6443, and GitHub-hosted runner IPs are
unpredictable - so you would also need a self-hosted runner or to leave 6443 open.

If you want to restrict anyway (e.g. you have a static IP or VPN dedicated IP):

```hcl
# terraform/hetzner/terraform.tfvars
admin_ips = ["203.0.113.42/32"]   # find your current IP with: curl -s ifconfig.me
```

**If you use a VPN with rotating exit IPs (e.g. Proton VPN):** a static `/32` entry will
lock you out when you switch servers. Either use a dedicated IP add-on for a stable exit
IP, or leave `admin_ips` at the default.

For a solo developer, SSH key authentication with open firewall rules is a reasonable
and pragmatic default. The attack surface is small and well-understood.

### Tailscale (recommended for stricter access control or team use)

[Tailscale](https://tailscale.com) puts every node on a private WireGuard mesh, so SSH
and the Kubernetes API travel over the tailnet instead of the public internet and
`admin_ips` can be locked to the CGNAT range (`100.64.0.0/10`). Ports 80 and 443 stay
open — that is public web traffic via Cloudflare.

It ships with the template but is **off by default**. The quickest way to turn it on is
`/dj-tailscale enable`, which handles both a fresh deploy and an existing cluster. What
follows is what that skill automates.

#### Setting up

In the Tailscale admin console:

1. Add `tag:k8s` and `tag:ci` to `tagOwners` under Access Controls.
2. Create an **OAuth client** (Settings → OAuth clients) with the `auth_keys` write
   scope and both tags.
3. Note your tailnet name, e.g. `tail1a2b3c.ts.net`.

Then in `terraform/hetzner/terraform.tfvars`:

```hcl
tailscale_oauth_client_secret = "tskey-client-..."
tailscale_tailnet             = "tail1a2b3c.ts.net"
```

**Use an OAuth client, not an auth key.** Auth keys expire after at most 90 days. Because
adding a node is a routine operation here, an expired key means nodes provisioned later
silently never reach the tailnet.

#### What happens on apply

Every node installs Tailscale during cloud-init and joins with a pinned hostname
(`<cluster>-server`, `<cluster>-webapp-1`, …). The server additionally gets its MagicDNS
name added to the k3s serving certificate as a TLS SAN, and `just get-kubeconfig` writes
that name as the API address instead of the public IP.

The hostname is pinned rather than left to Tailscale's own normalisation because the TLS
SAN has to be known at install time — the name cannot be corrected later without
regenerating the certificate.

#### Adding Tailscale to a cluster that is already running

Cloud-init only runs at node creation, and all servers set
`lifecycle { ignore_changes = [user_data] }`, so setting the variables is not enough for
an existing cluster. Two things have to happen on the running nodes:

```bash
TAILSCALE_OAUTH_CLIENT_SECRET=tskey-client-... \
TAILSCALE_TAILNET=tail1a2b3c.ts.net \
  .agents/skills/dj-tailscale/scripts/join-nodes.sh
```

This installs Tailscale on each node, and on the server writes a
`/etc/rancher/k3s/config.yaml.d/10-tailscale.yaml` drop-in with the new TLS SAN, clears
the cached serving certificate and **restarts k3s**. The Kubernetes API is briefly
unavailable during the restart; running pods are unaffected. The script then checks the
certificate actually carries the SAN and fails loudly if it does not.

Pass `--dry-run` first to see which nodes it would touch.

#### Locking the firewall — order matters

```hcl
admin_ips = ["100.64.0.0/10"]
```

**Never apply this until `kubectl get nodes` has worked over the tailnet.** If any node
is not on the tailnet when you close port 22, the only way back in is the Hetzner web
console. Verify first:

```bash
just get-kubeconfig
just --yes rkube get nodes
```

#### CI

The deploy workflow has a Tailscale step that activates only when
`TS_OAUTH_CLIENT_ID` is set as a repository secret:

```bash
gh secret set TS_OAUTH_CLIENT_ID
gh secret set TS_OAUTH_SECRET
just gh-set-secrets     # re-push the kubeconfig, which now uses the MagicDNS name
```

Runners join as ephemeral `tag:ci` nodes, so they do not accumulate in your device list.

#### Team access

Add team members to your tailnet and use ACLs to restrict who reaches which ports — for
example engineers get 6443, ops also gets 22.

### Secrets

- Environment variables stored in Kubernetes secrets via Helm
- `values.secret.yaml` is gitignored - never commit it
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
OTEL_SERVICE_NAME = "my_project"
OTEL_EXPORTER_OTLP_ENDPOINT = "http://otel-collector:4317"
```

## Scaling

See [Topology and scaling](#topology-and-scaling) for the full path from one node to five.

In brief:

1. Edit `terraform/hetzner/terraform.tfvars` (e.g. set `create_database = true`, or
   increase `webapp_count`)
2. Run `just terraform hetzner apply` - new nodes join the cluster automatically via
   cloud-init and pick up their workload label
3. Run `just helm site` to reschedule onto them

## Backup

Automated daily backups are optional and set up separately after initial deployment.
See `docs/database-backups.md` for the full setup and restore guide, or run `/dj-enable-db-backups`
to be guided through the process interactively.

In brief: a Kubernetes CronJob runs `pg_dump` nightly and uploads compressed dumps to a
private Hetzner Object Storage bucket (`<project>-db-backups`). Backup credentials are
stored in a dedicated `backup-secret` and are never exposed to the app pods.

## Cost

You pay per server, at Hetzner's published rates, regardless of traffic. What the
topology costs is therefore just a count of what it provisions:

| Topology | What you pay for |
| -------- | ---------------- |
| Single node (default) | 1x `cx33` + the PostgreSQL volume |
| Database split out | + 1 node |
| Jobrunner split out | + 1 node |
| N dedicated webapps | + N nodes |
| Observability | + 1 node (the monitor) |

Cloudflare DNS, CDN and SSL are free at the tier this template uses, and Tailscale's
free tier covers 3 users and 100 devices.

For current rates see [Hetzner Cloud pricing](https://www.hetzner.com/cloud/) - server
types are set by `server_type`, `database_server_type` and `agent_server_type` in
`terraform/hetzner/terraform.tfvars`.
