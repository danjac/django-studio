# ruff: noqa: INP001, T201
"""Check presence of deployment environment variables.

Loads .env (non-empty values take precedence over shell; empty placeholders
like KEY= fall back to the shell value). Reports missing required and
optional vars by name only — never prints values.

Usage:
    uv run python .agents/skills/resources/check-deploy-env.py

Exit code 1 if any required vars are missing.
"""

import os
import sys

from dotenv import dotenv_values
from environs import Env

# Merge .env into the environment: non-empty .env values win over shell;
# empty placeholders (KEY=) are skipped so they don't clobber real shell values.
for key, val in dotenv_values(".env").items():
    if val:
        os.environ[key] = val

env = Env()

REQUIRED = ["HETZNER_TOKEN", "CLOUDFLARE_TOKEN"]
OPTIONAL = [
    "MAILGUN_API_KEY",
    "MAILGUN_DKIM_VALUE",
    "HETZNER_STORAGE_ACCESS_KEY",
    "HETZNER_STORAGE_SECRET_KEY",
    "SENTRY_DSN",
    "OTLP_ENDPOINT",
]

missing_req = [v for v in REQUIRED if not env.str(v, default="")]
missing_opt = [v for v in OPTIONAL if not env.str(v, default="")]

for v in missing_req:
    print(f"MISSING (required): {v}")
for v in missing_opt:
    print(f"MISSING (optional): {v}")

if not missing_req and not missing_opt:
    print("All deployment vars present")
elif not missing_req:
    print("Required vars: OK")

sys.exit(1 if missing_req else 0)
