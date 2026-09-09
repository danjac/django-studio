---
description: Interactive first-deploy wizard: provisions infra, configures secrets, deploys
---

Interactive first-deploy wizard. Guides the user through provisioning infrastructure,
configuring secrets, and deploying the application end-to-end.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/infrastructure.md`
- `docs/deployment.md`

---

**Idempotency rule:** Never overwrite a value that is already set. Read existing files
first. Only fill in what is missing or still `CHANGE_ME`. Re-running is safe — it resumes
where it left off.

**Terraform rule:** Never use `cd terraform/<dir>` — it changes the working directory
for subsequent commands. Always use `terraform -chdir=terraform/<dir>` or the
`just terraform <dir>` wrapper instead.

**Secret handling rules:**
- All deployment secrets are stored directly in tfvars and helm values files (gitignored).
- Never echo, print, or repeat a secret value in the terminal or chat.
- Check presence only — report missing values by field name, not by value.
- When a secret field is empty or `CHANGE_ME`, stop and tell the user exactly which file
  and field to fill in. Wait for them to confirm, then re-read the file.
- Never ask the user to paste a secret into this chat.

---

## Step 0 — Deployment secrets overview (first run only)

If `terraform/hetzner/terraform.tfvars` does not yet exist, tell the user:

> **Before we begin:** You will need the following values during this process.
> Look them up now and have them ready — you will be asked to paste them into
> config files as we go. **Do not paste secrets into this chat.**
>
> **Required:**
> - **Hetzner Cloud API token** — console.hetzner.cloud → Security → API Tokens → Generate (Read & Write)
> - **Cloudflare API token** — dash.cloudflare.com → Profile → API Tokens (Zone permissions)
>
> **Optional:**
> - Mailgun API key — mailgun.com → Sending → Domains → API Keys (for outbound email)
> - Mailgun DKIM value (for DNS-based email verification via Cloudflare)
> - Hetzner object storage credentials (for file/media storage)
> - Sentry DSN (for error tracking — from your Sentry project settings)
>
> Say **ready** when you have them.

---

## Topology

Before provisioning infrastructure, ask the user:

> How do you want to start?
>
> **1. Single node** (recommended) — one cx33 running the app, worker,
>    PostgreSQL and Redis. ~€15/month. You can split roles onto dedicated
>    nodes later without touching the Helm chart.
> **2. Split** — dedicated nodes for database, jobrunner, and webapps.
>    ~€35/month.
>
> (1/2, default: 1)

If the user presses Enter or chooses **1**, set:

```
<create_database>  = false
<create_jobrunner> = false
<webapp_count>     = 0
<replicas>         = 1
```

If the user chooses **2**, ask how many webapp nodes they want (default 2), then set:

```
<create_database>  = true
<create_jobrunner> = true
<webapp_count>     = <their answer>
<replicas>         = <their answer>
```

These values are written to `terraform/hetzner/terraform.tfvars`, except `<replicas>`,
which goes in `helm/site/values.yaml`.

Tell the user:
> Starting single-node. See `docs/infrastructure.md` for the scaling path, or run
> `/dj-scale` when you need more capacity.

(Only say this if they chose option 1.)

---

## Monitor VM (observability)

Ask the user:

> Do you want to provision a **monitor VM** for the observability stack
> (Grafana + Prometheus + Loki)? This adds one extra Hetzner node.
> You can skip this now and run `/dj-deploy-observe` later to add it. (y/n)

Save the answer as `<create_monitor>` (`true` or `false`).

This value is written to `terraform/hetzner/terraform.tfvars` as `create_monitor`.

If **n**: tell the user:
> Monitor VM skipped. Run `/dj-deploy-observe` at any time to provision
> it and deploy the observability stack.

---

## Tailscale (private networking)

Ask the user:

> Do you want to put the cluster on a **Tailscale** tailnet? SSH and the
> Kubernetes API then travel over WireGuard instead of the public internet,
> and ports 22 and 6443 can be closed to everyone else. Requires a Tailscale
> account. (y/n)

If **y**: tell the user to run `/dj-tailscale enable` **after** this wizard
finishes, and continue. Enabling it now would mean collecting Tailscale
credentials before the cluster exists, and the firewall must not be locked down
until `kubectl` has been verified over the tailnet — `/dj-tailscale` sequences
that correctly.

If **n**: continue. SSH and the Kubernetes API stay reachable over the public
internet, protected by SSH keys and the K3s token. Mention that
`/dj-tailscale enable` can retrofit a running cluster later.

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

### Image mismatch check

Read the `postgres` and `redis` image values from both files:

```bash
# docker-compose.yml
dc_postgres=$(grep -A10 '^\s*postgres:' docker-compose.yml | grep 'image:' | head -1 | awk '{print $2}')
dc_redis=$(grep -A10 '^\s*redis:' docker-compose.yml | grep 'image:' | head -1 | awk '{print $2}')

