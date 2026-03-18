#!/usr/bin/env bash
# Download a PostgreSQL backup from S3 and decompress it.
# Called from the db-restore Pod download initContainer.
set -euo pipefail

aws --endpoint-url "${BACKUP_ENDPOINT}" s3 cp \
  "s3://${BACKUP_BUCKET}/${FILENAME}" /backup/dump.sql.gz
echo "Download complete: $(du -h /backup/dump.sql.gz | cut -f1)"
