# Django Studio cookiecutter commands

# Run tests
test:
    uv run pytest -v

# Run linting
lint:
    ruff check tests

# Run formatting check
format:
    ruff format --check tests

# Run all checks
check: lint format test
