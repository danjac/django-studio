# terraform/cloudflare

Sets up Cloudflare DNS, CDN caching, SSL/TLS, and security settings.

## What This Configures

- **DNS Records**: A record pointing to your Hetzner server (+ optional Grafana subdomain)
- **CDN**: Caching for static assets
- **SSL/TLS**: Full SSL mode with automatic HTTPS redirects
- **Security**: Firewall rules, security headers
- **Performance**: HTTP/3, Brotli compression, early hints

## Prerequisites

1. **Cloudflare Account** — sign up at <https://www.cloudflare.com/>
2. **Domain added to Cloudflare** with nameservers updated
3. **Cloudflare API Token** with these zone-level permissions:
   - Zone → Zone → Edit
   - Zone → Zone Settings → Edit
   - Zone → DNS → Edit
   - Zone → Page Rules → Edit
   - Zone → Zone WAF → Edit
   - Zone → Transform Rules → Edit

## Setup

```bash
cd terraform/cloudflare
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars   # set cloudflare_api_token, domain, server_ip
terraform init
terraform plan
terraform apply
```

## Origin Certificates

After `terraform apply`, create origin certificates for HTTPS:

1. Cloudflare Dashboard → SSL/TLS → Origin Server → Create Certificate (15-year validity)
2. Paste the certificate and key into `helm/{{cookiecutter.project_slug}}/values.secret.yaml` under
   `secrets.cloudflare.cert` and `secrets.cloudflare.key`

## Troubleshooting

**Could not find zone** — verify domain is added to Cloudflare and `domain` in `terraform.tfvars` matches exactly.

**Authentication error** — check API token has all required zone-level permissions.

**ruleset already exists** — import existing rulesets into Terraform state:

```bash
ZONE_ID=$(terraform show -json | jq -r \
  '.values.root_module.resources[] | select(.address == "data.cloudflare_zone.domain") | .values.id')

# List rulesets and get IDs by phase
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/rulesets" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  | jq '.result[] | select(.kind == "zone") | {id, phase}'

terraform import cloudflare_ruleset.zone_level_firewall "zone/$ZONE_ID/<ID>"
terraform import cloudflare_ruleset.transform_response_headers "zone/$ZONE_ID/<ID>"
```

**DNS status shows "pending"** — nameservers haven't propagated yet (can take up to 48 hours).
