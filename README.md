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

This template is built for **solo developers** building side projects
and small SaaS applications. It encodes one person's proven defaults (stack choices,
hosting provider, deployment topology) rather than aiming to be a general-purpose
starter kit.

This project is intended for experienced developers who are comfortable with the stack choices and general web development concepts. It gives new projects a working foundation and assumes you already know the stack.

This project provides AI-related features for those who wish to use LLMs as part of their workflow, but this is not a requirement and the project can be used without these features. You should always be comfortable taking the wheel and reviewing and modifying the code by hand as needed.

## Getting Started

You need [uv](https://docs.astral.sh/uv/getting-started/installation/),
[just](https://just.systems/man/en/packages.html),
[Docker](https://docs.docker.com/get-started/get-docker/) and the
[GitHub CLI](https://cli.github.com/) (`gh`). `uv` installs Python for you.

There are two ways to create a project: with the Claude Code plugin, which asks you
questions and sets everything up, or with Copier directly. Both produce the same
project.

### With Claude Code

1. Install the plugin. Run these two commands in your shell, from any directory:
   they install the plugin for your user account, not for the current directory,
   so you only do this once.

   ```bash
   claude plugin marketplace add danjac/django-studio --sparse .claude-plugin
   claude plugin install django-studio@django-studio
   ```

   The first command registers this repository as a plugin source. `--sparse
   .claude-plugin` skips the template, tests and images, which the plugin doesn't
   need. The second installs the plugin, fetching only its `plugin/` directory.

2. Start Claude Code in the directory where you keep your projects:

   ```bash
   cd ~/Projects
   claude
   ```

   `/dj-bootstrap` creates the project in a new subdirectory named after it, such
   as `recipe_box/`. If you start it in an empty directory instead, it uses that
   directory.

3. Describe the project to `/dj-bootstrap`:

   ```
   /dj-bootstrap "recipe sharing site for home cooks"
   ```

   The skill checks your tools, then asks for anything your description didn't
   cover: the project name, author, domain and licence (the same answers as the
   Copier prompts below), and a few questions about the product: core entities,
   user roles, public or login-only, languages, and whether it needs an API,
   webhooks or background tasks. The product answers become the project
   overview in `docs/this-project.md`, which the project's agents read.

   It then generates the project, starts the Docker services, installs
   dependencies, creates the database, runs every check with `just check-all`,
   and makes the first commit. It offers to create a GitHub repository, and
   waits for you to confirm first. This takes several minutes.

4. Quit Claude Code and start it again in the project directory:

   ```bash
   cd recipe_box
   claude
   ```

   The project comes with its own `/dj-*` skills and agent docs, which load only
   in a session started there.

5. Give the project its first shape with `/dj-kickoff`, unless you already ran it
   when `/dj-bootstrap` offered. It works from `docs/this-project.md`: it proposes
   changes to the `User` model, an app and model breakdown for your core entities
   (created only after you confirm it), sets up the extra languages, and fills in
   the rest of the project docs. Each step can be skipped, and it commits when
   `just check-all` passes.

The plugin's skills are also available as `/django-studio:dj-bootstrap` and
`/django-studio:dj-kickoff`, in case another plugin uses the same names.

#### Updating the plugin

The plugin only affects new projects. To get the latest `/dj-bootstrap` and `/dj-kickoff`, run:

```bash
claude plugin marketplace update django-studio
claude plugin update django-studio@django-studio
```

Or let Claude Code do it: run `/plugin`, open the **Marketplaces** tab, select
`django-studio` and choose **Enable auto-update**. Claude Code then checks for
updates when a session starts.

Projects you have already generated don't change when the plugin updates. Run
`/dj-sync` inside a project to pull template changes into it (see
[Updating a generated project](#updating-a-generated-project)).

### With Copier

```bash
uvx copier copy --trust gh:danjac/django-studio my-project
```

Then follow the prompts:

| Prompt         | Example                 | Notes                                                                                                  |
| -------------- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| `project_name` | `My Project`            | Human-readable name                                                                                    |
| `project_slug` | `my_project`            | Python package directory name                                                                          |
| `package_name` | `my_project`            | Python package name (snake_case)                                                                       |
| `description`  | `A project that does X` | One-sentence description                                                                               |
| `author`       | `Your Name`             |                                                                                                        |
| `author_email` | `you@example.com`       |                                                                                                        |
| `domain`       | `example.com`           | Production domain                                                                                      |
| `license`      | `MIT`                   | MIT, Apache-2.0, GPL-3.0, AGPL-3.0, LGPL-3.0, MPL-2.0, BSD-2-Clause, BSD-3-Clause, ISC, EUPL-1.2, None |

Copier prints the setup steps when it finishes.

To get the same guided start as `/dj-bootstrap`, install the plugin (step 1 above)
and run `/dj-kickoff` in the new project. It installs and commits the scaffold if
you haven't yet, asks the product questions, and records the answers in
`docs/this-project.md` before shaping the project.

### Generating from a branch

To generate from a specific branch (e.g. to test a pre-release feature):

```bash
uvx copier copy --trust "gh:danjac/django-studio@branch-name" my-project
```

### Updating a generated project

Once a project has been generated and committed, you can pull in template updates:

```bash
cd my-project
uvx copier update --trust
```

[Copier](https://pypi.org/project/copier/) performs a 3-way merge so your local changes are preserved. Resolve any conflicts, then commit.

The generated `README.md` will include instructions to get started with development, testing, and deployment.

## Features

- Django 6 with a modern stack (HTMX, Alpine.js, Tailwind CSS)
- Docker Compose setup for local development (PostgreSQL, Redis, Mailpit)
- Kubernetes deployment with Helm Charts
- Grafana dashboards for OpenTelemetry monitoring
- Terraform IaC scripts for provisioning Hetzner Cloud infrastructure and Cloudflare DNS
- Design system with reusable components
- AI-assisted development with agent documentation, agentic hooks, project Skills, and [MCP servers](#mcp-servers) (PostgreSQL, Playwright, Django shell)

## Stack

- Python 3.14, Django 6.1, PostgreSQL 18, Redis 8
- [HTMX](https://htmx.org) + [Alpine.js](https://alpinejs.dev) + [Tailwind CSS](https://tailwindcss.com) (no JS build step)
- [uv](https://docs.astral.sh/uv/) for dependency management
- [just](https://just.systems/man/en/) for task running
- [Django tasks](https://docs.djangoproject.com/en/6.1/topics/tasks/) for background tasks (instead of Celery)
- [django-allauth](https://docs.allauth.org/en/latest/) for authentication
- [pre-commit](https://pre-commit.com) hooks for linting
- [Cloudflare](https://cloudflare.com) for DNS, CDN, SSL, and DDoS protection
- [Hetzner Cloud](https://hetzner.com) for hosting (K3s) and object storage
- Full test coverage ([pytest](https://docs.pytest.org/en/stable/) + [Playwright](https://playwright.dev/python/))

The goal is a simple foundation, both for the people using the app and for the developers building it. Django is a tried and tested framework with a strong emphasis on convention and best practices, making it an ideal choice for the backend. For the frontend, HTMX and Alpine.js provide a powerful combination for building dynamic interfaces without the complexity of a full JavaScript framework, while Tailwind CSS offers a utility-first approach to styling that promotes consistency and rapid development.

A guiding principle throughout is [Locality of Behaviour](https://htmx.org/essays/locality-of-behaviour/): the behaviour of a piece of code should be obvious from looking at that code. HTMX, Alpine.js and Tailwind all put behaviour and styling directly on the element, and the generated project applies the same idea to its Python code - tests live beside the modules they test, feature code (such as an app's API or webhooks) lives in the app that owns it, and shared abstractions are extracted only once more than one app uses them. See [`template/docs/project-structure.md`](template/docs/project-structure.md#locality-of-behaviour) for details.

Further reading:

- [Locality of Behaviour](https://htmx.org/essays/locality-of-behaviour/) - Carson Gross, the htmx essay that names the principle
- [Colocation](https://kentcdodds.com/blog/colocation) - Kent C. Dodds on keeping code, tests and styles close to where they are used
- [The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) - Sandi Metz on why duplication is cheaper than a premature abstraction
- [CSS Utility Classes and "Separation of Concerns"](https://adamwathan.me/css-utility-classes-and-separation-of-concerns/) - Adam Wathan, creator of Tailwind CSS, on styling at the element

[K3s](https://k3s.io) is a lightweight Kubernetes distribution that allows for easy deployment and scaling of applications. By using K3s, we can ensure that our application is production-ready and can handle increased traffic as needed. Helm Charts have been provided to deploy your project along with Grafana dashboards for monitoring. Full Github Actions CI/CD pipelines are included for testing and deployment.

This stack will be assessed constantly to ensure it remains the best choice for the target audience and use cases. If better tools or libraries become available, they will be evaluated and potentially integrated into the template in addition to or in place of the current choices.

If you want to change any of the fundamental building-blocks of the stack - for example, switching from HTMX to React, or deploying to AWS instead of Hetzner - you are encouraged to make the changes you need in your project or fork this repository. The goal is to provide a solid starting point, not to lock you into a specific stack or workflow that does not suit your needs.

## Design system

UI components are provided by [DaisyUI](https://daisyui.com/), a Tailwind CSS component library with 50+ production-ready components, built-in dark mode, and semantic theming. DaisyUI is vendored as `.mjs` files (no npm required) and works with the `django-tailwind-cli` standalone binary.

- 50+ ready-made components (buttons, forms, modals, drawers, tabs, etc.)
- Automatic dark/light mode via DaisyUI themes
- Semantic color system (`primary`, `secondary`, `error`, etc.)
- Focus on accessibility
- Responsive layouts

## Skills

Generated projects include `dj-*` Claude Code and OpenCode slash commands for common workflows:

**General**

| Command        | Summary                                                                           |
| -------------- | --------------------------------------------------------------------------------- |
| `/dj-bootstrap` | Start a new project: interview, run Copier, write `docs/this-project.md`, smoke test (Plugin skill: see [With Claude Code](#with-claude-code)) |
| `/dj-kickoff`  | Shape a new project from `docs/this-project.md`: user model, apps, languages, docs (Plugin skill: see [With Claude Code](#with-claude-code)) |
| `/dj-help`     | List all dj-\* commands or show help for a specific command                       |
| `/dj-sync`     | Preview the changelog, pull latest template changes via Copier and resolve merge conflicts interactively |
| `/dj-feedback` | Report a bug or improvement against the django-studio template                    |
| `/dj-doc`      | Create or update project-specific docs: domain, apps, rules, APIs, integrations   |

**Generators**

| Command                | Summary                                                                |
| ---------------------- | ---------------------------------------------------------------------- |
| `/dj-create-app`       | Create a Django app (apps.py, models, views, urls, admin, tests)       |
| `/dj-create-view`      | Add a view, template, and URL                                          |
| `/dj-create-task`      | Add a `django-tasks-db` background task with correct async patterns    |
| `/dj-create-command`   | Add a management command with tests                                    |
| `/dj-create-model`     | Design and write a Django model with recipe, fixture, and model tests  |
| `/dj-create-migration` | Create a data migration (Python or SQL)                                |
| `/dj-create-crud`      | Generate full CRUD views, templates, URLs, and tests                   |
| `/dj-create-e2e`       | Write Playwright E2E test(s) for a described user interaction          |
| `/dj-create-tag`       | Add a template tag (simple_tag, simple_block_tag, inclusion_tag, Node) |
| `/dj-create-filter`    | Add a template filter with correct escaping flags                      |

**Localisation**

| Command        | Summary                                                                                   |
| -------------- | ----------------------------------------------------------------------------------------- |
| `/dj-localize` | Add localization formats, extract strings, translate with TranslateBot, compile `.mo` catalogue |

**Audits**

| Command             | Summary                                                                      |
| ------------------- | ---------------------------------------------------------------------------- |
| `/dj-perf`          | Performance audit: N+1 queries, missing indexes, caching, async              |
| `/dj-secure`        | Security audit: settings, views, XSS, CSRF, IDOR, SQL injection              |
| `/dj-gdpr`          | GDPR compliance audit: PII in models, erasure, consent, logging              |
| `/dj-a11y`          | Accessibility audit: WCAG 2.1 AA — forms, icons, HTMX, Alpine, semantic HTML |
| `/dj-deadcode`      | Remove unused Python code, Django templates and static assets                |
| `/dj-remove-slop`   | Audit and remove Django anti-patterns introduced by AI or inattentive devs   |
| `/dj-full-coverage` | Enable 100% coverage gate and write tests for all uncovered lines            |

**Deployment**

| Command                 | Summary                                                                        |
| ----------------------- | ------------------------------------------------------------------------------ |
| `/dj-deploy`            | Interactive first-deploy wizard: provisions infra, configures secrets, deploys |
| `/dj-deploy-observe`    | Deploy the observability stack (Grafana + Prometheus + Loki)                   |
| `/dj-tailscale [cmd]`   | Enable, check or disable Tailscale private networking for the cluster          |
| `/dj-scale [n]`         | View or change the webapp replica count                                        |
| `/dj-rotate-secrets`    | Rotate auto-generated and third-party Helm secrets and redeploy                |
| `/dj-enable-db-backups` | Enable automated daily PostgreSQL backups to a private Object Storage bucket   |
| `/dj-db-backup`         | Trigger an immediate database backup without waiting for the daily cron        |
| `/dj-db-restore`        | Guided production database restore from Object Storage backup                  |
| `/dj-deploy-cron`       | Schedule a management command as a Kubernetes cron job                         |

### Feedback Loop

Two skills in particular are designed to help you provide feedback on the template itself: `dj-sync` and `dj-feedback`. The first allows you to pull in the latest template changes and resolve any merge conflicts interactively, while the second lets you report bugs or suggest improvements directly from your project.

This alleviates a common issue with template projects: once a project is generated, it can be difficult to keep it up to date with the latest improvements and fixes. By providing these skills, we aim to create a feedback loop that benefits both the template maintainers and the developers using it. As more developers use `django-studio`, we expect to receive valuable feedback that will help us refine the template and make it even more useful for the community.

## MCP Servers

Generated projects include project-local [MCP servers](https://modelcontextprotocol.io) configured in `.mcp.json` (gitignored, generated at project creation). These give AI assistants direct access to your local development environment.

| Server                                  | Purpose                                                           |
| --------------------------------------- | ----------------------------------------------------------------- |
| `@modelcontextprotocol/server-postgres` | Direct database queries and schema inspection                     |
| `@playwright/mcp`                       | Browser automation and E2E test debugging                         |
| `mcp-django`                            | Django shell — ORM queries, model introspection, arbitrary Python |

See `docs/mcp.md` in the generated project for usage and security notes.

## Hosting

[Hetzner Cloud](https://hetzner.com) is a cost-effective, EU-based hosting provider. Cloudflare is currently the cheapest and most secure option for DNS, CDN, SSL, and DDoS protection. These solutions will be reviewed on a regular basis - if better options become available, they will be offered instead of or addition to these choices.

The point is that hosting is **low and fixed**. You pay per server, not per request, so the bill is the same whether the app is idle or busy - no egress charges, no per-request fees, no autoscaling that runs away. The default single-node topology is the cheapest option, and each role you split onto its own node adds exactly one server to the bill. See [Hetzner's pricing](https://www.hetzner.com/cloud/) for current rates.

### Private networking with Tailscale

[Tailscale](https://tailscale.com) is supported as an optional extra. When enabled, every node joins a private WireGuard mesh and SSH and the Kubernetes API travel over the tailnet instead of the public internet, so ports 22 and 6443 can be closed to everyone else. Ports 80 and 443 stay open for web traffic via Cloudflare.

It is **off by default** - there is no Copier question for it. Set `tailscale_oauth_client_secret` in `terraform/hetzner/terraform.tfvars`, or run `/dj-tailscale enable`, which handles both a fresh deploy and retrofitting a cluster that is already running.

Tailscale's free tier covers 3 users and 100 devices, so for solo projects and small teams this adds no cost. See `docs/infrastructure.md` in the generated project for the full setup.

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

| Tool                                                           | Purpose                                                      | Install          |
| -------------------------------------------------------------- | ------------------------------------------------------------ | ---------------- |
| [Terraform](https://developer.hashicorp.com/terraform/install) | Provision Hetzner infrastructure and Cloudflare DNS          | See install docs |
| [Helm](https://helm.sh/docs/intro/install/)                    | Deploy Kubernetes workloads                                  | See install docs |
| [kubectl](https://kubernetes.io/docs/tasks/tools/)             | Kubernetes CLI                                               | See install docs |
| [hcloud](https://github.com/hetznercloud/cli)                  | Hetzner Cloud CLI                                            | See install docs |
| [tailscale](https://tailscale.com/download)                    | Only if Tailscale is enabled - required to reach the cluster | See install docs |

See `docs/deployment.md` in the generated project for full deployment instructions.
