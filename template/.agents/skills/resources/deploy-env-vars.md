# Deployment Environment Variables

Set these in `.env` before running `/dj-launch` or `/dj-rotate-secrets`.
`.env` takes precedence over shell exports (e.g. from `.zshrc`).

**Security rules for all deployment skills:**
- Never echo or print a secret value to the terminal or chat
- Check presence only: `[ -n "${VAR:-}" ] && echo present || echo missing`
- Report errors by variable name: "HETZNER_TOKEN is invalid" — not the token itself
- Write values from env directly to destination files; never pass them as shell arguments

## Required

| Variable | Where to get it |
|----------|-----------------|
| `HETZNER_TOKEN` | [console.hetzner.cloud](https://console.hetzner.cloud) → project → Security → API Tokens → Generate (Read & Write) |
| `CLOUDFLARE_TOKEN` | [dash.cloudflare.com](https://dash.cloudflare.com) → Profile → API Tokens → Create Custom Token (Zone: Zone/Edit, Zone Settings/Edit, DNS/Edit, Page Rules/Edit, Zone WAF/Edit, Transform Rules/Edit, SSL and Certificates/Edit) |

## Required for email

| Variable | Where to get it |
|----------|-----------------|
| `MAILGUN_API_KEY` | mailgun.com → Sending → Domains → your domain → API Keys |

## Optional

| Variable | Notes |
|----------|-------|
| `MAILGUN_DKIM_VALUE` | Mailgun → Sending → Domains → DNS Records → `mailo._domainkey` TXT value (for Cloudflare DNS setup) |
| `HETZNER_STORAGE_ACCESS_KEY` | Hetzner → Security → S3 credentials → Generate credentials |
| `HETZNER_STORAGE_SECRET_KEY` | Hetzner → Security → S3 credentials → Generate credentials |
| `SENTRY_DSN` | Sentry → Project → Settings → Client Keys → DSN |
| `OTLP_ENDPOINT` | Your OpenTelemetry collector endpoint URL |
| `GRAFANA_ADMIN_PASSWORD` | Any secure password; auto-generated if not set |

## Destination mapping

| Variable | Written to |
|----------|------------|
| `HETZNER_TOKEN` | `terraform/hetzner/terraform.tfvars` → `hcloud_token` |
| `CLOUDFLARE_TOKEN` | `terraform/cloudflare/terraform.tfvars` → `cloudflare_api_token` |
| `MAILGUN_API_KEY` | `helm/site/values.secret.yaml` → `secrets.mailgunApiKey` |
| `MAILGUN_DKIM_VALUE` | `terraform/cloudflare/terraform.tfvars` → `mailgun_dkim_value` |
| `HETZNER_STORAGE_ACCESS_KEY` | `terraform/storage/terraform.tfvars` → `access_key` |
| `HETZNER_STORAGE_SECRET_KEY` | `terraform/storage/terraform.tfvars` → `secret_key` |
| `SENTRY_DSN` | `helm/site/values.secret.yaml` → `secrets.sentryUrl` |
| `OTLP_ENDPOINT` | `helm/site/values.secret.yaml` → `secrets.openTelemetryUrl` |
| `GRAFANA_ADMIN_PASSWORD` | `helm/observability/values.secret.yaml` → `kube-prometheus-stack.grafana.adminPassword` |

## How to check for presence (without exposing values)

```bash
uv run python .agents/skills/resources/check-deploy-env.py
```

See `resources/check-deploy-env.py` for the implementation. Exit code 1 if any required
vars are missing.
