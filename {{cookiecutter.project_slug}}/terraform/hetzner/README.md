# Hetzner Cloud Infrastructure with Terraform

This directory contains Terraform configuration for provisioning infrastructure on Hetzner Cloud. The infrastructure consists of multiple servers for running a K3s cluster with separate nodes for control plane, database, job processing, and web applications.

## Architecture

The Terraform configuration creates the following infrastructure:

- **1 Server Node** (k3s control plane + Traefik load balancer)

  - Ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
  - Public IP for external access
  - Private IP: 10.0.0.1 (configurable)

- **1 Database Node** (PostgreSQL + Redis)

  - Dedicated volume for PostgreSQL data
  - Port 22 (SSH) for management
  - All traffic within private network

- **1 Job Runner Node** (for cron jobs)

  - Runs scheduled tasks
  - Port 22 (SSH) for management
  - All traffic within private network

- **N Web Application Nodes** (default: 2)

  - Runs Django web application containers
  - Port 22 (SSH) for management
  - All traffic within private network

- **Private Network** (10.0.0.0/16)

  - Secure internal communication between nodes

- **Firewall Rules**

  - Server: SSH (22), HTTP (80), HTTPS (443) from internet
  - Agents: SSH (22) from internet, all traffic from private network

- **PostgreSQL Volume** (default: 50 GB)

  - Persistent storage for database data

## Prerequisites

1. **Hetzner Cloud Account**

    - Sign up at <https://www.hetzner.com/cloud>
    - Create a new project

2. **Hetzner Cloud API Token**

    - Go to: Cloud Console → Project → Security → API Tokens
    - Create a new token with Read & Write permissions

3. **Terraform**

    - Install Terraform >= 1.0: <https://www.terraform.io/downloads>

4. **SSH Key Pair**

    - Generate if you don't have one: `ssh-keygen -t rsa -b 4096 -C "your-email@example.com"`

## Setup

### 1. Configure Terraform Variables

```bash
cd terraform/hetzner
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your settings.

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Preview Changes

```bash
terraform plan
```

### 4. Create Infrastructure

```bash
terraform apply
```

### 5. Generate Ansible Inventory

```bash
terraform output -raw ansible_inventory > ../../ansible/hosts.yml
```

## Scaling

Edit `terraform.tfvars` and run `terraform apply`:

```hcl
webapp_count = 3  # Add more webapp nodes
```

## Destroying Infrastructure

```bash
terraform destroy
```

## Troubleshooting

- **Authentication failed**: Check `hcloud_token` is correct
- **SSH key already exists**: Change `cluster_name` in terraform.tfvars
- **Resource limit exceeded**: Check Hetzner Cloud project limits

## Resources

- [Hetzner Cloud Documentation](https://docs.hetzner.com/cloud/)
- [Terraform Hetzner Provider](https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs)
