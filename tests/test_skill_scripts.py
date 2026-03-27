"""Tests for Python helper scripts in template/.agents/skills/bin/."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def run_script(
    script: str,
    project: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "python", f".agents/skills/bin/{script}"],
        cwd=str(project),
        capture_output=True,
        text=True,
        env=env,
    )


class TestAddKubeMcp:
    script = "add-kube-mcp.py"

    def _write_mcp(self, project: Path, config: dict) -> None:
        (project / ".mcp.json").write_text(json.dumps(config))

    def _read_mcp(self, project: Path) -> dict:
        return json.loads((project / ".mcp.json").read_text())

    def test_adds_kubernetes_server(self, project_with_deps: Path) -> None:
        self._write_mcp(project_with_deps, {"mcpServers": {"postgres": {}}})
        result = run_script(self.script, project_with_deps)
        assert result.returncode == 0
        config = self._read_mcp(project_with_deps)
        assert config["mcpServers"]["kubernetes"] == {
            "command": "npx",
            "args": ["-y", "mcp-server-kubernetes"],
            "env": {"KUBECONFIG": "~/.kube/test_project.yaml"},
        }

    def test_idempotent_when_already_configured(self, project_with_deps: Path) -> None:
        existing = {
            "mcpServers": {
                "kubernetes": {
                    "command": "npx",
                    "args": ["-y", "mcp-server-kubernetes"],
                }
            }
        }
        self._write_mcp(project_with_deps, existing)
        result = run_script(self.script, project_with_deps)
        assert result.returncode == 0
        assert "skipping" in result.stdout
        assert self._read_mcp(project_with_deps) == existing

    def test_preserves_existing_servers(self, project_with_deps: Path) -> None:
        self._write_mcp(
            project_with_deps, {"mcpServers": {"postgres": {"command": "sh"}}}
        )
        run_script(self.script, project_with_deps)
        config = self._read_mcp(project_with_deps)
        assert "postgres" in config["mcpServers"]
        assert "kubernetes" in config["mcpServers"]


class TestRandomSlug:
    script = "random-slug.py"

    def test_outputs_valid_slug(self, project_with_deps: Path) -> None:
        result = run_script(self.script, project_with_deps)
        assert result.returncode == 0
        assert re.fullmatch(r"[a-z]+-[a-z]+", result.stdout.strip())
