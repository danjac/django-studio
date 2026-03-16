This is a Copier template to create a new Django project.

## Testing

Create a new project in `/tmp` using the Copier template:

```bash
uvx copier copy --trust --defaults --data project_name="My App" . /tmp/my_app
```

If a project has already been created in `/tmp`, remove it first (stop services to avoid port conflicts):

```bash
cd /tmp/my_app
just stop
cd ..
trash my_app
```

Then navigate to the generated project and test it:

```bash
cd /tmp/my_app
just start                      # start Docker services
just install                    # copies .env.example→.env, git init, Python deps, pre-commit hooks
just lint                       # run linters
just typecheck                  # run type checks
just dj makemigrations          # generate initial users migration (expected on first run)
just test                       # run tests
just test-e2e                   # run Playwright E2E tests
just stop                       # stop Docker services
```

**Pre-commit must report no lint errors** on the generated project. Auto-formatters
(ruff-format, DjHTML, DjCSS, Djade) modifying files is expected and fine. Actual
lint errors (`ruff check`, `djlint --lint`) must be zero. Run after install:

```bash
cd /tmp/my_app && uv run pre-commit run --all-files
```

**Expected on first run:**

- `just test` will report coverage below 100%. This is normal - the template ships utility
  modules (`admin.py`, `db/search.py`, `http/`) as starting points without tests. The 100%
  coverage target is a goal for developers to reach as they build their project, not a
  gate on the initial scaffold.
- `just dj makemigrations` is required before `just test` because the `users` app ships
  without an initial migration. Developers are expected to customise the `User` model
  fields before generating migrations.

**Note:** Run `uv sync` from the repo root first if working from a fresh clone and the virtual environment doesn't exist yet. This installs the Copier tooling itself; it is separate from the generated project's dependencies.

## Template Project Testing

The template project itself has its own tests and pre-commit config. Run these from the root directory:

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

## Working on the Template

Before adding or modifying any code under `template/`, read the generated project's documentation first:

- `template/AGENTS.md.jinja` — agent workflow, conventions, and command reference
- `template/docs/` — all reference docs (Django config, views, models, packages, HTMX, etc.)
- `template/design/` — component library and design tokens

These docs describe the patterns, types, and conventions the generated project uses. Code that ignores them will be wrong.

After any change to `template/`, regenerate the project and verify all checks pass before committing:

```bash
cd /tmp && trash my_app
uvx copier copy --trust --defaults --data project_name="My App" . /tmp/my_app
cd /tmp/my_app
git init && git add -A
uv run pre-commit run --all-files   # run twice if hooks auto-fix files
uv run pre-commit run --all-files
just typecheck
```

**Do not commit until all checks are clean.**

## Feature Flags

`copier.yml` exposes five boolean feature flags. The post-generation hook (`hooks/post_gen_project.py`) removes unused files based on these selections:

| Flag               | Default | Effect when disabled                          |
| ------------------ | ------- | --------------------------------------------- |
| `use_storage`      | `true`  | Removes `terraform/storage/`                  |
| `use_pwa`          | `true`  | Removes PWA manifest and service worker        |
| `use_opentelemetry`| `true`  | Removes observability Helm chart               |
| `use_sentry`       | `true`  | Removes Sentry SDK from settings and pyproject |

When adding template files that are conditional on a flag, update `hooks/post_gen_project.py` — do not hard-delete files from the template directory itself.

**Jinja2 processing:** Only files with a `.jinja` suffix are processed by Copier's Jinja2 engine; all other files are copied verbatim. Files that contain conflicting `{{ }}` syntax (e.g. `justfile` uses `{{ args }}`, GitHub Actions workflows use `${{ }}`) must remain plain files and use `PROJECT_SLUG` as a plain-text placeholder, substituted by the hook.

## Design System

The template includes a component library in `template/design/`. When modifying or adding UI components in the generated project, check the design system first:

- `design/README.md` - component index and design tokens
- `design/Navigation.md` - navbar, sidebar, user dropdown
- `design/Forms.md` - form wrapper, field template, input classes
- `design/Buttons.md` - button variants
- `design/Messages.md` - toast alerts
- `design/Cards.md` - link card component
- `design/Pagination.md` - paginated list
- `design/Typography.md` - markdown/prose, heading scale
- `design/Layout.md` - base templates, page layout patterns

When adding a component to the template, add a corresponding doc to `design/`.

## djstudio Commands

The `/djstudio` skill uses a thin dispatcher (`skills/djstudio.md`) that routes each subcommand to its own instructions file under `skills/djstudio/`. The post-gen hook copies the entire `skills/` tree to `.claude/commands/` in the generated project.

**Adding or changing a subcommand:**

1. Create or edit the file at `skills/djstudio/<subcommand>.md`.
2. Add or update the row in the dispatcher table in `skills/djstudio.md`.
3. Update the subcommand table in `template/AGENTS.md.jinja`.
4. Always update relevant docs when adding, removing, or changing a command — at minimum:
   - `template/AGENTS.md.jinja` — subcommand table
   - `template/README.md.jinja` — slash command table in the generated project
   - `README.md` — slash command table in this repo root
   - Any `docs/` page the subcommand references or produces output for

**Tracking in version control:**

Command files live in `skills/` at the repo root and are copied to `.claude/commands/` in the generated project by the post-gen hook (`install_skills()`). They are always tracked in git — no `git add -f` needed.

**Copying to global commands:**

After editing any djstudio command file, copy it to `~/.claude/commands/` if you want the change reflected in the global command registry:

```bash
cp skills/djstudio.md ~/.claude/commands/djstudio.md
```

**Adding new subcommand files:**

Create the file under `skills/djstudio/<subcommand>.md`. No `cookiecutter.json` change is needed — the post-gen hook copies the entire `skills/` tree verbatim.

## Bugs and Improvements

Use the `/djstudio feedback` skill to report bugs or suggest improvements to this template - it posts a GitHub issue directly. Requires the `gh` CLI authenticated with GitHub access.
