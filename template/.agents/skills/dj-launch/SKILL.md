---
description: Interactive first-deploy wizard: provisions infra, configures secrets, deploys
---

Interactive first-deploy wizard. Guides the user through provisioning infrastructure,
configuring secrets, and deploying the application end-to-end.

## Required reading

- `docs/infrastructure.md`
- `docs/deployment.md`
- `resources/deploy-env-vars.md` — deployment env var reference (shared)

---

**Idempotency rule:** Never overwrite a value that is already set. Read existing files
first. Only fill in what is missing or still `CHANGE_ME`. Re-running is safe — it resumes
where it left off.

**Secret handling rules:**
- All deployment secrets come from `.env` or the shell environment. `.env` takes precedence.
- Never echo, print, or repeat a secret value in the terminal or chat.
- Check presence only — report missing vars by name, not by value.
- If an API call fails due to authentication, report: "<VAR_NAME> appears to be invalid.
  Update it in `.env` and re-run." Do not repeat the value.
- Write values from env directly to destination files without printing them.

---

## Step 0 — Prepare deployment secrets

Tell the user:

> **Before we begin:** Add your deployment secrets to `.env`.
>
> Open `.env` and fill in the values under the `# ── Deployment ──` section.
> See `resources/deploy-env-vars.md` for where to find each key.
>
> Required:
> - `HETZNER_TOKEN` — Hetzner Cloud API token (Read & Write)
> - `CLOUDFLARE_TOKEN` — Cloudflare API token (Zone permissions)
>
> Required for email:
> - `MAILGUN_API_KEY` — Mailgun sending API key
>
> Optional (skip if not using):
> - `MAILGUN_DKIM_VALUE`, `HETZNER_STORAGE_ACCESS_KEY`, `HETZNER_STORAGE_SECRET_KEY`,
>   `SENTRY_DSN`, `OTLP_ENDPOINT`
>
> Once your `.env` is ready, say **done**.

After the user confirms, check presence of all deployment vars:

```bash
uv run python .agents/skills/resources/check-deploy-env.py
```

If any **required** vars are missing: tell the user which ones, ask them to add them to
`.env`, then re-check. Do not proceed until all required vars are present.

If **optional** vars are missing: warn the user which features will be skipped (e.g. no
email, no object storage, no observability), then continue.

---

## Pre-flight checks

Run all of the following before proceeding. If any fail, tell the user what to install
and stop.

```bash
gh auth status                    # GitHub CLI authenticated
terraform version                 # Terraform installed
helm version                      # Helm installed
just --version                    # just installed
kubectl version --client          # kubectl installed
```

Also verify:
- The project is in a git repository with a GitHub remote: `git remote get-url origin`
  must return a `github.com` URL. If not: STOP — tell the user to create a GitHub repo
  and push the project first. The image will be published to ghcr.io under this repo name.
- Derive the GitHub owner/repo: `gh repo view --json nameWithOwner -q .nameWithOwner`
  Save this as `<github_repo>` (e.g. `danjac/my_project`) for use in later steps.

Print a summary of what will be set up and ask the user to confirm before proceeding.

---

## Step 1 — Hetzner infrastructure

**Check:** Read `terraform/hetzner/terraform.tfvars` if it exists.

For each variable below, skip it if already set to a non-empty, non-`CHANGE_ME` value.

### 1a. Hetzner API token

Read `HETZNER_TOKEN` from the environment (already loaded from `.env` in Step 0).
Write it to `terraform/hetzner/terraform.tfvars` as `hcloud_token` without printing
the value. If the var is absent (should not happen after Step 0 check), stop.

### 1b. SSH public key

If `ssh_public_key` is missing or empty:
- Try to read `~/.ssh/id_ed25519.pub` automatically with `cat ~/.ssh/id_ed25519.pub`
- If found, show the key and ask: "Use this SSH public key? (y/n)"
- If yes, use it. If no (or file not found), ask the user to paste their public key.

