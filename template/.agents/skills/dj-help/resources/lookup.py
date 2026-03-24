#!/usr/bin/env python3
# ruff: noqa: T201
"""Look up help for dj-* skills."""

from __future__ import annotations

import sys
from pathlib import Path

_MIN_FRONTMATTER_PARTS = 3
_MIN_ARGS = 2


def _skills_dir() -> Path:
    # Script lives at .agents/skills/dj-help/resources/lookup.py
    # Go up: resources/ -> dj-help/ -> skills/
    return Path(__file__).parent.parent.parent


def _parse_description(skill_dir: Path) -> str:
    """Extract the description field from a SKILL.md frontmatter block."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return ""
    content = skill_file.read_text()
    parts = content.split("---", _MIN_FRONTMATTER_PARTS - 1)
    if len(parts) < _MIN_FRONTMATTER_PARTS:
        return ""
    for line in parts[1].splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return ""


def list_commands() -> None:
    """Print all available dj-* commands with their one-line descriptions."""
    skills_dir = _skills_dir()
    commands = sorted(
        d for d in skills_dir.iterdir()
        if d.is_dir() and d.name.startswith("dj-")
    )
    if not commands:
        print("No dj-* commands found.")
        return
    print("Available commands:\n")
    for cmd_dir in commands:
        desc = _parse_description(cmd_dir)
        print(f"  /{cmd_dir.name:<28} {desc}")


def show_help(command: str) -> None:
    """Print the help file for a specific dj-* command."""
    if not command.startswith("dj-"):
        command = f"dj-{command}"
    skills_dir = _skills_dir()
    help_file = skills_dir / command / "resources" / "help.md"
    if not help_file.exists():
        print(f"No help found for /{command}.")
        available = sorted(
            d.name for d in skills_dir.iterdir()
            if d.is_dir() and d.name.startswith("dj-")
        )
        if available:
            print(f"\nAvailable commands: {', '.join(available)}")
        sys.exit(1)
    print(help_file.read_text().rstrip())


if __name__ == "__main__":
    if len(sys.argv) < _MIN_ARGS:
        list_commands()
    else:
        show_help(sys.argv[1])
