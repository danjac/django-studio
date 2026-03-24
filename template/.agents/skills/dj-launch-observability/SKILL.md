---
description: Deploy the observability stack (Grafana + Prometheus + Loki)
---

Deploy the observability stack (Grafana + Prometheus + Loki) to a running cluster.

## Required reading

- `docs/Deployment.md`

---

Run this after `/dj-launch` once your application is live.

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

Read the file. If `kube-prometheus-stack.grafana.adminPassword` is `CHANGE_ME` or empty, ask:

> Enter a Grafana admin password (press Enter to auto-generate one):

If the user presses Enter, generate one:

```bash
openssl rand -hex 4
```

Write the chosen password to `helm/observability/values.secret.yaml` and tell the user
what it is — they will need it to log in at `https://grafana.<domain>`.

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

## Help

**/dj-launch-observability**

Deploys the observability stack (Grafana + Prometheus + Loki) to the cluster.
Run this after `/dj-launch` once the main application is live.

Sets a Grafana admin password (auto-generated if not provided), then runs
`just helm observability`.

Example:
  /dj-launch-observability
