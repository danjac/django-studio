#!/usr/bin/env -S uv run python
# ruff: noqa: T201
"""Print the backup directory for this project's pre-sync snapshots.

The post-gen hook backs up generated config files to
<tmpdir>/<project_slug>/ before running copier update.
This script prints that directory so dj-sync can diff the snapshots.
"""

import tempfile
from pathlib import Path

import yaml

answers = yaml.safe_load(Path(".copier-answers.yml").read_text())
slug = answers["project_slug"]
print(Path(tempfile.gettempdir()) / slug)
