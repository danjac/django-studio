#!/usr/bin/env -S uv run python
# ruff: noqa: T201, S603, S607
"""Print the template CHANGELOG entries added since this project's template commit.

Reads `_src_path` and `_commit` from .copier-answers.yml, clones the template
(without file contents) into a temporary directory, and prints the lines added
to CHANGELOG.md between `_commit` and the template's HEAD. Sections trimmed
from the end of the file show up as removed lines and are ignored.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

HOSTS = {
    "gh:": "https://github.com/",
    "gl:": "https://gitlab.com/",
}


def read_answers() -> dict[str, str]:
    """Return the private (underscore) keys from .copier-answers.yml."""
    answers = {}
    for line in Path(".copier-answers.yml").read_text().splitlines():
        key, sep, value = line.partition(":")
        if sep and key.startswith("_"):
            answers[key.strip()] = value.strip().strip("'\"")
    return answers


def resolve_source(src: str) -> str:
    """Expand Copier's gh:/gl: shorthands into clone URLs."""
    for prefix, url in HOSTS.items():
        if src.startswith(prefix):
            return f"{url}{src.removeprefix(prefix)}.git"
    return src


def git(repo: str, *args: str) -> subprocess.CompletedProcess:
    """Run a git command in repo without raising on failure."""
    return subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True, check=False
    )


answers = read_answers()
commit = answers.get("_commit", "")
source = resolve_source(answers.get("_src_path", ""))
if not commit or not source:
    print("No _commit or _src_path in .copier-answers.yml.")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmp:
    clone = subprocess.run(
        ["git", "clone", "-q", "--filter=blob:none", "--no-checkout", source, tmp],
        capture_output=True,
        text=True,
        check=False,
    )
    if clone.returncode:
        print(f"Could not clone the template from {source}:\n{clone.stderr}")
        sys.exit(1)
    if git(tmp, "cat-file", "-e", f"{commit}^{{commit}}").returncode:
        print(f"Template commit {commit} not found in {source}.")
        sys.exit(1)
    diff = git(tmp, "diff", "--no-color", "-U0", commit, "HEAD", "--", "CHANGELOG.md")

added = [
    line[1:]
    for line in diff.stdout.splitlines()
    if line.startswith("+") and not line.startswith("+++")
]
if any(line.strip() for line in added):
    print("\n".join(added).strip())
else:
    print(f"No changelog entries since template commit {commit}.")
