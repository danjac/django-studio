**/dj-rotate-secrets**

Rotates auto-generated and third-party secrets in `helm/site/values.secret.yaml`
and redeploys the Helm chart to apply them.

Requires an existing deployment (`values.secret.yaml` must exist). Always shows
exactly which secrets will change and waits for confirmation before writing
anything.

Example:
  /dj-rotate-secrets
