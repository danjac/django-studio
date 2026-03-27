---
description: Restore the production database from a Hetzner Object Storage backup
---

Restore the production database from a backup stored in Hetzner Object Storage.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/database-backups.md`
- `docs/cron-jobs.md`

---

## Step 1 — Check backups are configured

Check whether backup credentials exist in the cluster:

```bash
just --yes rkube get secret backup-secret --ignore-not-found -o name
```

If the output is empty, tell the user:

> Backups are not configured on this cluster. Run `/dj-enable-db-backups` to set up
> automated backups before attempting a restore.

Stop.

---

## Step 2 — List available backups

Run a one-off pod to list backups from Object Storage:

```bash
just --yes rkube run --rm -it list-backups \
  --image=amazon/aws-cli:2 \
  --restart=Never \
  --env="AWS_ACCESS_KEY_ID=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_ACCESS_KEY}' | base64 -d)" \
  --env="AWS_SECRET_ACCESS_KEY=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_SECRET_KEY}' | base64 -d)" \
  --env="AWS_DEFAULT_REGION=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_REGION}' | base64 -d)" \
  --env="BACKUP_ENDPOINT=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_ENDPOINT}' | base64 -d)" \
  --env="BACKUP_BUCKET=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_BUCKET}' | base64 -d)" \
  -- sh -c 'aws --endpoint-url "$BACKUP_ENDPOINT" s3 ls s3://$BACKUP_BUCKET/ | sort'
```

If the output is empty, tell the user no backups are available yet and stop.

Ask if they want to filter by date. Then present the list and ask the user to select a
backup (default: most recent):

> Available backups:
> 1. backup-20260325-030000.sql.gz  (2026-03-25 03:00)
> 2. backup-20260326-030000.sql.gz  (2026-03-26 03:00)
> 3. **backup-20260327-030000.sql.gz  (2026-03-27 03:00) [default]**
>
> Which backup would you like to restore? [3]

Wait for the user to confirm their selection.

---

## Step 3 — Confirm restore

Warn the user clearly before proceeding:

> ⚠️ This will restore the database to `<selected-filename>`.
> The current database will be overwritten. A safety backup will be taken first.
> Are you sure? [y/n]

If no, stop.

---

## Step 4 — Disable CronJobs

Suspend all CronJobs to prevent scheduled tasks from firing during the restore:

```bash
just --yes rcrons-disable
```

---

## Step 5 — Take a safety backup

Trigger an immediate backup before overwriting the database:

```bash
just --yes rkube create job postgres-backup-pre-restore --from=cronjob/postgres-backup
```

Wait for it to complete (timeout: 5 minutes):

```bash
just --yes rkube wait --for=condition=complete job/postgres-backup-pre-restore --timeout=300s
```

If the job fails or times out, tell the user:

> Safety backup failed. The restore has been paused. Re-enable CronJobs with:
>
> ```bash
> just --yes rcrons-enable
> ```
>
> Then check the backup job logs:
>
> ```bash
> just --yes rkube logs job/postgres-backup-pre-restore --all-containers
> ```

Stop without proceeding to the restore.

Clean up the job after success:

```bash
just --yes rkube delete job postgres-backup-pre-restore
```

---

## Step 6 — Restore the backup

```bash
just --yes rdb-restore <selected-filename>
```

Confirm the prompt when asked. The script scales down the app and worker, runs the
in-cluster restore pod, then scales them back up to their original replica counts.

---

## Step 7 — Verify

Run migrations to confirm the restored database is consistent:

```bash
just --yes rdj migrate
```

If migrations fail, stop and tell the user to check the backup file and restore logs
before proceeding.

---

## Step 8 — Re-enable CronJobs

```bash
just --yes rcrons-enable
```

---

## Step 9 — Done

Tell the user:

> Database restored from `<selected-filename>`. Migrations applied and CronJobs resumed.
> Open the site to confirm everything is working as expected.
