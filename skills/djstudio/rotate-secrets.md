Rotate secrets in `helm/site/values.secret.yaml` and redeploy.

**Safety rule:** Always show the user exactly which secrets will change and wait
for confirmation before writing any file or running any command.

---

## 1. Pre-flight

Check that `helm/site/values.secret.yaml` exists. If it does not, tell the user:
> `helm/site/values.secret.yaml` not found. Run `/djstudio launch` first to set
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

If **yes**, generate a new random human-readable slug using the same word
list as the launch wizard:

```python
import random
adjectives = ["amber","azure","brave","calm","cold","dark","deep","fast",
              "gold","iron","jade","keen","lime","mist","navy","oak","pale",
              "pine","sage","salt","sand","silk","snow","soft","teal","warm"]
nouns = ["arch","bay","cliff","cove","creek","dale","dell","dune","fall",
         "fen","ford","glen","hill","isle","lake","mead","moor","peak",
         "pool","rill","rock","shore","vale","weald","well","wood"]
new_admin_url = f"{random.choice(adjectives)}-{random.choice(nouns)}/"
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

For each of the following keys, if the key is present in the file and non-empty,
prompt the user to update it (pressing Enter keeps the current value):

| Key | Label |
|-----|-------|
| `secrets.mailgunApiKey` | Mailgun API key |
| `secrets.sentryUrl` | Sentry DSN URL |
| `secrets.openTelemetryUrl` | OpenTelemetry collector endpoint |
| `secrets.hetznerStorageAccessKey` | Hetzner S3 access key |
| `secrets.hetznerStorageSecretKey` | Hetzner S3 secret key |

For each, show:
> <Label> [current: ••••<last-4-chars>] (press Enter to keep):

Only prompt for keys that are currently set to a non-empty, non-`CHANGE_ME` value.
Skip keys that are empty or `CHANGE_ME` — they were not configured and are not in
scope for rotation.

---

## 4. Observability secrets (conditional)

Check whether `helm/observability/values.secret.yaml` exists. If it does, the
observability stack (Grafana + Prometheus + Loki) is deployed and its secrets
should also be offered for rotation.

**Grafana admin password:**

Read `kube-prometheus-stack.grafana.adminPassword` from the file. If it is set
to a non-empty, non-`CHANGE_ME` value, ask:

> Grafana admin password [current: ••••<last-4-chars>] (press Enter to keep,
> or type a new password):

If the user enters a new value, include it in the proposed changes summary
(truncated to first 8 chars + `…`) and write it to
`helm/observability/values.secret.yaml` as part of step 5.

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
  # auto-generated — rotate with: /djstudio rotate-secrets
  adminUrl: "<new-slug>/"

secrets:
  # auto-generated — rotate with: /djstudio rotate-secrets
  postgresPassword: "<new-value>"
  # auto-generated — rotate with: /djstudio rotate-secrets
  djangoSecretKey: "<new-value>"
  djangoSecretKeyFallbacks: "<old-django-key>"
  # auto-generated — rotate with: /djstudio rotate-secrets
  redisPassword: "<new-value>"
```

Then deploy:

```bash
just deploy-config
```

Tell the user:
> Secrets rotated and deployed. Once all pods are healthy, you can clear
> `djangoSecretKeyFallbacks` by running `/djstudio rotate-secrets` again
> and choosing not to rotate the Django key — or remove the fallback
> manually when all active sessions have expired.
