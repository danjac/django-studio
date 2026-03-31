#!/usr/bin/env bash
# List available database backups from Object Storage.
#
# Fetches credentials from the cluster backup-secret and runs a one-off
# aws-cli pod to list all objects in the backup bucket, sorted by date.
#
# Usage:
#   .agents/skills/dj-db-restore/bin/list-backups.sh
set -euo pipefail

# Resolve the kubeconfig path the same way the justfile does.
KUBECONFIG="${KUBECONFIG:-$HOME/.kube/PROJECT_SLUG.yaml}"
export KUBECONFIG

kubectl() { command kubectl --kubeconfig "$KUBECONFIG" "$@"; }

# Read the aws-cli image from the backup CronJob so the version matches exactly.
AWS_CLI_IMAGE=$(kubectl get cronjob postgres-backup \
  -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].image}')

# Delete any stale pod from a previous interrupted run.
kubectl delete pod list-backups --ignore-not-found=true

# Clean up the pod on exit regardless of how the script terminates.
trap 'kubectl delete pod list-backups --ignore-not-found=true 2>/dev/null || true' EXIT

# shellcheck disable=SC2016
# SC2016: $BACKUP_ENDPOINT and $BACKUP_BUCKET are intentionally in single quotes —
# they must expand inside the pod's shell, not the local shell.
kubectl run list-backups \
  --image="${AWS_CLI_IMAGE}" \
  --restart=Never \
  --env="AWS_ACCESS_KEY_ID=$(kubectl get secret backup-secret -o jsonpath='{.data.BACKUP_ACCESS_KEY}' | base64 -d)" \
  --env="AWS_SECRET_ACCESS_KEY=$(kubectl get secret backup-secret -o jsonpath='{.data.BACKUP_SECRET_KEY}' | base64 -d)" \
  --env="AWS_DEFAULT_REGION=$(kubectl get secret backup-secret -o jsonpath='{.data.BACKUP_REGION}' | base64 -d)" \
  --env="BACKUP_ENDPOINT=$(kubectl get secret backup-secret -o jsonpath='{.data.BACKUP_ENDPOINT}' | base64 -d)" \
  --env="BACKUP_BUCKET=$(kubectl get secret backup-secret -o jsonpath='{.data.BACKUP_BUCKET}' | base64 -d)" \
  --command -- sh -c 'aws --endpoint-url $BACKUP_ENDPOINT s3 ls s3://$BACKUP_BUCKET/ | sort'

kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/list-backups --timeout=120s \
  || { echo "Failed to list backups. Logs:"; kubectl logs pod/list-backups; exit 1; }

kubectl logs pod/list-backups
