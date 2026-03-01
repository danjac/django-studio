# Django Studio Feedback

@description Post feedback as a GitHub issue on the appropriate repository.
Requires the `gh` CLI tool authenticated with GitHub access.
@arguments $ARGUMENTS: Optional subcommand followed by natural language feedback

## Subcommands

Parse `$ARGUMENTS` to determine the subcommand and feedback text:

- **`cookiecutter <feedback>`** — issue is about the cookiecutter template itself. Post to `danjac/django-studio`.
- **`<feedback>`** (default, no subcommand) — issue is about the current (generated) project. Post to the current repo, detected by running `gh repo view --json nameWithOwner -q .nameWithOwner`.

If the first word of `$ARGUMENTS` is `cookiecutter`, the subcommand is `cookiecutter` and the feedback is everything after it. Otherwise the subcommand is the default and the feedback is all of `$ARGUMENTS`.

## Creating the Issue

Issue title: a concise summary (≤72 characters, imperative mood).
Issue body: one or two sentences describing what to change, where, and why.

**Cookiecutter subcommand** (posts to `danjac/django-studio`):

```bash
gh issue create \
  --repo danjac/django-studio \
  --title "<concise title>" \
  --body "<what to change, where, and why>"
```

**Default — current project** (detect repo first):

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh issue create \
  --repo "$REPO" \
  --title "<concise title>" \
  --body "<what to change, where, and why>"
```

Confirm to the user the issue was created and show the URL returned by `gh`.

---

## Requirements

- `gh` CLI installed and authenticated (`gh auth status`)
- For the default subcommand: must be run from within a git repo with a GitHub remote

## Installation

Copy to your global Claude Code commands directory so it is available in every project:

```bash
cp skills/django-studio.md ~/.claude/commands/django-studio.md
```

## Usage

From a generated project:

```
/django-studio missing variable X in templates/base.html
```

From anywhere (or the django-studio repo itself):

```
/django-studio cookiecutter add tmp_path fixture for media file tests
/django-studio cookiecutter post_gen hook does not remove i18n files correctly
```

Log feedback immediately when you notice it — do not wait until the end of a session.
