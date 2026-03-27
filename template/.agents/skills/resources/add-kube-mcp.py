# ruff: noqa: INP001, T201
"""Add the Kubernetes MCP server entry to .mcp.json.

Idempotent — safe to run multiple times. Does nothing if the entry
already exists with a non-empty configuration.

Sets KUBECONFIG to ~/.kube/<project_slug>.yaml so the MCP server
uses the project-specific kubeconfig instead of the default context.

Usage:
    uv run python .agents/skills/resources/add-kube-mcp.py
"""

import json
import re
from pathlib import Path

MCP_FILE = Path(".mcp.json")
COPIER_ANSWERS = Path(".copier-answers.yml")


def get_project_slug() -> str:
    """Read project_slug from .copier-answers.yml."""
    text = COPIER_ANSWERS.read_text()
    match = re.search(r"^project_slug:\s*(.+)$", text, re.MULTILINE)
    if not match:
        msg = "project_slug not found in .copier-answers.yml"
        raise ValueError(msg)
    return match.group(1).strip()


slug = get_project_slug()
kubeconfig_path = f"~/.kube/{slug}.yaml"

config = json.loads(MCP_FILE.read_text())
servers = config.setdefault("mcpServers", {})

if servers.get("kubernetes"):
    print("kubernetes MCP server already configured — skipping")
else:
    servers["kubernetes"] = {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "env": {
            "KUBECONFIG": kubeconfig_path,
        },
    }
    MCP_FILE.write_text(json.dumps(config, indent=2) + "\n")
    print(f"kubernetes MCP server added to .mcp.json (KUBECONFIG={kubeconfig_path})")
