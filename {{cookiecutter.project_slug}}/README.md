# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Requirements

### Development

| Tool                                                    | Purpose                                          | Install                                                     |
| ------------------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------- |
| [uv](https://docs.astral.sh/uv/)                        | Python package manager                           | `curl -LsSf https://astral.sh/uv/install.sh \| sh`          |
| [just](https://just.systems/)                           | Task runner                                      | `cargo install just` or via your OS package manager         |
| [Docker](https://docs.docker.com/get-docker/) + Compose | PostgreSQL, Redis, Mailpit                       | See Docker docs                                             |
| [gh](https://cli.github.com/)                           | GitHub CLI (issues, PRs, `/django-studio` skill) | See [install docs](https://github.com/cli/cli#installation) |

Python 3.14 is managed automatically by `uv` - no separate install needed.

### Deployment

| Tool                                                           | Purpose                                             | Install          |
| -------------------------------------------------------------- | --------------------------------------------------- | ---------------- |
| [Terraform](https://developer.hashicorp.com/terraform/install) | Provision Hetzner infrastructure and Cloudflare DNS | See install docs |
| [Helm](https://helm.sh/docs/intro/install/)                    | Deploy Kubernetes workloads                         | See install docs |
| [kubectl](https://kubernetes.io/docs/tasks/tools/)             | Kubernetes CLI                                      | See install docs |
| [hcloud](https://github.com/hetznercloud/cli)                  | Hetzner Cloud CLI                                   | See install docs |

See `DEPLOYMENT.md` for full deployment instructions.

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

| Command                                        | Effect                                                                                           |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `/django-studio issue <feedback>`              | File an issue against this repo                                                                  |
| `/django-studio issue cookiecutter <feedback>` | File an issue against the [django-studio](https://github.com/danjac/django-studio) template repo |
| `/django-studio create <app-name>`             | Scaffold a new Django app (wires `INSTALLED_APPS`, `conftest.py`, `urls.py`)                     |
| `/django-studio init`                          | Run Session Zero — define goals, write README, create `ROADMAP.md`                               |
| `/django-studio prelaunch`                     | Run pre-launch checks                                                                            |

Requires the `gh` CLI authenticated with GitHub access.

---

Built with [django-studio](https://github.com/danjac/django-studio)
