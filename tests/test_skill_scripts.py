"""Tests for Python helper scripts in template/.agents/skills/resources/."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def no_dotenv(project_with_deps: Path):
    """Remove .env before and after each test to prevent state leakage."""
    dotenv = project_with_deps / ".env"
    dotenv.unlink(missing_ok=True)
    yield
    dotenv.unlink(missing_ok=True)


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


class TestCheckDeployEnv:
    script = "check-deploy-env.py"

    def test_exits_1_when_required_vars_absent(self, project_with_deps: Path) -> None:
        result = run_script(self.script, project_with_deps)
        assert result.returncode == 1
        assert "MISSING (required): HETZNER_TOKEN" in result.stdout
        assert "MISSING (required): CLOUDFLARE_TOKEN" in result.stdout

    def test_exits_0_when_dotenv_has_required_vars(
        self, project_with_deps: Path
    ) -> None:
        (project_with_deps / ".env").write_text(
            "HETZNER_TOKEN=tok-hetzner\nCLOUDFLARE_TOKEN=tok-cloudflare\n"
        )
        result = run_script(self.script, project_with_deps)
        assert result.returncode == 0

    def test_empty_dotenv_value_falls_back_to_shell(
        self, project_with_deps: Path
    ) -> None:
        (project_with_deps / ".env").write_text("HETZNER_TOKEN=\nCLOUDFLARE_TOKEN=\n")
        env = {
            **os.environ,
            "HETZNER_TOKEN": "tok-hetzner",
            "CLOUDFLARE_TOKEN": "tok-cloudflare",
        }
        result = run_script(self.script, project_with_deps, env=env)
        assert result.returncode == 0

    def test_reports_missing_var_by_name_not_value(
        self, project_with_deps: Path
    ) -> None:
        (project_with_deps / ".env").write_text("CLOUDFLARE_TOKEN=tok-cf\n")
        result = run_script(self.script, project_with_deps)
        assert "MISSING (required): HETZNER_TOKEN" in result.stdout
        assert "tok-cf" not in result.stdout


class TestRandomSlug:
    script = "random-slug.py"

    def test_outputs_valid_slug(self, project_with_deps: Path) -> None:
        result = run_script(self.script, project_with_deps)
        assert result.returncode == 0
        assert re.fullmatch(r"[a-z]+-[a-z]+", result.stdout.strip())
