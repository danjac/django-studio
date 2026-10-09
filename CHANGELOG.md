# Changelog

User-visible changes to the django-studio template. `/djs-sync` shows the entries
added since your project's last update before it runs `copier update`.

Versions are date-based: `YY.WW.D` (ISO year, week and weekday, as printed by
`date +%y.%V.%u`), one section per day.

## 26.41.5 - 2026-10-09

### Added

- `/djs-full-audit` runs the security, performance, GDPR, accessibility, SEO,
  dead-code and anti-pattern audits in one sweep (in parallel where the agent
  supports subagents) without changing any file, and combines the findings into
  one report. It suggests which audits to skip for the project, such as SEO when
  there are no public pages, and then offers fixes one audit at a time.

## 26.41.4 - 2026-10-08

### Changed

- Form field rendering moves out of `templates/forms/partials.html` (removed) and
  `templates/django/forms/field.html` (removed). `FORM_RENDERER` is now
  `<package>.forms.FormRenderer`, which renders each field with
  `templates/forms/field.html`: the widget dispatch plus the `fieldset`, `errors`
  and `help_text` partials. `label`, `legend`, `input` and the per-widget partials
  move to `templates/forms/widgets.html`; add custom widget partials there and
  update any `forms/partials.html#...` references. **Expect a conflict on
  `copier update` in `config/settings.py` and in either removed template if you
  edited it.**

## 26.41.3 - 2026-10-07

### Added

- `docs/django-templates.md` explains how far to take the shipped components: edit
  them to change site-wide defaults, write markup by hand for custom cases (e.g. a
  one-button action form) instead of adding parameters, extract a repeated
  pattern into a new component built from partials, and make variants by
  extending a component and overriding its blocks.

### Changed

- Form fields render their widget partial with a plain `{% include %}`; there is no
  fallback to the `input` partial. `TextInput`, `EmailInput`, `URLInput`,
  `NumberInput`, `TelInput`, `SearchInput` and `ColorInput` have their own alias
  partials. **Each custom widget in your project now needs a `{% partialdef %}` in
  `templates/forms/partials.html`** (a one-line `{% partial input %}` alias if it
  renders like a plain input), or the field raises `TemplateDoesNotExist`.

### Removed

- The deprecated `/dj-<name>` skill aliases and the plugin's `/dj-bootstrap`; use
  `/djs-<name>`. `copier update` deletes the `.claude/commands/dj-*.md` stubs and
  the `dj-*` entries in `opencode.json`.
- The `{% try_include %}` template tag. Use `{% include %}`, which also accepts a
  list of template names and renders the first that exists.

## 26.41.2 - 2026-10-06

### Fixed

- The shipped E2E auth tests and the `auth_page` fixture look up button and
  link labels with `gettext`, so they pass when `LANGUAGE_CODE` isn't English.
  `/djs-create-e2e` and `docs/testing.md` do the same.

## 26.40.7 - 2026-10-04

### Fixed

- `docs/sse.md` shares one LISTEN connection per process between all open
  streams, instead of opening a Postgres connection per stream, and routes each
  notification to its recipient only (the previous example sent every
  notification to every user). It publishes with `pg_notify` on Django's
  connection so events fire on commit, sends heartbeats so proxies keep idle
  streams open, reads the user with `await request.auser()`, and notes that
  local SSE needs an ASGI `runserver`.

## 26.40.6 - 2026-10-03

### Changed

- `docs/seo.md` explains how to keep public pages out of search results with
  `noindex`, `nofollow` and `noarchive`, in a meta tag or an `X-Robots-Tag`
  header, and how to remove a page that is already indexed. `/djs-seo` checks
  for `noindex` on pages `robots.txt` blocks, file and export views without
  `X-Robots-Tag`, and user-submitted links without `rel="ugc nofollow"`.

## 26.40.5 - 2026-10-02

### Added

- `/djs-seo` audits public pages for search engine optimisation: robots.txt
  allow-list, titles and meta descriptions, content loaded by HTMX after the
  page arrives, status codes, canonical and Open Graph tags, sitemaps and JSON-LD.
  Projects with no public content get a short report.
- `docs/seo.md` covers the same topics, with recipes for per-page descriptions,
  canonical and Open Graph tags, sitemaps and JSON-LD for projects that need them.

### Fixed

- The about page sets its own `<title>` ("Site | About") instead of the bare site
  name.
- Form fields are labelled with `<label for>` instead of a `<legend>`, so screen
  readers and checkers such as axe find an accessible name and
  Playwright's `get_by_label` matches. Grouped widgets (radios, checkbox lists,
  multi-part inputs) keep `<legend>` through the new `{% partial legend %}`.
- The form fieldset no longer repeats the input's `aria-describedby`, and the
  errors list has the `<auto_id>_error` id that Django's `aria-describedby`
  points at.
- The password show/hide button is reachable by keyboard and exposes its state
  with `aria-pressed`.
