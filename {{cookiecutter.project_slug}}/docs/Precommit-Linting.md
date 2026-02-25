# Pre-commit and Linting

This project uses pre-commit hooks and multiple linters for code quality.

## Installation

```bash
just install
```

This runs `pre-commit install` and installs dependencies.

## Running Linters

```bash
just lint              # Run ruff (Python) and djlint (templates)
just typecheck        # Run basedpyright (type checking)
just precommit run --all-files  # Run all hooks manually
```

## Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # Python
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: "v0.15.2"
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  # Django templates
  - repo: https://github.com/adamchainz/djade-pre-commit
    rev: "1.8.0"
    hooks:
      - id: djade

  - repo: https://github.com/Riverside-Healthcare/djLint
    rev: v1.36.4
    hooks:
      - id: djlint-django

  # Tailwind
  - repo: local
    hooks:
      - id: rustywind
        name: rustywind
        entry: rustywind
        args: [--write]
        files: ^templates
        types: [html]

  # Shell scripts
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck

  # Docker
  - repo: https://github.com/hadolint/hadolint
    rev: v2.14.0
    hooks:
      - id: hadolint-docker

  # Secrets
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.0
    hooks:
      - id: gitleaks

  # Type upgrades
  - repo: https://github.com/asottile/pyupgrade
    rev: v3.21.2
    hooks:
      - id: pyupgrade
        args: [--py314]

  # Django upgrades
  - repo: https://github.com/adamchainz/django-upgrade
    rev: "1.30.0"
    hooks:
      - id: django-upgrade
        args: [--target-version, "6.0"]

  # Imports
  - repo: https://github.com/MarcoGorelli/absolufy-imports
    rev: v0.3.1
    hooks:
      - id: absolufy-imports

  # Commits
  - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
    rev: v9.24.0
    hooks:
      - id: commitlint
        stages: [commit-msg]
```

## Python: Ruff

```toml
# pyproject.toml
[tool.ruff]
target-version = "py314"

[tool.ruff.lint]
select = [
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "S",   # flake8-bandit
    # ... many more
]
```

Run manually:
```bash
ruff check --fix .
ruff format .
```

## Templates: djlint

```toml
# pyproject.toml
[tool.djlint]
profile = "django"
ignore = "H030,H031,H017,H021"
custom_blocks = "cache,partialdef,fragment"
```

## Templates: djade

Formats Django templates:
```bash
djade --target-version 5.1 .
```

## Templates: rustywind

Sorts Tailwind CSS classes:
```bash
rustywind templates/ --write
```

## Type Checking: basedpyright

```bash
just typecheck
```

Configured in pyproject.toml:
```toml
[tool.pyright]
include = ["{{cookiecutter.app_name}}"]
exclude = ["**/migrations/*.py", "**/tests/**/*.py"]
typeCheckingMode = "basic"
```

## Updating Hooks

```bash
just precommitupdate
```
