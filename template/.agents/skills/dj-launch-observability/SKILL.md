---
description: Deploy the observability stack (Grafana + Prometheus + Loki)
---

Deploy the observability stack (Grafana + Prometheus + Loki) to a running cluster.

## Required reading

- `docs/deployment.md`
- `resources/deploy-env-vars.md` — deployment env var reference (shared)

---

Run this after `/dj-launch` once your application is live.

**Secret handling rules:** Never echo or print secret values. Read from `.env` / shell
environment. Report errors by variable name, not value.

---

## Pre-flight

Verify the cluster is accessible:

```bash
just kube get nodes
```

If this fails, ensure your kubeconfig is set up (`just get-kubeconfig`).

---

## Step 1 — Grafana admin password

Check `helm/observability/values.secret.yaml`:

- If it does not exist, copy from the example:
  ```bash
  cp helm/observability/values.secret.yaml.example helm/observability/values.secret.yaml
  ```

Read the file. If `kube-prometheus-stack.grafana.adminPassword` is already set to a
non-empty, non-`CHANGE_ME` value, skip this step.

Otherwise, read `GRAFANA_ADMIN_PASSWORD` from the environment (load `.env` if present).

- If `GRAFANA_ADMIN_PASSWORD` is set: write it to `values.secret.yaml` without printing
  the value. Tell the user: "Grafana password loaded from environment."
- If not set: auto-generate one:
  ```bash
  openssl rand -hex 4
  ```
  Write the generated password to `helm/observability/values.secret.yaml`.
  Tell the user the generated password — they will need it to log in at
  `https://grafana.<domain>`. Suggest they save it to `.env` as
  `GRAFANA_ADMIN_PASSWORD` for future reference.

---

## Step 2 — Deploy

```bash
just helm observability
```

Wait for the command to complete. If it fails, show the error and help the user diagnose it.

Then show pod status:

```bash
just kube get pods -n monitoring
```

Once all pods are Running, tell the user:

> Observability stack deployed.
> Grafana is available at https://grafana.<domain> once DNS propagates.
> Log in with username `admin` and the password set above.

---

## User-facing outputs

| Value | Why the user needs it |
|-------|----------------------|
| Grafana URL (`https://grafana.<domain>`) | Confirm stack is reachable |
| Grafana admin password | Only printed if auto-generated — user must save it |
