**/dj-deploy-cron <app_name> <command_name>**

Adds a Kubernetes cron job to `helm/site/values.yaml` for an existing management
command.

Checks the command exists (offers `/dj-create-command` if not). Reads the command's
arguments, detects existing cron entries for the same command (offers to update
the schedule or add a second instance with a distinguishing key suffix). Asks for
the schedule in plain English and converts it to cron syntax (UTC).

If the project is already deployed, reminds you to commit and push so CI builds
the image and deploys the Helm chart atomically. Reminds you to run
`just gh-set-secrets` if GitHub Actions secrets haven't been configured.

Example:
  /dj-deploy-cron orders process_pending_refunds
