---
description: Start a new django-studio project with Copier, then smoke test it
---

Create a new Django project from the django-studio Copier template. Copier does the
generating: this skill gathers the answers, runs `copier copy` non-interactively, and
checks the result. The project is identical to one made with `uvx copier copy`, so
`copier update` and `/dj-sync` work on it.

Arguments: `$ARGUMENTS` — a free-text description of the project, e.g.
`"recipe sharing site for home cooks"`. May be empty.

**Never ask for something the arguments or earlier answers already give.** Before each
question, check whether the prompt states or clearly implies the answer, and use it.

## 1. Preflight

```bash
for cmd in uv just docker gh git; do command -v "$cmd" >/dev/null || echo "missing: $cmd"; done
docker info >/dev/null 2>&1 || echo "docker daemon not running"
ls -A
```

If a tool is missing or Docker is not running, stop and tell the user what to install
or start:

| Tool | Install |
| ---- | ------- |
| `uv` | https://docs.astral.sh/uv/getting-started/installation/ |
| `just` | https://just.systems/man/en/packages.html |
| `docker` | https://docs.docker.com/get-started/get-docker/ |
| `gh` | https://cli.github.com/ |

The target directory is the current directory when it is empty. Otherwise it is
`./<project_slug>`, which must not exist or must be empty; decide this after step 2,
once the slug is known. Stop if neither works.

## 2. Copier answers

The questions come from the template's `copier.yml`:

| Answer | Source |
| ------ | ------ |
| `project_name` | Ask if the prompt doesn't name the project. Suggest a name based on the purpose |
| `description` | The one-line purpose, taken from the prompt when it has one |
| `project_slug` | Default: `project_name` lower-cased, spaces and hyphens replaced by `_` |
| `package_name` | Always equal to `project_slug` |
| `author` | `git config user.name` |
| `author_email` | `git config user.email` |
| `domain` | From the prompt, else `example.com` (can be changed before deploying) |
| `license` | From the prompt, else `MIT`. One of: MIT, Apache-2.0, GPL-3.0, AGPL-3.0, LGPL-3.0, MPL-2.0, BSD-2-Clause, BSD-3-Clause, ISC, EUPL-1.2, None |

Ask only for the project name and purpose, if missing. Fill in the rest from the
sources above, then show all answers in one summary, with the target directory, and
ask the user to confirm or change any of them.

`project_slug` must be a valid Python identifier that doesn't shadow a standard library
or installed package (e.g. not `test`, `django`, `site`). Propose a different slug if it
does.

## 3. Domain interview

Ask about the product; Copier doesn't cover it. Skip anything the prompt already
answers, and ask the rest in one or two rounds, not one question at a time:

- Core entities: the main things users create, browse or manage
- User roles, and what each can do
- Public site, or login required for most pages
- Languages the UI needs
- Whether it needs a public API, incoming webhooks, or background tasks (email,
  imports, scheduled jobs)

The user may skip any question; record it as `_TODO_` in step 5. Keep the answers
for step 5. Stack choices are fixed by the template, so don't ask about packages or
frameworks.

## 4. Generate

Run Copier with every answer passed as `--data`, quoting each value:

```bash
uvx copier copy --trust --defaults \
    --data project_name="<project_name>" \
    --data project_slug="<project_slug>" \
    --data package_name="<project_slug>" \
    --data description="<description>" \
    --data author="<author>" \
    --data author_email="<author_email>" \
    --data domain="<domain>" \
    --data license="<license>" \
    gh:danjac/django-studio <target>
```

When the user names another template source, such as a fork or a local checkout,
use it in place of `gh:danjac/django-studio`. Add `--vcs-ref <branch>` only when the
user asks for a specific template branch.

If Copier fails, show the error and stop.

## 5. Write the project overview

Record the interview in `<target>/docs/this-project.md`, the project's permanent
overview. It is committed with the scaffold, the project's `AGENTS.md` tells agents
to read it, and `/dj-kickoff` and `/dj-doc` build on it later.

The generated file is a stub with guidance under each heading. Keep every heading
and fill in these sections, replacing their guidance and placeholder rows:

| Section | From the interview |
| ------- | ------------------ |
| Purpose | The one-line purpose, plus any detail the user gave |
| Users and Roles | One table row per role, with what it can do |
| Glossary | One entry per core entity: what it is and who creates it |
| Key Decisions | One row each, dated today: public or login-only access, the UI languages (the first is the default), and the public API, incoming webhooks and background tasks, each as "planned" (with what for) or "not needed" |

Write `_TODO: <what is missing>_` for anything the user skipped. Under Key Flows,
replace the guidance with `_TODO: the main end-to-end journeys_`. Leave Apps and
Integrations as they are: `/dj-doc` fills them from the code.

Remove the `<!-- dj-doc: stub -->` line and the `> **Stub.**` note, so `/dj-doc`
treats the page as written and keeps these answers.

## 6. Smoke test

From the target directory, run each step in order and stop at the first failure:

```bash
just start                  # Docker services
just install                # .env, git init, Python deps, pre-commit hooks, Playwright
just dj makemigrations      # the users app ships without an initial migration
just dj migrate
just check-all              # lint, typecheck, Django checks, unit and E2E tests
```

On failure, show the failing command and the relevant output, and stop. A freshly
generated project should pass every step, so a failure is a template bug: suggest
reporting it with `/dj-feedback` from inside the project. Don't edit generated files
to make the checks pass.

## 7. Finish

`just install` has run `git init`. Make the first commit:

```bash
git add -A
git commit -m "chore: initial commit from django-studio"
```

Ask whether to create a GitHub repository. It publishes the code, so wait for a
yes, and ask whether it should be private (the default) or public:

```bash
gh repo create <project_slug> --private --source=. --push
```

Ask whether to kick off the project now: `/dj-kickoff` turns
`docs/this-project.md` into a user model, domain apps and models, and languages.
If yes, run `/dj-kickoff <target>` and continue here when it finishes.

Then print the next steps:

1. Quit Claude Code, then `cd <target>` (when it is a subdirectory) and start
   Claude Code again. The project's own `/dj-*` skills and docs load only in a
   session started in the project.
2. `/dj-kickoff`, if it didn't run above.
3. `just dj set_default_site localhost:8000 "<project_name>"`
4. `just dj createsuperuser`
5. `just serve`, then open http://localhost:8000
6. `/dj-deploy` when you are ready to go live.
