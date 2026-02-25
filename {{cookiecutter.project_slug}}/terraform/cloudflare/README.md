# Cloudflare CDN and SSL Configuration with Terraform

This directory contains Terraform configuration for setting up Cloudflare as a CDN and SSL/TLS provider.

## What This Configures

- **DNS Records**: A record pointing to your server
- **CDN**: Caching for static assets
- **SSL/TLS**: Full SSL mode with automatic HTTPS redirects
- **Security**: Firewall rules, security headers
- **Performance**: HTTP/3, Brotli compression, early hints

## Prerequisites

1. **Cloudflare Account**

    Sign up at <https://www.cloudflare.com/>

2. **Add Domain to Cloudflare**

    1. Log in to Cloudflare Dashboard
    2. Click "Add a Site"
    3. Enter your domain name

3. **Cloudflare API Token**

    Create a token with these permissions:
    - Zone → Zone → Edit
    - Zone → Zone Settings → Edit
    - Zone → DNS → Edit
    - Zone → Page Rules → Edit
    - Zone → Zone WAF → Edit
    - Zone → Transform Rules → Edit

4. **Origin Certificates**

    Generate in Cloudflare Dashboard → SSL/TLS → Origin Server and save to `ansible/certs/`.

## Setup

### 1. Configure Variables

```bash
cd terraform/cloudflare
cp terraform.tfvars.example terraform.tfvars
```

Edit with your values.

### 2. Initialize and Apply

```bash
terraform init
terraform plan
terraform apply
```

## Troubleshooting

- **Could not find zone**: Verify domain is added to Cloudflare
- **Authentication error**: Check API token permissions
- **DNS status shows "pending"**: Wait for nameserver propagation
