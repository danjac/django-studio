---
description: Rotate auto-generated and third-party Helm secrets and redeploy
---

Rotate secrets in `helm/site/values.secret.yaml` and redeploy.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/deployment.md`

---

**Safety rule:** Always show the user exactly which secrets will change and wait
for confirmation before writing any file or running any command.

**Secret handling rules:** Never echo or print secret values. Report errors by
variable name, not value. Truncate displayed values to first 8 chars + `…`.

---

## 1. Pre-flight

Check that `helm/site/values.secret.yaml` exists. If it does not, tell the user:
> `helm/site/values.secret.yaml` not found. Run `/dj-launch` first to set
> up your deployment secrets.

Stop.

---

## 2. Auto-generated secrets

The following secrets were auto-generated during initial deploy and can be
rotated automatically:

- `secrets.postgresPassword`
- `secrets.djangoSecretKey`
- `secrets.redisPassword`
- `app.adminUrl`

Generate new values:

```bash
new_postgres=$(openssl rand -hex 32)
new_django=$(openssl rand -hex 32)
new_redis=$(openssl rand -hex 32)
```

For `djangoSecretKey`, the current value must be preserved as a fallback so that
existing sessions remain valid during the rollout window. Read the current value
and move it to `secrets.djangoSecretKeyFallbacks` alongside the new key.

For `app.adminUrl` — ask first, since changing the URL disrupts any bookmarks or
runbooks that reference the current admin path:
> Do you want to rotate the Django admin URL? Changing it will invalidate any
> bookmarks or scripts that use the current path. (y/n)

If **yes**, generate a new random human-readable slug:

```bash
new_admin_url="$(.agents/skills/bin/random-slug.py)/"
```

Present the pending changes before touching anything:

```
PROPOSED ROTATIONS
==================
secrets.postgresPassword    <current-truncated>  →  <new-truncated>
secrets.djangoSecretKey     <current-truncated>  →  <new-truncated>
  (current key moved to djangoSecretKeyFallbacks for session continuity)
secrets.redisPassword       <current-truncated>  →  <new-truncated>
app.adminUrl                <current-value>      →  <new-slug>/   (only if confirmed above)
```

Truncate displayed values to the first 8 characters followed by `…` — never
print full secret values.

Ask:
> Rotate these secrets? (y/n)

If **n**, stop without making any changes.

---

## 3. Third-party secrets

For each key below, check if it is currently set in `values.secret.yaml`
(non-empty, non-`CHANGE_ME`). For each that is set, ask:

> Do you want to rotate `<key>`? (y/n)

If **yes**:

> **Action required:** Open `helm/site/values.secret.yaml`, update `<key>` with
> your new value, then say **continue**.

Wait for the user to confirm, then re-read the file. Include the change in the
proposed summary (truncated to first 8 chars + `…`).

| `values.secret.yaml` key | Where to get the new value |
|--------------------------|---------------------------|
| `secrets.mailgunApiKey` | mailgun.com → Sending → Domains → API Keys |
| `secrets.sentryUrl` | Sentry → Project → Settings → Client Keys → DSN |
| `secrets.hetznerStorageAccessKey` | Hetzner → Security → S3 credentials |
| `secrets.hetznerStorageSecretKey` | Hetzner → Security → S3 credentials |
| `secrets.backupAccessKey` | Hetzner → Security → S3 credentials |
| `secrets.backupSecretKey` | Hetzner → Security → S3 credentials |

---

## 4. Observability secrets (conditional)

Check whether `helm/observability/values.secret.yaml` exists. If it does, the
observability stack (Grafana + Prometheus + Loki) is deployed and its secrets
should also be offered for rotation.

**Grafana admin password:**

Read `kube-prometheus-stack.grafana.adminPassword` from the file. If it is set
to a non-empty, non-`CHANGE_ME` value, ask:

> Do you want to rotate the Grafana admin password? (y/n)

If **yes**, auto-generate a new password:

```bash
openssl rand -hex 16
```

> **Action required:** Open `helm/observability/values.secret.yaml`, update
> `kube-prometheus-stack.grafana.adminPassword` with the new password, then
> say **continue**. Note the new password — you will need it to log in.

Wait for the user to confirm, then re-read the file. Include the change in the
proposed summary (truncated).

After applying, redeploy the observability stack:
```bash
just helm observability
```

Tell the user:
> Grafana password rotated and observability stack redeployed. Log in at
> https://grafana.<domain> with the new password.

If `helm/observability/values.secret.yaml` does not exist, skip this section
entirely — the observability stack has not been deployed.

---

## 5. Apply changes

Write the updated values to `helm/site/values.secret.yaml` (and
`helm/observability/values.secret.yaml` if Grafana password was changed),
preserving all other keys unchanged. Each auto-generated value must have its own rotation comment
immediately above it:

```yaml
app:
  # auto-generated — rotate with: /dj-rotate-secrets
  adminUrl: "<new-slug>/"

