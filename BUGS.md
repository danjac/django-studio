<!-- All bugs resolved. Add new bugs below this line. -->

~~## Errors in generated pyproject.toml:~~

**Resolved**: Removed invalid `profile = "black"` from ruff configuration. This option is not valid in modern ruff versions - ruff uses black-compatible formatting by default.


absolufy-imports.........................................................Passed
~~## `privacy` URL wired to `about` view~~

**Resolved**: `config/urls.py` — changed `views.about` to `views.privacy` for the privacy path.

~~## `privacy.html` references non-existent `header.html` template~~

**Resolved**: Created `templates/header.html` page header component (title + optional subtitle). Updated `about.html` to use it for consistency. Added `design/headers.md` doc and updated `design/README.md`.

~~## `privacy.html` references non-existent `users:delete_account` URL~~

**Resolved**: Replaced the broken URL link with a `mailto:{{ contact_email }}` link. Updated the `privacy` view to pass `contact_email` from `settings.CONTACT_EMAIL`.

~~## `@alpinejs/focus` plugin never loaded — `x-trap` in `modal.html` is broken~~

**Resolved**: Removed `modal.html` and `design/modals.md` — the modal pattern was untested and unrequested. No `x-trap` dependency remains.

~~## `playright.ini` filename typo~~

**Resolved**: Renamed to `playwright.ini`. Updated references in `justfile` and `checks.yml`.

~~## `SECURE_BROWSER_XSS_FILTER` is removed in Django 4.0+~~

**Resolved**: Removed the dead setting from `config/settings.py`.

~~## Shell scripts missing `set -euo pipefail`~~

**Resolved**: Updated `release.sh` and `manage.sh` to use `set -euo pipefail`.

~~## `appleboy/ssh-action@master` — floating ref, no SHA pin~~

**Resolved**: SHA-pinned to commit `8743aa11bfbda97acb45c151ae7a2e0b203f1914`.

~~## All GitHub Actions use version tags instead of SHA pins~~

**Resolved**: SHA-pinned all actions in `checks.yml`, `docker.yml`, `deploy.yml`, and `build.yml`.

~~## `workflow_dispatch: branches` filter has no effect~~

**Resolved**: Removed `branches: [main]` from `workflow_dispatch` in `build.yml` and `deploy.yml`.

~~## `accept_cookies` sets `secure=True` unconditionally~~

**Resolved**: Changed to `secure=settings.USE_HTTPS` in `views.py`.

~~## `HtmxRedirectMiddleware` intercepts non-redirect responses with `Location` header~~

**Resolved**: Added `response.status_code in range(300, 400)` guard in `middleware.py`.

~~## `gunicorn.conf.py` `wsgi_app` value missing `:application`~~

**Resolved**: Fixed to `"config.asgi:application"`.

~~## Python version mismatch in CI~~

**Resolved**: Standardised on `3.14.0` for both `setup-python` and `uv python install` in `checks.yml`.

~~Ansible configuration completely broken, not processing files correctly:~~

~~HINT: only process Ansible files we need to, and ignore the rest.~~

**Resolved**: Fixed three issues:

1. `terraform/hetzner/variables.tf` had duplicate `description`/`type`/`default` in `cluster_name` block — removed stale duplicate
2. `terraform/hetzner/storage.tf` was a standalone module in the same dir as `variables.tf`, causing duplicate `variable "location"` — moved to `terraform/storage/main.tf`
3. `cookiecutter.json` `_copy_without_render` had `"ansible/**"` preventing `group_vars/all.yml` and `k3s_observability/defaults/main.yml` from being rendered — replaced with specific task/template/vars/defaults patterns; added `{% raw %}` guards to `group_vars/all.yml` for Ansible-specific variables
