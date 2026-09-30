#!/usr/bin/env bash
# Install Python dependencies, keeping to uv.lock when it exists.
set -euo pipefail

if [ -f uv.lock ]; then
    uv sync --frozen --all-extras --no-install-project
else
    uv sync --all-extras --no-install-project
fi
