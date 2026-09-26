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

Read `replicas` from `helm/site/values.yaml` (it is non-secret config, so it lives
in the git-tracked values file).

Also read `webapp_count`, `create_jobrunner` and `create_database` from
`terraform/hetzner/terraform.tfvars` to determine the current topology.

If `webapp_count` is `0`, display:

> **Current deployment:** single-node topology
> - Webapp replicas: `<replicas>` (running on the server node)
> - Dedicated jobrunner node: `<create_jobrunner>`
> - Dedicated database node: `<create_database>`
>
> All webapp replicas share the server node with PostgreSQL, Redis and the
> worker. See `docs/infrastructure.md` for the scaling path.

Otherwise display:

> **Current deployment:** split topology
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

### Step 2 — Check node capacity (scale-up and scale-down)

Read `webapp_count` from `terraform/hetzner/terraform.tfvars`.

**Single-node topology (`webapp_count` is 0):** the webapp shares the server node
with PostgreSQL, Redis and the worker. Extra replicas on the same box add
resilience against a pod crash but no extra CPU or memory. If `<n>` > 1, advise:

> You are on the single-node topology, so all `<n>` replicas will run on the
> server node alongside PostgreSQL, Redis and the worker. That guards against a
> pod crash but does not add capacity — and each replica requests ~1 GB.
>
> To add real capacity, move the webapp to dedicated nodes by setting
> `webapp_count = <n>` in `terraform/hetzner/terraform.tfvars`
> (see `docs/infrastructure.md`).
>
> Options: [1] add replicas on the server node  [2] provision `<n>` dedicated
> webapp nodes  [3] cancel

If **2**, set `webapp_count` to `<n>` and follow the scale-up flow below.
If **3**, stop. If **1**, skip to Step 3.

**Scale-up:** If `<n>` > `webapp_count`, advise:

> You're scaling to `<n>` replicas but only have `<webapp_count>` Hetzner
> node(s). Consider increasing `webapp_count` in
> `terraform/hetzner/terraform.tfvars` to `<n>` first.
>
> Provision additional nodes first? [y/n]

If yes, update `webapp_count` to `<n>` in `terraform.tfvars` and run:

```bash
just terraform hetzner plan
```

Show the plan output, then ask:

> Proceed with apply? [y/n]

If yes:

```bash
just terraform hetzner apply -auto-approve
```

Wait for it to complete before proceeding.

If no, proceed with the current node count (Kubernetes will schedule pods as best
it can).

**Scale-down:** If `<n>` < `webapp_count`, note that Hetzner nodes will be
deprovisioned **after** the replica count is reduced (so pods are drained
first and no workload lands on the node being removed).

Proceed to Step 3 now. After deploy completes, return to Step 2 to deprovision.

If no scale-down is needed (node counts already match or user declines), proceed
without changing node count (user accepts the ongoing cost).

### Step 3 — Update replicas

Set `replicas: <n>` in `helm/site/values.yaml`.

That file is tracked by git — remind the user to commit the change.

### Step 4 — Deploy

`replicas` is non-secret config, so no secrets need pushing to GitHub:

```bash
just helm site
```

### Step 4b — Deprovision idle nodes (scale-down only)

If this was a scale-down and `<n>` < `webapp_count`, now deprovision the idle nodes:

> `<webapp_count - n>` idle Hetzner node(s) will be removed. Deprovision now? [y/n]

If yes, update `webapp_count` to `<n>` in `terraform.tfvars` and run:

```bash
just terraform hetzner plan
```

Show the plan output, then ask:

> Proceed with apply? [y/n]

If yes:

```bash
just terraform hetzner apply -auto-approve
```

Wait for it to complete before proceeding.

If no, leave the nodes running (user accepts the ongoing cost).

### Step 5 — Verify

```bash
just --yes rkube get pods -l app=django-app
```

Confirm the expected number of pods are running.
