#!/usr/bin/env -S uv run python
"""End-to-end eval runner for the dj-* skills.

Each case in evals/cases/ is run in four phases:

1. Setup  - render a fresh project, start services, install, migrate, run the
            case's optional setup block, commit a baseline. A /dj-bootstrap
            case gets an empty directory instead.
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
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from agents import NO_ISSUES, last_line, run_build, run_review
from cases import REPO_DIR, select_cases
from setup import setup_case

if TYPE_CHECKING:
    from typing import TextIO

    from cases import Case

LOGS_DIR = REPO_DIR / "evals" / "logs"


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
            env = setup_case(project, case, log)

            print("  build...")
            output = run_build(case, project, transcript_path, model, env)
            (workdir / "build-output.md").write_text(output)
            section("BUILD OUTPUT", output + "\n")
            result.build = bool(output)

            print("  check...")
            check = subprocess.run(
                ["bash", "-euo", "pipefail", "-c", case.check],
                cwd=project,
                env={**env, "EVAL_BUILD_OUTPUT": str(workdir / "build-output.md")},
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


def teardown(project: Path, workdir: Path, *, keep: bool, log: TextIO) -> None:
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
