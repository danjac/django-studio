"""Shared fixtures for django-studio template tests."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import copier
import pytest

from tests.helpers import DEFAULT_CONTEXT, TEMPLATE_DIR


@pytest.fixture
def output_dir():
    """Temporary directory for a single-use render; cleaned up after each test."""
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    """Render the template once with default context; reused across tests in a module."""
    dst = tmp_path_factory.mktemp("project") / "test_project"
    copier.run_copy(
        src_path=TEMPLATE_DIR,
        dst_path=str(dst),
        data=DEFAULT_CONTEXT,
        defaults=True,
        overwrite=True,
        unsafe=True,
        quiet=True,
    )
    return dst


@pytest.fixture(scope="module")
def project_with_deps(project):
    """Install dependencies and initialise git in the rendered project."""
    subprocess.run(
        ["uv", "sync", "--frozen"],
        cwd=str(project),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "init"],
        cwd=str(project),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(project),
        check=True,
        capture_output=True,
    )
    return project
