#!/usr/bin/env bash
# Install or upgrade a Helm chart on the production cluster.
# Usage: helm.sh <kubeconfig> <chart>
# Example: helm.sh ~/.kube/my_app.yaml site
set -euo pipefail

KUBECONFIG_PATH="$1"
CHART="$2"

if [[ ! -f "$KUBECONFIG_PATH" ]]; then
    echo "Error: kubeconfig not found at $KUBECONFIG_PATH"
    echo "Provision the cluster first, then run: just get-kubeconfig"
    exit 1
fi

helm dependency build "helm/$CHART/"
helm upgrade --install "$CHART" "helm/$CHART/" \
    --kubeconfig "$KUBECONFIG_PATH" \
    --reuse-values \
    -f "helm/$CHART/values.yaml" \
    -f "helm/$CHART/values.secret.yaml"
