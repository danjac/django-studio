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

The template uses [DaisyUI](https://daisyui.com/components/) for component styling (vendored as `.mjs` files in `template/tailwind/` — no npm). Project-specific patterns (forms, pagination, navigation, messages) are documented in `template/docs/Django-Templates.md`. Component classes, icons, dark mode, and Tailwind configuration are in `template/docs/Design.md`.

## dj-* Commands

Each slash command is a standalone skill at `template/.agents/skills/dj-<command>/SKILL.md`. The `.agents/` tree lives under `template/` and is copied verbatim by Copier into generated projects. The post-gen hook scans `.agents/skills/*/SKILL.md` and writes one stub per skill at `.claude/commands/<name>.md` — no list to maintain.

Supporting files (checklists, prompt templates, report templates, etc.) live in a `resources/` subdirectory: `template/.agents/skills/dj-<command>/resources/`.

### Writing a new skill

**SKILL.md structure** — every skill file must follow this layout:

```markdown
---
description: One-sentence summary shown in opencode.json and the UI (≤80 chars)
---

<workflow prose — steps, code blocks, decisions>

---

## Help

**/dj-<command> [args]**

<user-facing docs for the command>
Include: usage line, arguments, what it does, at least one example.
```

**Checklist when adding a command:**

1. Create `template/.agents/skills/dj-<command>/SKILL.md` with frontmatter + `## Help`.
2. Add supporting files in `resources/` if the skill has reference data or fill-in
   templates (e.g. `resources/PLURAL_FORMS.md`, `resources/ISSUE_TEMPLATE.md`).
   Reference them from `SKILL.md` as `resources/<FILE>`.
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

## Bugs and Improvements

Use the `/dj-feedback` skill to report bugs or suggest improvements to this template - it posts a GitHub issue directly. Requires the `gh` CLI authenticated with GitHub access.
