#!/usr/bin/env bash
# Atomically patch the live Kubernetes Secret with new database and cache credentials.
#
# Reads credentials from environment variables and patches all affected keys in a
# single kubectl call so pods restarted mid-rollout pick up consistent values.
#
# Required environment variables:
#   NEW_POSTGRES_PASSWORD  — new PostgreSQL password
#   NEW_REDIS_PASSWORD     — new Redis password
#   NAMESPACE              — Helm release namespace
#   KUBECONFIG             — path to kubeconfig (defaults to ~/.kube/<project>.yaml via just)
#
# Usage:
#   NEW_POSTGRES_PASSWORD=... NEW_REDIS_PASSWORD=... NAMESPACE=... \
#     .agents/skills/dj-rotate-secrets/bin/patch-k8s-secrets.sh
set -euo pipefail

: "${NEW_POSTGRES_PASSWORD:?NEW_POSTGRES_PASSWORD is required}"
: "${NEW_REDIS_PASSWORD:?NEW_REDIS_PASSWORD is required}"
: "${NAMESPACE:?NAMESPACE is required}"

b64_pg_pass=$(printf '%s' "$NEW_POSTGRES_PASSWORD" | base64 -w0)
b64_db_url=$(printf 'postgresql://postgres:%s@postgres.%s.svc.cluster.local:5432/postgres' \
  "$NEW_POSTGRES_PASSWORD" "$NAMESPACE" | base64 -w0)
b64_redis_pass=$(printf '%s' "$NEW_REDIS_PASSWORD" | base64 -w0)
b64_redis_url=$(printf 'redis://default:%s@redis.%s.svc.cluster.local:6379/0' \
  "$NEW_REDIS_PASSWORD" "$NAMESPACE" | base64 -w0)

# Call kubectl directly — `just rkube` passes args through the shell which splits
# the JSON on embedded newlines before kubectl receives the argument.
kubectl patch secret secrets \
  --namespace "$NAMESPACE" \
  -p "{\"data\":{\"POSTGRES_PASSWORD\":\"$b64_pg_pass\",\"DATABASE_URL\":\"$b64_db_url\",\"REDIS_PASSWORD\":\"$b64_redis_pass\",\"REDIS_URL\":\"$b64_redis_url\"}}"