# helm/site/values.yaml
helm_postgres=$(grep -A5 '^\s*postgres:' helm/site/values.yaml | grep 'image:' | head -1 | awk '{print $2}')
helm_redis=$(grep -A5 '^\s*redis:' helm/site/values.yaml | grep 'image:' | head -1 | awk '{print $2}')
```

If `dc_postgres != helm_postgres` or `dc_redis != helm_redis`, warn the user:

> **Image mismatch detected:**
>
> | Service  | docker-compose.yml | helm/site/values.yaml |
> |----------|--------------------|-----------------------|
> | postgres | `<dc_postgres>`    | `<helm_postgres>`     |
> | redis    | `<dc_redis>`       | `<helm_redis>`        |
>
> Production will run a different image than local dev. This can cause migration
> failures or runtime errors. Update `helm/site/values.yaml` to match
> `docker-compose.yml` (or vice versa), then say **continue**.

Wait for the user to confirm, then re-read `helm/site/values.yaml` and verify the values match before proceeding.

If both images match, continue silently.

Print a summary of what will be set up and ask the user to confirm before proceeding.

---

## Step 1 — Hetzner infrastructure

**Check:** Read `terraform/hetzner/terraform.tfvars` if it exists.

For each variable below, skip it if already set to a non-empty, non-`CHANGE_ME` value.

### 1a. Hetzner API token

Read `hcloud_token` from `terraform/hetzner/terraform.tfvars`.

If it is empty or `CHANGE_ME`:

> **Action required:** Open `terraform/hetzner/terraform.tfvars` and fill in `hcloud_token`
> with your Hetzner Cloud API token (Read & Write), then say **continue**.

Wait for the user to confirm, then re-read the file. Do not proceed until the value is set.

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

### 1e. Topology

Set `create_database`, `create_jobrunner` and `webapp_count` to the values collected
earlier. These determine which roles get dedicated Hetzner nodes; anything left `false`
or `0` runs on the server node.

### 1f. Write terraform.tfvars and apply

Write `terraform/hetzner/terraform.tfvars` with all collected values (including
`create_database`, `create_jobrunner`, `webapp_count` and `create_monitor`), preserving
any existing values that were already set.

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
"hcloud_token appears to be invalid. Update it in `terraform/hetzner/terraform.tfvars` and re-run."
Do not repeat the token value.

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

**Verify** the cluster is reachable before continuing:
```bash
just --yes rkube get nodes
```

If this fails, stop and tell the user:
> Cluster is not reachable. Check that the server is up and `just get-kubeconfig` succeeded,
> then re-run `/dj-deploy`.

---

## Step 2 — Cloudflare DNS and SSL

**Check:** Read `terraform/cloudflare/terraform.tfvars` if it exists. If it does not
exist, copy it from the example:

```bash
cp terraform/cloudflare/terraform.tfvars.example terraform/cloudflare/terraform.tfvars
```

### 2a. Confirm domain is Active in Cloudflare

Before proceeding, tell the user:

> **Before continuing:** Make sure your domain has been added to your Cloudflare account
> and its nameservers are pointing to Cloudflare (status: **Active**).
>
> Is `<domain>` showing as Active in your Cloudflare dashboard? (y/n)

If the user answers **n**, stop and tell them to:
1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → Add a Site → enter the domain
2. Update the domain's nameservers at their registrar to point to Cloudflare
3. Wait for the domain to show as **Active**, then re-run `/dj-deploy`

Only continue when the user confirms the domain is Active.

### 2b. Cloudflare API token

Read `cloudflare_api_token` from `terraform/cloudflare/terraform.tfvars`.

If it is empty or `CHANGE_ME`:

> **Action required:** Open `terraform/cloudflare/terraform.tfvars` and fill in `cloudflare_api_token`
> with your Cloudflare API token (Zone permissions), then say **continue**.

Wait for the user to confirm, then re-read the file. Do not proceed until the value is set.

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

Ask the user:

> Do you want to configure Mailgun DNS records in Cloudflare (for outbound email)? (y/n)

If **yes**:

Ask:
> Enter your full Mailgun sender domain (e.g. `mg.example.com`):

Save the full sender domain (e.g. `mg.example.com`) for use in Step 4
(`app.mailgunSenderDomain` in `values.yaml`).

Extract the subdomain prefix (everything before the first `.`) and set
`mailgun_subdomain` in `terraform/cloudflare/terraform.tfvars`. For example,
`mg.example.com` → `mailgun_subdomain = "mg"`. The Cloudflare zone handles
the base domain, so only the prefix is needed in tfvars.

Ask:
> Enter your Mailgun DKIM value (from Mailgun → Sending → Domains → DNS Records →
> `mailo._domainkey` TXT value). Open `terraform/cloudflare/terraform.tfvars` and
> fill in `mailgun_dkim_value`, then say **continue**.

Wait for the user to confirm, then re-read the file.

Ask:
> Are you using EU Mailgun servers? (Y/n) [default: yes]

Set:
- `mailgun_mx_servers` ← `["mxa.eu.mailgun.org", "mxb.eu.mailgun.org"]` if yes (default),
  otherwise `["mxa.mailgun.org", "mxb.mailgun.org"]`

If user answers **no**, skip. Tell the user:
> Mailgun DNS records will not be added automatically. Add them manually in Cloudflare DNS
> after deploy if you want outbound email to work.

### 2f. Write terraform.tfvars and apply

Write `terraform/cloudflare/terraform.tfvars` with all collected values, including
`mailgun_subdomain`, `mailgun_dkim_value`, and `mailgun_mx_servers` if collected in 2e.

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
"cloudflare_api_token appears to be invalid. Update it in `terraform/cloudflare/terraform.tfvars` and re-run."

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
# http_request_firewall_custom → cloudflare_ruleset.zone_level_firewall
terraform -chdir=terraform/cloudflare import cloudflare_ruleset.zone_level_firewall zone/<zone_id>/<ruleset_id>

# http_response_headers_transform → cloudflare_ruleset.transform_response_headers
terraform -chdir=terraform/cloudflare import cloudflare_ruleset.transform_response_headers zone/<zone_id>/<ruleset_id>
```

