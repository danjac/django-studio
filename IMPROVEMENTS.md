## Improvements

Add improvements here.

## `buttons.css` focus style removes outline with no visible replacement

`.btn` focus variant sets `outline: 2px solid transparent` with no ring or box-shadow. Keyboard-focused buttons have no visible focus indicator — WCAG 2.1 AA failure (SC 2.4.7).

## `base.css` and `tweaks.css` use `gray-*` tokens instead of `zinc-*`

`base.css:7` uses `--color-gray-200` and `tweaks.css` uses `--color-gray-600` in dark overrides. The rest of the design system uses `zinc`. These are different color scales in Tailwind v4.

## `tweaks.css` `@utility` overrides break Tailwind built-ins

`@utility divide-x`, `@utility divide-y`, etc. replace Tailwind's built-in utilities entirely rather than extending them. This can lose the default `border-width` behavior. Should use theme tokens or `@layer base` dark variants instead.

## `messages.html` has no manual dismiss button

Messages auto-dismiss after 4 seconds with no way to pause or close. WCAG 2.1 SC 2.2.1 requires users can pause/stop/hide auto-updating content.

## `markdown.html` output missing `|safe`

`templates/markdown.html:23` outputs `{{ markdown }}` without `|safe`. Django auto-escaping will escape all HTML tags, rendering raw `&lt;h1&gt;` text instead of formatted prose.

## `ACCOUNT_PREVENT_ENUMERATION = False` weakens user privacy

`config/settings.py:255` explicitly disables allauth's enumeration protection. The login/reset forms will reveal whether an email is registered. Should be removed to use the allauth default (`True`).

## `HSTS` disabled by default even when `USE_HTTPS = True`

`config/settings.py:343` defaults `SECURE_HSTS_SECONDS` to `0`. A production deployment with `USE_HTTPS=True` gets HTTPS redirect but no HSTS, which is incomplete.

## Dead `[tool.isort]` config in `pyproject.toml`

`pyproject.toml:181-183` configures `[tool.isort]` but the project uses ruff for import sorting. Dead config.

## `django-redis` dependency may be unused

`pyproject.toml` lists `django-redis` but `env.dj_cache_url()` from environs sets the backend to Django's built-in `RedisCache`, not `django_redis.cache.RedisCache`. If no `django-redis`-specific features are used, the dependency can be removed.

## Hardcoded `lang="en"` in base templates

`default_base.html:3` and `error_base.html:3` hardcode `<html lang="en">`. When `use_i18n` is enabled, should use `{{ LANGUAGE_CODE }}` for correct screen-reader language detection.

## Sidebar has no active-link detection

`sidebar.html` renders all nav items with identical styling. No `request.path` comparison is done to highlight the current page, despite `.link.active` CSS class existing in `links.css`.

## Mobile nav absent for unauthenticated users

`navbar.html` gates the hamburger button and mobile menu on `{% if user.is_authenticated %}`. Logged-out users on narrow screens get cramped desktop nav with no mobile alternative.

## `setInterval` in HTMX progress indicator never cleared

`default_base.html:17-27` — the progress bar animation uses `setInterval` in `x-init` but never stores or clears it. Potential memory leak if the element is removed via HTMX swap.

~~## Dependabot configured for `pip` instead of `uv`~~

**Resolved**: Switched to `package-ecosystem: "uv"` and added `github-actions` ecosystem entry, both on weekly schedule with 7-day cooldown and grouped updates.

## `build.yml` workflow permissions too broad

`build.yml:8-12` grants `contents: write` at workflow level but the `checks` job only needs `contents: read`. Permissions should be scoped per-job.

## `docker-compose.yml` PostgreSQL volume path

`docker-compose.yml:15` mounts to `/var/lib/postgresql` instead of `/var/lib/postgresql/data`. The official `postgres` image uses the `/data` subdirectory.

~~## Remove modal pattern~~

**Resolved**: Removed `templates/modal.html`, `design/modals.md`, and related references in `design/README.md` and `AGENTS.md`.

~~## Add `header.html` template and design doc~~

**Resolved**: Created `templates/header.html` (title + optional subtitle), `design/headers.md`, updated `design/README.md` and `AGENTS.md`. `about.html` updated to use the component.

## `form/field.html` password toggle icons missing `x-cloak`

Both eye icons (`heroicon_mini "eye"` and `"eye-slash"`) render without `x-cloak`. Before Alpine initializes, both icons flash briefly on screen simultaneously.

~~## Document Pydantic for JSON serialization instead of DRF (2026-02-28)~~

~~Add a note to the template documentation (AGENTS.md or equivalent) stating that Pydantic should be used for JSON serialization and validation — both for third-party/external API responses and for internal APIs — instead of Django REST Framework serializers. When Pydantic is added, also include the following in `pyproject.toml` to prevent ruff from moving Pydantic base class imports into `TYPE_CHECKING` blocks:~~

**Resolved**: Added a "JSON Serialization and Validation" section to the generated project's `AGENTS.md` documenting Pydantic as the preferred approach over DRF, and including the ruff `flake8-type-checking` config snippet to add when Pydantic is installed.

~~## Rename justfile `e2e` command to `test-e2e` and update docs (2026-02-27)~~

~~Rename the `e2e` just recipe to `test-e2e` (and `e2e-headed` to `test-e2e-headed`) for consistency with the `test` command naming convention. Update AGENTS.md/CLAUDE.md documentation to reference `just test-e2e` and `just test-e2e-headed` accordingly.~~

**Resolved**: Renamed `e2e` → `test-e2e` and `e2e-headed` → `test-e2e-headed` in justfile; updated references in AGENTS.md, docs/Testing.md, and docs/Local-Development.md.
