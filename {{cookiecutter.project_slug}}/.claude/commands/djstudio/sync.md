Update the djstudio command files in this project to the latest versions
from the django-studio template repository.

**Prerequisites:** `gh` must be installed and authenticated (`gh auth status`).

---

### Step 1 — Fetch the latest file list

List all files currently in the template's commands directory:

```bash
gh api 'repos/danjac/django-studio/contents/{{cookiecutter.project_slug}}/.claude/commands/djstudio' \
  --jq '.[].name'
```

Also fetch the dispatcher:

```bash
gh api 'repos/danjac/django-studio/contents/{{cookiecutter.project_slug}}/.claude/commands/djstudio.md' \
  --jq '.name'
```

If either call fails, tell the user and stop — the template repo may have
moved or `gh` may not be authenticated.

---

### Step 2 — Compare with local files

For each file returned:

- Compare the template version with the local file at
  `.claude/commands/djstudio/<name>` (or `.claude/commands/djstudio.md` for
  the dispatcher).
- Note whether the local file: **missing** (new in template), **changed**
  (differs from template), or **unchanged**.

Download each file's content from the template:

```bash
gh api 'repos/danjac/django-studio/contents/{{cookiecutter.project_slug}}/.claude/commands/djstudio/<name>' \
  --jq '.content' | base64 -d
```

Also check for local files that no longer exist in the template (removed
subcommands) — list these separately as candidates for deletion.

---

### Step 3 — Show the diff summary and confirm

Print a table before making any changes:

```
djstudio command sync — danjac/django-studio → this project

  NEW (in template, not local):
    secure.md
    create-e2e.md

  CHANGED (differs from template):
    djstudio.md
    create-view.md

  UNCHANGED:
    create-app.md
    create-model.md
    ...

  LOCAL ONLY (removed from template — will not be deleted automatically):
    my-custom-command.md
```

Then ask:

> Apply these updates? New and changed files will be overwritten.
> Local-only files will not be touched. [y/n]

Wait for confirmation before proceeding.

---

### Step 4 — Apply updates

For each **new** or **changed** file, write the template content to the local
path. Do not touch **unchanged** or **local-only** files.

After writing all files, force-add them to git:

```bash
git add -f .claude/commands/djstudio.md .claude/commands/djstudio/
```

---

### Step 5 — Report

Print a summary:

```
Synced N files from danjac/django-studio:
  updated: djstudio.md, create-view.md
  added:   secure.md, create-e2e.md
```

If any **local-only** files were found, remind the user:

> These local command files were not in the template and were left untouched:
>   .claude/commands/djstudio/my-custom-command.md
> Remove them manually if they are no longer needed.

Offer to commit the changes:

> Commit the updated command files? [y/n]

If yes:

```bash
git commit -m "chore: sync djstudio commands from django-studio template"
```
