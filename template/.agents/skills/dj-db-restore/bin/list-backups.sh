#!/usr/bin/env bash
# List available database backups from Object Storage.
#
# Fetches credentials from the cluster backup-secret and runs a one-off
# aws-cli pod to list all objects in the backup bucket, sorted by date.
#
# Usage:
#   .agents/skills/dj-db-restore/bin/list-backups.sh
set -euo pipefail

# Read the aws-cli image from the backup CronJob so the version matches exactly.
AWS_CLI_IMAGE=$(just --yes rkube get cronjob postgres-backup \
  -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].image}')

# Delete any stale pod from a previous interrupted run.
just --yes rkube delete pod list-backups --ignore-not-found=true

# Clean up the pod on exit regardless of how the script terminates.
trap 'just --yes rkube delete pod list-backups --ignore-not-found=true 2>/dev/null || true' EXIT

# \$ escaping: just runs recipes via sh -c "...", so bare $VAR would expand in just's shell
# (to empty — these vars only exist inside the pod). \$ survives just's shell as $, which
# kubectl passes verbatim to the pod where the pod's sh expands it from the --env values.
just --yes rkube run list-backups \
  --image="${AWS_CLI_IMAGE}" \
  --restart=Never \
  --env="AWS_ACCESS_KEY_ID=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_ACCESS_KEY}' | base64 -d)" \
  --env="AWS_SECRET_ACCESS_KEY=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_SECRET_KEY}' | base64 -d)" \
  --env="AWS_DEFAULT_REGION=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_REGION}' | base64 -d)" \
  --env="BACKUP_ENDPOINT=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_ENDPOINT}' | base64 -d)" \
  --env="BACKUP_BUCKET=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_BUCKET}' | base64 -d)" \
  --command -- sh -c 'aws --endpoint-url \$BACKUP_ENDPOINT s3 ls s3://\$BACKUP_BUCKET/ | sort'

just --yes rkube wait --for=jsonpath='{.status.phase}'=Succeeded pod/list-backups --timeout=120s \
  || { echo "Failed to list backups. Logs:"; just --yes rkube logs pod/list-backups; exit 1; }

just --yes rkube logs pod/list-backups
