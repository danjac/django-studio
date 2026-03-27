---
description: Trigger an immediate production database backup without waiting for the daily cron
---

Take an on-demand snapshot of the production database and upload it to Object Storage.
Useful before deployments, migrations, or any operation that modifies data.

## Required reading

- `docs/database-backups.md`

---

## Step 1 — Check backups are configured

```bash
just --yes rkube get secret backup-secret --ignore-not-found -o name
```

If the output is empty, tell the user:

> Backups are not configured on this cluster. Run `/dj-enable-db-backups` to set up
> automated backups first.

Stop.

---

## Step 2 — Confirm

Tell the user:

> This will trigger an immediate database backup and upload it to Object Storage.
> The site stays up — no downtime required.
> Proceed? [y/n]

If no, stop.

---

## Step 3 — Run the backup

```bash
just --yes rdb-backup
```

This creates a one-off Kubernetes job from the `postgres-backup` CronJob, waits for it
to complete (timeout: 5 minutes), streams the logs, then deletes the job.

If the command exits non-zero, show the error output and tell the user:

> Backup failed. Check the logs above. Common causes:
> - Database unreachable — check `just rkube get pods`
> - Object Storage credentials incorrect — check `backup-secret` and `values.secret.yaml`

---

## Step 4 — Done

Tell the user:

> Backup complete. The new snapshot is now available in Object Storage and will appear
> when you next run `/dj-db-restore`.