Set `ssh_public_key`. (SSH public keys are not secrets — showing them is fine.)

### 1c. K3s token

If `k3s_token` is `CHANGE_ME` or empty, generate one automatically:

```bash
openssl rand -hex 32
```

Set `k3s_token`. Tell the user it has been generated.

### 1d. Location

If `location` is not already set, ask:

> Which Hetzner datacenter location? (default: `nbg1`)
> Options: `nbg1` (Nuremberg), `fsn1` (Falkenstein), `hel1` (Helsinki), `ash` (Ashburn), `hil` (Hillsboro)

Set `location`.

### 1e. Write terraform.tfvars and apply

Write `terraform/hetzner/terraform.tfvars` with all collected values, preserving any
existing values that were already set.

Then:
```bash
just terraform hetzner init    # skip if terraform/hetzner/.terraform/ already exists
just terraform hetzner plan
```

Show the plan output to the user and ask:

> Review the plan above. Proceed with apply? (y/n)

If **n**, stop. If **y**:

```bash
just terraform hetzner apply -auto-approve
```

Wait for apply to complete. If it fails with an authentication error, tell the user:
"HETZNER_TOKEN appears to be invalid. Update it in `.env` and re-run." Do not repeat
the token value.

If it fails for another reason, show the error and stop.

Then add the new server to SSH known hosts (required to avoid host key verification
failures when fetching the kubeconfig):
```bash
server_ip=$(just terraform-value hetzner server_public_ip)
ssh-keyscan -H "$server_ip" >> ~/.ssh/known_hosts
```

Tell the user the server IP address — they may need it for DNS verification or SSH.

Then fetch the kubeconfig:
```bash
just get-kubeconfig
```

---

## Step 2 — Cloudflare DNS and SSL

**Check:** Read `terraform/cloudflare/terraform.tfvars` if it exists.

### 2a. Confirm domain is Active in Cloudflare

Before proceeding, tell the user:

> **Before continuing:** Make sure your domain has been added to your Cloudflare account
> and its nameservers are pointing to Cloudflare (status: **Active**).
>
> Is `<domain>` showing as Active in your Cloudflare dashboard? (y/n)

If the user answers **n**, stop and tell them to:
1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → Add a Site → enter the domain
2. Update the domain's nameservers at their registrar to point to Cloudflare
3. Wait for the domain to show as **Active**, then re-run `/dj-launch`

Only continue when the user confirms the domain is Active.

### 2b. Cloudflare API token

Read `CLOUDFLARE_TOKEN` from the environment and write it to
`terraform/cloudflare/terraform.tfvars` as `cloudflare_api_token` without printing
the value.

### 2c. Domain

If `domain` is missing, empty, or `example.com`, ask the user to confirm or enter their domain.
Otherwise use the existing value.

### 2d. Server IP

Get automatically from Hetzner terraform output (already applied in Step 1):
```bash
just terraform-value hetzner server_public_ip
```
Set `server_ip`.

### 2e. Mailgun DNS records

If `MAILGUN_DKIM_VALUE` is set in the environment, ask:

> Configure Mailgun DNS records in Cloudflare using the DKIM value from your `.env`? (y/n)

If **yes**:

Ask:
> Enter your Mailgun sender domain (e.g. `mg.example.com`):

Ask:
> Are you using EU Mailgun servers? (Y/n) [default: yes]

Set:
- `mailgun_dkim_value` ← from `$MAILGUN_DKIM_VALUE` (write directly, do not print)
- `mailgun_mx_servers` ← `["mxa.eu.mailgun.org", "mxb.eu.mailgun.org"]` if yes (default),
  otherwise `["mxa.mailgun.org", "mxb.mailgun.org"]`

If `MAILGUN_DKIM_VALUE` is not set, or user answers **no**, skip. Tell the user:
> Mailgun DNS records will not be added automatically. Add them manually in Cloudflare DNS
> after deploy if you want outbound email to work.