- `RadioSelect`, `TimeInput`, `NullBooleanSelect`, `SplitDateTimeWidget` and
  `SelectDateWidget` get their own partials instead of falling back to the text
  `input` partial. `tests/test_forms.py` checks that every Django widget has a
  partial or is a plain text-like input.

- `/.well-known/security.txt` now meets RFC 9116: it adds `Expires` (the last
  day of next month), `Preferred-Languages` from `settings.LANGUAGES` and
  `Canonical`.
- `TextResponse` (used by `robots.txt` and `security.txt`) sends
  `text/plain; charset=utf-8` instead of `text/plain`.

### Changed

- `base.html` has a `{% block meta %}` after `{% meta_tags %}` for per-page tags
  such as a description, canonical link or Open Graph tags. Projects that
  customised `base.html` may conflict on `copier update`.
- `templates/forms/partials.html` changes its `label`, `fieldset` and `errors`
  partials, and adds partials for more widgets. Projects that customised it will
  conflict on `copier update`.
- Each view in `views.py` sets its own `cache_control` instead of sharing a
  one-year `immutable` policy, and none uses `cache_page`, whose Redis copy
  outlived deploys. `robots.txt` and the favicon are cached for a day;
  `security.txt`, `manifest.json` and `assetlinks.json` for an hour, so env
  changes such as `CONTACT_EMAIL` or `PWA_*` show up quickly. Projects that
  customised these views will conflict on `copier update`.

## 26.40.3 - 2026-09-30

### Changed

- The `install`, `pyinstall` and `helm` recipes in `justfile` call scripts in
  `just/` (`install.sh`, `pyinstall.sh`, `helm.sh`) instead of embedding them.
  Projects that customised these recipes will conflict on `copier update`.

## 26.40.1 - 2026-09-28

### Changed

- `/djs-deadcode` runs deptry inside the project environment and reports unused
  dependencies only. Before proposing a removal, it checks each package for
  references from settings, `{% load %}` tags, scripts and backend URLs.
  Approved packages are removed with `uv remove`.
- Updated Python dependency minimums to the latest releases (OpenTelemetry 1.45 /
  0.66b0, uvicorn 0.54, sentry-sdk 2.70, ruff 0.16.9, and others).
- Updated vendored Alpine.js to 3.17.4 and DaisyUI to 5.7.46.
- Bumped uv to 0.12.19 in `Dockerfile`, `checks.yml` and the `uv-lock` pre-commit
  hook, and updated the ruff, djLint and commitlint hooks.
- `.github/workflows/checks.yml` sets the CI Python version once, as
  `env.PYTHON_VERSION`, used by `setup-python` and both `uv python install` steps.
- CI runs Python 3.14.2, matching the `Dockerfile` (was 3.14.0).

## 26.39.7 - 2026-09-27

### Fixed

- `/djs-create-crud` defines the form partial with
  `{% partialdef <name> inline %}` … `{% endpartialdef %}`. It used
  `{% partial %}` … `{% endpartial %}`, which isn't valid Django, so the generated
  form template failed to load.
- `/djs-create-crud`'s list view HTMX test sends `HX-Target: pagination`, the
  paginator's default target. It sent `<model>-list`, so the test got the full page
  and never checked the partial.
- The debug toolbar keeps its styles after an HTMX redirect (`HX-Location`) swaps
  in a new page. htmx moves the toolbar's `hx-preserve` root with `moveBefore()`,
  and Chromium drops the stylesheets of a moved `<link>`; in `DEBUG`, `base.html`
  re-adds them after each swap.
- `base.html` no longer triggers a Content-Security-Policy error after an
  `HX-Location` swap.

### Changed

- `base.html` loads its site-wide scripts (`indicator.js` and the inline HTMX and
  service worker listeners) in `<head>` instead of `{% block scripts %}`, so body
  swaps don't run them again. `{% block scripts %}` is now empty by default.
  Expect a conflict if you edited that block in `base.html`.

## 26.39.6 - 2026-09-26

### Fixed

- `deploy.yml` no longer fails to load: the "Connect to Tailscale" step's `if:`
  read the `secrets` context, which GitHub doesn't allow in step conditions. It
  now tests a job-level `TS_OAUTH_CLIENT_ID` env var.
- `deploy.yml` drops the `branches:` key under `workflow_dispatch`, which GitHub
  ignores.

### Added

- An actionlint pre-commit hook checks `.github/workflows/`, with its config in
  `.github/actionlint.yaml`. It ignores the `$/` reusable-workflow paths that
  zizmor requires.
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

- `/djs-backlog` makes GitHub issues the backlog when the project has a GitHub
  remote: `bug`, `enhancement` and `chore` labels for the type, optional
  `priority: high` / `priority: low` labels, and GitHub's "blocked by"
  relationships. `next` works from the open issues and needs no bookkeeping
  commits, since merging a PR that says `Closes #N` finishes the item.
  `/djs-backlog` moves an existing `docs/backlog.md` to issues and deletes it;
  projects without a GitHub remote keep `docs/backlog.md`. `/djs-kickoff` creates
  issues in place of the file when there is a remote.
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
