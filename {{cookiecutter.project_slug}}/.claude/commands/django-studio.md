# Django Studio

@description Manage your Django project: file issues, scaffold new apps, and initialize your project roadmap.
@arguments $ARGUMENTS: Subcommand followed by arguments

## Subcommands

Parse the first word of `$ARGUMENTS` to determine the subcommand:

| Subcommand | Purpose |
|------------|---------|
| `issue`    | File a GitHub issue |
| `create`   | Create a new Django project |
| `init`     | Run Session Zero |

If `$ARGUMENTS` is empty or the first word is not a recognised subcommand, print usage and stop.

---

## `issue` — File a GitHub Issue

Parse `$ARGUMENTS` after `issue`:

- **`issue cookiecutter <feedback>`** — target the django-studio template repo (`danjac/django-studio`). Feedback is everything after `cookiecutter`.
- **`issue <feedback>`** — target the current project.

**Steps:**

1. Draft a concise issue title (≤72 characters, imperative mood).
2. Write a one- or two-sentence body: what to change, where, and why.
3. Create the issue:

   **Current project** — run from the project root:
   ```bash
   gh issue create --title "<title>" --body "<body>"
   ```

   **Template repo** (`danjac/django-studio`):
   ```bash
   gh issue create --repo danjac/django-studio --title "<title>" --body "<body>"
   ```

4. Confirm the issue was created and show the URL.

Log feedback immediately when you notice it — do not wait until the end of a session.

---

## `create` — Create a New Django Project

Run `git config user.name` and `git config user.email` to get author defaults, then ask the user **all** of the following questions in a single conversational message:

1. What is the name of your project? *(e.g. "My Blog" — required)*
2. What should the project directory / repo be called? *(kebab-case, e.g. `my-blog` — default: project name lowercased with spaces replaced by hyphens)*
3. What should the top-level Python package be called? *(snake_case, e.g. `myblog` — default: directory name with hyphens replaced by underscores)*
4. Describe the project in one sentence.
5. What is your name? *(default: value from `git config user.name`, if available)*
6. What is your email address? *(default: value from `git config user.email`, if available)*
7. Will this project use SPA-like navigation without full page reloads? *(enables HTMX Boost — default: yes)*
8. Will this project need to store user-uploaded files or media in the cloud? *(enables S3/Hetzner object storage — default: yes)*
9. Will this project need to support multiple languages? *(enables Django i18n/l10n — default: no)*
10. Should this project work as a Progressive Web App (installable, offline-capable)? *(adds PWA manifest and service worker — default: no)*

Wait for the user to provide their answers, then confirm the choices and run:

```bash
uvx cookiecutter gh:danjac/django-studio \
  --no-input \
  project_name="<project_name>" \
  project_slug="<project_slug>" \
  package_name="<package_name>" \
  description="<description>" \
  author="<author>" \
  author_email="<author_email>" \
  use_hx_boost="<y_or_n>" \
  use_storage="<y_or_n>" \
  use_i18n="<y_or_n>" \
  use_pwa="<y_or_n>"
```

After the project is created, report the path to the new directory and remind the user to:

```bash
cd <project_slug>
cp .env.example .env
# Edit .env with your local settings, then:
just start              # start Docker services
just install            # install Python deps + pre-commit hooks
just dj makemigrations  # generate the initial users app migration
just test               # run the test suite
```

---

## `init` — Session Zero

Run Session Zero to establish the project's purpose and roadmap before any development work begins.

**Steps:**

1. Ask all of these questions in a single message:
   - What problem is this project solving?
   - Who are the users and stakeholders?
   - What are the key features and success criteria?
   - What should the project **not** do (out of scope)?
   - What is the intended license? (MIT, BSD-3, GPL-3, AGPL-3, or proprietary)

2. Update `README.md` with a project overview based on the answers.

3. Create `ROADMAP.md` with milestones and tasks. Each task gets a checkbox (`- [ ] Task`).
   Group related tasks into milestones.

4. Present the roadmap to the user for approval.

Do not start any implementation work until the user has explicitly approved the roadmap.

---

## Requirements

- `gh` CLI installed and authenticated (`gh auth status`)
- Working git repository with a remote (for `issue` on the current project)

## Installation

After editing this file in the django-studio repo, sync to your global Claude Code commands:

```bash
just sync-skills
```
