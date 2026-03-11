#!/usr/bin/env python
"""Pre-generation hook: validates user inputs before any files are created."""

import sys

PROJECT_NAME = "{{cookiecutter.project_name}}"
PROJECT_SLUG = "{{cookiecutter.project_slug}}"


def validate() -> None:
    if not PROJECT_NAME.strip():
        print(
            "ERROR: project_name is required.\n"
            "  Example: uvx cookiecutter . project_name='Photo Blog'"
        )
        sys.exit(1)

    if not PROJECT_SLUG.isidentifier():
        print(
            f"ERROR: derived project_slug '{PROJECT_SLUG}' is not a valid Python "
            "identifier. Use only letters, digits, spaces, and underscores in "
            "project_name."
        )
        sys.exit(1)


validate()
