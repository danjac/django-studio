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

# Sync skills from generated project template to global Claude commands
sync-skills:
    cp skills/django-studio.md ~/.claude/commands/django-studio.md
