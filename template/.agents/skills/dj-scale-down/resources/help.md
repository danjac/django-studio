**/dj-scale-down <n>**

Scale the number of `django-app` replicas down to `<n>`. Shows the current
replica count, warns if scaling to 0 (unavailable) or 1 (no redundancy),
asks for confirmation, updates `replicas` in `helm/site/values.secret.yaml`,
runs `just deploy-config` to apply, and optionally removes excess Hetzner
nodes via Terraform to reduce costs.

Requires: `terraform`, `helm`, `kubectl`, and `just` installed and
authenticated. The project must have been deployed with `/dj-launch` first.

Example:
  /dj-scale-down 2
