**/dj-scale-up <n>**

Scale the number of `django-app` replicas up to `<n>`. Shows the current
replica count, asks for confirmation, provisions additional Hetzner nodes
via Terraform if the cluster needs more capacity, updates `replicas` in
`helm/site/values.secret.yaml`, and runs `just deploy-config` to apply.

Requires: `terraform`, `helm`, `kubectl`, and `just` installed and
authenticated. The project must have been deployed with `/dj-launch` first.

Example:
  /dj-scale-up 4
