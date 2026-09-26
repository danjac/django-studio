"""Tests for the Claude Code plugin: marketplace manifest and the /dj-bootstrap skill."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN_DIR = ROOT / "plugin"
DJ_BOOTSTRAP = PLUGIN_DIR / "skills" / "dj-bootstrap" / "SKILL.md"


def _copier_questions() -> dict:
    config = yaml.safe_load((ROOT / "copier.yml").read_text())
    return {key: value for key, value in config.items() if not key.startswith("_")}


class TestMarketplace:
    def test_plugin_source_points_at_plugin_dir(self):
        marketplace = json.loads(MARKETPLACE.read_text())
        [entry] = marketplace["plugins"]
        source = entry["source"]
        assert source["source"] == "git-subdir"
        assert source["url"] == "danjac/django-studio"
        assert (ROOT / source["path"]).resolve() == PLUGIN_DIR.resolve()

    def test_entry_name_matches_plugin_manifest(self):
        marketplace = json.loads(MARKETPLACE.read_text())
        manifest = json.loads(
            (PLUGIN_DIR / ".claude-plugin" / "plugin.json").read_text()
        )
        assert marketplace["plugins"][0]["name"] == manifest["name"]

    @pytest.mark.skipif(
        shutil.which("claude") is None, reason="claude CLI not installed"
    )
    @pytest.mark.parametrize("path", [ROOT, PLUGIN_DIR], ids=["marketplace", "plugin"])
    def test_claude_plugin_validate(self, path):
        result = subprocess.run(
            ["claude", "plugin", "validate", str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


class TestPluginSkills:
    @pytest.mark.parametrize(
        "skill_dir",
        sorted((PLUGIN_DIR / "skills").iterdir()),
        ids=lambda path: path.name,
    )
    def test_skill_layout(self, skill_dir):
        text = (skill_dir / "SKILL.md").read_text()
        match = re.match(r"---\n(.+?)\n---\n", text, re.DOTALL)
        assert match, "SKILL.md must start with a frontmatter block"
        frontmatter = yaml.safe_load(match.group(1))
        assert len(frontmatter["description"]) <= 80
        assert (skill_dir / "references" / "help.md").is_file()


class TestDjBootstrapMatchesCopier:
    """The skill passes Copier answers by name, so it must track copier.yml."""

    def test_passes_every_copier_question(self):
        text = DJ_BOOTSTRAP.read_text()
        for question in _copier_questions():
            assert f"--data {question}=" in text, (
                f"{question} missing from dj-bootstrap"
            )

    def test_lists_every_license_choice(self):
        text = DJ_BOOTSTRAP.read_text()
        choices = _copier_questions()["license"]["choices"]
        assert f"One of: {', '.join(choices)}" in text
