# Database Backups

Automated daily backups of the PostgreSQL database to a private Hetzner Object Storage
bucket. Backups are application-consistent `pg_dump` exports — safe to restore from at
any time without risk of data corruption.

Backups are **optional** and disabled by default. Follow this guide to set them up when
you are ready.

## Overview

| What | Detail |
|------|--------|
| Method | `pg_dump` piped through `gzip` |
| Format | Plain SQL (`.sql.gz`) — human-readable, portable |
| Schedule | Daily at 03:00 UTC (configurable) |
| Retention | 7 most recent backups (configurable) |
| Storage | Private Hetzner Object Storage bucket (`<project>-db-backups`) |
| Credentials | Separate Kubernetes secret (`backup-secret`) — not exposed to the app |

## How It Works

A Kubernetes CronJob runs daily at 03:00 UTC. It uses two containers that share an
in-memory volume:

1. **`dump` (initContainer)** — runs `pg_dump` using the same PostgreSQL image as the
   running database, pipes the output through `gzip`, and writes it to a shared volume.
   Filename format: `backup-YYYYMMDD-HHMMSS.sql.gz`.

2. **`upload` (main container)** — uses `amazon/aws-cli` to upload the dump file to the
   private Object Storage bucket, then prunes old backups beyond the configured retention
   count.

The backup credentials are stored in a dedicated `backup-secret` Kubernetes secret and
are never mounted into the app or worker pods.

## Setting Up Backups

### Step 1 — Provision the backup bucket

```bash
cd terraform/backups
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars
```

Fill in:
- `access_key` and `secret_key` — your Hetzner S3 credentials
  (Cloud Console → Security → S3 credentials; the same credentials used for
  `terraform/storage/` work here)
- `location` — must match your cluster location (default: `fsn1`)

Then apply:

```bash
just terraform backups init
just terraform backups apply
```

Note the outputs — you will need them in Step 2:

```bash
just terraform-value backups bucket_name    # e.g. my_project-db-backups
just terraform-value backups endpoint_url   # e.g. https://fsn1.your-objectstorage.com
```

### Step 2 — Configure Helm

Edit `helm/site/values.secret.yaml` and add:

```yaml
backup:
  enabled: true

secrets:
  backupAccessKey: "<access_key from terraform.tfvars>"
  backupSecretKey: "<secret_key from terraform.tfvars>"
  backupBucket: "<output: bucket_name>"
  backupEndpoint: "<output: endpoint_url>"
  backupRegion: "fsn1"   # match your location
```

### Step 3 — Deploy

```bash
just helm site
```

Verify the CronJob was created:

```bash
just kube get cronjob postgres-backup
```

### Step 4 — Trigger a test backup

Run a manual job to confirm the first backup works before relying on the schedule:

```bash
just kube create job postgres-backup-test --from=cronjob/postgres-backup
```

Watch the logs:

```bash
just kube logs -f job/postgres-backup-test -c dump
just kube logs -f job/postgres-backup-test -c upload
```

You should see the dump size and "Upload complete". Then verify the file appeared in
the bucket by following the "List available backups" steps in the Restore section below.

Clean up the test job:

```bash
just kube delete job postgres-backup-test
```

## Configuration

In `helm/site/values.yaml` (or override in `values.secret.yaml`):

```yaml
backup:
  enabled: false           # set to true to activate
  schedule: "0 3 * * *"   # daily at 03:00 UTC
  retention: 7             # keep this many backups; older ones are deleted automatically
  awsCliImage: "amazon/aws-cli:2"
```

## Restoring a Backup

> **3 AM emergency?** You need only `kubectl` and cluster access. Start at Step 1.
> The restore runs entirely in-cluster — no local `aws` CLI or `psql` required.

### What you need before starting

- Cluster access (`KUBECONFIG` configured — test with `just kube get pods`)
- The backup filename you want to restore (Step 1 shows how to find it)

### Step 1 — List available backups

Run a one-off pod using the `backup-secret` credentials already in your cluster:

```bash
just kube run --rm -it list-backups \
  --image=amazon/aws-cli:2 \
  --restart=Never \
  --env="AWS_ACCESS_KEY_ID=$(just kube get secret backup-secret -o jsonpath='{.data.BACKUP_ACCESS_KEY}' | base64 -d)" \
  --env="AWS_SECRET_ACCESS_KEY=$(just kube get secret backup-secret -o jsonpath='{.data.BACKUP_SECRET_KEY}' | base64 -d)" \
  --env="AWS_DEFAULT_REGION=$(just kube get secret backup-secret -o jsonpath='{.data.BACKUP_REGION}' | base64 -d)" \
  --env="BACKUP_ENDPOINT=$(just kube get secret backup-secret -o jsonpath='{.data.BACKUP_ENDPOINT}' | base64 -d)" \
  --env="BACKUP_BUCKET=$(just kube get secret backup-secret -o jsonpath='{.data.BACKUP_BUCKET}' | base64 -d)" \
  -- sh -c 'aws --endpoint-url "$BACKUP_ENDPOINT" s3 ls s3://$BACKUP_BUCKET/ | sort'
```

Output looks like this (newest last):

