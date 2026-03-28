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
.agents/skills/dj-db-restore/bin/list-backups.sh
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

## Step 4 — Restore the backup

```bash
.agents/skills/dj-db-restore/bin/db-restore.sh <selected-filename>
```

The script handles the full restore atomically:
1. Suspends all CronJobs
2. Scales down the app and worker
3. Takes a safety backup (after scale-down, no in-flight writes)
4. Runs the in-cluster restore pod
5. Scales the app and worker back up
6. Resumes all CronJobs (even if interrupted)

---

## Step 5 — Verify

Run migrations to confirm the restored database is consistent:

```bash
just --yes rdj migrate
```

If migrations fail, stop and tell the user to check the backup file and restore logs
before proceeding.

---

## Step 6 — Done

Tell the user:

> Database restored from `<selected-filename>`. Migrations applied and CronJobs resumed.
> Open the site to confirm everything is working as expected.
