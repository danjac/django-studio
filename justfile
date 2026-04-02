# Django Studio cookiecutter commands

# Run tests
test:
    uv run pytest -v

# Run linting
lint:
    ruff check tests

# Run precommit
precommit *args:
   uv run --with pre-commit-uv pre-commit {{ args }}

# Run formatting check
format:
    ruff format --check tests

# Run all checks
check: lint format test

# Update dependencies
update:
   uv lock --upgrade
   @just precommit autoupdate
