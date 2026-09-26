This is a Copier template to create a new Django project.

## General Rules

STOP and ask before applying a fix. Before making any changes, state your hypothesis about
the root cause and which files you plan to modify. Wait for confirmation before proceeding.
If the user corrects you, re-read the relevant code/docs before responding.

Do not make excessive or environment-specific changes beyond what was requested. If the
user asks for a targeted edit, make only that edit. Ask before adding dev/staging/production
variants.

When the user corrects you or says 'stop', immediately stop, acknowledge the correction,
and re-examine the situation from scratch. Do not repeat the same approach or question the
user's stated facts.

**Debugging — confirm root cause before fixing.** Before proposing any fix, state the
single most likely root cause and the specific evidence (file:line, ORM output, test
failure message) that confirms it. Do not propose a fix based on a guess. Keep a mental
list of hypotheses the user has already ruled out and never revisit them.

**Refactors and renames — lock scope before touching anything.** Before any rename,
move, or restructuring, list the exact file paths and symbol names you will change.
Wait for explicit approval. Do not touch anything outside that list, even if adjacent
code looks related.

**TDD gate for bug fixes.** Do not edit implementation code before a failing test exists
and you have run it and confirmed it fails for the right reason. Write the test, show the
failure output, wait for confirmation, then fix.

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

**Pre-commit must pass on the first run** on the generated project: no lint errors,
and no auto-formatter (ruff-format, pyupgrade, django-upgrade, DjHTML, Djade,
rustywind) may modify a file. If a hook rewrites a file, format the template source
to match; `tests/test_quality.py` enforces this. Run after install:

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

## Skill Evals

`tests/` checks the generated scaffold. `evals/` checks that the `djs-*` skills produce
working code: each case renders a fresh project, runs a skill headless with
`claude -p`, runs a shell check, and has an independent read-only `claude -p`
review the result.

```bash
just eval              # every case
just eval 02           # one case (file name prefix)
just eval --keep 02    # keep the generated project to inspect it
```

Evals cost tokens and take several minutes per case, so they are not part of
`just check` or CI. Run the affected cases when you change a skill, or a doc that a
skill tells the agent to read. Case format and rules: `evals/README.md`.

## Working on the Template

Before adding or modifying any code under `template/`, read the generated project's documentation first:

- `template/AGENTS.md.jinja` — agent workflow, conventions, and command reference
- `template/docs/` — all reference docs (Django config, views, models, packages, HTMX, etc.)

These docs describe the patterns, types, and conventions the generated project uses. Code that ignores them will be wrong.

**Locality of Behaviour:** template code and docs follow the principle described in
`template/docs/project-structure.md#locality-of-behaviour`. When adding to `template/`,
place code beside its caller (in the owning app or feature package) rather than in new
shared modules, and keep behaviour in `hx-*`/`x-data` attributes rather than separate
JavaScript. Doc examples must model this layout.

**Naming convention:** all files under `template/docs/` and `template/.agents/skills/*/references/` use lower-kebab-case (e.g. `django-views.md`, `help.md`). New docs and reference files must follow the same pattern.

After any change to `template/`, regenerate the project and verify all checks pass before committing
(documentation-only changes are exempt; see Git Workflow):

```bash
cd /tmp && trash my_app && find /tmp/.Trash-1000 -mindepth 1 -delete
uvx copier copy --trust --defaults --data project_name="My App" . /tmp/my_app
cd /tmp/my_app
git init && git add -A
uv run pre-commit run --all-files   # must pass first time; no files modified
just typecheck
```

**Always trash and delete the old project before regenerating.** Stale generated
projects cause `just check` to pass locally while CI fails — the repo-level tests in
`tests/test_project.py` regenerate from scratch every run and catch mismatches that
a cached `/tmp/my_app` hides.

**Do not commit until all checks are clean.**

**Jinja2 processing:** Only files with a `.jinja` suffix are processed by Copier's Jinja2 engine; all other files are copied verbatim. Files that contain conflicting `{{ }}` syntax (e.g. `justfile` uses `{{ args }}`, GitHub Actions workflows use `${{ }}`) must remain plain files and use `PROJECT_SLUG` as a plain-text placeholder, substituted by the hook.

## Writing Docs and Skills

Agents copy `template/docs/` and skill files closely, so their wording ends up in
generated code and agent behaviour. When writing or editing them:

- **Show the correct example, and drop the matching "don't" line.** A `Wrong` block
  earns its place only when the mistake is common and the correct example alone
  doesn't prevent it.
- **Give one reason, not a list of alternatives.** State the rule and why it holds.
- **Describe the current path only.** History and migration notes go in
  `CHANGELOG.md`.
- **Cross-reference instead of duplicating.** Link to the doc or section that owns
  the topic.
- **Cut filler.** Drop intensifiers ("genuinely", "truly", "actually", "very") and
  puffery ("robust", "seamless", "production-ready"). Say what the code does, or what
  a task takes, instead of calling it easy or straightforward.

## UI Components

