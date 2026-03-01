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

# Sync skills to global Claude commands and generated project template
sync-skills:
    cp skills/django-studio.md ~/.claude/commands/django-studio.md
    cp skills/django-studio.md "{{cookiecutter.project_slug}}/.claude/commands/django-studio.md"
