# Django Studio cookiecutter commands

# Run tests
test:
    uv run pytest -v

# Run linting
lint:
    ruff check tests evals

# Run precommit
precommit *args:
   uv run --with pre-commit-uv pre-commit {{ args }}

# Run formatting check
format:
    ruff format --check tests evals

# Run all checks
check: lint format test

# Run skill evals (costs tokens; see evals/README.md). Keeps the machine awake.
eval *args:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v systemd-inhibit >/dev/null; then
        exec systemd-inhibit --what=sleep:idle --why="skill evals" uv run evals/run.py {{ args }}
    elif command -v caffeinate >/dev/null; then
        exec caffeinate -i uv run evals/run.py {{ args }}
    else
        exec uv run evals/run.py {{ args }}
    fi

# Update dependencies
update:
   uv lock --upgrade
   @just precommit autoupdate
