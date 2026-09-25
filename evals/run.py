#!/usr/bin/env -S uv run python
"""End-to-end eval runner for the dj-* skills.

Each case in evals/cases/ is run in four phases:

1. Setup  - render a fresh project, start services, install, migrate, run the
            case's optional setup block, commit a baseline.
2. Build  - run the case prompt with a headless `claude -p` in the project.
3. Check  - run the case's shell block; it must exit 0.
4. Review - a fresh, read-only `claude -p` checks the result with no build context.

Usage:
    uv run evals/run.py              # every case
    uv run evals/run.py 01 03        # cases whose file name starts with 01 or 03
    uv run evals/run.py --keep 02    # keep the generated project for inspection
"""

# ruff: noqa: T201, S603, S607

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import copier

REPO_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = REPO_DIR / "evals" / "cases"
LOGS_DIR = REPO_DIR / "evals" / "logs"

PROJECT_NAME = "My App"

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

Files changed since the baseline commit (`git status --porcelain`):

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


@dataclass
class Case:
    """A parsed eval case."""

    name: str
    prompt: str
    check: str
    review: str
    setup: str | None = None


@dataclass
class Result:
    """The outcome of one case."""

    case: str
    build: bool = False
    check: bool = False
    review: bool = False
    note: str = ""

    @property
    def passed(self) -> bool:
        """True when every phase passed."""
        return self.build and self.check and self.review


