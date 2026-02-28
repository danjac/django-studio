# django-studio

Cookiecutter template for Django projects with HTMX, Alpine.js, and Tailwind CSS.

This project is designed to be a starting point for building modern Django applications with a focus on simplicity, performance, and developer experience. It includes a carefully curated stack of tools and libraries to help you get up and running quickly while following best practices. It includes Markdown documentation and a design pattern library to assist with AI-driven development and code generation while keeping skilled developers in the loop.

## Stack

- Python 3.14, Django 6.0, PostgreSQL 18, Redis 8
- HTMX + Alpine.js + Tailwind CSS (no JS build step)
- uv for dependency management
- just for task running
- django-tasks-db for background tasks (not Celery)
- django-allauth for authentication
- Hetzner Cloud for hosting (K3s)
- Design pattern library
- Full test coverage (pytest + Playright)

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

The `/django-studio` skill is used to provide feedback for this cookiecutter while working on a generated project. It has two options:

- `/django-studio improvement`: Add a suggestion to improve the cookiecutter template based on your experience using it.
- `/django-studio bug`: Report a bug you encountered while using the generated project. Copy and paste any relevant stack traces or other error messages.

These are added to the documents `IMPROVEMENTS.md` and `BUGS.md` respectively in this project. Bugs are prioritized over improvements, and the most upvoted items in each document are the ones that will be worked on first.
