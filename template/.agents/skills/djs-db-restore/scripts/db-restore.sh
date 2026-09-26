#!/usr/bin/env bash
# Restore the production database from a named backup file in Object Storage.
# Runs entirely in-cluster — no local aws CLI or psql installation required.
#   filename: e.g. backup-20240103-030000.sql.gz
# See docs/database-backups.md for the full restore guide including how to list available backups.
set -euo pipefail

export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/PROJECT_SLUG.yaml}"

FILENAME="${1:?Usage: db-restore.sh <backup-filename.sql.gz>}"

# Read the postgres image from the running StatefulSet so the restore version matches exactly.
POSTGRES_IMAGE=$(kubectl get statefulset postgres -o jsonpath='{.spec.template.spec.containers[0].image}')

# Capture current replica counts so we restore to the same number after the restore.
APP_REPLICAS=$(kubectl get deployment/django-app -o jsonpath='{.spec.replicas}' 2>/dev/null || echo 1)
WORKER_REPLICAS=$(kubectl get deployment/django-worker -o jsonpath='{.spec.replicas}' 2>/dev/null || echo 1)

# Resume CronJobs on exit (normal or interrupted) so they are never left suspended.
_resume_cronjobs() {
    echo "==> Resuming CronJobs..."
    while IFS= read -r cj; do
        kubectl patch "$cj" -p '{"spec":{"suspend":false}}' 2>/dev/null || true
    done < <(kubectl get cronjobs -o name 2>/dev/null)
    echo "All CronJobs resumed."
}
trap _resume_cronjobs EXIT

echo "==> Suspending CronJobs..."
while IFS= read -r cj; do
    kubectl patch "$cj" -p '{"spec":{"suspend":true}}'
done < <(kubectl get cronjobs -o name 2>/dev/null)
echo "All CronJobs suspended."

echo "==> Scaling down app (${APP_REPLICAS} replicas) and worker (${WORKER_REPLICAS} replicas)..."
kubectl scale deployment/django-app --replicas=0
kubectl wait --for=delete pod -l app=django-app --timeout=60s 2>/dev/null || true
kubectl scale deployment/django-worker --replicas=0
kubectl wait --for=delete pod -l app=django-worker --timeout=60s 2>/dev/null || true

echo "==> Taking safety backup (app is down, no in-flight writes)..."
kubectl delete job postgres-backup-pre-restore --ignore-not-found=true
kubectl create job postgres-backup-pre-restore --from=cronjob/postgres-backup
kubectl wait --for=condition=complete job/postgres-backup-pre-restore --timeout=300s \
  || { echo "Safety backup failed. Logs:"; kubectl logs job/postgres-backup-pre-restore --all-containers; kubectl delete job postgres-backup-pre-restore --ignore-not-found=true; exit 1; }
kubectl delete job postgres-backup-pre-restore

echo "==> Starting in-cluster restore pod for: ${FILENAME}"
kubectl delete pod db-restore --ignore-not-found=true

kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: db-restore
spec:
  restartPolicy: Never
  nodeSelector:
    role: jobrunner
  initContainers:
    - name: download
      image: amazon/aws-cli:2.34.11
      command: ["/bin/bash", "/scripts/db_download.sh"]
      env:
        - name: FILENAME
          value: "${FILENAME}"
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: backup-secret
              key: BACKUP_ACCESS_KEY
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: backup-secret
              key: BACKUP_SECRET_KEY
        - name: AWS_DEFAULT_REGION
          valueFrom:
            secretKeyRef:
              name: backup-secret
              key: BACKUP_REGION
        - name: BACKUP_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: backup-secret
              key: BACKUP_ENDPOINT
        - name: BACKUP_BUCKET
          valueFrom:
            secretKeyRef:
              name: backup-secret
              key: BACKUP_BUCKET
      volumeMounts:
        - name: data
          mountPath: /backup
        - name: scripts
          mountPath: /scripts
  containers:
    - name: restore
      image: ${POSTGRES_IMAGE}
      command: ["/bin/bash", "/scripts/db_restore.sh"]
      env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: secrets
              key: POSTGRES_PASSWORD
      volumeMounts:
        - name: data
          mountPath: /backup
        - name: scripts
          mountPath: /scripts
  volumes:
    - name: data
      emptyDir: {}
    - name: scripts
      configMap:
        name: db-scripts
        defaultMode: 0555
EOF

echo "==> Waiting for restore to complete (timeout: 10 minutes)..."
kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/db-restore --timeout=600s \
  || { echo "Restore failed. Logs:"; kubectl logs pod/db-restore --all-containers=true; kubectl delete pod db-restore; exit 1; }

echo "--- download ---"
kubectl logs pod/db-restore -c download
echo "--- restore ---"
kubectl logs pod/db-restore -c restore

kubectl delete pod db-restore

echo "==> Scaling app back up to ${APP_REPLICAS} replicas..."
kubectl scale deployment/django-app --replicas="${APP_REPLICAS}"
kubectl scale deployment/django-worker --replicas="${WORKER_REPLICAS}"

echo ""
echo "Done. Run: just rdj migrate"
# trap EXIT fires here, resuming CronJobs
