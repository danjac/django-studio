# Additional Packages

These packages are not in the default stack but are the preferred choices when
the need arises. **Only add them when actually needed — do not install
speculatively.**

Check this list before reaching for an unfamiliar package; the preferred choice
per use-case is already decided.

## Choosing a package not on this list

If your need isn't covered above, research before recommending. Check in order:

1. **[djangopackages.org](https://djangopackages.org)** — compare alternatives
   side-by-side for Django-specific packages.
2. **PyPI** — check release recency and download trends.
3. **The project repo (GitHub/GitLab)** — look for: open issues going
   unanswered, last commit date, whether the maintainer responds to PRs,
   CI passing on current Python/Django versions.

Recommend a package only if it passes all of:

- Active maintenance: meaningful commits within the last 12 months
- Compatible with Python 3.14 and Django 6.0
- Open issues are acknowledged, not silently accumulating
- Licence is compatible (MIT, BSD, Apache 2.0)

State your findings explicitly when suggesting a package — don't just name it.

| Need                                                      | Package(s)            | Install                   |
| --------------------------------------------------------- | --------------------- | ------------------------- |
| Image thumbnails                                          | `sorl-thumbnail`      | `uv add sorl-thumbnail`   |
| Multi-tenancy                                             | `django-tenants`      | `uv add django-tenants`   |
| HTTP API client                                           | `aiohttp`             | `uv add aiohttp`          |
| WebSockets / real-time                                    | `channels` + `daphne` | `uv add channels daphne`  |
| Querystring filtering                                     | `django-filter`       | `uv add django-filter`    |
| Audit logging                                             | `django-auditlog`     | `uv add django-auditlog`  |
| Payments                                                  | `stripe`              | `uv add stripe`           |
| Excel export                                              | `openpyxl`            | `uv add openpyxl`         |
| Money / currency                                          | `django-money`        | `uv add django-money`     |
| Data validation / serialization                           | `pydantic`            | `uv add pydantic`         |
| Data analysis / dataframes                                | `polars`              | `uv add polars`           |
| Natural language processing                               | `nltk`                | `uv add nltk`             |
| Markdown parsing / rendering                              | `markdown-it-py`      | `uv add markdown-it-py`   |
| Country names & codes                                     | `django-countries`    | `uv add django-countries` |
| Geocoding (address → lat/lng)                             | `geopy`               | `uv add geopy`            |
| XML / HTML parsing                                        | `lxml`                | `uv add lxml`             |
| Date parsing & relative deltas                            | `python-dateutil`     | `uv add python-dateutil`  |
| Scientific computing                                      | `scipy` + `numpy`     | `uv add scipy numpy`      |
| Machine learning                                          | `scikit-learn`        | `uv add scikit-learn`     |
| HTML sanitization                                         | `nh3`                 | `uv add nh3`              |
| Complex authorization (code-defined rules)                | `django-rules`        | `uv add django-rules`     |
| Complex authorization (runtime per-object DB permissions) | `django-guardian`     | `uv add django-guardian`  |

## Notes

- **sorl-thumbnail**: add `"sorl.thumbnail"` to `INSTALLED_APPS`. Uses the
  Redis cache backend (already configured).
- **aiohttp**: use for async HTTP calls to third-party APIs. See
  `docs/Views.md` for the async view and HTTP client patterns.
- **channels + daphne**: replace the Uvicorn ASGI server with Daphne
  (`daphne config.asgi:application`). Add `"channels"` to `INSTALLED_APPS`
  and configure `ASGI_APPLICATION`.
- **django-money**: pairs with `py-moneyed`. Use `MoneyField` on models;
  arithmetic respects currency. Add a `{% partialdef moneywidget %}` block to
  `templates/form/field.html` — see `docs/Templates.md`.
- **pydantic**: use for parsing and validating external API responses, complex
  form payloads, and structured config. Add to `pyproject.toml` to prevent
  ruff from moving base class imports into `TYPE_CHECKING` blocks:

  ```toml
  [tool.ruff.lint.flake8-type-checking]
  runtime-evaluated-base-classes = ["pydantic.BaseModel"]
  ```

- **markdown-it-py**: preferred Markdown renderer. Use the `mdit-py-plugins`
  extras for footnotes, tasklists, etc. Pair with `nh3` to sanitize the
  rendered HTML before serving.
- **nh3**: Rust-backed HTML sanitizer (successor to `bleach`). Use to strip
  unsafe tags/attributes from user-supplied or rendered Markdown content before
  inserting into templates.
- **nltk**: download corpora at startup or in a management command; do not
  download inside request handlers.
- **django-rules**: predicate-based authorization. Define composable rule
  functions (`is_owner`, `is_member`, etc.) combined with `&`, `|`, `~`.
  Integrates with Django's standard `has_perm`/`has_object_perm` via a custom
  backend. No DB overhead. Best fit when authorization logic is expressed in
  code (ownership checks, role membership, state-based rules).
- **geopy**: use the `Nominatim` geocoder (no API key required). Run geocoding in
  a background task — never in a request handler. See `docs/Maps.md` for the full
  pattern including the django-tasks integration and OSM embed.
- **django-guardian**: per-object permissions stored in the database. Best fit
  when permissions must be assigned at runtime by users or admins (e.g. "grant
  user A edit access to document B"). Has admin integration and queryset
  helpers, but every `has_perm` check hits the DB unless permissions are
  prefetched.
