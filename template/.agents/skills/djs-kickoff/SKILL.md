---
description: Shape a new project from its overview (user model, apps, languages, docs)
---

Give a new django-studio project its first shape from the product overview in
`docs/this-project.md`: the `User` model, domain apps and models, languages, the
rest of the project docs, and a backlog of what comes next. This skill only orchestrates. Each step follows
another project skill or doc, so the result matches what those skills produce
when run by hand.

## 1. Check the project

Work from the project root for the rest of this skill. Check what setup has
already run, and run only what's missing:

1. If `.env` or `.venv` is missing, run `just install`. It creates `.env`, runs
   `git init`, and installs the dependencies and pre-commit hooks.
2. Start the services:

   ```bash
   just start --wait
   ```

3. If the repository has no commits (`git rev-parse --verify HEAD` fails), commit
   the scaffold as it is, so this skill's changes get their own commit:

   ```bash
   git add -A
   git commit -m "chore: initial commit from django-studio"
   ```

   Otherwise, if `git status --porcelain` shows uncommitted changes, ask whether to
   continue: this skill ends with a commit of everything it changed.

Read `.copier-answers.yml` for `package_name`, and read `docs/this-project.md`. If
it still has the `<!-- djs-doc: stub -->` line, the overview hasn't been written:
ask the product questions and write the page as `references/overview.md`
describes, then continue.

The rest of this skill calls the page "the overview". It may have been edited
since it was written; take it as it is now.

## 2. Choose the steps

Show the steps below, each with one line on what it will do for this project,
and ask which to run. Default: all of them. Skip a step the overview makes
pointless (e.g. Languages when English is the only UI language) and say why.

1. User model (its migration commands run even if the user skips the rest of
   the step)
2. Domain apps and models
3. Languages
4. Project docs
5. Backlog and changelog

## How to run a project skill

Run each skill by reading `.agents/skills/<name>/SKILL.md` and following it, with
the project root as the working directory. This works whether or not the session
has loaded the project's skills, for example when `/djs-bootstrap` hands over in
the session that created the project.

Those skills ask questions one at a time. Answer them from the overview and from
the choices the user confirmed in this skill, and ask the user only what neither
settles. Where a skill asks for approval of something the user has already
confirmed here (such as a model sketch), treat it as approved.

## 3. User model

Compare `<package_name>/users/models.py` with the overview's roles and anything it
says about user profiles. Read `docs/authorization.md` first: roles are permission
predicates over existing data, not fields on `User`, so most projects need no
change here.

Propose the fields to add, if any, or "no changes", and wait for confirmation. For
each field, follow `docs/django-models.md`. Personal data (names, bios, locations)
must also be handled in `<package_name>/users/gdpr.py`; see `docs/gdpr.md`.

Then run the migrations, even with no changes or when the user skipped this step.
The template ships the `users` app without a migration, and the domain models'
foreign keys to `User` need one. If there is none yet, this creates
`0001_initial`, including any new fields:

```bash
just dj makemigrations users
just dj migrate
```

Update the user recipe and tests in `<package_name>/users/tests/` if the new
fields need values.

## 4. Domain apps and models

Propose a breakdown from the overview's Glossary and Users and Roles:

- The apps, each named in lower-case plural (e.g. `recipes`). Group entities that
  change together into one app, following `docs/project-structure.md`. An app name
  must not shadow a Python standard library module or an installed package
  (e.g. not `collections`, `calendar`, `email`).
- For each model: its fields with types and options, foreign keys (including to
  the user model), `__str__`, and whether to register it in the admin.
- Which models get CRUD views.

Keep models to what the overview states. Show the whole breakdown at once and wait
for the user to approve or change it. Then, for each app in turn:

1. `djs-create-app <app>`
2. `djs-create-model <app> <Model>` for each model, in dependency order. Run the
   migrations when the skill offers to.
3. `djs-create-crud <app> <Model>` for each model marked for CRUD.

