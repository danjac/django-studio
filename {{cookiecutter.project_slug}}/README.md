# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Requirements

### Development

| Tool                                                    | Purpose                                          | Install                                                     |
| ------------------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------- |
| [uv](https://docs.astral.sh/uv/)                        | Python package manager                           | `curl -LsSf https://astral.sh/uv/install.sh \| sh`          |
| [just](https://just.systems/)                           | Task runner                                      | `cargo install just` or via your OS package manager         |
| [Docker](https://docs.docker.com/get-docker/) + Compose | PostgreSQL, Redis, Mailpit                       | See Docker docs                                             |
| [gh](https://cli.github.com/)                           | GitHub CLI (issues, PRs)                         | See [install docs](https://github.com/cli/cli#installation) |

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
git init                    # initialise Git repository
just start                  # start Docker services (PostgreSQL, Redis, Mailpit)
just install                # install Python deps + pre-commit hooks
just dj makemigrations      # generate initial migrations (required on first run)
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

## Slash Commands

Claude Code slash commands are available via `/djstudio <subcommand>`:

| Subcommand | Purpose |
| ----------------------------------------- | ----------------------------------------------- |
| `create-app <name>` | Create a Django app (apps.py, models, views, urls, admin, tests) |
| `create-view [<app>] <view>` | Add a view, template, and URL; omit app for top-level views |
| `create-task <app> <task>` | Add a background task |
| `create-model <app> <model>` | Design and write a Django model with factory, fixture, and model tests |
| `create-crud <app> <model>` | Generate full CRUD views, templates, URLs, and tests |
| `create-e2e [<app>] <description>` | Write Playwright E2E test(s) for a described interaction |
| `secure` | Security audit: settings, views, XSS, CSRF, IDOR, SQL injection |
| `gdpr` | Audit the project for GDPR compliance issues |
| `translate <locale>` | Extract strings, translate via Claude, compile `.mo` catalogue |
| `feedback` | Report a bug or improvement against the django-studio template |

## Stack

- Python 3.14, Django 6.0, PostgreSQL 18, Redis 8
- HTMX + Alpine.js + Tailwind CSS (no JS build step)
- `uv` for dependency management, `just` for task running
- `django-tasks-db` for background tasks
- `django-allauth` for authentication

See `docs/` for detailed documentation on each part of the stack.

---

Built with [django-studio](https://github.com/danjac/django-studio)
