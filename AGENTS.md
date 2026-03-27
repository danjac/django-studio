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

These docs describe the patterns, types, and conventions the generated project uses. Code that ignores them will be wrong.

**Naming convention:** all files under `template/docs/` and `template/.agents/skills/*/resources/` use lower-kebab-case (e.g. `django-views.md`, `help.md`). New docs and resource files must follow the same pattern.

After any change to `template/`, regenerate the project and verify all checks pass before committing:

```bash
cd /tmp && trash my_app && find /tmp/.Trash-1000 -mindepth 1 -delete
uvx copier copy --trust --defaults --data project_name="My App" . /tmp/my_app
cd /tmp/my_app
git init && git add -A
uv run pre-commit run --all-files   # run twice if hooks auto-fix files
uv run pre-commit run --all-files
just typecheck
```

**Always trash and delete the old project before regenerating.** Stale generated
projects cause `just check` to pass locally while CI fails — the repo-level tests in
`tests/test_project.py` regenerate from scratch every run and catch mismatches that
a cached `/tmp/my_app` hides.

**Do not commit until all checks are clean.**

**Jinja2 processing:** Only files with a `.jinja` suffix are processed by Copier's Jinja2 engine; all other files are copied verbatim. Files that contain conflicting `{{ }}` syntax (e.g. `justfile` uses `{{ args }}`, GitHub Actions workflows use `${{ }}`) must remain plain files and use `PROJECT_SLUG` as a plain-text placeholder, substituted by the hook.

## UI Components

The template uses [DaisyUI](https://daisyui.com/components/) for component styling (vendored as `.mjs` files in `template/tailwind/` — no npm). Project-specific patterns (forms, pagination, navigation, messages) are documented in `template/docs/django-templates.md`. Component classes, icons, dark mode, and Tailwind configuration are in `template/docs/design.md`.

## Slash Commands

Each slash command is a standalone skill at `template/.agents/skills/<command>/SKILL.md`. The `.agents/` tree lives under `template/` and is copied verbatim by Copier into generated projects. The post-gen hook scans `.agents/skills/*/SKILL.md` and writes one stub per skill at `.claude/commands/<name>.md` — no list to maintain.

Supporting files (Markdown docs, prompt templates, JSON/text reference data) live in a `resources/` subdirectory: `template/.agents/skills/<command>/resources/`.

Python helper scripts live in a `bin/` subdirectory: `template/.agents/skills/<command>/bin/`.

Files shared across multiple skills live in `template/.agents/skills/resources/` (docs) or `template/.agents/skills/bin/` (scripts) and are referenced as `.agents/skills/resources/<file>` or `.agents/skills/bin/<file>` from SKILL.md prose.

### Writing a new skill

**SKILL.md structure** — every skill file must follow this layout:

```markdown
---
description: One-sentence summary shown in opencode.json and the UI (≤80 chars)
---

<workflow prose — steps, code blocks, decisions>
```

**resources/help.md** — every skill must have one. Content:

```markdown
**/<command> [args]**

<user-facing docs for the command>
Include: usage line, arguments, what it does, at least one example.
```

All resource files use lower-kebab-case (e.g. `help.md`, `factory-reference.md`).

**Checklist when adding a command:**

1. Create `template/.agents/skills/<command>/SKILL.md` with frontmatter.
2. Create `template/.agents/skills/<command>/resources/help.md` with usage docs.
3. Add Markdown/JSON/text reference files in `resources/` if the skill needs them
   (e.g. `resources/plural-forms.md`, `resources/issue-template.md`).
   Add Python helper scripts in `bin/` (e.g. `bin/my-script.py`).
   Reference them from `SKILL.md` as `resources/<file>` or `bin/<file>`.
3. The post-gen hook auto-discovers the skill (no list to update) and generates
   `opencode.json` from the frontmatter `description` field.
4. Update relevant docs:
   - `template/AGENTS.md.jinja` — command table
   - `template/README.md.jinja` — slash command table in the generated project
   - `README.md` — slash command table in this repo root
   - Any `docs/` page the command references or produces output for

   **The `## Skills` section in `README.md` and the `## Slash Commands` section in
   `template/README.md.jinja` must stay in sync**: same sections (General, Generators,
   Localisation, Audits, Deployment), same command list, same summaries.

**Tracking in version control:**

Skill files live in `template/.agents/` and are copied verbatim by Copier into the generated project's `.agents/`. They are tracked in git — no `git add -f` needed.

### Writing Python helper scripts for skills

Scripts live in `template/.agents/skills/bin/` (shared) or
`template/.agents/skills/<command>/bin/` (command-specific).

**Always invoke with `uv run python`** — never plain `python`. This ensures the script
runs in the project's virtual environment rather than system Python, making behaviour
predictable and easier to debug.

```bash
# In SKILL.md code blocks:
uv run python .agents/skills/bin/my-script.py
```

**Ruff header for standalone scripts** — scripts outside a package need a noqa header.
See `template/.agents/skills/bin/random-slug.py` as the canonical example:

```python
# ruff: noqa: INP001, T201
```

- `INP001` — not part of a package (no `__init__.py`) — expected for skill scripts
- `T201` — `print` is intentional for CLI output

Other rules that commonly apply:
- `PTH123` — use `Path("file").read_text()` instead of `open("file")`
- `PLW2901` — don't reassign the loop variable; use a separate name for the transformed value

## Python 3.14 — `except` Without Parentheses (PEP 758)

`pyupgrade --py314` rewrites multi-exception handlers to the Python 3.14 syntax:

```python
# Before (pyupgrade rewrites this automatically)
except (ValueError, TypeError):

# After — correct Python 3.14 syntax (PEP 758)
except ValueError, TypeError:
```

**Do not revert this.** AI assistants commonly flag it as invalid syntax and revert
it to the parenthesised form — that is wrong. The parenthesised form is the
pre-3.14 style; the unparenthesised form is now correct.
See [pyright#10546](https://github.com/microsoft/pyright/issues/10546) for upstream tracking.

## Git Workflow

When the user requests any change — feature, bug fix, documentation update, or
otherwise — **always create a new branch**, commit the change there, push, and
open a pull request. Do **not** commit directly to `main` unless the user
explicitly instructs you to do so.

Before creating a new branch, ensure you are on `main`. If you are not:

- If all changes on the current branch are committed, check out `main` first.
- If there are uncommitted changes, **stop and ask the user for instructions**
  before proceeding.

## GitHub Issues

When asked to fix a GitHub issue, follow the Git Workflow above (new branch,
commit, PR). Always reference the issue in the PR so it closes on merge (e.g.
`Closes #123` in the PR body). **One issue per PR** — do not bundle multiple
issues together unless the user explicitly asks.

When asked to "fix all open issues":

1. Go through each open issue and check whether it is already addressed in
   `main`.
2. If already fixed — tell the user and ask whether to close it.
3. If not fixed — create a separate branch and PR for each issue, following
   the protocol above.

## Bugs and Improvements

Use the `/dj-feedback` skill to report bugs or suggest improvements to this template - it posts a GitHub issue directly. Requires the `gh` CLI authenticated with GitHub access.
