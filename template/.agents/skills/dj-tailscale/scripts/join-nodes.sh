#!/usr/bin/env bash
# Join already-running nodes to a tailnet.
#
# Nodes created *after* Tailscale is enabled join automatically via cloud-init.
# This script covers the two cases cloud-init cannot:
#
#   1. Retrofitting a cluster provisioned before Tailscale was enabled.
#   2. Recovering a node where the cloud-init Tailscale step failed.
#
# On the server it additionally adds the MagicDNS name to the k3s serving
# certificate. That is not optional: the existing certificate only carries the
# private and public IPs, so kubectl over Tailscale would fail verification.
#
# Usage:
#   TAILSCALE_OAUTH_CLIENT_SECRET=tskey-client-... \
#   TAILSCALE_TAILNET=tail1a2b3c.ts.net \
#     .agents/skills/dj-tailscale/scripts/join-nodes.sh [--dry-run]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TF_DIR="$REPO_ROOT/terraform/hetzner"

: "${TAILSCALE_OAUTH_CLIENT_SECRET:?set TAILSCALE_OAUTH_CLIENT_SECRET (tskey-client-...)}"
: "${TAILSCALE_TAILNET:?set TAILSCALE_TAILNET (e.g. tail1a2b3c.ts.net)}"
TAILSCALE_TAG="${TAILSCALE_TAG:-tag:k8s}"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

if [[ ! -d "$TF_DIR" ]]; then
    echo "Error: $TF_DIR not found" >&2
    exit 1
fi

# Node name -> public IP, derived from Terraform outputs so the hostnames match
# exactly what cloud-init would set on a freshly created node.
nodes() {
    (cd "$TF_DIR" && terraform output -json) | python3 -c '
import json, sys

out = json.load(sys.stdin)
value = lambda key: (out.get(key) or {}).get("value")

prefix = value("tailscale_name_prefix")
if not prefix:
    sys.exit("Error: terraform output tailscale_name_prefix is empty; run terraform apply first")

rows = []
for key, suffix in (
    ("server_public_ip", "server"),
    ("database_public_ip", "database"),
    ("jobrunner_public_ip", "jobrunner"),
    ("monitor_public_ip", "monitor"),
):
    if value(key):
        rows.append((f"{prefix}-{suffix}", value(key)))

for index, ip in enumerate(value("webapp_public_ips") or [], start=1):
    rows.append((f"{prefix}-webapp-{index}", ip))

for name, ip in rows:
    print(name, ip)
'
}

join_node() {
    local name="$1" ip="$2"
    echo "==> $name ($ip)"

    if [[ "$DRY_RUN" == true ]]; then
        echo "    [dry-run] would install Tailscale and join as $name"
        return 0
    fi

    # The key goes over stdin and into a 0600 file rather than the command
    # line, so it never appears in the remote process list.
    printf '%s?preauthorized=true&ephemeral=false' "$TAILSCALE_OAUTH_CLIENT_SECRET" \
        | ssh -o StrictHostKeyChecking=accept-new "ubuntu@$ip" \
            "sudo install -m 600 /dev/stdin /run/tailscale-authkey"

    ssh -o StrictHostKeyChecking=accept-new "ubuntu@$ip" \
        "sudo TS_TAG='$TAILSCALE_TAG' TS_NAME='$name' bash -s" <<'REMOTE'
set -euo pipefail
if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi
tailscale up \
    --auth-key="file:/run/tailscale-authkey" \
    --advertise-tags="$TS_TAG" \
    --hostname="$TS_NAME" \
    --ssh
rm -f /run/tailscale-authkey
tailscale status --self --peers=false || true
REMOTE
}

# Add the server's MagicDNS name to the k3s serving certificate.
#
# k3s merges every file in config.yaml.d, so this drops a new fragment in
# rather than rewriting a config file that may already have content. The
# serving certificate is generated once and cached in dynamic-cert.json;
# removing it makes k3s regenerate with the current SAN list on restart.
add_server_tls_san() {
    local ip="$1" san="$2"
    echo "==> adding TLS SAN $san to k3s"

    if [[ "$DRY_RUN" == true ]]; then
        echo "    [dry-run] would add SAN and restart k3s"
        return 0
    fi

    ssh -o StrictHostKeyChecking=accept-new "ubuntu@$ip" \
        "sudo SAN='$san' bash -s" <<'REMOTE'
set -euo pipefail

if openssl s_client -connect 127.0.0.1:6443 </dev/null 2>/dev/null \
    | openssl x509 -noout -text 2>/dev/null | grep -q "$SAN"; then
    echo "SAN already present - nothing to do"
    exit 0
fi

mkdir -p /etc/rancher/k3s/config.yaml.d
cat > /etc/rancher/k3s/config.yaml.d/10-tailscale.yaml <<EOF
tls-san:
  - $SAN
EOF

rm -f /var/lib/rancher/k3s/server/tls/dynamic-cert.json
echo "restarting k3s (API briefly unavailable; running workloads unaffected)"
systemctl restart k3s

for _ in $(seq 1 36); do
    if openssl s_client -connect 127.0.0.1:6443 </dev/null 2>/dev/null \
        | openssl x509 -noout -text 2>/dev/null | grep -q "$SAN"; then
        echo "SAN confirmed in serving certificate"
        exit 0
    fi
    sleep 5
done

echo "ERROR: $SAN is still not in the serving certificate after 3 minutes." >&2
echo "       The drop-in is at /etc/rancher/k3s/config.yaml.d/10-tailscale.yaml." >&2
echo "       Do NOT lock admin_ips to the tailnet - kubectl will not connect." >&2
exit 1
REMOTE
}

SERVER_NAME=""
SERVER_IP=""

while read -r name ip; do
    [[ -z "$name" ]] && continue
    join_node "$name" "$ip"
    if [[ "$name" == *-server ]]; then
        SERVER_NAME="$name"
        SERVER_IP="$ip"
    fi
done < <(nodes)

if [[ -z "$SERVER_IP" ]]; then
    echo "Error: no server node found in Terraform outputs" >&2
    exit 1
fi

add_server_tls_san "$SERVER_IP" "$SERVER_NAME.$TAILSCALE_TAILNET"

echo
echo "All nodes joined. Next:"
echo "  1. just get-kubeconfig     # rewrites the API address to the tailnet"
echo "  2. just --yes rkube get nodes"
echo "  3. Only once that works, set admin_ips = [\"100.64.0.0/10\"] and apply."
