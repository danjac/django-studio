# Django Studio

_A production‑ready starter kit for modern Django applications._

![Photo by James Kovin on Unsplash](images/studio.jpg)

_Photo by James Kovin on [Unsplash](https://unsplash.com/photos/black-and-green-audio-mixer-F2h_WbKnX4o)_

## Overview

[Copier](https://pypi.org/project/copier/) template for Django projects with HTMX, Alpine.js, and Tailwind CSS.

This project is designed to be a starting point for building modern Django applications with a focus on simplicity, performance, and developer experience. It includes an opinionated and carefully curated stack of tools and libraries to help you get up and running quickly while following best practices, a design pattern library with tried-and-tested components and agentic Markdown documentation and custom Skills for AI-assisted development.

## Status

This project is best described as "pre-alpha". While based on working projects in production, this is a new repo and the template has not yet been tested by external users. Expect many breaking changes and rough edges.

## Audience

This template is built for **solo developers based in the EU** building side projects
and small SaaS applications. It encodes one person's proven defaults (stack choices,
hosting provider, deployment topology) rather than aiming to be a general-purpose
starter kit.

The EU focus is deliberate: hosting is on [Hetzner Cloud](https://hetzner.com)
(Germany-based, GDPR-compliant), DNS/CDN via [Cloudflare](https://cloudflare.com),
GDPR compliance guidance is built into the docs, and i18n/l10n patterns assume a
European-first audience. If you are based outside the EU, the template will still
work but the hosting defaults and compliance tooling are optimised for EU data
residency requirements.

This project is intended for experienced developers who are comfortable with the stack choices and general web development concepts. It is not a tutorial or learning resource for beginners, but rather a practical tool to jumpstart new projects with a solid foundation.

This project provides AI-related features for those who wish to use LLMs as part of their workflow, but this is not a requirement and the project can be used without these features. You should always be comfortable taking the wheel and reviewing and modifying the code by hand as needed.

## Getting Started

```bash
uvx copier copy --trust gh:danjac/django-studio my-project
```

Then follow the prompts:

| Prompt              | Example                 | Notes                                                                                                  |
| ------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| `project_name`      | `My Project`            | Human-readable name                                                                                    |
| `project_slug`      | `my_project`            | Python package directory name                                                                          |
| `package_name`      | `my_project`            | Python package name (snake_case)                                                                       |
| `description`       | `A project that does X` | One-sentence description                                                                               |
| `author`            | `Your Name`             |                                                                                                        |
| `author_email`      | `you@example.com`       |                                                                                                        |
| `domain`            | `example.com`           | Production domain                                                                                      |
| `license`           | `MIT`                   | MIT, Apache-2.0, GPL-3.0, AGPL-3.0, LGPL-3.0, MPL-2.0, BSD-2-Clause, BSD-3-Clause, ISC, EUPL-1.2, None |

### Updating a generated project

Once a project has been generated and committed, you can pull in template updates:

```bash
cd my-project
uvx copier update --trust
```

[Copier](https://pypi.org/project/copier/) performs a 3-way merge so your local changes are preserved. Resolve any conflicts, then commit.

The generated `README.md` will include instructions to get started with development, testing, and deployment.

## Philosophy

- **Low friction**: Minimal setup steps; generate a project with a single command.
- **High velocity**: Opinionated defaults so you can focus on business logic and end-user needs.
- **Best practices**: Uses proven tools and patterns for security, performance, and observability.

## Features

- Django 6 with a modern stack (HTMX, Alpine.js, Tailwind CSS)
- Docker Compose setup for local development (PostgreSQL, Redis, Mailpit)
- Kubernetes deployment with Helm Charts
- Grafana dashboards for OpenTelemetry monitoring
- Terraform IaC scripts for provisioning Hetzner Cloud infrastructure and Cloudflare DNS
- Design system with reusable components
- AI-assisted development with agent documentation, agentic hooks, and project Skills

## Stack

- Python 3.14, Django 6.0, PostgreSQL 18, Redis 8
- [HTMX](https://htmx.org) + [Alpine.js](https://alpinejs.dev) + [Tailwind CSS](https://tailwindcss.com) (no JS build step)
- [uv](https://docs.astral.sh/uv/) for dependency management
- [just](https://just.systems/man/en/) for task running
- [Django tasks](https://docs.djangoproject.com/en/6.0/topics/tasks/) for background tasks (instead of Celery)
- [django-allauth](https://docs.allauth.org/en/latest/) for authentication
- [pre-commit](https://pre-commit.com) hooks for linting
- [Cloudflare](https://cloudflare.com) for DNS, CDN, SSL, and DDoS protection
- [Hetzner Cloud](https://hetzner.com) for hosting (K3s) and object storage
- Full test coverage ([pytest](https://docs.pytest.org/en/stable/) + [Playwright](https://playwright.dev/python/))

The focus of this project is a simple and robust foundation for both user and developer experience. Django is a tried and tested framework with a strong emphasis on convention and best practices, making it an ideal choice for the backend. For the frontend, HTMX and Alpine.js provide a powerful combination for building dynamic interfaces without the complexity of a full JavaScript framework, while Tailwind CSS offers a utility-first approach to styling that promotes consistency and rapid development.

[K3s](https://k3s.io) is a lightweight Kubernetes distribution that allows for easy deployment and scaling of applications. By using K3s, we can ensure that our application is production-ready and can handle increased traffic as needed. Helm Charts have been provided to deploy your project along with Grafana dashboards for monitoring. Full Github Actions CI/CD pipelines are included for testing and deployment.

This stack will be assessed constantly to ensure it remains the best choice for the target audience and use cases. If better tools or libraries become available, they will be evaluated and potentially integrated into the template in addition to or in place of the current choices.

## Design system

UI components are provided by [DaisyUI](https://daisyui.com/), a Tailwind CSS component library with 50+ production-ready components, built-in dark mode, and semantic theming. DaisyUI is vendored as `.mjs` files (no npm required) and works with the `django-tailwind-cli` standalone binary.

- 50+ ready-made components (buttons, forms, modals, drawers, tabs, etc.)
- Automatic dark/light mode via DaisyUI themes
- Semantic color system (`primary`, `secondary`, `error`, etc.)
- Focus on accessibility
- Responsive layouts

## Skills

Generated projects include a `/djstudio` Claude Code slash command with subcommands for common workflows:

**General**

| Subcommand        | Summary                                                                           |
| ----------------- | --------------------------------------------------------------------------------- |
| `help`            | Print documentation for a subcommand                                              |
| `sync`            | Pull latest template changes via Copier and resolve merge conflicts interactively |
| `feedback`        | Report a bug or improvement against the django-studio template                    |

**Generators**

| Subcommand       | Summary                                                                |
| ---------------- | ---------------------------------------------------------------------- |
| `create-app`     | Create a Django app (apps.py, models, views, urls, admin, tests)       |
| `create-view`    | Add a view, template, and URL                                          |
| `create-task`    | Add a `django-tasks-db` background task with correct async patterns    |
| `create-command` | Add a management command with tests                                    |
| `create-cron`    | Schedule a management command as a Kubernetes cron job                 |
| `create-model`   | Design and write a Django model with factory, fixture, and model tests |
| `create-crud`    | Generate full CRUD views, templates, URLs, and tests                   |
| `create-e2e`     | Write Playwright E2E test(s) for a described user interaction          |
| `create-tag`     | Add a template tag (simple_tag, simple_block_tag, inclusion_tag, Node) |
| `create-filter`  | Add a template filter with correct escaping flags                      |

**Documentation**

| Subcommand | Summary                                                     |
| ---------- | ----------------------------------------------------------- |
| `docs`     | Look up or create project documentation                     |
| `daisyui`  | Fetch DaisyUI component docs with project conventions       |

**Localisation**

| Subcommand  | Summary                                                        |
| ----------- | -------------------------------------------------------------- |
| `translate` | Extract strings, translate via Claude, compile `.mo` catalogue |

**Audits**

| Subcommand | Summary                                                                      |
| ---------- | ---------------------------------------------------------------------------- |
| `perf`     | Performance audit: N+1 queries, missing indexes, caching, async              |
| `secure`   | Security audit: settings, views, XSS, CSRF, IDOR, SQL injection              |
| `gdpr`     | GDPR compliance audit: PII in models, erasure, consent, logging              |
| `a11y`     | Accessibility audit: WCAG 2.1 AA — forms, icons, HTMX, Alpine, semantic HTML |
| `deadcode` | Remove unused Python code and static assets                                  |

**Deployment**

| Subcommand          | Summary                                                                        |
| ------------------- | ------------------------------------------------------------------------------ |
| `launch`               | Interactive first-deploy wizard: provisions infra, configures secrets, deploys |
| `launch-observability` | Deploy the observability stack (Grafana + Prometheus + Loki)                   |
| `rotate-secrets`       | Rotate auto-generated and third-party Helm secrets and redeploy                |
| `enable-db-backups`    | Enable automated daily PostgreSQL backups to a private Object Storage bucket   |

## Hosting

[Hetzner Cloud](https://hetzner.com) is a very cost-effective, EU-based hosting provider. Cloudflare is currently the cheapest and most secure option for DNS, CDN, SSL, and DDoS protection. These solutions will be reviewed on a regular basis - if better options become available, they will be offered instead of or addition to these choices.

Prices are subject to change, but the current hosting costs based on the default settings should range between 20-40 EUR per month.

## Requirements

### Development

| Tool                                                    | Purpose                                    | Install                                                     |
| ------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------- |
| [uv](https://docs.astral.sh/uv/)                        | Python package manager (runs `uvx copier`) | `curl -LsSf https://astral.sh/uv/install.sh \| sh`          |
| [just](https://just.systems/)                           | Task runner                                | `cargo install just` or via your OS package manager         |
| [Docker](https://docs.docker.com/get-docker/) + Compose | PostgreSQL, Redis, Mailpit                 | See Docker docs                                             |
| [gh](https://cli.github.com/)                           | GitHub CLI (issues, PRs)                   | See [install docs](https://github.com/cli/cli#installation) |

Python 3.14 is managed automatically by `uv` - no separate install needed.

### Deployment

| Tool                                                           | Purpose                                             | Install          |
| -------------------------------------------------------------- | --------------------------------------------------- | ---------------- |
| [Terraform](https://developer.hashicorp.com/terraform/install) | Provision Hetzner infrastructure and Cloudflare DNS | See install docs |
| [Helm](https://helm.sh/docs/intro/install/)                    | Deploy Kubernetes workloads                         | See install docs |
| [kubectl](https://kubernetes.io/docs/tasks/tools/)             | Kubernetes CLI                                      | See install docs |
| [hcloud](https://github.com/hetznercloud/cli)                  | Hetzner Cloud CLI                                   | See install docs |

See `docs/Deployment.md` in the generated project for full deployment instructions.
