Check that all deployment configuration is complete before the first production
deploy. Read each file listed below, scan for placeholder values, and report
results in two groups: **BLOCKING** (deploy will fail or be insecure) and
**ADVISORY** (worth reviewing, but won't necessarily break anything).

Placeholder patterns to flag: empty string `""`, `"CHANGE_ME"`, `"example.com"`,
`"grafana.example.com"`, literal `CHANGE_ME` inside cert/key PEM blocks.

---

### 1. `terraform/hetzner/terraform.tfvars`

If the file does not exist: BLOCKING — copy from `.example` and fill in values.

Check these keys:
| Key | BLOCKING if |
| --- | --- |
| `hcloud_token` | empty string |
| `ssh_public_key` | empty string |
| `k3s_token` | `"CHANGE_ME"` |

### 2. `terraform/cloudflare/terraform.tfvars`

If the file does not exist: BLOCKING.

| Key | BLOCKING if |
| --- | --- |
| `cloudflare_api_token` | empty string |
| `domain` | `"example.com"` or empty |
| `server_ip` | empty string — must be set after `terraform apply` in hetzner |

### 3. `helm/<project-slug>/values.secret.yaml`

If the file does not exist: BLOCKING — copy from `.example` and fill in values.

| Key | Severity | Condition |
| --- | --- | --- |
| `postgres.volumePath` | BLOCKING | `"CHANGE_ME"` — set from `terraform output -raw postgres_volume_mount_path` |
| `domain` | BLOCKING | `"CHANGE_ME"` |
| `image` | BLOCKING | contains `CHANGE_ME` |
| `app.admins` | BLOCKING | `"CHANGE_ME"` |
| `app.contactEmail` | BLOCKING | `"CHANGE_ME"` |
| `app.mailgunSenderDomain` | BLOCKING | `"CHANGE_ME"` |
| `secrets.postgresPassword` | BLOCKING | `"CHANGE_ME"` |
| `secrets.djangoSecretKey` | BLOCKING | `"CHANGE_ME"` |
| `secrets.cloudflare.cert` | BLOCKING | contains `CHANGE_ME` — run `terraform -chdir=terraform/cloudflare output -raw origin_cert_pem` |
| `secrets.cloudflare.key` | BLOCKING | contains `CHANGE_ME` — run `terraform -chdir=terraform/cloudflare output -raw origin_key_pem` |
| `app.adminUrl` | ADVISORY | still `"admin/"` — change for security |
| `app.metaAuthor` | ADVISORY | `"CHANGE_ME"` |
| `app.metaDescription` | ADVISORY | `"CHANGE_ME"` |

If `terraform/storage/main.tf` exists (i.e. the project was generated with `use_storage=y`),
also check:

**`terraform/storage/terraform.tfvars`**

If the file does not exist: BLOCKING — storage has not been provisioned yet.

If it exists, check:

| Key | BLOCKING if |
| --- | --- |
| `access_key` | empty string |
| `secret_key` | empty string |

Then check the Helm values — regardless of the current value of `useS3Storage`:

| Key | Severity | Condition |
| --- | --- | --- |
| `secrets.useS3Storage` | BLOCKING | `"false"` — object storage was included at project generation but has not been enabled |
| `secrets.hetznerStorageAccessKey` | BLOCKING | empty string |
| `secrets.hetznerStorageSecretKey` | BLOCKING | empty string |
| `secrets.hetznerStorageBucket` | ADVISORY | still the default value — confirm it matches the bucket provisioned by `terraform/storage` |
| `secrets.hetznerStorageEndpoint` | ADVISORY | still the default endpoint — confirm the region matches your Hetzner datacenter |

If any storage credential is missing or `useS3Storage` is still `"false"`, give
the user the following provisioning steps:

1. Create S3 credentials in the Hetzner console:
   Cloud Console → `<your project>` → Security → S3 credentials → Generate credentials
   (the secret key is only shown once — save it immediately)
2. Fill in the Terraform variables:
   ```
   cp terraform/storage/terraform.tfvars.example terraform/storage/terraform.tfvars
   $EDITOR terraform/storage/terraform.tfvars  # set access_key and secret_key
   ```
3. Provision the bucket:
   ```
   terraform -chdir=terraform/storage init
   terraform -chdir=terraform/storage apply
   ```
4. Copy the terraform outputs into `helm/site/values.secret.yaml`:
   - `secrets.hetznerStorageAccessKey` ← `access_key` from `terraform.tfvars`
   - `secrets.hetznerStorageSecretKey` ← `secret_key` from `terraform.tfvars`
   - `secrets.hetznerStorageBucket` ← `terraform -chdir=terraform/storage output -raw bucket_name`
   - `secrets.hetznerStorageEndpoint` ← `terraform -chdir=terraform/storage output -raw endpoint_url`
   - `secrets.useS3Storage` ← set to `"true"`
5. See `docs/File-Storage.md` for the full provisioning guide.

### 4. `helm/observability/values.secret.yaml` (if it exists)

| Key | Severity | Condition |
| --- | --- | --- |
| `kube-prometheus-stack.grafana.adminPassword` | BLOCKING | `"CHANGE_ME"` |
| grafana ingress host | BLOCKING | `"grafana.example.com"` |

### 5. GitHub Actions secrets

Run `gh secret list` and cross-reference against secrets referenced in
`.github/workflows/*.yml`. For each secret name found in workflows, flag as
BLOCKING if it is absent from `gh secret list` output.

### 6. Kubeconfig

Check whether `~/.kube/<project-slug>.yaml` exists. If not: ADVISORY —
run `just get-kubeconfig` after Hetzner provisioning.

### 7. Docker image

The Docker image is stored in GitHub Container Registry (ghcr.io) and is built
by GitHub Actions — it is never built locally.

Check whether a Docker image has ever been built by running:

```bash
gh run list --workflow=build.yml --limit=5
gh run list --workflow=deploy.yml --limit=5
```

| Condition | Severity |
| --- | --- |
| No successful `build.yml` or `deploy.yml` run found | BLOCKING — no image exists in the registry yet |

If BLOCKING: instruct the user to build the image first:

```bash
just gh build
```

This triggers the `build.yml` workflow (runs checks + builds and pushes the
image to ghcr.io). Monitor progress with `gh run watch`.

**Note:** `just gh deploy` also builds the image as part of the same
run, so it is safe to go straight to deploy if all other BLOCKING items are
resolved. `just helm` (direct Helm upgrade) does **not** build — only use it
when an image already exists in the registry.

---

### Report format

Print a summary like:

```
BLOCKING (must fix before deploy):
  [terraform/hetzner] hcloud_token is empty
  [helm/values.secret.yaml] secrets.djangoSecretKey is CHANGE_ME
  ...

ADVISORY (review before go-live):
  [helm/values.secret.yaml] app.adminUrl is still "admin/" — change for security
  ...

OK:
  terraform/hetzner/terraform.tfvars — all required values set
  ...
```

If there are no BLOCKING items, confirm the project looks ready to deploy and
suggest running `just gh deploy` to proceed (this builds the image and
deploys in a single workflow run).
