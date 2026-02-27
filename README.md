# django-studio

Cookiecutter template for Django projects with HTMX, Alpine.js, and Tailwind CSS.

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
just dj migrate
just serve        # Dev server + Tailwind watcher
```

See `docs/` for full documentation.
