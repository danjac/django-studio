#!/usr/bin/env -S uv run python
# ruff: noqa: T201
"""Print named URL patterns with no references in templates or Python files.

Collects all name=... entries from urls.py files, then scans all .html and
.py files for {% url 'name' %}, reverse('name'), and redirect('name') usages.
Reports any name that appears in no reference.
"""

import re
from pathlib import Path


def is_project_file(path: Path) -> bool:
    """Return True if path is not inside a dependency directory."""
    return ".venv" not in path.parts and "node_modules" not in path.parts


# Collect all named URL patterns: name -> "file:line"
url_names: dict[str, str] = {}
for path in Path().rglob("urls.py"):
    if not is_project_file(path):
        continue
    for i, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
        m = re.search(r"name=['\"]([^'\"]+)['\"]", line)
        if m:
            url_names[m.group(1)] = f"{path}:{i}"

# Collect all references across templates and Python
referenced: set[str] = set()
for pattern in ("**/*.html", "**/*.py"):
    for path in Path().glob(pattern):
        if not is_project_file(path):
            continue
        try:
            content = path.read_text(errors="ignore")
        except OSError:
            continue
        # {% url 'name' %} / {% url "name" %} — may be namespaced (e.g. 'projects:dashboard')
        for ref in re.findall(r"""\{%[-\s]*url\s+['"]([^'"]+)['"]""", content):
            referenced.add(ref.rsplit(":", 1)[-1])
        # reverse and redirect calls
        for ref in re.findall(r"""(?:reverse|redirect)\s*\(\s*['"]([^'"]+)['"]""", content):
            referenced.add(ref.rsplit(":", 1)[-1])

# Report unreferenced
for name, loc in sorted(url_names.items()):
    if name not in referenced:
        print(f"{name}  ({loc})")
