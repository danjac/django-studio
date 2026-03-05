# Django Studio

_A production‑ready starter kit for modern Django applications._

![Photo by James Kovin on Unsplash](images/studio.jpg)

_Photo by James Kovin on [Unsplash](https://unsplash.com/photos/black-and-green-audio-mixer-F2h_WbKnX4o)_

## Overview

Cookiecutter template for Django projects with HTMX, Alpine.js, and Tailwind CSS.

This project is designed to be a starting point for building modern Django applications with a focus on simplicity, performance, and developer experience. It includes an opinionated and carefully curated stack of tools and libraries to help you get up and running quickly while following best practices, a design pattern library with tried-and-tested components and agentic Markdown documentation and custom Skills for AI-assisted development.

## Status

This project is best described as "pre-alpha". While based on working projects in production, this is a new repo and the cookiecutter template has not yet been tested by external users. Expect many breaking changes and rough edges.

## Philosophy

- Low friction: Minimal setup steps; generate a ready‑to‑run project with a single command.
- High velocity: Opinionated defaults so you can focus on business logic and end-user needs.
- Best practices: Uses proven tools and patterns for security, performance, and observability.

## Stack

- Python 3.14, Django 6.0, PostgreSQL 18, Redis 8
- HTMX + Alpine.js + Tailwind CSS (no JS build step)
- `uv` for dependency management
- `just` for task running
- `django-tasks-db` for background tasks (not Celery)
- `django-allauth` for authentication
- `pre-commit` hooks for linting
- Cloudflare for DNS, CDN, SSL, and DDoS protection
- Hetzner Cloud for hosting (K3s)
- Full test coverage (pytest + Playwright)

The focus of this project is a simple and robust foundation for both user and developer experience. Django is a tried and tested framework with a strong emphasis on convention and best practices, making it an ideal choice for the backend. For the frontend, HTMX and Alpine.js provide a powerful combination for building dynamic interfaces without the complexity of a full JavaScript framework, while Tailwind CSS offers a utility-first approach to styling that promotes consistency and rapid development.

[K3s](https://k3s.io) is a lightweight Kubernetes distribution that allows for easy deployment and scaling of applications. By using K3s, we can ensure that our application is production-ready and can handle increased traffic as needed. Helm Charts have been provided to deploy your project along with Grafana dashboards for monitoring. Full Github Actions CI/CD pipelines are included for testing and deployment.

## Hosting

[Hetzner Cloud](https://hetzner.com) is a very cost-effective, EU-based hosting provider. Cloudflare is currently the cheapest and most secure option for DNS, CDN, SSL, and DDoS protection. These solutions will be reviewed on a regular basis - if better options become available, they will be offered instead of or addition to these choices.

Prices are subject to change, but the current hosting costs based on the default settings should range between 20-40 EUR per month.

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

## Skills

Every generated project ships with the `/django-studio` skill at `.claude/commands/django-studio.md`.

The skill source lives in `skills/django-studio.md` at the repo root. Run `just sync-skills` to install or update it in `~/.claude/commands/`:

```bash
just sync-skills
```

| Command                                        | Effect                                                                      |
| ---------------------------------------------- | --------------------------------------------------------------------------- |
| `/django-studio issue <feedback>`              | File an issue against the current project                                   |
| `/django-studio issue cookiecutter <feedback>` | File an issue against this template repo                                    |
| `/django-studio create`                        | Create a new Django project (prompts for name, slug, package, and settings) |
| `/django-studio init`                          | Run Session Zero — define goals, write README, create `ROADMAP.md`          |
| `/django-studio prelaunch`                     | Runs prelaunch checks before first deployment                               |

Run `just sync-skills` after editing the skill to propagate changes to `~/.claude/commands/`.

Requires the `gh` CLI authenticated with GitHub access.
