#!/usr/bin/env -S uv run python
# ruff: noqa: T201, S603, S607
"""Print all HTML templates with no references anywhere in the codebase.

Searches .py and .html files for the template path string, catching all
reference forms: TemplateResponse, render_to_string, render(), {% extends %},
{% include %}, {% fragment %}, {% partial "file#name" %}, etc.

Skips base/layout templates (basename starts with 'base' or '_') since
these are extended rather than referenced by name.
"""

import subprocess
from pathlib import Path

templates_dir = Path("templates")
project_dir = Path()

for path in sorted(templates_dir.rglob("*.html")):
    basename = path.name
    if basename.startswith(("base", "_")):
        continue
    name = str(path.relative_to(templates_dir))
    result = subprocess.run(
        [
            "grep",
            "-r",
            "--include=*.html",
            "--include=*.py",
            "-l",
            name,
            str(project_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    hits = [
        line
        for line in result.stdout.splitlines()
        if Path(line).resolve() != path.resolve()
    ]
    if not hits:
        print(name)