Then re-run `just terraform cloudflare apply`.

Wait for apply to complete. If it fails for a different reason, show the error and stop.

---

## Step 3 — Object Storage (optional — skip if user does not want file/media storage)

**Check:** Read `terraform/storage/terraform.tfvars` if it exists. If it does not
exist, copy it from the example:

```bash
cp terraform/storage/terraform.tfvars.example terraform/storage/terraform.tfvars
```

Set `location` to match the Hetzner cluster location chosen in step 1. Confirm with
the user:

> Storage location set to `<location>` to match your cluster — OK?

If the user wants a different location, let them override it.

If `access_key` and `secret_key` are already set, skip this step entirely.

Read `access_key` and `secret_key` from `terraform/storage/terraform.tfvars`.

If either is empty or `CHANGE_ME`:

> **Action required:** Open `terraform/storage/terraform.tfvars` and fill in `access_key`
> and `secret_key` with your Hetzner S3 credentials (Hetzner → Security → S3 credentials
> → Generate credentials). **Note:** the secret key is shown only once when generated.
> Say **continue** when done.

Wait for the user to confirm, then re-read the file. Do not proceed until both are set.

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

## Step 4 — Helm values

There are two files, and it matters which value goes where:

| File | Tracked by git? | Holds |
| ---- | --------------- | ----- |
| `helm/site/values.yaml` | **yes — commit your changes** | all non-secret config |
| `helm/site/values.secret.yaml` | no, gitignored | secrets only (`secrets.*`) |

