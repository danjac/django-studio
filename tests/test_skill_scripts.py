"""Tests for Python helper scripts in template/.agents/skills/scripts/."""

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
        [f".agents/skills/scripts/{script}"],
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


class TestDjHelpLookup:
    script = ".agents/skills/dj-help/scripts/lookup.py"

    def run(self, project: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self.script, *args],
            cwd=str(project),
            capture_output=True,
            text=True,
        )

    def test_lists_all_commands(self, project_with_deps: Path) -> None:
        result = self.run(project_with_deps)
        assert result.returncode == 0
        assert "/dj-deploy" in result.stdout

    def test_shows_help_for_exact_name(self, project_with_deps: Path) -> None:
        result = self.run(project_with_deps, "dj-deploy")
        assert result.returncode == 0
        assert "**/dj-deploy**" in result.stdout

    def test_shows_help_for_suffix_match(self, project_with_deps: Path) -> None:
        result = self.run(project_with_deps, "a11y")
        assert result.returncode == 0
        assert "**/dj-a11y**" in result.stdout

    def test_unknown_name_exits_nonzero(self, project_with_deps: Path) -> None:
        result = self.run(project_with_deps, "nope-not-a-skill")
        assert result.returncode == 1
        assert "No skill found" in result.stdout
