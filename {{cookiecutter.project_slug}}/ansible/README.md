# Ansible Playbooks

This directory contains Ansible playbooks for deploying to a K3s cluster.

## Setup

1. Copy `hosts.yml.example` to `hosts.yml`
2. Edit with your server settings
3. Encrypt with `ansible-vault` if needed
4. Copy Cloudflare origin certificates to `certs/`:
   - `cloudflare.pem`
   - `cloudflare.key`
5. Add SSH public keys to `ssh-keys/` (must have `.pub` extension)

## Deployment

Run from project root:

```bash
just apb site      # Full deployment
just apb deploy    # Redeploy application only
just apb upgrade  # Upgrade server packages
```

## Post-deployment

```bash
just kube get pods    # Check pod status
just rdj migrate      # Run migrations
```

## Generated Scripts

Ansible generates scripts for production commands:

```bash
just rdj <command>  # Django management command
just rpsql         # Connect to PostgreSQL
just kube get pods # kubectl commands
```