```
2024-01-01 03:00:05    1453291 backup-20240101-030000.sql.gz
2024-01-02 03:00:04    1461873 backup-20240102-030000.sql.gz
2024-01-03 03:00:03    1459204 backup-20240103-030000.sql.gz
```

Pick the filename you want to restore. In most cases this is the most recent one (last line).

### Step 2 — Run the restore

```bash
just rdb-restore backup-20240103-030000.sql.gz
```

Confirm the prompt. The script will:

1. Scale down `django-app` and `django-worker` (stops writes to the database)
2. Start a temporary in-cluster pod that downloads the backup from Object Storage
3. Drop and restore the `postgres` database inside the pod
4. Delete the pod
5. Scale `django-app` and `django-worker` back up

You will see progress logs for each phase streamed to your terminal. The whole
process takes 2–10 minutes depending on database size.

### Step 3 — Run migrations and confirm the site is live

```bash
just rdj migrate
```

Open the site in a browser. If the home page loads and you can log in, you are done.

---

### Manual restore (fallback)

If `just rdb-restore` fails or the backup CronJob is not set up, you can restore
manually. You will need `kubectl`, `aws` CLI, and `psql` installed locally.

**Step A — Set credentials**

Open `helm/site/values.secret.yaml` and copy the backup and postgres values:

```bash
export AWS_ACCESS_KEY_ID="<backupAccessKey>"
export AWS_SECRET_ACCESS_KEY="<backupSecretKey>"
export AWS_DEFAULT_REGION="fsn1"
export BACKUP_ENDPOINT="https://fsn1.your-objectstorage.com"
export BACKUP_BUCKET="my_project-db-backups"
export PGPASSWORD="<postgresPassword>"
```

**Step B — Download and decompress**

```bash
BACKUP_FILE="backup-20240103-030000.sql.gz"
aws --endpoint-url "$BACKUP_ENDPOINT" s3 cp s3://$BACKUP_BUCKET/$BACKUP_FILE /tmp/$BACKUP_FILE
gunzip /tmp/$BACKUP_FILE
SQL_FILE="/tmp/backup-20240103-030000.sql"
```

**Step C — Scale down the app**

```bash
just kube scale deployment/django-app --replicas=0
just kube scale deployment/django-worker --replicas=0
just kube get pods   # wait until app/worker pods are gone
```

**Step D — Port-forward postgres and restore**

```bash
just kube port-forward service/postgres 5432:5432 &
PF_PID=$!
sleep 2

psql -h localhost -p 5432 -U postgres -d postgres \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres;"
psql -h localhost -p 5432 -U postgres -d postgres < $SQL_FILE

kill $PF_PID
```

**Step E — Verify and scale up**

```bash
just kube scale deployment/django-app --replicas=1
just kube scale deployment/django-worker --replicas=1
just rdj migrate
rm $SQL_FILE
```

---

## Troubleshooting

### Backup job fails — dump stage

```bash
just kube logs job/<job-name> -c dump
```

Common causes:
- **`pg_isready` healthy but pg_dump fails** — the postgres pod may be under heavy load.
  Check `just kube logs statefulset/postgres`.
- **Password error** — the `backup-secret` may be out of sync with the postgres password.
  Re-run `just helm site` to re-apply secrets.

### Backup job fails — upload stage

```bash
just kube logs job/<job-name> -c upload
```

Common causes:
- **`NoCredentialProviders`** — check `secrets.backupAccessKey` and `backupSecretKey`
  in `values.secret.yaml`, then re-run `just helm site`.
- **Bucket not found** — confirm `secrets.backupBucket` matches the Terraform output:
  `just terraform-value backups bucket_name`.
- **Region mismatch** — `secrets.backupRegion` must match the `location` in
  `terraform/backups/terraform.tfvars`.

### Restore: `psql` hangs or connection refused

The port-forward may have dropped. Kill it and restart:

```bash
kill $PF_PID 2>/dev/null; sleep 1
just kube port-forward service/postgres 5432:5432 &
PF_PID=$!
sleep 2
```

### Restore: `DROP SCHEMA` fails with "other users are connected"

The app pods did not fully terminate. Wait and recheck:

```bash
just kube get pods
```

If Django pods are still Terminating, wait 30 seconds and try again.

### Object Storage bucket is inaccessible

Confirm the bucket is private and your credentials are correct:

```bash
aws --endpoint-url "$BACKUP_ENDPOINT" s3 ls
# Should list your buckets
```

If credentials work but the bucket is missing, it may have been accidentally deleted.
Recreate it:

```bash
just terraform backups apply
```

---

## What pg_dump Captures

`pg_dump -d postgres` exports:
- All tables, views, sequences, and indexes in the `postgres` database
- All table data (as SQL `COPY` or `INSERT` statements)
- Constraints, triggers, and functions
- Row-level security policies

It does **not** export:
- Other PostgreSQL databases (only the `postgres` database is backed up)
- PostgreSQL server configuration (`postgresql.conf`, `pg_hba.conf`)
- Real-time WAL — you can only restore to a backup point, not an arbitrary timestamp

The output is plain SQL, so you can open the `.sql` file in a text editor to inspect
or extract specific rows before doing a full restore.
