"""Slow integration tests: pre-commit hooks and type checking on the rendered project."""

from __future__ import annotations

import os
import subprocess


class TestRenderedPreCommitChecks:
    """Verify the rendered project passes all pre-commit hooks."""

    def test_pre_commit_passes(self, project_with_deps):
        # Skip terraform_validate: runs `terraform init` which downloads providers
        # — unreliable in a test context (network, disk quota). All other hooks
        # including terraform_fmt and helm-lint are exercised here.
        env = {"SKIP": "terraform_validate"}
        # Run twice to let auto-fixers (pyupgrade, ruff-format, etc.) reach idempotency
        for _ in range(2):
            subprocess.run(
                [
                    "uv",
                    "run",
                    "--with",
                    "pre-commit-uv",
                    "pre-commit",
                    "run",
                    "--all-files",
                ],
                cwd=str(project_with_deps),
                capture_output=True,
                text=True,
                env={**os.environ, **env},
            )
        # Third run must be fully clean
        result = subprocess.run(
            [
                "uv",
                "run",
                "--with",
                "pre-commit-uv",
                "pre-commit",
                "run",
                "--all-files",
            ],
            cwd=str(project_with_deps),
            capture_output=True,
            text=True,
            env={**os.environ, **env},
        )
        assert result.returncode == 0, (
            f"pre-commit failed after auto-fix passes:\n{result.stdout}\n{result.stderr}"
        )


class TestRenderedPythonTypeCheck:
    """Verify the rendered project passes basedpyright type checking."""

    def test_python_files_pass_basedpyright(self, project_with_deps):
        result = subprocess.run(
            ["uv", "run", "basedpyright"],
            cwd=str(project_with_deps),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"basedpyright failed:\n{result.stdout}\n{result.stderr}"
        )


class TestRenderedUnitTests:
    """Verify the rendered project's unit tests pass (no database required)."""

    def test_unit_tests_pass(self, project_with_deps):
        result = subprocess.run(
            ["uv", "run", "pytest", "-m", "not django_db", "-q", "--tb=short"],
            cwd=str(project_with_deps),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"pytest failed:\n{result.stdout}\n{result.stderr}"
        )
