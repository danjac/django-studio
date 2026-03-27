---
description: Scale down django-app replicas and optionally remove Hetzner nodes
---

Scale the number of `django-app` replicas down to a target count. Warns about
availability risks, updates the Helm values, redeploys, and optionally removes
excess Hetzner nodes via Terraform to reduce costs.

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

## Step 2 — Validate and warn

If `<n>` is greater than or equal to the current replica count, tell the user:

> Target (<n>) is not lower than current replicas (<current>).
> Use `/dj-scale-up` to increase replicas.

Stop.

If `<n>` is 0, warn:

> **WARNING:** Scaling to 0 replicas will make the application completely
> unavailable. Are you sure? (y/n)

If `<n>` is 1, warn:

> **WARNING:** Running with 1 replica means zero redundancy — a single pod
> failure will cause downtime. Consider keeping at least 2 replicas for
> availability. Continue? (y/n)

If the user says **n** to any warning, stop.

Otherwise, ask:

> Proceed with scaling down to <n> replicas? (y/n)

If **n**, stop.

## Step 3 — Update replicas in Helm values

Edit `helm/site/values.secret.yaml` and set `replicas` to `<n>`.

## Step 4 — Deploy

```bash
just deploy-config
```

This pushes the updated secret to GitHub Actions and applies the Helm chart.

## Step 5 — Remove excess Hetzner nodes (optional)

After the deploy succeeds, check whether fewer nodes are now needed. A
reasonable heuristic: each node can run ~2 app replicas.

If the current `server_count` exceeds what `<n>` replicas require:

> You now have <current_server_count> Hetzner nodes but only need
> <new_server_count> for <n> replicas. Removing <excess> node(s) will
> reduce your hosting costs.
>
> Remove excess nodes via Terraform? (y/n)

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

After apply, fetch the updated kubeconfig:

```bash
just get-kubeconfig
```

If **n**, skip — tell the user they can remove nodes later.

## Step 6 — Summary

Tell the user:

> **Scale-down complete.**
> Replicas: <old> -> <n>
>
> Verify with: `just kube get pods`
