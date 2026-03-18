"""Shared constants and render helper for template tests."""

from __future__ import annotations

from pathlib import Path

import copier

TEMPLATE_DIR = str(Path(__file__).parent.parent.resolve())

DEFAULT_CONTEXT = {
    "project_name": "Test Project",
    "description": "A test project",
    "author": "Test Author",
    "author_email": "test@example.com",
}


def render(output_dir: Path, context: dict) -> Path:
    """Render the template into output_dir and return the project path."""
    dst = output_dir / "project"
    copier.run_copy(
        src_path=TEMPLATE_DIR,
        dst_path=str(dst),
        data=context,
        defaults=True,
        overwrite=True,
        unsafe=True,
        quiet=True,
    )
    return dst
