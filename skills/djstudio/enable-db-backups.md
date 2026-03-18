Interactive wizard to enable automated daily PostgreSQL backups to a private Hetzner
Object Storage bucket.

**Idempotency rule:** Read existing config files before writing. Skip steps where values
are already set. Re-running is safe.

---

## Pre-flight checks

Verify the cluster is accessible and Terraform is installed:

```bash
just kube get pods    # cluster must be reachable
terraform version     # Terraform must be installed
```

If either fails, stop and tell the user what to fix.

Check that `terraform/backups/` exists in the project. If it does not, stop and tell
the user this project does not have the backup infrastructure — they may need to run
`/djstudio sync` to pull the latest template changes.

---

## Step 1 — Provision the backup bucket

**Check:** Read `terraform/backups/terraform.tfvars` if it exists.

If `access_key` and `secret_key` are already set to non-empty values, skip to Step 2.

Otherwise, tell the user:

> **Action required — S3 credentials for the backup bucket**
>
> The backup bucket uses the same Hetzner S3 credentials as the media storage bucket.
>
> If you already ran `terraform/storage/`, reuse the same credentials:
> - Open `terraform/storage/terraform.tfvars` and copy `access_key` and `secret_key`.
>
> If you have not set up object storage yet, generate credentials now:
> 1. Go to [console.hetzner.cloud](https://console.hetzner.cloud)
> 2. Select your project → **Security** → **S3 credentials**
> 3. Click **Generate credentials**
> 4. **Copy both the Access Key and Secret Key immediately** — the secret is shown only once
>
> Paste the Access Key:

Read `access_key`. Then:

> Paste the Secret Key:

Read `secret_key`.

If `location` is not set, try to read it from `terraform/hetzner/terraform.tfvars`. If
found, use it and tell the user. If not found, ask:

> Which Hetzner datacenter location? (default: `fsn1`)

Set `location`.

Write `terraform/backups/terraform.tfvars` with all collected values. Preserve any
existing values that were already set.

Then apply:

```bash
just terraform backups init    # skip if terraform/backups/.terraform/ already exists
just terraform backups apply -auto-approve
```

Wait for apply to complete. If it fails, show the error and stop.

---

## Step 2 — Configure Helm secrets

**Check:** Read `helm/site/values.secret.yaml`. Skip any value already set to non-empty,
non-`CHANGE_ME`.

Fetch bucket outputs from Terraform:

```bash
just terraform-value backups bucket_name
just terraform-value backups endpoint_url
```

Set in `helm/site/values.secret.yaml`:

```yaml
backup:
  enabled: true

secrets:
  backupAccessKey: "<access_key from terraform/backups/terraform.tfvars>"
  backupSecretKey: "<secret_key from terraform/backups/terraform.tfvars>"
  backupBucket: "<output: bucket_name>"
  backupEndpoint: "<output: endpoint_url>"
  backupRegion: "<location from terraform/backups/terraform.tfvars>"
```

Preserve all other existing values.

---

## Step 3 — Deploy

```bash
just helm site
```

Wait for the command to complete. If it fails, show the error and help the user diagnose.

Verify the CronJob and secret were created:

```bash
just kube get cronjob postgres-backup
just kube get secret backup-secret
```

---

## Step 4 — Run a test backup

Tell the user:

> **Testing the first backup now...**

```bash
just kube create job postgres-backup-test --from=cronjob/postgres-backup
```

Wait for the job to complete (poll every 5 seconds, timeout after 3 minutes):

```bash
just kube wait --for=condition=complete job/postgres-backup-test --timeout=180s
```

If it times out or fails, show the logs from both containers:

```bash
just kube logs job/postgres-backup-test -c dump
just kube logs job/postgres-backup-test -c upload
```

Diagnose the failure and help the user fix it before declaring success.

If the job succeeds, show the upload logs and then clean up:

```bash
just kube logs job/postgres-backup-test -c upload
just kube delete job postgres-backup-test
```

---

## Step 5 — Push updated secrets to GitHub

The `values.secret.yaml` has changed. Push the updated secrets so the CI deploy workflow
uses the new values:

```bash
just gh-set-secrets
```

---

## Completion

Tell the user:

> **Backups enabled!**
>
> PostgreSQL will be backed up daily at 03:00 UTC to:
> `s3://<bucket_name>/backup-YYYYMMDD-HHMMSS.sql.gz`
>
> Retention: the 7 most recent backups are kept; older ones are pruned automatically.
>
> To restore from a backup, follow `docs/Backups.md` — it has step-by-step instructions
> including a "3 AM emergency" restore guide.
>
> To adjust the schedule or retention, edit the `backup:` section in
> `helm/site/values.yaml` and run `just helm site`.

---

## Help

**djstudio enable-db-backups**

Interactive wizard to enable automated daily PostgreSQL backups to a private
Hetzner Object Storage bucket. Provisions the backup bucket via Terraform,
configures Helm secrets, deploys the backup CronJob, and runs a test backup
to confirm everything works.

Backups run daily at 03:00 UTC. The 7 most recent dumps are retained.
Restore instructions are in `docs/Backups.md`.

Requires: `terraform`, `just`, and `kubectl` installed and authenticated.

Example:
  /djstudio enable-db-backups
