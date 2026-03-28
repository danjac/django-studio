**/dj-db-restore**

Guided production database restore from a Hetzner Object Storage backup.

**Usage**

```
/dj-db-restore
```

No arguments — the skill walks you through every step interactively.

**What it does**

1. Checks that backup credentials are configured in the cluster (`backup-secret`).
2. Lists available backups from Object Storage and asks you to select one (default: most recent). Offers date filtering.
3. Asks for confirmation before overwriting the database.
4. Runs `.agents/skills/dj-db-restore/bin/db-restore.sh <filename>` — suspends CronJobs, scales down app and worker, takes a safety backup, restores in-cluster, scales back up, resumes CronJobs (even if interrupted).
5. Runs `just rdj migrate` to verify the restored database is consistent.

**Prerequisites**

- Cluster access configured (`KUBECONFIG` set or `~/.kube/<project>.yaml` present)
- Backups enabled (`backup.enabled: true` in `helm/site/values.secret.yaml` and deployed)

**Related commands**

- `/dj-enable-db-backups` — set up automated backups if not yet configured
- `/dj-db-backup` — trigger a manual backup immediately

**See also:** `docs/database-backups.md`
