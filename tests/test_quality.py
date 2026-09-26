"""Slow integration tests: pre-commit hooks and type checking on the rendered project."""

from __future__ import annotations

import os
import subprocess

import pytest


class TestRenderedPreCommitChecks:
    """Verify the rendered project passes all pre-commit hooks."""

    def test_pre_commit_passes(self, project_with_deps):
        # Skip terraform_validate: runs `terraform init` which downloads providers
        # — unreliable in a test context (network, disk quota). All other hooks
        # including terraform_fmt and helm-lint are exercised here.
        env = {"SKIP": "terraform_validate"}
        # The first run must be clean: template sources are already formatted,
        # so no auto-fixer (pyupgrade, ruff-format, djhtml, etc.) may modify a file.
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
            f"pre-commit failed on the first run:\n{result.stdout}\n{result.stderr}"
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


DEPLOYMENT_TOOLS = ("helm", "terraform")
DEPLOYMENT_HOOKS = ("helm-lint", "terraform_fmt", "terraform_validate")


@pytest.fixture(scope="module")
def path_without_deployment_tools(tmp_path_factory):
    """A PATH with every executable on the current PATH except Helm and Terraform."""
    shadow = tmp_path_factory.mktemp("bin")
    for directory in os.environ["PATH"].split(os.pathsep):
        if not os.path.isdir(directory):
            continue
        for entry in os.scandir(directory):
            target = shadow / entry.name
            if entry.name in DEPLOYMENT_TOOLS or target.exists():
                continue
            if os.access(entry.path, os.X_OK):
                target.symlink_to(entry.path)
    return str(shadow)


class TestDeploymentHooksWithoutTools:
    """Helm and Terraform hooks skip locally when the tool is missing, but not in CI."""

    def _run_hook(self, project, path, hook, *, ci):
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        env["PATH"] = path
        if ci:
            env["CI"] = "true"
        return subprocess.run(
            ["uv", "run", "--with", "pre-commit-uv", "pre-commit", "run", hook],
            cwd=str(project),
            capture_output=True,
            text=True,
            env=env,
        )

    @pytest.mark.parametrize("hook", DEPLOYMENT_HOOKS)
    def test_skips_locally(
        self, project_with_deps, path_without_deployment_tools, hook
    ):
        result = self._run_hook(
            project_with_deps, path_without_deployment_tools, hook, ci=False
        )
        assert result.returncode == 0, result.stdout + result.stderr

    @pytest.mark.parametrize("hook", DEPLOYMENT_HOOKS)
    def test_fails_in_ci(self, project_with_deps, path_without_deployment_tools, hook):
        result = self._run_hook(
            project_with_deps, path_without_deployment_tools, hook, ci=True
        )
        assert result.returncode != 0, result.stdout + result.stderr