secrets:
  # auto-generated — rotate with: /dj-rotate-secrets
  postgresPassword: "<new-value>"
  # auto-generated — rotate with: /dj-rotate-secrets
  djangoSecretKey: "<new-value>"
  djangoSecretKeyFallbacks: "<old-django-key>"
  # auto-generated — rotate with: /dj-rotate-secrets
  redisPassword: "<new-value>"
```

### 5a. Update passwords in running services

**Before** redeploying the app, update the passwords in the running database and
cache services. Otherwise the app will restart with new credentials while the
services still expect the old ones, causing immediate 500 errors.

**PostgreSQL:**
```bash
kubectl --kubeconfig "$(just --evaluate kubeconfig)" exec postgres-0 -- su postgres -c "psql -U postgres -c \"ALTER USER postgres PASSWORD '<new_postgres_password>';\""
```

**Verify** the output contains `ALTER ROLE`. If it does not (empty output, error, or
unexpected text), **stop immediately**. Tell the user what went wrong (show the
error output) and ask:

> PostgreSQL password was **not** updated — the database still has the old password.
> Deploy has been paused. Would you like me to diagnose and retry, or do you want
> to fix it manually? (retry/manual)

If **retry**, investigate the error, adjust the command, and try again. Do not
proceed to deploy until `ALTER ROLE` is confirmed.

If **manual**, stop and tell the user to re-run `/dj-rotate-secrets` when ready.

**Redis:**
```bash
kubectl --kubeconfig "$(just --evaluate kubeconfig)" exec deploy/redis -- redis-cli -a "<old_redis_password>" CONFIG SET requirepass "<new_redis_password>"
```

**Verify** the output contains `OK`. If it does not, **stop immediately**. Tell the
user what went wrong and ask:

> Redis password was **not** updated — Redis still has the old password.
> Deploy has been paused. Would you like me to diagnose and retry, or do you want
> to fix it manually? (retry/manual)

Same flow as above — do not proceed to deploy until `OK` is confirmed.

Replace `<new_postgres_password>`, `<old_redis_password>`, and `<new_redis_password>`
with the actual values (do not print them to the chat — pipe them from variables).

### 5b. Patch the live Kubernetes Secret atomically

After updating the running services, patch **all** affected keys in the live
Kubernetes Secret in a single `kubectl patch` call. This ensures that any pods
restarted before `helm upgrade` completes will pick up consistent credentials —
including the full connection-string keys (`DATABASE_URL`, `REDIS_URL`) that
embed the passwords.

Build base64-encoded values for every key that changed and patch them in one
call:

```bash
NEW_POSTGRES_PASSWORD="$new_postgres" \
NEW_REDIS_PASSWORD="$new_redis" \
NAMESPACE="$namespace" \
KUBECONFIG="$(just --evaluate kubeconfig)" \
  .agents/skills/dj-rotate-secrets/bin/patch-k8s-secrets.sh
```

Replace `$namespace` with the Helm release namespace (the same namespace the
chart is deployed into).

**Verify** the output contains `secret/secrets patched`. If it does not, **stop
immediately** and tell the user what went wrong.

### 5c. Restart app deployments

Environment variables are baked into pods at start time. Restart the app and
worker deployments so running pods pick up the patched secret:

```bash
just --yes rkube rollout restart deployment/django-app deployment/django-worker
```

**Verify** each deployment shows `deployment.apps/django-app restarted` and
`deployment.apps/django-worker restarted`. If either fails, stop and ask the
user before continuing.

### 5d. Deploy the app

```bash
just deploy-config
```

Tell the user:
> Secrets rotated and deployed. Once all pods are healthy, you can clear
> `djangoSecretKeyFallbacks` by running `/dj-rotate-secrets` again
> and choosing not to rotate the Django key — or remove the fallback
> manually when all active sessions have expired.

---

## User-facing outputs

| Value | Why the user needs it |
|-------|----------------------|
| Proposed rotations summary (truncated) | Confirm before applying |
| New admin URL (if rotated) | Update bookmarks/runbooks |
| Grafana URL (if password rotated) | Confirm login works |
