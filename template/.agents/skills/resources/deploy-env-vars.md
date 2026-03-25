# Deployment Variables

These values are entered directly into the relevant config files during `/dj-launch`.
**Never paste secret values into this chat.**

**Security rules for all deployment skills:**
- Never echo or print a secret value to the terminal or chat
- Check presence only: read the file and verify the field is non-empty and not `CHANGE_ME`
- Report errors by field name: "hcloud_token is invalid" — not the token itself
- When a secret field is empty or `CHANGE_ME`, stop and tell the user which file and field to fill in

## Required

| Variable | File | Field | Where to get it |
|----------|------|-------|-----------------|
| Hetzner Cloud API token | `terraform/hetzner/terraform.tfvars` | `hcloud_token` | [console.hetzner.cloud](https://console.hetzner.cloud) → project → Security → API Tokens → Generate (Read & Write) |
| Cloudflare API token | `terraform/cloudflare/terraform.tfvars` | `cloudflare_api_token` | [dash.cloudflare.com](https://dash.cloudflare.com) → Profile → API Tokens → Create Custom Token (Zone: Zone/Edit, Zone Settings/Edit, DNS/Edit, Page Rules/Edit, Zone WAF/Edit, Transform Rules/Edit, SSL and Certificates/Edit) |

## Required for email

| Variable | File | Field | Where to get it |
|----------|------|-------|-----------------|
| Mailgun API key | `helm/site/values.secret.yaml` | `secrets.mailgunApiKey` | mailgun.com → Sending → Domains → your domain → API Keys |

## Optional

| Variable | File | Field | Notes |
|----------|------|-------|-------|
| Mailgun DKIM value | `terraform/cloudflare/terraform.tfvars` | `mailgun_dkim_value` | Mailgun → Sending → Domains → DNS Records → `mailo._domainkey` TXT value |
| Hetzner storage access key | `terraform/storage/terraform.tfvars` | `access_key` | Hetzner → Security → S3 credentials → Generate credentials |
| Hetzner storage secret key | `terraform/storage/terraform.tfvars` | `secret_key` | Hetzner → Security → S3 credentials → Generate credentials |
| Sentry DSN | `helm/site/values.secret.yaml` | `secrets.sentryUrl` | Sentry → Project → Settings → Client Keys → DSN |
| OTLP endpoint | `helm/site/values.secret.yaml` | `secrets.openTelemetryUrl` | Your OpenTelemetry collector endpoint URL |
| Grafana admin password | `helm/observability/values.secret.yaml` | `kube-prometheus-stack.grafana.adminPassword` | Any secure password; auto-generated if not set |
