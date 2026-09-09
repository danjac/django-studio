#!/usr/bin/env -S uv run python
# ruff: noqa: T201
"""Look up help for skills in .agents/skills/."""

from __future__ import annotations

import sys
from pathlib import Path

_MIN_ARGS = 2


def _skills_dir() -> Path:
    # Script lives at .agents/skills/<name>/scripts/lookup.py
    # Go up: scripts/ -> <name>/ -> skills/
    return Path(__file__).parent.parent.parent


def _is_skill(path: Path) -> bool:
    """Return True if the path is a skill directory (contains SKILL.md)."""
    return path.is_dir() and (path / "SKILL.md").exists()


def _help_file(skill_dir: Path) -> Path:
    return skill_dir / "references" / "help.md"


def _has_help(skill_dir: Path) -> bool:
    """Return True if the skill has a references/help.md file."""
    return _help_file(skill_dir).exists()


def _print_help(skill_dir: Path) -> None:
    """Print the references/help.md for a skill."""
    print(_help_file(skill_dir).read_text().rstrip())


def list_commands() -> None:
    """Print all available skills."""
    skills_dir = _skills_dir()
    skills = sorted(d.name for d in skills_dir.iterdir() if _is_skill(d))
    if not skills:
        print("No skills found.")
        return
    print("Available commands:\n")
    for name in skills:
        print(f"  /{name}")


def show_help(name: str) -> None:
    """Print help for a skill, matched by exact name or unique suffix."""
    skills_dir = _skills_dir()
    # Exact match
    exact = skills_dir / name
    matches = [exact] if _is_skill(exact) else []
    if not matches:
        # Suffix match: e.g. "a11y" finds "dj-a11y"
        matches = [
            d for d in skills_dir.iterdir() if _is_skill(d) and d.name.endswith(name)
        ]
    if len(matches) == 1:
        skill_dir = matches[0]
        if _has_help(skill_dir):
            _print_help(skill_dir)
            return
        print(f"No help available for '{skill_dir.name}' (missing references/help.md).")
    elif not matches:
        print(f"No skill found matching '{name}'.")
    else:
        names = ", ".join(d.name for d in sorted(matches))
        print(f"Ambiguous: '{name}' matches multiple skills: {names}")
    available = sorted(d.name for d in skills_dir.iterdir() if _is_skill(d))
    if available:
        print(f"\nAvailable: {', '.join(available)}")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < _MIN_ARGS:
        list_commands()
    else:
        show_help(sys.argv[1])