### 2f. Write terraform.tfvars and apply

Write `terraform/cloudflare/terraform.tfvars` with all collected values, including
`mailgun_dkim_value` and `mailgun_mx_servers` if collected in 2e.

Then:
```bash
just terraform cloudflare init    # skip if terraform/cloudflare/.terraform/ already exists
just terraform cloudflare plan
```

Show the plan output to the user and ask:

> Review the plan above. Proceed with apply? (y/n)

If **n**, stop. If **y**:

```bash
just terraform cloudflare apply -auto-approve
```

If `terraform apply` fails with an authentication error, tell the user:
"CLOUDFLARE_TOKEN appears to be invalid. Update it in `.env` and re-run."

If it fails with "A similar configuration with rules already exists and overwriting will
have unintended consequences", existing Cloudflare rulesets must be imported before
applying. Run:

```bash
# Get zone ID from Cloudflare (read cloudflare_api_token from terraform.tfvars)
zone_id=$(cd terraform/cloudflare && terraform output -raw zone_id 2>/dev/null || \
  curl -s "https://api.cloudflare.com/client/v4/zones?name=<domain>" \
    -H "Authorization: Bearer <cloudflare_api_token>" | jq -r '.result[0].id')

# List existing rulesets
curl -s "https://api.cloudflare.com/client/v4/zones/$zone_id/rulesets" \
  -H "Authorization: Bearer <cloudflare_api_token>" | jq '.result[] | {id, phase}'
```

Match rulesets by phase and import using format `zone/<zone_id>/<ruleset_id>`:

```bash
cd terraform/cloudflare
# http_request_firewall_custom → cloudflare_ruleset.zone_level_firewall
terraform import cloudflare_ruleset.zone_level_firewall zone/<zone_id>/<ruleset_id>

# http_response_headers_transform → cloudflare_ruleset.transform_response_headers
terraform import cloudflare_ruleset.transform_response_headers zone/<zone_id>/<ruleset_id>
```

Then re-run `just terraform cloudflare apply`.

Wait for apply to complete. If it fails for a different reason, show the error and stop.

---

## Step 3 — Object Storage (skip if terraform/storage/ does not exist)

**Check:** Read `terraform/storage/terraform.tfvars` if it exists.

If `access_key` and `secret_key` are already set, skip this step entirely.

If `HETZNER_STORAGE_ACCESS_KEY` and `HETZNER_STORAGE_SECRET_KEY` are set in the
environment, write them to `terraform/storage/terraform.tfvars` as `access_key` and
`secret_key` without printing the values.

If either is missing from the environment, tell the user:

> **HETZNER_STORAGE_ACCESS_KEY or HETZNER_STORAGE_SECRET_KEY is not set.**
> Add them to `.env` (Hetzner → Security → S3 credentials → Generate credentials)
> and re-run. The secret key is shown only once when generated.

Stop until the vars are present.

Write `terraform/storage/terraform.tfvars` with collected values.

```bash
just terraform storage init    # skip if terraform/storage/.terraform/ already exists
just terraform storage plan
```

Show the plan output to the user and ask:

> Review the plan above. Proceed with apply? (y/n)

If **n**, stop. If **y**:

```bash
just terraform storage apply -auto-approve
```

---

## Database backups

Tell the user:

> Automated database backups are not set up here. Run `/dj-enable-db-backups` when your project is live and actively used.

Then continue to Step 4.

---

## Step 4 — Helm secrets

**Check:** If `helm/site/values.secret.yaml` does not exist, copy it from the example:
```bash
cp helm/site/values.secret.yaml.example helm/site/values.secret.yaml
```

Read the current file. For each value below, skip if already set to a non-empty,
non-`CHANGE_ME` value.

### Auto-generated secrets

Generate each with `openssl rand -hex 32` if not already set:
- `secrets.postgresPassword`
- `secrets.djangoSecretKey`
- `secrets.redisPassword`

Write each value with an individual comment immediately above it:

