**/dj-enable-db-backups**

Interactive wizard to enable automated daily PostgreSQL backups to a private
Hetzner Object Storage bucket. Provisions the backup bucket via Terraform,
configures Helm secrets, deploys the backup CronJob, and runs a test backup
to confirm everything works.

By default, backups run daily at 03:00 UTC and the 7 most recent dumps are
retained. You will be prompted to change these before deploying.
Restore instructions are in `docs/database-backups.md`.

Requires: `terraform`, `just`, and `kubectl` installed and authenticated.

Example:
  /dj-enable-db-backups
