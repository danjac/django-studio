**/dj-launch**

Interactive first-deploy wizard. Guides you through provisioning infrastructure,
configuring secrets, and deploying the application end-to-end.

Covers: Hetzner infrastructure (Terraform), Cloudflare DNS and SSL, object
storage (if enabled), Helm secrets, GitHub Actions secrets, the three-step
first production deploy (build image → deploy infra → deploy app),
configuring the default Django site (`set_default_site`), and optionally
adding the Kubernetes MCP server to `.mcp.json`. Idempotent —
safe to re-run if interrupted; existing values are never overwritten.

Requires: `gh`, `terraform`, `helm`, `kubectl`, and `just` installed and
authenticated.

Example:
  /dj-launch
