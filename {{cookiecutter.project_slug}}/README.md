# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Requirements

| Tool | Purpose | Install |
|------|---------|---------|
| [uv](https://docs.astral.sh/uv/) | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [just](https://just.systems/) | Task runner | `cargo install just` or via your OS package manager |
| [Docker](https://docs.docker.com/get-docker/) + Compose | PostgreSQL, Redis, Mailpit | See Docker docs |

Python 3.14 is managed automatically by `uv` - no separate install needed.

## Setup

```bash
cp .env.example .env        # configure environment variables
just start                  # start Docker services (PostgreSQL, Redis, Mailpit)
just install                # install Python deps + pre-commit hooks
just dj migrate             # run database migrations
just serve                  # start dev server + Tailwind watcher
```

## Common Commands

```bash
just test                   # run unit tests with coverage
just lint                   # ruff + djlint
just typecheck              # basedpyright
just dj <command>           # run any manage.py command
just stop                   # stop Docker services
```

Run `just` with no arguments to list all available commands.

## Stack

- Python 3.14, Django 6.0, PostgreSQL 18, Redis 8
- HTMX + Alpine.js + Tailwind CSS (no JS build step)
- `uv` for dependency management, `just` for task running
- `django-tasks-db` for background tasks
- `django-allauth` for authentication

See `docs/` for detailed documentation on each part of the stack.

## Skills

The `/django-studio` skill is available in `.claude/commands/` and works from any Claude Code session in this project.

- `/django-studio <feedback>` - posts an issue to this repo
- `/django-studio cookiecutter <feedback>` - posts an issue to the [django-studio](https://github.com/danjac/django-studio) template repo

Requires the `gh` CLI authenticated with GitHub access.
