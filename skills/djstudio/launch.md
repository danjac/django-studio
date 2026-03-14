Interactive first-deploy wizard. Guides the user through provisioning infrastructure,
configuring secrets, and deploying the application end-to-end.

**Idempotency rule:** Never overwrite a value that is already set. Read existing files
first. Only fill in what is missing or still `CHANGE_ME`. Re-running is safe — it resumes
where it left off.

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
  Save this as `<github_repo>` (e.g. `danjac/myapp`) for use in later steps.

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
> 5. Name: anything (e.g. `myapp-terraform`)
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
just terraform hetzner apply -auto-approve
```

Wait for apply to complete. If it fails, show the error and stop.

Then fetch the kubeconfig:
```bash
just get-kubeconfig
```

---

## Step 2 — Cloudflare DNS and SSL

**Check:** Read `terraform/cloudflare/terraform.tfvars` if it exists.

### 2a. Cloudflare API token

If `cloudflare_api_token` is missing or empty, pause and tell the user:

> **Action required — Cloudflare API token**
>
> 1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Profile** (top right) → **API Tokens**
> 2. Click **Create Token** → **Create Custom Token**
> 3. Name: anything (e.g. `myapp-terraform`)
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

### 2b. Domain

If `domain` is missing, empty, or `example.com`, ask the user to confirm or enter their domain.
Otherwise use the existing value.

### 2c. Server IP

Get automatically from Hetzner terraform output (already applied in Step 1):
```bash
just terraform-value hetzner server_public_ip
```
Set `server_ip`.

### 2d. Write terraform.tfvars and apply

Write `terraform/cloudflare/terraform.tfvars` with all collected values.

Then:
```bash
just terraform cloudflare init    # skip if terraform/cloudflare/.terraform/ already exists
just terraform cloudflare apply -auto-approve
```

Wait for apply to complete. If it fails, show the error and stop.

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
just terraform storage apply -auto-approve
```

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
- `app.allowedHosts` ← `.` + domain (e.g. `.myapp.com`)

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

**Admin URL** (default `admin/` — change for security):
> Enter a custom Django admin URL path (default: `admin/`):
> Tip: use something non-obvious like `secret-admin-42/` to reduce attack surface.

**Meta author, description, keywords** — prompt for each, allow empty to skip.

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

---

## Step 6 — First deploy

Tell the user:
> **Triggering first deploy via GitHub Actions...**
> This will build the Docker image, push it to ghcr.io, and deploy to the cluster.
> This typically takes 5–10 minutes.

```bash
just gh deploy
```

Then watch the run:
```bash
gh run watch
```

When the workflow completes successfully, read the actual deployed image tag from the
cluster and update `values.secret.yaml` so that `just helm site` works correctly for
future manual deploys:

```bash
just kube get deployment django-app -o jsonpath='{.spec.template.spec.containers[0].image}'
```

Update `image` in `values.secret.yaml` with this value, then re-push the secret:

```bash
just gh-set-secrets
```

Then show pod status:
```bash
just kube get pods
```

If all pods are Running, tell the user:

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
