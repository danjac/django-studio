"""Headless `claude -p` runs: the build agent and the independent reviewer."""

# ruff: noqa: S603, S607

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

from cases import REPO_DIR
from setup import BASELINE_TAG

if TYPE_CHECKING:
    from pathlib import Path

    from cases import Case

PLUGIN_DIR = REPO_DIR / "plugin"

BUILD_TIMEOUT = 60 * 60
REVIEW_TIMEOUT = 20 * 60

NO_ISSUES = "No issues found."

UNATTENDED = """

---

This is an unattended evaluation run. Nobody will answer questions or confirm
steps. Every answer the skill would ask for is given above: apply those answers
and carry on through every step without stopping. Where the skill asks something
not answered above, take its stated default."""

REVIEW_RULES = f"""

---

You are an independent reviewer. You did not build this project and have no
knowledge of how it was built. Your tools are read-only.

Files changed since the baseline commit, including any commits made during the run:

```
{{changed_files}}
```

Rules:

- Verify each fact listed above by reading the files. For every fact, quote the
  literal text you read that confirms or contradicts it.
- Report only real defects: code that would not run or boot, a listed fact that
  does not hold, or a security hole. No style notes, no suggestions, no nitpicks.
- End your reply with either a list of defects under the heading `DEFECTS:`, or
  the exact line `{NO_ISSUES}` on its own as the last line."""


def run_build(
    case: Case,
    project: Path,
    transcript: Path,
    model: str | None,
    env: dict[str, str],
) -> str:
    """Run the case prompt headless; return the agent's final message."""
    command = [
        "claude",
        "-p",
        case.prompt + UNATTENDED,
        "--dangerously-skip-permissions",
        "--setting-sources",
        "project",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--output-format",
        "stream-json",
        "--verbose",
        "--plugin-dir",
        str(PLUGIN_DIR),
    ]
    if model:
        command += ["--model", model]
    with transcript.open("w") as out:
        subprocess.run(
            command,
            cwd=project,
            env=env,
            stdout=out,
            stderr=subprocess.STDOUT,
            timeout=BUILD_TIMEOUT,
            check=False,
        )
    for line in reversed(transcript.read_text().splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            return event.get("result") or ""
    return ""


def run_review(case: Case, project: Path, build_output: str, model: str | None) -> str:
    """Run the independent reviewer; return its reply."""
    if case.bootstrap:
        changed = "(new project: every file was generated in this run)"
    else:
        changed = changed_files(project)
    prompt = (case.review + REVIEW_RULES).replace(
        "{changed_files}", changed or "(none)"
    )
    prompt = prompt.replace("{build_output}", build_output)
    command = [
        "claude",
        "-p",
        prompt,
        "--tools",
        "Read,Grep,Glob",
        "--setting-sources",
        "",
        "--strict-mcp-config",
        "--no-session-persistence",
    ]
    if model:
        command += ["--model", model]
    review = subprocess.run(
        command,
        cwd=project,
        capture_output=True,
        text=True,
        timeout=REVIEW_TIMEOUT,
        check=False,
    )
    return review.stdout.strip() or review.stderr.strip()


def changed_files(project: Path) -> str:
    """List files changed since the baseline tag, committed or not, and new files."""

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=project,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    changed = git("diff", "--name-status", BASELINE_TAG)
    untracked = git("ls-files", "--others", "--exclude-standard")
    return (
        changed + "".join(f"A\t{path}\n" for path in untracked.splitlines())
    ).strip()


def last_line(text: str) -> str:
    """Return the last non-empty line of text, stripped."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""
