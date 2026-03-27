---
description: View or change the webapp replica count
---

View or change the webapp replica count.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/deployment.md`

Parse `$ARGUMENTS` as: `[n]` (optional target replica count).

---

## No arguments — show current replica count

Read `replicas` from `helm/site/values.secret.yaml` (falls back to
`helm/site/values.yaml` if the secret file does not exist).

Also read `webapp_count` from `terraform/hetzner/terraform.tfvars` to show the
current Hetzner node count.

Display:

> **Current deployment:**
> - Webapp replicas: `<replicas>`
> - Hetzner nodes (webapp): `<webapp_count>`

Then stop — do not prompt to change anything.

---

## With argument — scale to `<n>` replicas

### Step 1 — Validate and warn

Read the current `replicas` value (same lookup as above).

If `<n>` equals the current value:

> Already running `<n>` replicas — nothing to do.

Stop.

If `<n>` is **0**, warn:

> ⚠️ Scaling to 0 replicas will make the application **unavailable**.
> Are you sure? [y/n]

Wait for confirmation. If no, stop.

If `<n>` is **1**, warn:

> ⚠️ Running a single replica means **no redundancy** — a pod restart
> will cause brief downtime.
> Continue? [y/n]

Wait for confirmation. If no, stop.

### Step 2 — Check node capacity

Read `webapp_count` from `terraform/hetzner/terraform.tfvars`.

If `<n>` > `webapp_count`, advise:

> You're scaling to `<n>` replicas but only have `<webapp_count>` Hetzner
> node(s). Consider increasing `webapp_count` in
> `terraform/hetzner/terraform.tfvars` to `<n>` and running:
>
> ```bash
> just tf hetzner apply
> ```
>
> Provision additional nodes first? [y/n]

If yes, update `webapp_count` in `terraform.tfvars` and run `just tf hetzner apply`.
Wait for it to complete before proceeding.

If no, proceed with the current node count (Kubernetes will schedule pods as best
it can).

### Step 3 — Update replicas

Set `replicas: <n>` in `helm/site/values.secret.yaml`.

If `values.secret.yaml` does not exist, set it in `helm/site/values.yaml` instead.

### Step 4 — Deploy

```bash
just deploy-config
```

### Step 5 — Verify

```bash
kubectl get pods -l app=django-app
```

Confirm the expected number of pods are running.
