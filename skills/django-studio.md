# Django Studio Feedback

@description Post feedback as a GitHub issue on the Django Studio repository.
Requires the `gh` CLI tool authenticated with GitHub access.
@arguments $FEEDBACK: Natural language description of the feedback

Use the `gh` CLI to create a GitHub issue on `danjac/django-studio`:

Issue title: a concise summary (≤72 characters, imperative mood).
Issue body: one or two sentences describing what to change, where, and why.

```bash
gh issue create \
  --repo danjac/django-studio \
  --title "<concise title>" \
  --body "<what to change, where, and why>"
```

Confirm to the user the issue was created and show the URL returned by `gh`.

---

## Requirements

- `gh` CLI installed and authenticated (`gh auth status`)

## Installation

Copy to your global Claude Code commands directory so it is available in every project:

```bash
cp skills/django-studio.md ~/.claude/commands/django-studio.md
```

## Usage

From any generated project (or the django-studio repo itself):

```
/django-studio add tmp_path fixture for media file tests
/django-studio missing variable X in templates/base.html
```

Log feedback immediately when you notice it — do not wait until the end of a session.