**Check:** If `helm/site/values.secret.yaml` does not exist, copy it from the example:
```bash
cp helm/site/values.secret.yaml.example helm/site/values.secret.yaml
```

`values.yaml` already ships with defaults filled in from the answers given when the
project was generated. Read both files. For each value below, skip if already set to a
non-empty, non-`CHANGE_ME` value.

### Auto-generated secrets

→ `values.secret.yaml`

Generate each with `openssl rand -hex 32` if not already set:
- `secrets.postgresPassword`
- `secrets.djangoSecretKey`
- `secrets.redisPassword`

Write each value with an individual comment immediately above it:

```yaml
secrets:
  # auto-generated — rotate with: /dj-rotate-secrets
  postgresPassword: "<generated>"
  # auto-generated — rotate with: /dj-rotate-secrets
  djangoSecretKey: "<generated>"
  # auto-generated — rotate with: /dj-rotate-secrets
  redisPassword: "<generated>"
```

Tell the user these have been generated automatically.

### Webapp replicas

→ `values.yaml`

Set `replicas` to `<replicas>` (collected at the start of the wizard).

Single-node topology uses `1`. In a split topology this must match `webapp_count` in
`terraform/hetzner/terraform.tfvars` so each replica has a dedicated node.

### Values from Terraform outputs

Fetch automatically — never prompt for these:

→ `values.yaml`
- `postgres.volumePath` ← `just terraform-value hetzner postgres_volume_mount_path`

→ `values.secret.yaml`
- `secrets.cloudflare.cert` ← `just terraform-value cloudflare origin_cert_pem`
- `secrets.cloudflare.key` ← `just terraform-value cloudflare origin_key_pem`

**Verify the origin certificate signature** after writing it to `values.secret.yaml`.
A single corrupted base64 character will cause Cloudflare 526 errors that are nearly
impossible to diagnose (all metadata checks pass, only crypto verification fails):

```bash
curl -s https://developers.cloudflare.com/ssl/static/origin_ca_rsa_root.pem -o /tmp/cf_root.pem
terraform -chdir=terraform/cloudflare output -raw origin_cert_pem > /tmp/origin_cert.pem
openssl verify -CAfile /tmp/cf_root.pem /tmp/origin_cert.pem
```

The output must be `/tmp/origin_cert.pem: OK`. If verification fails, re-read the cert
from terraform output and write it again — do not proceed until it verifies.

If `terraform/storage/` exists:
- `secrets.objectStorageBucket` ← `just terraform-value storage bucket_name`
- `secrets.objectStorageEndpoint` ← `just terraform-value storage endpoint_url`
- `secrets.objectStorageAccessKey` ← read from `terraform/storage/terraform.tfvars` (do not print)
- `secrets.objectStorageSecretKey` ← read from `terraform/storage/terraform.tfvars` (do not print)
- `secrets.useS3Storage` ← set to `"true"`

### Domain values

→ `values.yaml`

These are pre-filled from the `domain` given at project generation. Only change them if
the domain confirmed in Step 2 differs:

- `domain` ← the domain confirmed in Step 2
- `app.allowedHosts` ← `.` + domain (e.g. `.my_domain.com`)

### Image

→ `values.yaml`

Replace the `CHANGE_ME` owner placeholder. `just gh deploy` overrides this with the
actual SHA tag via `--set image=...`, so the value here only affects a manual
`just helm site`:
- `image` ← `ghcr.io/<github_repo>:main`

### Values already defaulted from the project answers

→ `values.yaml`

`app.admins`, `app.contactEmail`, `app.metaAuthor`, `app.metaDescription` and
`app.mailgunSenderDomain` are pre-filled from the author, email, description and domain
given when the project was generated. Show the current values and ask:

