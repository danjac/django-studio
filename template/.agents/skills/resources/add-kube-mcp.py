# ruff: noqa: INP001, T201
"""Add the Kubernetes MCP server entry to .mcp.json.

Idempotent — safe to run multiple times. Does nothing if the entry
already exists with a non-empty configuration.

Usage:
    uv run python .agents/skills/resources/add-kube-mcp.py
"""

import json
from pathlib import Path

MCP_FILE = Path(".mcp.json")

config = json.loads(MCP_FILE.read_text())
servers = config.setdefault("mcpServers", {})

if servers.get("kubernetes"):
    print("kubernetes MCP server already configured — skipping")
else:
    servers["kubernetes"] = {
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
    }
    MCP_FILE.write_text(json.dumps(config, indent=2) + "\n")
    print("kubernetes MCP server added to .mcp.json")
