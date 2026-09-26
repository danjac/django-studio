# Changelog

User-visible changes to the django-studio template. `/dj-sync` shows the entries
added since your project's last update before it runs `copier update`.

Versions are date-based: `YY.WW.D` (ISO year, week and weekday, as printed by
`date +%y.%V.%u`), one section per day.

## 26.39.6 - 2026-09-26

### Added

- `/djs-backlog`: keeps the project's work queue in `docs/backlog.md` (bugs,
  features and chores, with blockers and linked GitHub issues) and its own
  `CHANGELOG.md`. `/djs-backlog next` suggests the first unblocked item and, once
  you approve, opens an issue, does the work on a branch and opens a PR;
  `/djs-backlog release` turns `Unreleased` into a tagged release. Run
  `/djs-backlog` in an existing project to create both files.
- `/djs-kickoff` writes the first backlog and creates `CHANGELOG.md`, in place of
  its "Optional features" step. `AGENTS.md` asks for a changelog entry with every
  user-visible change.
- A `django-studio` Claude Code plugin with a `/dj-bootstrap` skill: a conversational
  front end to `copier copy` that asks for the Copier answers and a few product
  questions, generates the project, records the product answers in
  `docs/this-project.md`, runs `just check-all` and makes the first commit. See
  "With Claude Code" in the README.
- `/dj-kickoff`: shapes a new project from `docs/this-project.md` by following the
  project's other skills: `User` model changes, domain apps and models (after you
  confirm the breakdown), extra UI languages, and the app docs. Each step can be
  skipped; it commits when `just check-all` passes. It works on any new project,
  and asks the product questions first if the overview is still the stub.
  `/dj-bootstrap` offers to run it.
- A placeholder favicon: the site name's initial in the PWA colours, served at
  `/favicon.svg` and `/favicon.ico`, linked from `base.html` and listed in
  `manifest.json`. Customise it in `templates/favicon.svg` (see `docs/design.md`).
- `/dj-sync` shows the changelog entries since your project's template commit
  before running `copier update`.

### Changed

- All skills renamed from `dj-<name>` to `djs-<name>` (e.g. `/dj-sync` is now
  `/djs-sync`), so they don't collide with other Django skill packs. Expect
  conflicts in any skill you edited locally. The post-gen hook now deletes
  `.claude/commands/*.md` stubs for skills that no longer exist.
- The `django-studio` plugin skill is now `/djs-bootstrap`.
- The `helm-lint`, `terraform_fmt` and `terraform_validate` pre-commit hooks are
  now local hooks that skip when Helm or Terraform isn't installed, and fail in CI
  (`$CI` set) instead of skipping. They replace the `antonbabenko/pre-commit-terraform`
  repo in `.pre-commit-config.yaml`; expect a conflict there if you changed it.
- Wording-only edits across `docs/` and the skills: filler words ("genuinely",
  "truly", "actually") and puffery removed. If you edited those files, expect small
  conflicts on sync.
- `config/settings.py` no longer sets `DEFAULT_AUTO_FIELD`; `BigAutoField` is the
  Django 6 default.
- Template sources are formatted by the generated project's own pre-commit hooks,
  so the first `pre-commit run --all-files` modifies no files. Expect formatting-only
  conflicts in templates and Python modules on your next sync.

### Deprecated

- The old `/dj-<name>` commands (and the plugin's `/dj-bootstrap`) still work as
  aliases: they print a deprecation notice and run `/djs-<name>`. They will be
  removed in a future release.

### Fixed

- Generated code marks all user-visible strings for translation, even in an
  English-only project. `/djs-create-model` wraps field and `Meta` verbose names,
  `help_text` and choice labels in `gettext_lazy`, and `/djs-create-crud` wraps
  its template text in `{% translate %}`; before, their examples used bare
  strings. Every `create-*` skill now points to `docs/localization.md`. Check
  models and templates generated earlier for bare strings before you add a
  language: `just dj makemessages -l <locale>` only picks up marked strings.
- `/dj-create-crud`: the delete button sends the CSRF header, so deleting no longer
  fails with 403.
