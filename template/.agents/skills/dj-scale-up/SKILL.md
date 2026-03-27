---
description: Scale up django-app replicas and provision Hetzner nodes if needed
---

Scale the number of `django-app` replicas up to a target count. Provisions
additional Hetzner nodes via Terraform if the cluster does not have enough
capacity, then updates the Helm values and redeploys.

## Required reading

- `docs/infrastructure.md`
- `docs/deployment.md`

---

**Terraform rule:** Never use `cd terraform/<dir>` — always use
`terraform -chdir=terraform/<dir>` or the `just terraform <dir>` wrapper.

**Secret handling rules:**
- Never echo, print, or repeat a secret value in the terminal or chat.
- Check presence only — report missing values by field name, not by value.

---

## Step 1 — Read current state

Read `helm/site/values.secret.yaml` and extract the current `replicas` value.

Read `terraform/hetzner/terraform.tfvars` and extract the current `server_count`
(defaults to 1 if not set).

Tell the user:

> **Current state:**
> - Replicas: <current_replicas>
> - Hetzner nodes: <current_server_count>
>
> **Target:** <n> replicas
>
> Proceed? (y/n)

If the user says **n**, stop.

## Step 2 — Validate

If `<n>` is less than or equal to the current replica count, tell the user:

> Target (<n>) is not higher than current replicas (<current>).
> Use `/dj-scale-down` to reduce replicas.

Stop.

## Step 3 — Provision additional Hetzner nodes (if needed)

Estimate whether additional nodes are needed. A reasonable heuristic: each
node can run ~2 app replicas (adjust based on resource requests in the Helm
chart if visible).

If `<n>` requires more nodes than `server_count`:

1. Calculate the new `server_count` (e.g. `ceil(n / 2)`).
2. Tell the user:

> Scaling to <n> replicas requires <new_server_count> Hetzner nodes
> (currently <current_server_count>). This will provision
> <new - current> additional node(s).
>
> Proceed with Terraform apply? (y/n)

If **y**:

```bash
# Update server_count in terraform.tfvars
# (edit the file, do not overwrite other values)
```

```bash
just terraform hetzner plan
```

Show the plan. Ask for final confirmation, then:

```bash
just terraform hetzner apply -auto-approve
```

After apply, add new nodes to SSH known hosts and fetch the updated kubeconfig:

```bash
just get-kubeconfig
```

If **n**, stop.

## Step 4 — Update replicas in Helm values

Edit `helm/site/values.secret.yaml` and set `replicas` to `<n>`.

## Step 5 — Deploy

```bash
just deploy-config
```

This pushes the updated secret to GitHub Actions and applies the Helm chart.

Tell the user:

> **Scale-up complete.**
> Replicas: <old> -> <n>
>
> Verify with: `just kube get pods`
