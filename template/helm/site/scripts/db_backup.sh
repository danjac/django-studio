#!/usr/bin/env bash
# Upload a PostgreSQL backup to S3 and prune old backups.
# Called from the postgres-backup CronJob upload container.
set -euo pipefail

FILENAME=$(cat /backup/latest)
echo "Uploading: ${FILENAME}"
aws --endpoint-url "${BACKUP_ENDPOINT}" s3 cp \
  "/backup/${FILENAME}" \
  "s3://${BACKUP_BUCKET}/${FILENAME}"
echo "Upload complete"

TO_DELETE=$(aws --endpoint-url "${BACKUP_ENDPOINT}" s3 ls \
  "s3://${BACKUP_BUCKET}/" \
  | sort \
  | head -n -"${RETENTION}" \
  | awk '{print $4}')

if [ -n "${TO_DELETE}" ]; then
  echo "Pruning old backups:"
  echo "${TO_DELETE}"
  echo "${TO_DELETE}" | xargs -I{} aws --endpoint-url "${BACKUP_ENDPOINT}" \
    s3 rm "s3://${BACKUP_BUCKET}/{}"
else
  echo "No backups to prune (fewer than ${RETENTION} stored)"
fi