def main() -> int:
    """Run the selected cases and print a summary."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cases", nargs="*", help="case file name prefixes")
    parser.add_argument(
        "--keep", action="store_true", help="keep generated projects after the run"
    )
    parser.add_argument("--model", help="model for the build and review agents")
    args = parser.parse_args()

    cases = select_cases(args.cases)
    if not cases:
        print("No matching cases.")
        return 1

    # `uv run` points VIRTUAL_ENV at this repo's venv; the generated projects have
    # their own, and uv warns on every command when the two differ.
    os.environ.pop("VIRTUAL_ENV", None)

    LOGS_DIR.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    results = [
        run_case(case, stamp, keep=args.keep, model=args.model) for case in cases
    ]

    print("\nSummary:")
    for result in results:
        phases = " ".join(
            f"{name}={'pass' if ok else 'FAIL'}"
            for name, ok in (
                ("build", result.build),
                ("check", result.check),
                ("review", result.review),
            )
        )
        status = "PASS" if result.passed else "FAIL"
        print(f"  {status}  {result.case}  {phases}  {result.note}".rstrip())
    return 0 if all(r.passed for r in results) else 1


def select_cases(prefixes: list[str]) -> list[Case]:
    """Parse case files, filtered by file name prefix."""
    paths = sorted(CASES_DIR.glob("*.md"))
    if prefixes:
        paths = [p for p in paths if any(p.name.startswith(x) for x in prefixes)]
    return [parse_case(p) for p in paths]


def parse_case(path: Path) -> Case:
    """Extract the fenced block under each `## <Section>` heading."""
    sections: dict[str, str] = {}
    for match in re.finditer(
        r"^## (\w+)\s*\n.*?^```[a-z]*\n(.*?)^```", path.read_text(), re.M | re.S
    ):
        sections[match.group(1).lower()] = match.group(2)
    missing = {"prompt", "check", "review"} - sections.keys()
    if missing:
        raise SystemExit(f"{path.name}: missing sections {sorted(missing)}")
    return Case(
        name=path.stem,
        prompt=sections["prompt"].strip(),
        check=sections["check"],
        review=sections["review"].strip(),
        setup=sections.get("setup"),
    )


def run_case(case: Case, stamp: str, *, keep: bool, model: str | None) -> Result:
    """Run all phases of one case, logging to evals/logs/."""
    result = Result(case=case.name)
    log_path = LOGS_DIR / f"{stamp}-{case.name}.log"
    transcript_path = LOGS_DIR / f"{stamp}-{case.name}.jsonl"
    workdir = Path(tempfile.mkdtemp(prefix="dj-eval-"))
    project = workdir / f"eval_{case.name}"

    print(f"\n=== {case.name}  (log: {log_path.relative_to(REPO_DIR)})")
    with log_path.open("w") as log:

        def section(title: str, body: str = "") -> None:
            log.write(f"\n===== {title} =====\n{body}")
            log.flush()

        try:
            print("  setup...")
            section("SETUP", f"project: {project}\n")
            setup_project(project, case, log)

            print("  build...")
            output = run_build(case, project, transcript_path, model)
            (workdir / "build-output.md").write_text(output)
            section("BUILD OUTPUT", output + "\n")
            result.build = bool(output)

            print("  check...")
            check = subprocess.run(
                ["bash", "-euo", "pipefail", "-c", case.check],
                cwd=project,
                env={
                    **os.environ,
                    "EVAL_BUILD_OUTPUT": str(workdir / "build-output.md"),
                },
                capture_output=True,
                text=True,
            )
            section(f"CHECK (exit {check.returncode})", check.stdout + check.stderr)
            result.check = check.returncode == 0

            print("  review...")
            review = run_review(case, project, output, model)
            section("REVIEW", review + "\n")
            result.review = last_line(review) == NO_ISSUES
        except subprocess.CalledProcessError as exc:
            result.note = f"setup failed: {' '.join(map(str, exc.cmd))}"
            section("ERROR", f"{result.note}\n{exc.stdout or ''}{exc.stderr or ''}")
        except subprocess.TimeoutExpired as exc:
            result.note = f"timed out: {exc.cmd[0]}"
            section("ERROR", result.note + "\n")
        finally:
            teardown(project, workdir, keep=keep, log=log)
            section("RESULT", f"{result}\n")

    print(f"  {'PASS' if result.passed else 'FAIL'}")
    return result


def setup_project(project: Path, case: Case, log) -> None:
    """Render the template and prepare the project up to a baseline commit."""
    copier.run_copy(
        src_path=str(REPO_DIR),
        dst_path=str(project),
        data={"project_name": PROJECT_NAME},
        defaults=True,
        unsafe=True,
        quiet=True,
    )
    write_env(project)

    def sh(command: str) -> None:
        log.write(f"$ {command}\n")
        log.flush()
        subprocess.run(
            command,
            shell=True,
            cwd=project,
            check=True,
            stdout=log,
            stderr=subprocess.STDOUT,
            executable="/bin/bash",
        )

    sh("just start --wait")
    sh("just install")
    sh("just dj makemigrations users")
    sh("just dj migrate")
    if case.setup:
        sh(case.setup)
    sh(
        "git add -A && git -c user.name=eval -c user.email=eval@example.com "
        "commit --no-verify -q -m baseline"
    )


def write_env(project: Path) -> None:
    """Write .env with free host ports so runs never clash with other stacks."""
    ports = {
        name: free_port()
        for name in (
            "POSTGRES_PORT",
            "REDIS_PORT",
            "MAILPIT_WEB_PORT",
            "MAILPIT_SMTP_PORT",
        )
    }
    env = (project / ".env.example").read_text()
    env = env.replace("127.0.0.1:5432/", f"127.0.0.1:{ports['POSTGRES_PORT']}/")
    env = env.replace("127.0.0.1:6379/", f"127.0.0.1:{ports['REDIS_PORT']}/")
    env = env.replace("localhost:1025", f"localhost:{ports['MAILPIT_SMTP_PORT']}")
    env += "".join(f"{name}={port}\n" for name, port in ports.items())
    (project / ".env").write_text(env)


def free_port() -> int:
    """Return a TCP port that is free right now."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def run_build(case: Case, project: Path, transcript: Path, model: str | None) -> str:
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
    ]
    if model:
        command += ["--model", model]
    with transcript.open("w") as out:
        subprocess.run(
            command,
            cwd=project,
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
    changed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
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


def last_line(text: str) -> str:
    """Return the last non-empty line of text, stripped."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def teardown(project: Path, workdir: Path, *, keep: bool, log) -> None:
    """Stop services and remove their volumes; remove the project unless kept."""
    if (project / "docker-compose.yml").exists():
        subprocess.run(
            ["docker", "compose", "down", "-v", "--remove-orphans"],
            cwd=project,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if keep:
        log.write(f"kept project: {project}\n")
        print(f"  kept: {project}")
    else:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
