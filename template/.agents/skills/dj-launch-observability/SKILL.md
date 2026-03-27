---
description: Deploy the observability stack (Grafana + Prometheus + Loki)
---

Deploy the observability stack (Grafana + Prometheus + Loki) to a running cluster.

Run this after `/dj-launch` once your application is live.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

**Secret handling rules:**
- Never echo or print secret values to the terminal or chat.
- When a secret field is empty or `CHANGE_ME`, fill it in the values file directly.
- Never ask the user to paste a secret into this chat.

---

## Pre-flight — Monitor VM

Read `create_monitor` from `terraform/hetzner/terraform.tfvars`.

If `create_monitor` is `false` or the file does not exist, the monitor VM was not
provisioned during `/dj-launch`. Ask the user:

> The monitor VM has not been provisioned yet. Provisioning it will create one
> additional Hetzner node and apply the Hetzner terraform. Proceed? (y/n)

If **n**, stop.

If **y**:

1. Set `create_monitor = true` in `terraform/hetzner/terraform.tfvars`.
2. Run:
   ```bash
   just terraform hetzner plan
   ```
   Show the plan. Confirm it adds only the monitor node and its firewall, then apply:
   ```bash
   just terraform hetzner apply -auto-approve
   ```

Wait for apply to complete before continuing.

---

## Pre-flight — Cluster

Check if the Kubernetes MCP server is configured in `.mcp.json`. If
`mcpServers.kubernetes` is present, use it to verify the cluster is accessible
by listing nodes. Otherwise:

```bash
just --yes rkube get nodes
```

If this fails, ensure your kubeconfig is set up (`just get-kubeconfig`).

---

## Step 1 — Grafana admin password

Check `helm/observability/values.secret.yaml`:

- If it does not exist, copy from the example:
  ```bash
  cp helm/observability/values.secret.yaml.example helm/observability/values.secret.yaml
  ```

Read `kube-prometheus-stack.grafana.adminPassword` from the file.

If it is already set to a non-empty, non-`CHANGE_ME` value, skip this step.

Otherwise, auto-generate a password:

```bash
openssl rand -hex 16
```

Write the generated password to `helm/observability/values.secret.yaml` without
printing it. Tell the user:

> A Grafana admin password has been generated and saved to
> `helm/observability/values.secret.yaml`. You will need it to log in at
> `https://grafana.<domain>` — note it somewhere safe now.

---

## Step 1b — Grafana DNS record

Read `terraform/cloudflare/terraform.tfvars`. If `grafana_subdomain` is not set or
is empty, set it to `"grafana"` and set `monitor_ip` to the monitor node's public IP:

```bash
monitor_ip=$(just terraform-value hetzner monitor_public_ip)
```

Then re-apply the Cloudflare terraform to create the Grafana DNS record:

```bash
just terraform cloudflare apply -auto-approve
```

---

## Step 2 — Deploy

```bash
just helm observability
```

Wait for the command to complete. If it fails, show the error and help the user diagnose it.

Then verify pods are running. If Kubernetes MCP is configured, use it to check pod
status in the `monitoring` namespace. Otherwise:

```bash
just --yes rkube get pods -n monitoring
```

Once all pods are Running, tell the user:

> Observability stack deployed.
> Grafana is available at https://grafana.<domain> once DNS propagates.
> Log in with username `admin` and the password noted above.

---

## Step 3 — Configure OTLP endpoint in app

Now that the observability stack is deployed, configure the app to send telemetry.

Read `secrets.openTelemetryUrl` from `helm/site/values.secret.yaml`.

If it is empty, discover the OTLP collector service name dynamically:

```bash
just --yes rkube get svc -A | grep otel
```

Use the discovered service name and namespace to build the endpoint URL. The
typical result is:

```
http://otel-gateway.default.svc.cluster.local:4318
```

If no otel service is found, tell the user:

> No OTLP collector service found in the cluster. Verify the observability
> chart deployed correctly with `just --yes rkube get pods -n monitoring`.

Write the discovered endpoint to `secrets.openTelemetryUrl`.

Then push the updated config and redeploy:

```bash
just deploy-config
```

Tell the user:
> App configured to send telemetry to the observability stack.

---

## User-facing outputs

| Value | Why the user needs it |
|-------|----------------------|
| Grafana URL (`https://grafana.<domain>`) | Confirm stack is reachable |
| Grafana admin password | Auto-generated — user must note it |
