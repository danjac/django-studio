**/dj-db-backup**

Trigger an immediate production database backup without waiting for the daily cron job.

Useful before deployments, risky migrations, or any operation you want to snapshot first.
The site stays up — no downtime required.

**Prerequisites:** Backups must be configured (`/dj-enable-db-backups`).

**Example:**

```
/dj-db-backup
```

The backup is uploaded to Hetzner Object Storage and will appear when you run `/dj-db-restore`.
