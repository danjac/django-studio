This is a cookiecutter project to create a new Django project.

## Testing

Create a new project in `/tmp` using the cookiecutter template:

```bash
uvx cookiecutter --no-input --output-dir /tmp ./
```

If a project has already been created in `/tmp`, remove it first (stop services to avoid port conflicts):

```bash
cd /tmp/my_django_project
just stop
cd ..
trash my_django_project
```

Then navigate to the generated project and test it:

```bash
cd /tmp/my_django_project
cp .env.example .env
just start                      # start Docker services
just install                    # install Python deps + pre-commit hooks
just precommit run --all-files  # run all pre-commit hooks
just lint                       # run linters
just typecheck                  # run type checks
just dj makemigrations          # generate initial users migration (expected on first run)
just test                       # run tests
just stop                       # stop Docker services
```

**Expected on first run:**

- `just test` will report coverage below 100%. This is normal — the template ships utility
  modules (`admin.py`, `db/search.py`, `http/`) as starting points without tests. The 100%
  coverage target is a goal for developers to reach as they build their project, not a
  gate on the initial scaffold.
- `just dj makemigrations` is required before `just test` because the `users` app ships
  without an initial migration. Developers are expected to customise the `User` model
  fields before generating migrations.

**Note:** Run `uv sync` from the cookiecutter repo root first if working from a fresh clone and the virtual environment doesn't exist yet. This installs the cookiecutter tooling itself; it is separate from the generated project's dependencies.

## Cookiecutter Project Testing

The cookiecutter project itself has its own tests and pre-commit config. Run these from the root directory:

```bash
just check      # Run lint, format, and tests
just test       # Run pytest
just lint       # Run ruff on tests
just format     # Check formatting
```

To install pre-commit hooks for the cookiecutter project itself:

```bash
uv run pre-commit install
```

Run pre-commit hooks on all files in the cookiecutter project to ensure all checks pass:

```bash
git init && git commit -A && pre-commit run --all-files
```

## Feature Flags

`cookiecutter.json` exposes four boolean feature flags. The post-generation hook (`hooks/post_gen_project.py`) removes unused files based on these selections:

| Flag           | Default | Effect when disabled                      |
| -------------- | ------- | ----------------------------------------- |
| `use_hx_boost` | `"y"`   | Removes HTMX boost config                 |
| `use_storage`  | `"y"`   | Removes `terraform/storage/`              |
| `use_i18n`     | `"n"`   | Removes i18n middleware and locale config |
| `use_pwa`      | `"n"`   | Removes PWA manifest and service worker   |

When adding template files that are conditional on a flag, update `hooks/post_gen_project.py` — do not hard-delete files from the template directory itself. When adding files that contain Django or Tailwind `{{ }}` syntax, add their paths to `_copy_without_render` in `cookiecutter.json` so cookiecutter copies them verbatim instead of treating them as Jinja2 templates.

## Design System

The template includes a component library in `{{cookiecutter.project_slug}}/design/`. When modifying or adding UI components in the generated project, check the design system first:

- `design/README.md` — component index and design tokens
- `design/navigation.md` — navbar, sidebar, user dropdown
- `design/forms.md` — form wrapper, field template, input classes
- `design/buttons.md` — button variants
- `design/messages.md` — toast alerts
- `design/cards.md` — link card component
- `design/pagination.md` — paginated list
- `design/typography.md` — markdown/prose, heading scale
- `design/layout.md` — base templates, page layout patterns

Components are sourced from the `radiofeed-app` production codebase and generalized for reuse. When adding a component to the template, add a corresponding doc to `design/`.

## Bugs and Improvements

Use the `/django-studio cookiecutter` skill to report bugs or suggest improvements to this template — it posts a GitHub issue directly. Requires the `gh` CLI authenticated with GitHub access.

After editing `{{cookiecutter.project_slug}}/.claude/commands/django-studio.md`, run `just sync-skills` to propagate the change to `~/.claude/commands/`.
