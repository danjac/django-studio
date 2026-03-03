# django-studio

![Photo by James Kovin on Unsplash](images/studio.jpg)

_Photo by James Kovin on [Unsplash](https://unsplash.com/photos/black-and-green-audio-mixer-F2h_WbKnX4o)_

Cookiecutter template for Django projects with HTMX, Alpine.js, and Tailwind CSS.

This project is designed to be a starting point for building modern Django applications with a focus on simplicity, performance, and developer experience. It includes an opinionated and carefully curated stack of tools and libraries to help you get up and running quickly while following best practices. It includes Markdown documentation, MCP support, custom Skills and a design pattern library to assist with AI-driven development and code generation while keeping skilled developers in the loop.

## Stack

- Python 3.14, Django 6.0, PostgreSQL 18, Redis 8
- HTMX + Alpine.js + Tailwind CSS (no JS build step)
- `uv` for dependency management
- `just` for task running
- `django-tasks-db` for background tasks (not Celery)
- `django-allauth` for authentication

- Cloudflare for DNS, CDN, SSL, and DDoS protection

- Hetzner Cloud for hosting (K3s)
- Design pattern library
- Full test coverage (pytest + Playwright)

Note that while this is an opinionated stack, you can easily swap out any of these choices after generating the project to craft it to your specific needs.

## Requirements

### Development

| Tool                                                    | Purpose                                          | Install                                                     |
| ------------------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------- |
| [uv](https://docs.astral.sh/uv/)                        | Python package manager (runs `uvx cookiecutter`) | `curl -LsSf https://astral.sh/uv/install.sh \| sh`          |
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

See `DEPLOYMENT.md` in the generated project for full deployment instructions.

## Usage

```bash
uvx cookiecutter gh:danjac/django-studio
```

Then follow the prompts:

- `project_name`: Human-readable project name (e.g. "My Project")
- `project_slug`: Directory/repo name (e.g. "my-project")
- `package_name`: Python package name (e.g. "myapp")
- `description`: Short project description
- `author`: Your name
- `author_email`: Your email

## After Generation

```bash
cd {{project_slug}}
cp .env.example .env
just start        # Start Docker services
just install      # Install dependencies + pre-commit hooks
just update       # Update dependencies
just dj migrate   # Run Django migrations
just serve        # Dev server + Tailwind watcher
```

See `docs/` for full documentation.

## Skills

Every generated project ships with the `/django-studio` skill at `.claude/commands/django-studio.md`.

| Command                                        | Effect                                                                       |
| ---------------------------------------------- | ---------------------------------------------------------------------------- |
| `/django-studio issue <feedback>`              | File an issue against the current project                                    |
| `/django-studio issue cookiecutter <feedback>` | File an issue against this template repo                                     |
| `/django-studio create`                        | Create a new Django project (prompts for name, slug, package, and settings)  |
| `/django-studio init`                          | Run Session Zero — define goals, write README, create `ROADMAP.md`           |

Run `just sync-skills` after editing the skill to propagate changes to `~/.claude/commands/`.

Requires the `gh` CLI authenticated with GitHub access.
