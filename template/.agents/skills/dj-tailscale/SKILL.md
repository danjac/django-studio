---
description: Enable, check or disable Tailscale private networking for the cluster
---

Put the cluster on a Tailscale tailnet so SSH and the Kubernetes API are reachable
over WireGuard instead of the public internet, then close ports 22 and 6443 to
everyone else.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/infrastructure.md`
- `docs/deployment.md`

---

**Lockout rule — the one that matters.** Never tighten `admin_ips` until you have
confirmed, in this session, that `kubectl` works over the tailnet. Locking
`admin_ips` to `100.64.0.0/10` while any node is off the tailnet leaves no way in
except the Hetzner web console. Verify first, lock second, always.

**Secret handling.** The OAuth client secret goes in
`terraform/hetzner/terraform.tfvars` (gitignored) or an environment variable.
Never echo it, never ask the user to paste it into this chat.

**Ports 80 and 443 stay open.** Those carry public web traffic via Cloudflare and
have nothing to do with administrative access.

Parse `$ARGUMENTS` as: `[enable|status|disable]`. Default to `status`.

---

## status

Read `tailscale_oauth_client_secret` from `terraform/hetzner/terraform.tfvars`
(presence only — never print it) and `admin_ips` from the same file.

```bash
just terraform hetzner output tailscale_enabled
just terraform hetzner output server_tailscale_host
```

Report:

> **Tailscale:** `<enabled|not enabled>`
> **API address:** `<MagicDNS name, or public IP if not enabled>`
> **admin_ips:** `<value>`

If Tailscale is enabled but `admin_ips` is still `["0.0.0.0/0", "::/0"]`, add:

> ⚠️ Tailscale is enabled but SSH (22) and the Kubernetes API (6443) are still
> open to the internet. Run `/dj-tailscale enable` to finish locking down, or
> leave as-is if that is deliberate.

Then stop.

---

## enable

### Step 1 — Determine which path applies

Check whether infrastructure already exists:

```bash
just terraform hetzner output server_public_ip
```

- **Fails or empty** → *day one*: nothing is provisioned yet. Nodes will join at
  boot via cloud-init. Go to Step 2, then Step 4.
- **Returns an IP** → *retrofit*: the cluster is already running. Existing nodes
  cannot pick this up from cloud-init, because all servers set
  `lifecycle { ignore_changes = [user_data] }`. Go to Step 2, then Step 3.

Tell the user which path you are taking and why.

### Step 2 — Collect Tailscale settings

Tell the user what to create, then wait:

> **In the Tailscale admin console:**
>
> 1. **Tag** — under Access Controls, add `tag:k8s` and `tag:ci` to `tagOwners`.
> 2. **OAuth client** — Settings → OAuth clients → Generate. Give it the
>    `auth_keys` **write** scope and both tags above.
>    Use an OAuth client, **not** an auth key: auth keys expire after at most 90
>    days, and once expired any node you add later silently fails to join.
> 3. **Tailnet name** — shown at the top of the admin console, e.g.
>    `tail1a2b3c.ts.net`.
>
> Then open `terraform/hetzner/terraform.tfvars` and set:
>
> ```hcl
> tailscale_oauth_client_secret = "tskey-client-..."
> tailscale_tailnet             = "tail1a2b3c.ts.net"
> ```
>
> Say **continue** when done.

Re-read the file and confirm both are non-empty. Do not print the secret.

### Step 3 — Retrofit path only: join the running nodes

This installs Tailscale on each existing node and adds the server's MagicDNS name
to the k3s serving certificate.

Show the user what will happen before running anything:

> This will, on each existing node: install Tailscale and join it to your tailnet.
> On the server it will also add the MagicDNS name to the k3s TLS certificate,
> which requires **restarting k3s** — the Kubernetes API is briefly unavailable.
> Running pods are not affected.
>
> Proceed? [y/n]

Show the plan first:

```bash
TAILSCALE_OAUTH_CLIENT_SECRET="$(grep tailscale_oauth_client_secret terraform/hetzner/terraform.tfvars | cut -d'"' -f2)" \
TAILSCALE_TAILNET="$(grep tailscale_tailnet terraform/hetzner/terraform.tfvars | cut -d'"' -f2)" \
  .agents/skills/dj-tailscale/scripts/join-nodes.sh --dry-run