> These are set in `helm/site/values.yaml`:
> - admins: `<value>`
> - contact email: `<value>`
> - meta author: `<value>`
> - meta description: `<value>`
> - mailgun sender domain: `<value>`
>
> Change any of them? (y/n)

If **n**, continue. If **y**, ask which and update only those.

If the user provided a different Mailgun sender domain in Step 2e, set
`app.mailgunSenderDomain` to that value (e.g. `mg.example.com`).

### Values requiring user input

For each, only prompt if currently `CHANGE_ME` or empty:

**Admin URL** (→ `values.yaml`) — generate a random human-readable slug if the user skips:

```bash
slug=$(.agents/skills/scripts/random-slug.py)
default_admin_url="${slug}/"
```

Then prompt:
> Enter a custom Django admin URL path (or type **skip** for `<generated-slug>/`):

- If the user types **skip** (or empty input), use the generated slug (e.g. `calm-peak/`).
- If the user types a value, use that value.
- Only fall back to `admin/` if the user explicitly types `admin/`.

Tell the user which URL was chosen — they will need this to access Django admin.

**Site name** — the human-readable name stored in the Django sites framework:
> Enter the site name (e.g. `My Photo Blog`):

Save this as `<site_name>` for use in Step 6c.

**Meta keywords** (→ `values.yaml`) — comma-separated; the user can type **skip** to
leave empty. Author and description are already defaulted above.

### Sentry DSN

Read `secrets.sentryUrl` from `values.secret.yaml`.
If empty and the user wants error tracking:

> **Action required:** Open `helm/site/values.secret.yaml` and fill in
> `secrets.sentryUrl` with your Sentry DSN, then say **continue**.

If the user skips, leave it empty. The OTLP endpoint (`secrets.openTelemetryUrl`)
is configured later by `/dj-deploy-observe` — do not prompt for it here.

### Mailgun API key

Read `secrets.mailgunApiKey` from `values.secret.yaml`.
If it is empty and the user wants email:

> **Action required:** Open `helm/site/values.secret.yaml` and fill in
> `secrets.mailgunApiKey` with your Mailgun API key, then say **continue**.

If the user skips, leave it empty — outbound email will not work until this is set.

### Write the files

Write each value to the file marked above it, preserving any values that were already
set and were not listed as needing update.

`values.yaml` is tracked by git. Tell the user to review and commit it:

```bash
git diff helm/site/values.yaml
```

Never write a `secrets.*` value to `values.yaml`, and never write config to
`values.secret.yaml` — the split is what keeps the tracked file safe to commit.

---

## Step 5 — GitHub Actions secrets

```bash
just gh-set-secrets
```

This pushes `KUBECONFIG_BASE64` and `HELM_VALUES_SECRET` to the GitHub repository secrets.
Tell the user what was pushed and confirm with `gh secret list`.

> **After the initial deploy:**
> - Changed a **config** value in `helm/site/values.yaml` (admin email, meta tags,
>   replicas)? Commit it, then run `just helm site`.
> - Changed a **secret** in `helm/site/values.secret.yaml`? Run `just deploy-config`
>   instead of `just gh-set-secrets` and `just helm site` separately. It pushes the
>   secrets to GitHub **and** applies the updated chart in one step, keeping CI and the
>   running cluster in sync.

---

## Step 6 — First deploy

The first deploy requires three steps in sequence. `just gh deploy` alone only updates
app/worker containers — it does not deploy Postgres, Redis, Secrets, or other resources
for the first time. Follow the full sequence below.

### 6a. Build and push the Docker image

**Pre-check: gh token scope**

```bash
gh auth status 2>&1 | grep -q 'write:packages'
```

If `write:packages` is missing, stop and tell the user:

> Your gh token is missing the `write:packages` scope. Fix it by running:
>
>     gh auth refresh -h github.com -s write:packages
>
> This opens a browser to re-authorize. Say **continue** when done.

Wait for the user to confirm, then re-check.

**Pre-check: stale ghcr.io package**

