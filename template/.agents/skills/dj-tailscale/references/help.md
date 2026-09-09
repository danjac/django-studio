**/dj-tailscale [enable|status|disable]**

Put the cluster on a Tailscale tailnet so SSH and the Kubernetes API travel over
WireGuard instead of the public internet, then close ports 22 and 6443 to
everything else. Ports 80 and 443 stay open — that is public web traffic via
Cloudflare.

**Arguments**

| Argument | What it does |
|----------|--------------|
| `status` (default) | Reports whether Tailscale is enabled, the current API address, and whether `admin_ips` is still open |
| `enable` | Sets Tailscale up end to end, detecting whether this is a fresh deploy or an existing cluster |
| `disable` | Reopens the firewall first, verifies public access, then removes Tailscale |

**What `enable` does**

It picks one of two paths automatically:

- **Day one** — no infrastructure yet. Nodes install Tailscale and join during
  cloud-init, and the k3s certificate gets the server's MagicDNS name at install
  time.
- **Retrofit** — the cluster is already running. Existing nodes cannot pick this
  up from cloud-init, so the skill runs
  `.agents/skills/dj-tailscale/scripts/join-nodes.sh` over SSH instead. On the
  server it also adds the MagicDNS name to the k3s serving certificate, which
  requires **restarting k3s** — the API is briefly unavailable, running pods are
  not affected.

Either way it then repoints the kubeconfig at the tailnet, verifies
`kubectl get nodes` works, and only then closes the public ports.

**Before you start**

In the Tailscale admin console you need:

1. `tag:k8s` and `tag:ci` added to `tagOwners` under Access Controls
2. An **OAuth client** with the `auth_keys` write scope and both tags —
   not an auth key, which expires after at most 90 days and would silently
   break any node added later
3. Your tailnet name, e.g. `tail1a2b3c.ts.net`

**Examples**

```bash
/dj-tailscale                 # is it on, and is the firewall still open?
/dj-tailscale enable          # set it up, or retrofit a running cluster
/dj-tailscale disable         # unwind it safely
```

**Safety**

The skill never tightens `admin_ips` until `kubectl get nodes` has succeeded over
the tailnet in that same session. If verification fails it stops and leaves the
firewall open. Recovery from a lockout is via the Hetzner web console.
