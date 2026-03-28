#!/usr/bin/env -S uv run python
# ruff: noqa: T201
"""Print the most recent backup directory for pre-sync snapshots.

The post-gen hook backs up generated config files to .backups/<n>/
(incrementing integers) preserving their relative paths. This script
prints the highest-numbered directory so dj-sync can diff each file
against its counterpart in the project root.
"""

from pathlib import Path

backup_root = Path(".backups")
if backup_root.exists():
    dirs = [d for d in backup_root.iterdir() if d.is_dir() and d.name.isdigit()]
    if dirs:
        print(max(dirs, key=lambda d: int(d.name)))
