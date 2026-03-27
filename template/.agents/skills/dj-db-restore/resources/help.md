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
4. Suspends all CronJobs (`just rcrons-disable`).
5. Takes a safety backup of the current database before proceeding.
6. Runs `just rdb-restore <filename>` — scales down app and worker, restores in-cluster, scales back up.
7. Runs `just rdj migrate` to verify the restored database is consistent.
8. Resumes all CronJobs (`just rcrons-enable`).

**Prerequisites**

- Cluster access configured (`KUBECONFIG` set or `~/.kube/<project>.yaml` present)
- Backups enabled (`backup.enabled: true` in `helm/site/values.secret.yaml` and deployed)

**Related commands**

- `/dj-enable-db-backups` — set up automated backups if not yet configured
- `just rdb-backup` — trigger a manual backup immediately
- `just rcrons-disable [name]` — suspend all or one CronJob
- `just rcrons-enable [name]` — resume all or one CronJob

**See also:** `docs/database-backups.md`
