"""Tests for Python helper scripts in template/.agents/skills/resources/."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def run_script(
    script: str,
    project: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "python", f".agents/skills/resources/{script}"],
        cwd=str(project),
        capture_output=True,
        text=True,
        env=env,
    )


class TestRandomSlug:
    script = "random-slug.py"

    def test_outputs_valid_slug(self, project_with_deps: Path) -> None:
        result = run_script(self.script, project_with_deps)
        assert result.returncode == 0
        assert re.fullmatch(r"[a-z]+-[a-z]+", result.stdout.strip())
