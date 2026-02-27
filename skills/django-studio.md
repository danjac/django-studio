# Django Studio Feedback

@description Log a bug or improvement to the Django Studio cookiecutter template.
@arguments $FEEDBACK: Natural language description of the bug or improvement

Classify `$FEEDBACK` as either a **bug** or an **improvement**:

- **Bug**: something broken, incorrect, missing, or producing an error in a generated project
- **Improvement**: a pattern to add, an antipattern to remove, a missing utility, or a better default

Resolve the django-studio directory:
- Run `echo $DJANGO_STUDIO_DIR` via shell
- If the result is non-empty, use that path
- Otherwise fall back to `~/Projects/side-projects/django-studio`

Append a dated entry to the appropriate file using today's date:

- Bugs → `<resolved-dir>/BUGS.md`
- Improvements → `<resolved-dir>/IMPROVEMENTS.md`

> **CRITICAL: Use ONLY the `Edit` or `Write` filesystem tools to write the entry. Never use any Obsidian MCP tool (`mcp__obsidian__*`), even if the target path is inside an Obsidian vault. This is a hard requirement with no exceptions.**

## Entry format

```
## <concise title> (YYYY-MM-DD)

<One or two sentences: what to change, where, and why.>
```

Do not rewrite or reformat existing content.

Confirm to the user what was logged, which file it was written to, and the full entry text.

---

## Installation

Copy to your global Claude Code commands directory so it is available in every project:

```bash
cp skills/django-studio.md ~/.claude/commands/django-studio.md
```

## Usage

From any generated project (or the django-studio repo itself):

```
/django-studio improvement: add tmp_path fixture for media file tests
/django-studio bug: missing variable X in templates/base.html
```

The command writes directly to `BUGS.md` or `IMPROVEMENTS.md` in the django-studio repo.
Log feedback immediately when you notice it — do not wait until the end of a session.
