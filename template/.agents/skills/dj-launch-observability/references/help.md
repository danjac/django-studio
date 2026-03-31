**/dj-launch-observability**

Deploys the observability stack (Grafana + Prometheus + Loki) to the cluster.
Run this after `/dj-launch` once the main application is live.

Sets a Grafana admin password (auto-generated if not provided), then runs
`just helm observability`.

Example:
  /dj-launch-observability
