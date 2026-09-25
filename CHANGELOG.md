# Changelog

User-visible changes to the django-studio template. `/dj-sync` shows the entries
added since your project's last update before it runs `copier update`.

Versions are date-based: `YY.WW.D` (ISO year, week and weekday, as printed by
`date +%y.%V.%u`), one section per day.

## 26.39.6 - 2026-09-26

### Added

- A placeholder favicon: the site name's initial in the PWA colours, served at
  `/favicon.svg` and `/favicon.ico`, linked from `base.html` and listed in
  `manifest.json`. Customise it in `templates/favicon.svg` (see `docs/design.md`).
- `/dj-sync` shows the changelog entries since your project's template commit
  before running `copier update`.

### Changed

- Wording-only edits across `docs/` and the skills: filler words ("genuinely",
  "truly", "actually") and puffery removed. If you edited those files, expect small
  conflicts on sync.
- `config/settings.py` no longer sets `DEFAULT_AUTO_FIELD`; `BigAutoField` is the
  Django 6 default.
- Template sources are formatted by the generated project's own pre-commit hooks,
  so the first `pre-commit run --all-files` modifies no files. Expect formatting-only
  conflicts in templates and Python modules on your next sync.

### Fixed

- `/dj-create-crud`: the delete button sends the CSRF header, so deleting no longer
  fails with 403.