The template uses [DaisyUI](https://daisyui.com/components/) for component styling (vendored as `.mjs` files in `template/tailwind/` — no npm). Project-specific patterns (forms, pagination, navigation, messages) are documented in `template/docs/django-templates.md`. Component classes, icons, dark mode, and Tailwind configuration are in `template/docs/design.md`.

## Slash Commands

Each slash command is a standalone skill at `template/.agents/skills/<command>/SKILL.md`. The `.agents/` tree lives under `template/` and is copied verbatim by Copier into generated projects. The post-gen hook scans `.agents/skills/*/SKILL.md` and writes one stub per skill at `.claude/commands/<name>.md` — no list to maintain.

Supporting files (Markdown docs, prompt templates, JSON/text reference data) live in a `references/` subdirectory: `template/.agents/skills/<command>/references/`.

Python helper scripts live in a `scripts/` subdirectory: `template/.agents/skills/<command>/scripts/`.

Files shared across multiple skills live in `template/.agents/skills/scripts/` (scripts) and are referenced as `.agents/skills/scripts/<file>` from SKILL.md prose.

### Writing a new skill

**SKILL.md structure** — every skill file must follow this layout:

```markdown
---
description: One-sentence summary shown in opencode.json and the UI (≤80 chars)
---

<workflow prose — steps, code blocks, decisions>
```

**references/help.md** — every skill must have one. Content:

```markdown
**/<command> [args]**

<user-facing docs for the command>
Include: usage line, arguments, what it does, at least one example.
```

All reference files use lower-kebab-case (e.g. `help.md`, `factory-reference.md`).

**Checklist when adding a command:**

1. Create `template/.agents/skills/<command>/SKILL.md` with frontmatter.
2. Create `template/.agents/skills/<command>/references/help.md` with usage docs.
3. Add Markdown/JSON/text reference files in `references/` if the skill needs them
   (e.g. `references/plural-forms.md`, `references/issue-template.md`).
   Add Python helper scripts in `scripts/` (e.g. `scripts/my-script.py`).
   Reference them from `SKILL.md` as `references/<file>` or `scripts/<file>`.
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

Scripts live in `template/.agents/skills/scripts/` (shared) or
`template/.agents/skills/<command>/scripts/` (command-specific).

Scripts must have a `#!/usr/bin/env -S uv run python` shebang and be `chmod +x`.
Invoke them directly — no `uv run python` prefix needed:

```bash
# In SKILL.md code blocks:
.agents/skills/scripts/my-script.py
```

This ensures the script runs in the project's virtual environment via uv.

**Ruff header for standalone scripts** — scripts with a shebang don't need `INP001`
(ruff recognises them as scripts, not package files). Only suppress what's used.
See `template/.agents/skills/scripts/random-slug.py` as the canonical example:

```python
# ruff: noqa: T201
```

- `T201` — `print` is intentional for CLI output

Other rules that commonly apply:
- `PTH123` — use `Path("file").read_text()` instead of `open("file")`
- `PLW2901` — don't reassign the loop variable; use a separate name for the transformed value

## Claude Code Plugin

`plugin/` is a Claude Code plugin with one skill, `/djs-bootstrap`
(`plugin/skills/djs-bootstrap/`): a conversational front end to `copier copy`. It is
not copied into generated projects. `.claude-plugin/marketplace.json` publishes it
with a `git-subdir` source, so installing it fetches only `plugin/`.

After generating, `/djs-bootstrap` hands over to the new project's own skills: it
writes `docs/this-project.md` by following
`.agents/skills/djs-kickoff/references/overview.md`, and offers to run
`/djs-kickoff` by following its `SKILL.md`. Keep project behaviour in those
project files, not in the plugin.

The root `README.md` lists `/djs-bootstrap` under General skills with a note that
it's a plugin skill; it is the one command that `template/README.md.jinja` doesn't
list.

Plugin skills follow the same `SKILL.md` + `references/help.md` layout as the
template skills. `/djs-bootstrap` passes each `copier.yml` question as `--data`, so when you
add, rename or remove a Copier question, update the skill too;
`tests/test_plugin.py` checks this and runs `claude plugin validate` on both
manifests when the `claude` CLI is installed.
Run `just eval 04` after changing `/djs-bootstrap`, and `just eval 05` after changing
`/djs-kickoff` or a skill it follows.

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

## Changelog

`CHANGELOG.md` records user-visible template changes; `/djs-sync` shows generated
projects the entries added since their last sync.

- With every user-visible `template/` change (code, templates, settings, skills,
  generated docs), add a bullet in the same commit under today's section, creating
  it if needed: `## <date +%y.%V.%u> - <YYYY-MM-DD>` with Keep-a-Changelog
  headings (`Added` / `Changed` / `Deprecated` / `Fixed` / `Removed`).
- Repo tooling, tests, evals and CI earn no entry.
- Call out changes likely to conflict on `copier update` (settings, renamed or
  removed files) under **Changed** or **Removed**.
- When the file grows past about 200 lines, delete the oldest sections.

## Git Workflow

When the user requests any change — feature, bug fix, or otherwise — **always
create a new branch**, commit the change there, push, and open a pull request.
Do **not** commit directly to `main` unless the user explicitly instructs you to
do so.

**Documentation-only changes:** tasks that only change documentation (Markdown
docs, `AGENTS.md`, READMEs, skill prose) do not normally require running tests
or creating a branch/PR, unless the user requests it.

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

Work on them ONE AT A TIME sequentially — do not use parallel agents or worktrees.
For each: create branch, fix, test, open PR, then move to the next issue.

1. Go through each open issue and check whether it is already addressed in
   `main`.
2. If already fixed — tell the user and ask whether to close it.
3. If not fixed — create a separate branch and PR for each issue, following
   the protocol above.

## Bugs and Improvements

Use the `/djs-feedback` skill to report bugs or suggest improvements to this template - it posts a GitHub issue directly. Requires the `gh` CLI authenticated with GitHub access.