```yaml
app:
  # auto-generated — rotate with: /dj-rotate-secrets
  adminUrl: "<generated-slug>/"

secrets:
  # auto-generated — rotate with: /dj-rotate-secrets
  postgresPassword: "<generated>"
  # auto-generated — rotate with: /dj-rotate-secrets
  djangoSecretKey: "<generated>"
  # auto-generated — rotate with: /dj-rotate-secrets
  redisPassword: "<generated>"
```

Tell the user these have been generated automatically.

### Values from Terraform outputs

Fetch automatically — never prompt for these:

- `postgres.volumePath` ← `just terraform-value hetzner postgres_volume_mount_path`
- `secrets.cloudflare.cert` ← `just terraform-value cloudflare origin_cert_pem`
- `secrets.cloudflare.key` ← `just terraform-value cloudflare origin_key_pem`

If `terraform/storage/` exists:
- `secrets.hetznerStorageBucket` ← `just terraform-value storage bucket_name`
- `secrets.hetznerStorageEndpoint` ← `just terraform-value storage endpoint_url`
- `secrets.hetznerStorageAccessKey` ← read from `terraform/storage/terraform.tfvars` (do not print)
- `secrets.hetznerStorageSecretKey` ← read from `terraform/storage/terraform.tfvars` (do not print)
- `secrets.useS3Storage` ← set to `"true"`

### Domain values

- `domain` ← use the domain confirmed in Step 2
- `app.allowedHosts` ← `.` + domain (e.g. `.my_domain.com`)

### Image

Set a placeholder for now — `just gh deploy` overrides this with the actual SHA tag via
`--set image=...`, so the value here does not affect the first deploy:
- `image` ← `ghcr.io/<github_repo>:main`

### Values requiring user input

For each, only prompt if currently `CHANGE_ME` or empty:

**Admins email** (comma-separated list of Django admin email addresses):
> Enter admin email address(es), comma-separated (e.g. `you@example.com`):

**Contact email:**
> Enter the public contact email address:

**Mailgun sender domain** (the `mg.yourdomain.com` subdomain for outbound email):
> Enter your Mailgun sender domain (e.g. `mg.yourdomain.com`), or press Enter to skip:

**Admin URL** — generate a random human-readable slug if the user skips:

```bash
slug=$(python .agents/skills/resources/random-slug.py)
default_admin_url="${slug}/"
```

Then prompt:
> Enter a custom Django admin URL path (press Enter for `<generated-slug>/`):

- If the user presses Enter (empty input), use the generated slug (e.g. `calm-peak/`).
- If the user types a value, use that value.
- Only fall back to `admin/` if the user explicitly types `admin/`.

Tell the user which URL was chosen — they will need this to access Django admin.

**Site name** — the human-readable name stored in the Django sites framework:
> Enter the site name (e.g. `My Photo Blog`):

Save this as `<site_name>` for use in Step 6c.

**Meta author, description, keywords** — prompt for each, allow empty to skip.

### Observability credentials

Read `SENTRY_DSN` and `OTLP_ENDPOINT` from the environment.
Write each to `values.secret.yaml` if present — without printing the values.
If not set, skip silently (the user was warned in Step 0).

### Mailgun API key

Read `MAILGUN_API_KEY` from the environment.
Write to `secrets.mailgunApiKey` if present — without printing the value.
If not set, skip silently.

### Write the file

Write all values to `helm/site/values.secret.yaml`, preserving any values that were
already set and were not listed above as needing update.

---

## Step 5 — GitHub Actions secrets

```bash
just gh-set-secrets
```

This pushes `KUBECONFIG_BASE64` and `HELM_VALUES_SECRET` to the GitHub repository secrets.
Tell the user what was pushed and confirm with `gh secret list`.

> **After the initial deploy:** whenever you change a config value in
> `values.secret.yaml` (e.g. admin email, feature flag), run `just deploy-config`
> instead of `just gh-set-secrets` and `just helm site` separately. It pushes the
> secrets to GitHub **and** applies the updated Helm chart to the cluster in one step,
> keeping CI and the running cluster in sync.