## 5. Languages

If English is the only UI language, skip this step. The source strings are
already English and marked for translation, so nothing is needed until another
language is added, and `gettext` isn't required.

For each UI language in the overview's Key Decisions other than English, follow
`djs-localize` in single-locale mode for that locale:

- Check `gettext` first (its prerequisite 1). If it is missing, show the install
  command for the user's OS from that prerequisite, ask them to install it and
  say when it's done, then check again. If they'd rather not, skip this step and
  tell them to run `/djs-localize <locale>` once `gettext` is installed.
- TranslateBot (its prerequisite 2) is optional here. If `.env` has no
  `TRANSLATEBOT_API_KEY`, don't ask for one: run the steps that don't translate
  (`makemessages`, `LANGUAGES`, the format module, the plural forms and
  `compilemessages`) and skip steps 6 and 8. Tell the user to run
  `/djs-localize <locale>` once they have a key.

## 6. Project docs

Run `djs-doc` with no argument, now that the apps exist. It keeps the overview's
written sections, fills in the Apps and Integrations sections from the code, and
writes a README for each new app. Answer its questions from the overview and the
breakdown the user confirmed; leave `_TODO_` markers for the rest rather than
asking about every gap.

## 7. Backlog and changelog

Don't build anything in this step. Create the backlog of work that comes next, and
the project's changelog, following
`.agents/skills/djs-backlog/references/backlog-format.md` and
`.agents/skills/djs-backlog/references/changelog-format.md`. Check where the
backlog lives as "Where the backlog lives" in `.agents/skills/djs-backlog/SKILL.md`
says: GitHub issues if the project has a GitHub remote, otherwise
`docs/backlog.md`.

**`CHANGELOG.md`**: the intro and an empty `## Unreleased` section. The work this
skill did is the starting point, not a change, so it gets no entry.

**Backlog**:

- **Features**: each feature the overview's Key Decisions lists as planned, with
  where to start:

  | Feature | Start with |
  | ------- | ---------- |
  | Public API | `docs/building-apis.md` |
  | Incoming webhooks | `docs/webhooks.md` |
  | Background tasks | `/djs-create-task`, `docs/django-tasks.md` |
  | Scheduled jobs | `/djs-deploy-cron`, `docs/cron-jobs.md` |

  Also add CRUD views (`/djs-create-crud <app> <Model>`) for any model the user
  chose not to give them in step 4, if the overview implies users manage it.
- **Chores**: the `_TODO_` gaps left in `docs/this-project.md` (Key Flows
  especially); each language set up in step 5 but not translated, as
  `/djs-localize <locale>`; and the path to production: E2E tests for the key
  flows (`/djs-create-e2e`), `/djs-secure`, `/djs-a11y`, `/djs-perf`,
  `/djs-full-coverage` and `/djs-deploy`. Block the E2E tests on the Key Flows
  item, and `/djs-full-coverage` and `/djs-deploy` on the planned features.
- **Bugs**: none.

Show the backlog in order, with each item's type, priority and blockers, and wait
for the user to approve or change it. Then write `docs/backlog.md`, or, with a
GitHub remote, create the labels, issues and blockers as "Moving to GitHub issues"
in `backlog-format.md` describes. If they skip this step, still create
`CHANGELOG.md`.

## 8. Check and commit

```bash
just check-all
```

If it fails, fix the code this skill generated, following the project's docs,
and run it again. Don't change template files to make it pass. If it still
fails, stop and report the failure without committing.

```bash
git add -A
git commit -m "feat: kick off project from the overview"
```

If the project has a GitHub remote, ask before pushing.

Print a summary: apps and models created (with CRUD or not), `User` changes,
languages set up (translated or waiting for `/djs-localize`), the docs written,
the backlog's first few items, and any steps skipped. End with: start Claude Code
in the project if this session started elsewhere, then `just serve`, and
`/djs-backlog next` to pick up the first item.
