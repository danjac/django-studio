---
description: Rotate auto-generated and third-party Helm secrets and redeploy
---

Rotate secrets in `helm/site/values.secret.yaml` and redeploy.

## Required reading

- `docs/deployment.md`
- `resources/deploy-env-vars.md` — deployment env var reference (shared)

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
new_admin_url="$(uv run python .agents/skills/resources/random-slug.py)/"
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

Third-party secrets are rotated by updating them in `.env` and re-running this skill.
The wizard reads the current value from `.env` (or shell env) and the stored value
from `values.secret.yaml`, and proposes an update if they differ.

Tell the user:

> To rotate a third-party secret, update the relevant variable in `.env`, then
> say **done**. The wizard will detect changed values and propose an update.
> Press Enter to continue without rotating.

For each key below, check if it is present in `values.secret.yaml` (non-empty,
non-`CHANGE_ME`). If so, read the corresponding env var from `.env` / shell env
and compare to the stored value:

| `values.secret.yaml` key | Env var |
|--------------------------|---------|
| `secrets.mailgunApiKey` | `MAILGUN_API_KEY` |
| `secrets.sentryUrl` | `SENTRY_DSN` |
| `secrets.openTelemetryUrl` | `OTLP_ENDPOINT` |
| `secrets.hetznerStorageAccessKey` | `HETZNER_STORAGE_ACCESS_KEY` |
| `secrets.hetznerStorageSecretKey` | `HETZNER_STORAGE_SECRET_KEY` |
| `secrets.backupAccessKey` | (no env var — skip) |
| `secrets.backupSecretKey` | (no env var — skip) |

- If the env var value differs from the stored value: include it in the proposed
  changes summary (truncated to first 8 chars + `…`).
- If they match or the env var is unset: skip silently.

Only prompt for keys that are currently set to a non-empty, non-`CHANGE_ME` value.

---

## 4. Observability secrets (conditional)

Check whether `helm/observability/values.secret.yaml` exists. If it does, the
observability stack (Grafana + Prometheus + Loki) is deployed and its secrets
should also be offered for rotation.

**Grafana admin password:**

Read `kube-prometheus-stack.grafana.adminPassword` from the file. If it is set
to a non-empty, non-`CHANGE_ME` value, read `GRAFANA_ADMIN_PASSWORD` from
`.env` / shell env and compare to the stored value.

- If they differ: include in proposed changes (truncated).
- If they match or `GRAFANA_ADMIN_PASSWORD` is unset: skip.

Tell the user before proceeding:
> To rotate the Grafana password, update `GRAFANA_ADMIN_PASSWORD` in `.env`,
> then continue.

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

Then deploy:

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
