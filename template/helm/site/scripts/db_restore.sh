#!/usr/bin/env bash
# Restore PostgreSQL from a downloaded dump file.
# Called from the db-restore Job restore container.
set -euo pipefail

echo "Clearing database..."
psql -h postgres -U postgres -d postgres \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres;"
echo "Restoring from dump..."
psql -h postgres -U postgres -d postgres < /backup/dump.sql
echo "Restore complete."
