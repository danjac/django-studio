# Improvements

Add improvements here.

~~## Document sorl-thumbnail for image processing and thumbnails (2026-02-28)~~

**Resolved**: Added "Image Processing and Thumbnails" section to the generated project's `AGENTS.md` covering when to use `sorl-thumbnail`, how to install it, and a `{% thumbnail %}` usage example with a note about Redis and storage backend requirements.

~~## `buttons.css` focus style removes outline with no visible replacement~~

**Resolved**: Added `box-shadow: 0 0 0 2px var(--color-bg), 0 0 0 4px var(--color-indigo-500)` to focus variant for visible focus indicator; also changed disabled state to use `zinc-400` instead of `gray-400`.

~~## `base.css` and `tweaks.css` use `gray-*` tokens instead of `zinc-*`~~

**Resolved**: Changed `base.css:7` to use `--color-zinc-200` and `tweaks.css` to use `zinc-600` consistently with the rest of the design system.

~~## `tweaks.css` `@utility` overrides break Tailwind built-ins~~

**Resolved**: Replaced `@utility` declarations with `@layer base` class-based selectors to extend rather than replace Tailwind's built-in utilities.

~~## `messages.html` has no manual dismiss button~~

**Resolved**: Added dismiss button (X icon) to each message with `@click="show = false"` handler; added `{% translate "Dismiss" %}` for i18n; wrapped message text in `<span>` for proper button adjacency.

~~## `ACCOUNT_PREVENT_ENUMERATION = False` weakens user privacy~~

**Resolved**: Removed `ACCOUNT_PREVENT_ENUMERATION = False` from `config/settings.py` to restore allauth's default enumeration protection.

~~## Dead `[tool.isort]` config in `pyproject.toml`~~

**Resolved**: Removed `[tool.isort]` section from `pyproject.toml`; kept `[tool.ruff.lint.isort]` which is the actual ruff configuration.

~~## Hardcoded `lang="en"` in base templates~~

**Resolved**: Changed `default_base.html` and `error_base.html` to use `{{ LANGUAGE_CODE }}` instead of hardcoded `lang="en"`.

~~## Mobile nav absent for unauthenticated users~~

**Resolved**: Moved hamburger button outside of `{% if user.is_authenticated %}` block; added mobile menu for unauthenticated users with Sign in/Sign up links.

~~## `setInterval` in HTMX progress indicator never cleared~~

**Not a bug**: The indicator is in the base template and persists for the page lifetime - no cleanup needed.

**Resolved**: Stored interval ID in variable and added `$cleanup(() => clearInterval(interval))` to clear it when element is removed.

~~## `form/field.html` password toggle icons missing `x-cloak`~~

**Resolved**: Added `x_cloak` attribute to both eye and eye-slash heroicons.

~~## Dependabot configured for `pip` instead of `uv`~~

**Resolved**: Switched to `package-ecosystem: "uv"` and added `github-actions` ecosystem entry, both on weekly schedule with 7-day cooldown and grouped updates.

## `build.yml` workflow permissions too broad

`build.yml:8-12` grants `contents: write` at workflow level but the `checks` job only needs `contents: read`. Permissions should be scoped per-job.

~~## Remove modal pattern~~

**Resolved**: Removed `templates/modal.html`, `design/modals.md`, and related references in `design/README.md` and `AGENTS.md`.

~~## Add `header.html` template and design doc~~

**Resolved**: Created `templates/header.html` (title + optional subtitle), `design/headers.md`, updated `design/README.md` and `AGENTS.md`. `about.html` updated to use the component.

~~## Document Pydantic for JSON serialization instead of DRF (2026-02-28)~~

~~Add a note to the template documentation (AGENTS.md or equivalent) stating that Pydantic should be used for JSON serialization and validation — both for third-party/external API responses and for internal APIs — instead of Django REST Framework serializers. When Pydantic is added, also include the following in `pyproject.toml` to prevent ruff from moving Pydantic base class imports into `TYPE_CHECKING` blocks:~~

**Resolved**: Added a "JSON Serialization and Validation" section to the generated project's `AGENTS.md` documenting Pydantic as the preferred approach over DRF, and including the ruff `flake8-type-checking` config snippet to add when Pydantic is installed.

~~## Rename justfile `e2e` command to `test-e2e` and update docs (2026-02-27)~~

~~Rename the `e2e` just recipe to `test-e2e` (and `e2e-headed` to `test-e2e-headed`) for consistency with the `test` command naming convention. Update AGENTS.md/CLAUDE.md documentation to reference `just test-e2e` and `just test-e2e-headed` accordingly.~~

**Resolved**: Renamed `e2e` → `test-e2e` and `e2e-headed` → `test-e2e-headed` in justfile; updated references in AGENTS.md, docs/Testing.md, and docs/Local-Development.md.
