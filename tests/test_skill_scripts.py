"""Tests for Python helper scripts in template/.agents/skills/resources/."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_VARS = {"HETZNER_TOKEN": "tok-hetzner", "CLOUDFLARE_TOKEN": "tok-cloudflare"}


def _base_env() -> dict[str, str]:
    """Current environment stripped of any deployment vars that could interfere."""
    return {
        k: v
        for k, v in os.environ.items()
        if k not in {"HETZNER_TOKEN", "CLOUDFLARE_TOKEN"}
    }


def _run(
    script: str, project: Path, extra_env: dict | None = None
) -> subprocess.CompletedProcess:
    env = _base_env()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["uv", "run", "python", f".agents/skills/resources/{script}"],
        cwd=str(project),
        capture_output=True,
        text=True,
        env=env,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_dotenv(project_with_deps: Path):
    """Remove .env before and after each test to prevent state leakage."""
    dotenv = project_with_deps / ".env"
    dotenv.unlink(missing_ok=True)
    yield
    dotenv.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# check-deploy-env.py
# ---------------------------------------------------------------------------


class TestCheckDeployEnv:
    script = "check-deploy-env.py"

    def test_exits_1_when_required_vars_absent(self, project_with_deps: Path) -> None:
        result = _run(self.script, project_with_deps)
        assert result.returncode == 1
        assert "MISSING (required): HETZNER_TOKEN" in result.stdout
        assert "MISSING (required): CLOUDFLARE_TOKEN" in result.stdout

    def test_exits_0_when_required_vars_in_shell_env(
        self, project_with_deps: Path
    ) -> None:
        result = _run(self.script, project_with_deps, extra_env=REQUIRED_VARS)
        assert result.returncode == 0

    def test_dotenv_values_take_precedence_over_shell(
        self, project_with_deps: Path
    ) -> None:
        # Shell has no tokens; .env has them — should pass
        (project_with_deps / ".env").write_text(
            "HETZNER_TOKEN=tok-from-dotenv\nCLOUDFLARE_TOKEN=tok-cf-dotenv\n"
        )
        result = _run(self.script, project_with_deps)
        assert result.returncode == 0

    def test_empty_dotenv_value_falls_back_to_shell(
        self, project_with_deps: Path
    ) -> None:
        # .env has empty placeholders; real tokens are in shell env — must not false-positive
        (project_with_deps / ".env").write_text("HETZNER_TOKEN=\nCLOUDFLARE_TOKEN=\n")
        result = _run(self.script, project_with_deps, extra_env=REQUIRED_VARS)
        assert result.returncode == 0

    def test_reports_missing_var_by_name_only(self, project_with_deps: Path) -> None:
        # Only CF token set; HZ token missing — output must name the var, not print any value
        result = _run(
            self.script, project_with_deps, extra_env={"CLOUDFLARE_TOKEN": "tok-cf"}
        )
        assert "MISSING (required): HETZNER_TOKEN" in result.stdout
        assert "tok-cf" not in result.stdout


# ---------------------------------------------------------------------------
# random-slug.py
# ---------------------------------------------------------------------------


class TestRandomSlug:
    script = "random-slug.py"

    def test_outputs_valid_slug(self, project_with_deps: Path) -> None:
        result = _run(self.script, project_with_deps)
        assert result.returncode == 0
        assert re.fullmatch(r"[a-z]+-[a-z]+", result.stdout.strip())