```bash
gh api "user/packages/container/<repo>" 2>/dev/null
```

If the package exists but `just gh build` fails with `permission_denied: write_package`,
a previous failed build may have created a ghcr.io package with no repository linked.
Tell the user:

> A stale ghcr.io package exists from a previous failed build.
> Go to: https://github.com/users/<owner>/packages/container/<repo>/settings
> Under "Actions repository access", click "Add Repository" and add `<owner>/<repo>`
> with Write role. Say **continue** when done.

**Build:**

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

**Verify** core pods are Running before continuing:
```bash
just --yes rkube get pods
```

Check that `postgres-0`, `redis-*`, and ingress pods are Running. If any are not, stop and diagnose:
```bash
just --yes rkube describe pod <failing-pod>
just --yes rkube logs <failing-pod>
```

Do not proceed to Step 6c until postgres and redis are Running — the app deploy will fail
if the database or cache is not ready.

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
just --yes rkube get pods
```

If all pods are Running:

### django-tenants initialisation (if applicable)

Check whether django-tenants is installed:

```bash
grep -q 'django-tenants' pyproject.toml && echo "tenants" || echo "no-tenants"
```

If django-tenants is present, the public tenant and domain record must be created now or
the app pods will stay in a 404/crash loop. Get the package name from `.copier-answers.yml`:

```bash
package_name=$(grep '^package_name:' .copier-answers.yml | awk '{print $2}')
```

Then seed the public tenant via the worker pod (which is healthy even when app pods are crashing):

```bash
just --yes rkube exec deployment/django-worker -- python manage.py shell -c "
from ${package_name}.tenants.models import Tenant, Domain
t, _ = Tenant.objects.get_or_create(schema_name='public', defaults={'name': 'Public'})
Domain.objects.get_or_create(domain='<domain>', defaults={'tenant': t, 'is_primary': True})
"
```

Tell the user: "Public tenant and domain record created — app pods should now become healthy."

Verify the app pods recover:

```bash
just --yes rkube get pods
```

If any app pods are still not Running after the tenant is created, diagnose with logs before continuing.

If django-tenants is not present, skip this section.

### Set default site

If `<site_name>` was provided in Step 4, run:
```bash
just --yes rdj set_default_site <domain> "<site_name>"
```

If it was not provided, tell the user:
> You can set the default site name at any time by running:
> `just --yes rdj set_default_site <domain> "Your Site Name"`

Then tell the user:

> **Launch complete!**
> Your app is live at https://<domain>
>
> Next steps:
> - Run `just --yes rdj createsuperuser` to create an admin account
> - Visit https://<domain>/<admin-url> to access the Django admin

If any pods are not Running, show the pod status and relevant logs:
```bash
just --yes rkube describe pod <failing-pod>
just --yes rkube logs <failing-pod>
```
Diagnose and help the user fix the issue before declaring success.

---

## Step 7 — Post-launch (optional)

Tell the user:

> **Next steps (optional):**
> - Run `/dj-scale [n]` to view or change the webapp replica count
> - Run `/dj-enable-db-backups` to set up automated daily PostgreSQL backups
> - Run `/dj-rotate-secrets` to rotate auto-generated secrets when ready

If `<create_monitor>` is `true`, also include:

> - Run `/dj-deploy-observe` to deploy Grafana + Prometheus + Loki

If `<create_monitor>` is `false`, also include:

> - Run `/dj-deploy-observe` to provision the monitor VM and deploy Grafana + Prometheus + Loki

---

## User-facing outputs

The following values are printed to the user during the wizard — they are either
non-secret or required for the user to take action:

| Value | Step | Why the user needs it |
|-------|------|----------------------|
| Webapp replica count | Pre-flight | Confirms node and replica count |
| Server IP address | 1f | SSH access, DNS verification |
| Domain (confirmed) | 2c | Sanity check |
| Admin URL path | 4 | Needed to bookmark Django admin |
| Site URL (`https://<domain>`) | 6c | Confirm app is live |
| Pod status | 6c | Diagnose deploy issues |
| Next-step commands | 6c | `migrate`, `createsuperuser` |