---

## Step 6 — First deploy

The first deploy requires three steps in sequence. `just gh deploy` alone only updates
app/worker containers — it does not deploy Postgres, Redis, Secrets, or other resources
for the first time. Follow the full sequence below.

### 6a. Build and push the Docker image

Tell the user:
> **Step 1/3 — Building Docker image via GitHub Actions...**
> This pushes the image to ghcr.io so Helm can pull it.

```bash
just gh build
```

Watch the build:
```bash
gh run watch
```

Wait for the build workflow to complete successfully before continuing.

### 6b. Deploy all infrastructure via Helm

Tell the user:
> **Step 2/3 — Deploying infrastructure via Helm...**
> This installs Postgres, Redis, Secrets, Ingress, and all other resources for the first time.
> This runs locally using your kubeconfig.

```bash
just helm site
```

Wait for the command to complete. If it fails, show the error and help the user diagnose it.

### 6c. Trigger app deploy via GitHub Actions

Tell the user:
> **Step 3/3 — Triggering app deploy via GitHub Actions...**
> This deploys the app and worker containers using the image built in step 1.

```bash
just gh deploy
```

Watch the run:
```bash
gh run watch
```

Then show pod status:
```bash
just kube get pods
```

If all pods are Running:

If `<site_name>` was provided in Step 4, run:
```bash
just rdj set_default_site <domain> "<site_name>"
```

If it was not provided, tell the user:
> You can set the default site name at any time by running:
> `just rdj set_default_site <domain> "Your Site Name"`

Then tell the user:

> **Launch complete!**
> Your app is live at https://<domain>
>
> Next steps:
> - Run `just rdj migrate` to apply database migrations
> - Run `just rdj createsuperuser` to create an admin account
> - Visit https://<domain>/<admin-url> to access the Django admin

If any pods are not Running, show the pod status and relevant logs:
```bash
just kube describe pod <failing-pod>
just kube logs <failing-pod>
```
Diagnose and help the user fix the issue before declaring success.

---

## Step 6d — Kubernetes MCP

Now that the cluster is live, offer to add the Kubernetes MCP server to `.mcp.json`
so AI assistants can inspect pods, logs, and deployments directly.

Tell the user:

> Would you like to add the Kubernetes MCP server to `.mcp.json`?
> This lets AI assistants (Claude Code) inspect pods, view logs, and manage
> deployments using your current kubectl context.
>
> Add Kubernetes MCP? (y/n)

If **y**, patch `.mcp.json`:

```bash
python3 -c "
import json, pathlib
p = pathlib.Path('.mcp.json')
config = json.loads(p.read_text())
config['mcpServers']['kubernetes'] = {
    'command': 'npx',
    'args': ['-y', 'mcp-server-kubernetes']
}
p.write_text(json.dumps(config, indent=2) + '\n')
"
```

Tell the user:
> Kubernetes MCP added to `.mcp.json`. Restart Claude Code to activate it.

If **n**, skip silently.

---

## Step 7 — Observability

Check whether `helm/observability/values.secret.yaml` exists.

If it does **not** exist, tell the user:

> The observability stack (Grafana + Prometheus + Loki) is not yet deployed.
> Run `/dj-launch-observability` when you are ready to set it up.

---

## User-facing outputs

The following values are printed to the user during the wizard — they are either
non-secret or required for the user to take action:

| Value | Step | Why the user needs it |
|-------|------|----------------------|
| Server IP address | 1e | SSH access, DNS verification |
| Domain (confirmed) | 2c | Sanity check |
| Admin URL path | 4 | Needed to bookmark Django admin |
| Site URL (`https://<domain>`) | 6c | Confirm app is live |
| Pod status | 6c | Diagnose deploy issues |
| Next-step commands | 6c | `migrate`, `createsuperuser` |
