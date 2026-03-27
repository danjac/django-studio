#!/usr/bin/env -S uv run python
# ruff: noqa: T201, INP001
"""Look up help for skills in .agents/skills/."""

from __future__ import annotations

import sys
from pathlib import Path

_MIN_ARGS = 2


def _skills_dir() -> Path:
    # Script lives at .agents/skills/<name>/resources/lookup.py
    # Go up: resources/ -> <name>/ -> skills/
    return Path(__file__).parent.parent.parent


def _is_skill(path: Path) -> bool:
    """Return True if the path is a skill directory (contains SKILL.md)."""
    return path.is_dir() and (path / "SKILL.md").exists()


def _has_help(skill_dir: Path) -> bool:
    """Return True if the skill has a resources/help.md file."""
    return (skill_dir / "resources" / "help.md").exists()


def _print_help(skill_dir: Path) -> None:
    """Print the resources/help.md for a skill."""
    print((skill_dir / "resources" / "help.md").read_text().rstrip())


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
    if _is_skill(exact) and _has_help(exact):
        _print_help(exact)
        return
    # Suffix match: e.g. "a11y" finds "dj-a11y"
    matches = [d for d in skills_dir.iterdir() if _is_skill(d) and d.name.endswith(name)]
    if len(matches) == 1 and _has_help(matches[0]):
        _print_help(matches[0])
        return
    if not matches:
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
