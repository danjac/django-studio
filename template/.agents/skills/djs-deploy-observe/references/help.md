**/djs-deploy-observe**

Deploys the observability stack (Grafana + Prometheus + Loki) to the cluster.
Run this after `/djs-deploy` once the main application is live.

Sets a Grafana admin password (auto-generated if not provided), then runs
`just helm observability`.

Example:
  /djs-deploy-observe