```

Then run it for real by dropping `--dry-run`.

The script verifies the certificate itself and exits non-zero if the SAN is not
present after the restart. **If it fails, stop.** Do not continue to Step 5 — tell
the user kubectl will not work over the tailnet and the firewall must stay open
until it is resolved.

### Step 4 — Day-one path only: provision

```bash
just terraform hetzner plan
```

Show the plan. Ask for confirmation, then:

```bash
just terraform hetzner apply
```

Nodes install Tailscale and join during cloud-init. Wait for the apply to finish.

### Step 5 — Point kubectl at the tailnet

```bash
just get-kubeconfig
```

This rewrites the API address to the server's MagicDNS name. Confirm the output
mentions "Tailscale enabled".

### Step 6 — Verify before locking anything

The user must be on the tailnet themselves for this to work.

```bash
just --yes rkube get nodes
```

**Every node must be `Ready`.** If this fails for any reason, stop here and report
it. Do not proceed to Step 7 — the firewall change is what makes a failure
unrecoverable without the Hetzner console.

### Step 7 — Close the public ports

Only after Step 6 succeeded. Tell the user:

> **Action required:** In `terraform/hetzner/terraform.tfvars`, set:
>
> ```hcl
> admin_ips = ["100.64.0.0/10"]
> ```
>
> This closes SSH (22) and the Kubernetes API (6443) to everything except your
> tailnet. Ports 80 and 443 stay open for web traffic.
>
> Say **continue** when done.

Then:

```bash
just terraform hetzner plan
```

Show the plan — it should change firewall rules only, no server replacement. If it
proposes replacing any server, **stop** and report that; something is wrong.

Then apply, and re-run `just --yes rkube get nodes` to confirm access still works.

### Step 8 — CI

CI reaches the cluster over the tailnet too, so the runner needs its own credentials.

> **Action required:** Add two repository secrets:
>
> - `TS_OAUTH_CLIENT_ID`
> - `TS_OAUTH_SECRET`
>
> Use the OAuth client from Step 2 (or a separate one scoped to `tag:ci`).
>
> ```bash
> gh secret set TS_OAUTH_CLIENT_ID
> gh secret set TS_OAUTH_SECRET
> ```

The deploy workflow already has a Tailscale step that activates only when
`TS_OAUTH_CLIENT_ID` is set, so no workflow edit is needed.

Then push the updated kubeconfig, which now points at the MagicDNS name:

```bash
just gh-set-secrets
```

Finally, tell the user to run a deploy and confirm it succeeds.

---

## disable

**Order matters — reopen the firewall first, or you lock yourself out.**

### Step 1 — Reopen public access

> **Action required:** In `terraform/hetzner/terraform.tfvars`, set:
>
> ```hcl
> admin_ips = ["0.0.0.0/0", "::/0"]
> ```
>
> (Or your own IP, if you have a static one.) Say **continue** when done.

```bash
just terraform hetzner apply
```

### Step 2 — Confirm public access works

```bash
just get-kubeconfig
just --yes rkube get nodes
```

The kubeconfig now points at the public IP again. Do not continue until this works.

### Step 3 — Remove Tailscale

> **Action required:** Clear `tailscale_oauth_client_secret` in
> `terraform/hetzner/terraform.tfvars`. Say **continue** when done.

New nodes will no longer join the tailnet. Existing nodes stay joined until you
run `sudo tailscale logout` on each — tell the user this, and that the k3s TLS SAN
drop-in at `/etc/rancher/k3s/config.yaml.d/10-tailscale.yaml` is harmless to leave.

Finally, remove `TS_OAUTH_CLIENT_ID` and `TS_OAUTH_SECRET` from the repository
secrets so the CI step stops running.

---

## User-facing outputs

| Value | Why the user needs it |
|-------|----------------------|
| Which path (day one vs retrofit) | Sets expectations about the k3s restart |
| `kubectl get nodes` result before locking | The gate on the firewall change |
| MagicDNS API address | Confirms kubectl traffic is on the tailnet |
| Reminder that they must be on the tailnet | Otherwise every later command fails confusingly |
