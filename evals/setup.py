"""Prepare the directory a case runs in, and the environment it runs with."""

# ruff: noqa: S602

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

import copier
from cases import REPO_DIR
from utils import free_ports, service_env, write_env

if TYPE_CHECKING:
    from pathlib import Path
    from typing import TextIO

    from cases import Case

PROJECT_NAME = "My App"


def setup_case(project: Path, case: Case, log: TextIO) -> dict[str, str]:
    """Prepare the case's directory; return the environment for build and check."""
    if case.bootstrap:
        return setup_bootstrap(project)
    setup_project(project, case, log)
    return {**os.environ}


def setup_bootstrap(project: Path) -> dict[str, str]:
    """Create an empty directory for /dj-bootstrap to generate the project in.

    The skill writes .env itself. The project reads settings from .env without
    overriding the environment, and so does Compose, so free ports go in the
    environment instead.
    """
    project.mkdir()
    return {**os.environ, **service_env(free_ports())}


def setup_project(project: Path, case: Case, log: TextIO) -> None:
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
