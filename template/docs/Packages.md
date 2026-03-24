# Additional Packages

> **Frontend JS/CSS dependencies** (HTMX, Alpine.js, DaisyUI) are vendored, not installed via pip. See `docs/Frontend-Dependencies.md` to add or update them.

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
| Image thumbnails                                          | [`sorl-thumbnail`](https://sorl-thumbnail.readthedocs.io/) | `uv add sorl-thumbnail`   |
| Multi-tenancy                                             | [`django-tenants`](https://django-tenants.readthedocs.io/) | `uv add django-tenants`   |
| HTTP API client                                           | [`aiohttp`](https://docs.aiohttp.org/) | `uv add aiohttp`          |
| Server-push / event streaming (notifications, live feed)  | `psycopg` LISTEN/NOTIFY (built-in)    | no extra package          |
| WebSockets / real-time (bidirectional)                    | [`channels`](https://channels.readthedocs.io/) + [`channels-redis`](https://pypi.org/project/channels-redis/) | `uv add channels channels-redis` |
| Querystring filtering                                     | [`django-filter`](https://django-filter.readthedocs.io/) | `uv add django-filter`    |
| Audit logging                                             | [`django-auditlog`](https://django-auditlog.readthedocs.io/) | `uv add django-auditlog`  |
| Payments                                                  | [`stripe`](https://docs.stripe.com/api?lang=python) | `uv add stripe`           |
| Excel export                                              | [`openpyxl`](https://openpyxl.readthedocs.io/) | `uv add openpyxl`         |
| Money / currency                                          | [`django-money`](https://pypi.org/project/django-money/) | `uv add django-money`     |
| Data validation / serialization                           | [`pydantic`](https://docs.pydantic.dev/) | `uv add pydantic`         |
| Data analysis / dataframes                                | [`polars`](https://docs.pola.rs/) | `uv add polars`           |
| Natural language processing                               | [`nltk`](https://www.nltk.org/) | `uv add nltk`             |
| Markdown parsing / rendering                              | [`markdown-it-py`](https://markdown-it-py.readthedocs.io/) | `uv add markdown-it-py`   |
| Translatable model content (i18n)                         | [`django-modeltranslation`](https://django-modeltranslation.readthedocs.io/) | `uv add django-modeltranslation` |
| Country names & codes                                     | [`django-countries`](https://pypi.org/project/django-countries/) | `uv add django-countries` |
| Geocoding (address → lat/lng)                             | [`geopy`](https://geopy.readthedocs.io/) | `uv add geopy`            |
| XML / HTML parsing                                        | [`lxml`](https://lxml.de/) | `uv add lxml`             |
| Date parsing & relative deltas                            | [`python-dateutil`](https://dateutil.readthedocs.io/) | `uv add python-dateutil`  |
| Scientific computing                                      | [`scipy`](https://scipy.org/) + [`numpy`](https://numpy.org/) | `uv add scipy numpy`      |
| Machine learning                                          | [`scikit-learn`](https://scikit-learn.org/) | `uv add scikit-learn`     |
| Rich text editor (admin + forms)                          | [`django-prose-editor`](https://django-prose-editor.readthedocs.io/) | `uv add "django-prose-editor[sanitize]"` |
| HTML sanitization                                         | [`nh3`](https://pypi.org/project/nh3/) | `uv add nh3`              |
| Complex authorization (code-defined rules)                | [`django-rules`](https://pypi.org/project/django-rules/) | `uv add django-rules`     |
| Complex authorization (runtime per-object DB permissions) | [`django-guardian`](https://django-guardian.readthedocs.io/) | `uv add django-guardian`  |

## Notes

- **sorl-thumbnail**: add `"sorl.thumbnail"` to `INSTALLED_APPS`. Uses the
  Redis cache backend (already configured).
- **aiohttp**: use for async HTTP calls to third-party APIs. See
  `docs/API-Integration.md` for the `USER_AGENT` setting, error handling, and testing patterns.
- **psycopg LISTEN/NOTIFY**: for server-push scenarios (notifications, live
  feeds, progress events) — no extra package needed. See `docs/Channels.md` for
  setup and HTMX SSE integration.
- **channels**: for bidirectional WebSocket needs. See `docs/Channels.md` for
  setup, consumers, and HTMX WebSocket integration.
- **django-money**: pairs with `py-moneyed`. Use `MoneyField` on models;
  arithmetic respects currency. `MoneyWidget` renders an amount input and a
  currency select side-by-side. See `docs/Django-Forms.md#moneywidget` for the
  `{% partialdef moneywidget %}` partial.
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
- **django-prose-editor**: ProseMirror/Tiptap-based rich text editor. Add
  `"django_prose_editor"` to `INSTALLED_APPS`. Use `ProseEditorField` instead
  of `TextField` for rich text model fields; it renders the editor automatically
  in admin and forms. The `[sanitize]` extra uses `nh3` to sanitize HTML on
  save — always install with this extra. Configure allowed extensions
  (`Bold`, `Italic`, `BulletList`, `Link`, etc.) per field via the `extensions`
  argument.
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
- **django-modeltranslation**: adds language-specific columns for selected model
  fields using a `translation.py` registration file — no schema changes to
  existing fields. Add `"modeltranslation"` to `INSTALLED_APPS` **before**
  `"django.contrib.admin"`. Define `LANGUAGES` in settings (the project already
  sets `LANGUAGE_CODE`; add the full `LANGUAGES` tuple for each locale you
  support). Create `<app>/translation.py`:

  ```python
  from modeltranslation.translator import TranslationOptions, register
  from myapp.models import Article

  @register(Article)
  class ArticleTranslationOptions(TranslationOptions):
      fields = ("title", "body")
  ```

  Run `makemigrations` after registering — it adds `title_en`, `title_fr`, etc.
  columns automatically. The original field (`title`) proxies to the active
  language at runtime. Use `modeltranslation.admin.TranslationAdmin` (or
  `TabbedTranslationAdmin` for a tabbed UI) instead of `ModelAdmin`.

- **django-guardian**: per-object permissions stored in the database. Best fit
  when permissions must be assigned at runtime by users or admins (e.g. "grant
  user A edit access to document B"). Has admin integration and queryset
  helpers, but every `has_perm` check hits the DB unless permissions are
  prefetched.
