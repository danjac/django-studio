# Ansible and Terraform

This project uses Terraform for infrastructure and Ansible for configuration management/deployment.

## Overview

- **Terraform**: Provisions infrastructure (servers, networking, volumes)
- **Ansible**: Deploys applications and configures servers

## Terraform

### Structure

```
terraform/
├── hetzner/        # Hetzner Cloud infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
└── cloudflare/     # Cloudflare DNS/CDN
    ├── main.tf
    ├── variables.tf
    └── terraform.tfvars.example
```

### Commands

```bash
cd terraform/hetzner
terraform init
terraform plan
terraform apply
```

### Variables

Copy example file and fill in:
```bash
cp terraform.tfvars.example terraform.tfvars
# Edit with your values
```

Never commit `terraform.tfvars` - it's gitignored.

## Ansible

### Structure

```
ansible/
├── site.yml           # Main playbook
├── deploy.yml         # Application deployment
├── hosts.yml          # Inventory
├── group_vars/        # Group variables
└── roles/
    ├── k3s_cluster/  # K3s cluster setup
    ├── k3s_deploy/   # App deployment
    ├── k3s_crons/    # Cron jobs
    └── ...
```

### Playbooks

```bash
# Full deployment
just apb site

# Redeploy application only
just apb deploy

# Upgrade server packages
just apb upgrade
```

### Custom Scripts

Ansible generates scripts for production commands:

```bash
# Run Django management command
just rdj migrate
just rdj createsuperuser

# Connect to production database
just rpsql

# Run kubectl commands
just kube get pods
```

### Inventory

Inventory is generated from Terraform:
```bash
terraform output -raw ansible_inventory
```

Then encrypted with `ansible-vault`.

## CI/CD Pipeline

1. **Terraform** creates/updates infrastructure
2. **Ansible** deploys application to K3s cluster

## Best Practices

1. Use `terraform.tfvars.example` as template
2. Never commit secrets to terraform
3. Use ansible-vault for sensitive variables
4. Test playbooks locally first
5. Use idempotent roles
