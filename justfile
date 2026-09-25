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

# Run skill evals (costs tokens; see evals/README.md)
eval *args:
    uv run evals/run.py {{ args }}

# Update dependencies
update:
   uv lock --upgrade
   @just precommit autoupdate
