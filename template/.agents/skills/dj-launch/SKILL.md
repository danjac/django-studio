---
description: Interactive first-deploy wizard: provisions infra, configures secrets, deploys
---

Interactive first-deploy wizard. Guides the user through provisioning infrastructure,
configuring secrets, and deploying the application end-to-end.

## Required reading

- `docs/infrastructure.md`
- `docs/deployment.md`

---

**Idempotency rule:** Never overwrite a value that is already set. Read existing files
first. Only fill in what is missing or still `CHANGE_ME`. Re-running is safe — it resumes
where it left off.

---

## Required accounts checklist

Before starting, tell the user:

> **Before we begin, make sure you have accounts and credentials ready for these services.
> The wizard will ask for them during setup — having them ready will save you from
> stopping mid-flow.**
>
> **1. Hetzner Cloud** ([console.hetzner.cloud](https://console.hetzner.cloud))
> - A project created (or select an existing one)
> - API token with **Read & Write** permissions
>   (Security → API Tokens → Generate API Token)
> - *(If using object storage)* S3 credentials
>   (Security → S3 credentials → Generate credentials)
>
> **2. Cloudflare** ([dash.cloudflare.com](https://dash.cloudflare.com))
> - Your domain added to Cloudflare and showing as **Active**
>   (nameservers must be pointing to Cloudflare at your registrar)
> - API token with Zone permissions:
>   Zone (Edit), Zone Settings (Edit), DNS (Edit), Page Rules (Edit),
>   Zone WAF (Edit), Transform Rules (Edit), SSL and Certificates (Edit)
>
> **3. Mailgun** ([mailgun.com](https://www.mailgun.com)) — *optional, required for email*
> - A sending domain configured (e.g. `mg.yourdomain.com`)
> - Sending API key
> - DKIM TXT record value
>   (Sending → Domains → your domain → DNS Records)
>
> Do you have all of the above ready? (y/n)

If the user answers **n**, tell them to prepare the accounts above and re-run
`/dj-launch` when ready. Stop.

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

If `hcloud_token` is missing or empty, pause and tell the user:

> **Action required — Hetzner API token**
>
> 1. Go to [console.hetzner.cloud](https://console.hetzner.cloud)
> 2. Select your project (or create one)
> 3. Left sidebar → **Security** → **API Tokens**
> 4. Click **Generate API Token**
> 5. Name: anything (e.g. `my_project-terraform`)
> 6. Permissions: **Read & Write**
> 7. Click **Generate Token** — copy it immediately, it won't be shown again
>
> Paste the token:

Read the user's input. Set `hcloud_token`.

### 1b. SSH public key

If `ssh_public_key` is missing or empty:
- Try to read `~/.ssh/id_ed25519.pub` automatically with `cat ~/.ssh/id_ed25519.pub`
- If found, show the key and ask: "Use this SSH public key? (y/n)"
- If yes, use it. If no (or file not found), ask the user to paste their public key.

Set `ssh_public_key`.

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

Wait for apply to complete. If it fails, show the error and stop.

Then add the new server to SSH known hosts (required to avoid host key verification
failures when fetching the kubeconfig):
```bash
server_ip=$(just terraform-value hetzner server_public_ip)
ssh-keyscan -H "$server_ip" >> ~/.ssh/known_hosts
```

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

If `cloudflare_api_token` is missing or empty, pause and tell the user:

> **Action required — Cloudflare API token**
>
> 1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Profile** (top right) → **API Tokens**
> 2. Click **Create Token** → **Create Custom Token**
> 3. Name: anything (e.g. `my_project-terraform`)
> 4. Under **Permissions**, add all of these (Zone level):
>    - Zone → Zone → Edit
>    - Zone → Zone Settings → Edit
>    - Zone → DNS → Edit
>    - Zone → Page Rules → Edit
>    - Zone → Zone WAF → Edit
>    - Zone → Transform Rules → Edit
>    - Zone → SSL and Certificates → Edit
> 5. Under **Zone Resources**: Include → All zones (or select your specific zone)
> 6. Click **Continue to summary** → **Create Token** — copy it immediately
>
> Paste the token:

Read the user's input. Set `cloudflare_api_token`.

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

If the user wants to configure outbound email (Mailgun), collect the DNS values needed
so they can be added to Cloudflare DNS via Terraform.

Ask:

> Do you want to configure Mailgun DNS records in Cloudflare? (y/n)
> (Required for outbound email to work. You can skip and add records manually later.)

If **yes**, ask:

> Enter your Mailgun sender domain (e.g. `mg.example.com`):

Then:

> Paste your Mailgun DKIM TXT record value (from Mailgun → Sending → Domains → DNS Records,
> the value for the `mailo._domainkey.<sender-domain>` TXT record):

> Are you using EU Mailgun servers? (y/n) [default: n]
>
> (EU: `mxa.eu.mailgun.org`, `mxb.eu.mailgun.org`; US: `mxa.mailgun.org`, `mxb.mailgun.org`)

Set:
- `mailgun_dkim_value` = the DKIM value entered
- `mailgun_mx_servers` = `["mxa.eu.mailgun.org", "mxb.eu.mailgun.org"]` (EU) or
  `["mxa.mailgun.org", "mxb.mailgun.org"]` (US)

If **no**, skip this subsection. Tell the user:
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

If `terraform apply` fails with a message like "A similar configuration with rules already
exists and overwriting will have unintended consequences", existing Cloudflare rulesets must
be imported before applying. Run:

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

Otherwise, pause and tell the user:

> **Action required — Hetzner S3 credentials**
>
> 1. Go to [console.hetzner.cloud](https://console.hetzner.cloud)
> 2. Select your project → **Security** → **S3 credentials**
> 3. Click **Generate credentials**
> 4. **Copy both the Access Key and Secret Key immediately** — the secret is shown only once
>
> Paste the Access Key:

Read `access_key`. Then:

> Paste the Secret Key:

Read `secret_key`.

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
- `secrets.hetznerStorageAccessKey` ← read from `terraform/storage/terraform.tfvars`
- `secrets.hetznerStorageSecretKey` ← read from `terraform/storage/terraform.tfvars`
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

Tell the user which URL was chosen.

**Site name** — the human-readable name stored in the Django sites framework:
> Enter the site name (e.g. `My Photo Blog`):

Save this as `<site_name>` for use in Step 6c.

**Meta author, description, keywords** — prompt for each, allow empty to skip.

### Observability credentials

**If `secrets.sentryUrl` is empty**, ask:
> Paste your Sentry DSN URL (Sentry project → Settings → Client Keys → DSN), or press Enter to skip:

Set `secrets.sentryUrl` if provided.

**If `secrets.openTelemetryUrl` is empty**, ask:
> Paste your OTLP collector endpoint URL (e.g. `https://otel.yourdomain.com`), or press Enter to skip:

Set `secrets.openTelemetryUrl` if provided.

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
