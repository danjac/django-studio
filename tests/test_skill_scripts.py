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
    script = ".agents/skills/djs-help/scripts/lookup.py"

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
        assert "/djs-deploy" in result.stdout

    def test_shows_help_for_exact_name(self, project_with_deps: Path) -> None:
        result = self.run(project_with_deps, "djs-deploy")
        assert result.returncode == 0
        assert "**/djs-deploy**" in result.stdout

    def test_shows_help_for_suffix_match(self, project_with_deps: Path) -> None:
        result = self.run(project_with_deps, "a11y")
        assert result.returncode == 0
        assert "**/djs-a11y**" in result.stdout

    def test_unknown_name_exits_nonzero(self, project_with_deps: Path) -> None:
        result = self.run(project_with_deps, "nope-not-a-skill")
        assert result.returncode == 1
        assert "No skill found" in result.stdout


class TestDjSyncChangelogSince:
    script = (
        Path(__file__).parent.parent
        / "template/.agents/skills/djs-sync/scripts/changelog-since.py"
    )

    @staticmethod
    def git(repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def commit_changelog(self, repo: Path, content: str) -> str:
        (repo / "CHANGELOG.md").write_text(content)
        self.git(repo, "add", "CHANGELOG.md")
        self.git(repo, "commit", "-q", "-m", "changelog")
        return self.git(repo, "rev-parse", "--short", "HEAD")

    def run(self, project: Path, template: Path, commit: str):
        (project / ".copier-answers.yml").write_text(
            f"_commit: {commit}\n_src_path: {template}\nproject_name: X\n"
        )
        return subprocess.run(
            [str(self.script)], cwd=str(project), capture_output=True, text=True
        )

    def make_repos(self, tmp_path: Path) -> tuple[Path, Path]:
        template = tmp_path / "template"
        project = tmp_path / "project"
        template.mkdir()
        project.mkdir()
        self.git(template, "init", "-q")
        return template, project

    def test_shows_entries_added_since_commit(self, tmp_path: Path) -> None:
        template, project = self.make_repos(tmp_path)
        old = self.commit_changelog(
            template,
            "# Changelog\n\n## 26.39.5 - 2026-09-25\n\n### Fixed\n\n- Old fix\n",
        )
        self.commit_changelog(
            template,
            "# Changelog\n\n## 26.39.6 - 2026-09-26\n\n### Added\n\n- New thing\n\n"
            "## 26.39.5 - 2026-09-25\n\n### Fixed\n\n- Old fix\n",
        )
        result = self.run(project, template, old)
        assert result.returncode == 0, result.stderr
        assert "## 26.39.6 - 2026-09-26" in result.stdout
        assert "- New thing" in result.stdout
        assert "Old fix" not in result.stdout

    def test_up_to_date(self, tmp_path: Path) -> None:
        template, project = self.make_repos(tmp_path)
        head = self.commit_changelog(template, "# Changelog\n\n## 26.39.6\n\n- A\n")
        result = self.run(project, template, head)
        assert result.returncode == 0, result.stderr
        assert "No changelog entries" in result.stdout

    def test_unknown_commit(self, tmp_path: Path) -> None:
        template, project = self.make_repos(tmp_path)
        self.commit_changelog(template, "# Changelog\n")
        result = self.run(project, template, "deadbeef")
        assert result.returncode == 1
        assert "deadbeef" in result.stdout
