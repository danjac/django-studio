"""Check presence of deployment environment variables.

Loads .env (takes precedence over shell environment), then reports missing
required and optional vars by name only — never prints values.

Usage:
    python .agents/skills/resources/check-deploy-env.py

Exit code 1 if any required vars are missing.
"""

import os
import sys

# Load .env (overrides shell env for same keys)
try:
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
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
