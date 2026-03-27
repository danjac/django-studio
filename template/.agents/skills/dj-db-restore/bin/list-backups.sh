#!/usr/bin/env bash
# List available database backups from Object Storage.
#
# Fetches credentials from the cluster backup-secret and runs a one-off
# aws-cli pod to list all objects in the backup bucket, sorted by date.
#
# Usage:
#   .agents/skills/dj-db-restore/bin/list-backups.sh
set -euo pipefail

just --yes rkube run --rm -it list-backups \
  --image=amazon/aws-cli:2 \
  --restart=Never \
  --env="AWS_ACCESS_KEY_ID=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_ACCESS_KEY}' | base64 -d)" \
  --env="AWS_SECRET_ACCESS_KEY=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_SECRET_KEY}' | base64 -d)" \
  --env="AWS_DEFAULT_REGION=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_REGION}' | base64 -d)" \
  --env="BACKUP_ENDPOINT=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_ENDPOINT}' | base64 -d)" \
  --env="BACKUP_BUCKET=$(just --yes rkube get secret backup-secret -o jsonpath='{.data.BACKUP_BUCKET}' | base64 -d)" \
  # shellcheck disable=SC2016  # vars intentionally expand inside the container, not here
  -- sh -c 'aws --endpoint-url "$BACKUP_ENDPOINT" s3 ls s3://$BACKUP_BUCKET/ | sort'
