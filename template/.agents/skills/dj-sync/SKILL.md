---
description: Pull latest template changes via Copier and resolve merge conflicts
---

Pull the latest django-studio template changes into this project and resolve
any merge conflicts interactively.

## Steps

### 1. Run Copier update

```bash
uvx copier update --trust
```

The post-gen hook automatically backs up `.claude/settings.json`, `.mcp.json`,
and `opencode.json` to `<tmpdir>/<project-slug>/` before regenerating them.

This pulls the latest template into the project and stages the merged files.
If there are no conflicts, skip to Step 3.

### 2. Detect and resolve conflicts

Check for merge conflicts introduced by the update:

```bash
git status
```

List any files with conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`):

```bash
grep -rn "<<<<<<" . --include="*.py" --include="*.html" --include="*.jinja" \
    --include="*.yml" --include="*.toml" --include="*.md" 2>/dev/null
```

For every conflicted file:

1. Read the file and show the conflict to the user:
   ```
   Conflict in <file>:
   <<< Current (your project)
   <your version>
   ===
   <template version>
   >>> Incoming (django-studio template)
   ```
2. Explain what each side does in plain language.
3. Ask the user which version to keep, or whether to merge them manually.
4. Apply the user's decision and remove the conflict markers.

Repeat until no conflict markers remain.

### 3. Restore local overrides in generated files

Diff the auto-generated backups against the freshly regenerated files:

```bash
BACKUP_DIR=$(uv run python .agents/skills/dj-sync/resources/get-backup-dir.py)
diff "$BACKUP_DIR/settings.json.bak" .claude/settings.json
diff "$BACKUP_DIR/mcp.json.bak" .mcp.json
diff "$BACKUP_DIR/opencode.json.bak" opencode.json
```

For each file with a non-empty diff:

1. Show the diff to the user.
2. Identify which lines are new template additions vs. local customizations
   the user had made (e.g. extra `permissions.allow` entries, extra MCP
   servers such as `kubernetes`).
3. Ask the user which local customizations to restore, then apply them.

If the backup files don't exist (first sync on a fresh project), skip this step.

### 4. Verify

After all conflicts are resolved:

```bash
just check-all
```

Fix any issues before continuing.

---

### 5. Commit

Stage all resolved files and commit:

```bash
git add -A
git commit -m "chore: sync with django-studio template"
```

Inform the user the sync is complete and the project is ready to push.
