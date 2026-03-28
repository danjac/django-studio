# Database Backups

Automated daily backups of the PostgreSQL database to a private Hetzner Object Storage
bucket. Backups are application-consistent `pg_dump` exports — safe to restore from at
any time without risk of data corruption.

Backups are **optional** and disabled by default. Follow this guide to set them up when
you are ready.

## Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Setting Up Backups](#setting-up-backups)
- [Configuration](#configuration)
- [Restoring a Backup](#restoring-a-backup)
- [Troubleshooting](#troubleshooting)
- [What pg_dump Captures](#what-pg_dump-captures)

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
just rkube get cronjob postgres-backup
```

### Step 4 — Trigger a test backup

Run a manual job to confirm the first backup works before relying on the schedule:

```bash
just rkube create job postgres-backup-test --from=cronjob/postgres-backup
```

Watch the logs:

```bash
just rkube logs -f job/postgres-backup-test -c dump
just rkube logs -f job/postgres-backup-test -c upload
```

You should see the dump size and "Upload complete". Then verify the file appeared in
the bucket by running `.agents/skills/dj-db-restore/bin/list-backups.sh`.

Clean up the test job:

```bash
just rkube delete job postgres-backup-test
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

Use `/dj-db-restore` for a guided restore. The steps below are for manual use.

### List available backups

```bash
.agents/skills/dj-db-restore/bin/list-backups.sh
```

### Run the restore

```bash
.agents/skills/dj-db-restore/bin/db-restore.sh backup-20240103-030000.sql.gz
```

The script handles the full lifecycle: suspend CronJobs, scale down app/worker, safety
backup, in-cluster restore, scale back up, resume CronJobs (EXIT trap ensures CronJobs
are always resumed, even on failure).

### Verify

```bash
just rdj migrate
```

Open the site in a browser. If the home page loads and you can log in, you are done.

### Manual restore (fallback)

If the restore script fails or the backup CronJob is not set up, you can restore
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

**Step C — Disable CronJobs and scale down the app**

```bash
kubectl get cronjobs -o name | xargs -I{} kubectl patch {} -p '{"spec":{"suspend":true}}'
kubectl scale deployment/django-app --replicas=0
kubectl scale deployment/django-worker --replicas=0
kubectl wait --for=delete pod -l app=django-app --timeout=60s 2>/dev/null || true
kubectl wait --for=delete pod -l app=django-worker --timeout=60s 2>/dev/null || true
```

**Step D — Port-forward postgres and restore**

```bash
just rkube port-forward service/postgres 5432:5432 &
PF_PID=$!
sleep 2

psql -h localhost -p 5432 -U postgres -d postgres \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres;"
psql -h localhost -p 5432 -U postgres -d postgres < $SQL_FILE

kill $PF_PID
```

**Step E — Scale up, re-enable CronJobs, and verify**

```bash
kubectl scale deployment/django-app --replicas=1
kubectl scale deployment/django-worker --replicas=1
kubectl get cronjobs -o name | xargs -I{} kubectl patch {} -p '{"spec":{"suspend":false}}'
just rdj migrate
rm $SQL_FILE
```

## Troubleshooting

### Backup job fails — dump stage

```bash
just rkube logs job/<job-name> -c dump
```

Common causes:
- **`pg_isready` healthy but pg_dump fails** — the postgres pod may be under heavy load.
  Check `just rkube logs statefulset/postgres`.
- **Password error** — the `backup-secret` may be out of sync with the postgres password.
  Re-run `just helm site` to re-apply secrets.

### Backup job fails — upload stage

```bash
just rkube logs job/<job-name> -c upload
```

Common causes:
- **`NoCredentialProviders`** — check `secrets.backupAccessKey` and `backupSecretKey`
  in `values.secret.yaml`, then re-run `just helm site`.
- **Bucket not found** — confirm `secrets.backupBucket` matches the Terraform output:
  `just terraform-value backups bucket_name`.
- **Region mismatch** — `secrets.backupRegion` must match the `location` in
  `terraform/backups/terraform.tfvars`.

### Restore: `psql` hangs or connection refused (manual fallback only)

The port-forward may have dropped. Kill it and restart:

```bash
kill $PF_PID 2>/dev/null; sleep 1
just rkube port-forward service/postgres 5432:5432 &
PF_PID=$!
sleep 2
```

### Restore: `DROP SCHEMA` fails with "other users are connected"

The app pods did not fully terminate. Wait and recheck:

```bash
just rkube get pods
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
