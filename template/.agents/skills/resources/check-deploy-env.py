# ruff: noqa: INP001, T201
"""Check presence of deployment environment variables.

Loads .env (takes precedence over shell environment), then reports missing
required and optional vars by name only — never prints values.

Usage:
    python .agents/skills/resources/check-deploy-env.py

Exit code 1 if any required vars are missing.
"""

import os
import sys
from pathlib import Path

# Load .env (overrides shell env for same keys)
try:
    for raw in Path(".env").read_text().splitlines():
        entry = raw.strip()
        if entry and not entry.startswith("#") and "=" in entry:
            k, _, v = entry.partition("=")
            os.environ[k.strip()] = v.strip()
except FileNotFoundError:
    pass

REQUIRED = ["HETZNER_TOKEN", "CLOUDFLARE_TOKEN"]
OPTIONAL = [
    "MAILGUN_API_KEY",
    "MAILGUN_DKIM_VALUE",
    "HETZNER_STORAGE_ACCESS_KEY",
    "HETZNER_STORAGE_SECRET_KEY",
    "SENTRY_DSN",
    "OTLP_ENDPOINT",
]

missing_req = [v for v in REQUIRED if not os.environ.get(v)]
missing_opt = [v for v in OPTIONAL if not os.environ.get(v)]

for v in missing_req:
    print(f"MISSING (required): {v}")
for v in missing_opt:
    print(f"MISSING (optional): {v}")

if not missing_req and not missing_opt:
    print("All deployment vars present")
elif not missing_req:
    print("Required vars: OK")

sys.exit(1 if missing_req else 0)
