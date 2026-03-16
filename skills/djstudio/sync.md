Pull the latest django-studio template changes into this project and resolve
any merge conflicts interactively.

## Steps

### 1. Run Copier update

```bash
uvx copier update --trust
```

This pulls the latest template into the project and stages the merged files.
If there are no conflicts, skip to Step 4.

### 2. Detect conflicts

Check for merge conflicts introduced by the update:

```bash
git status
```

List any files with conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`):

```bash
grep -rn "<<<<<<" . --include="*.py" --include="*.html" --include="*.jinja" \
    --include="*.yml" --include="*.toml" --include="*.md" 2>/dev/null
```

### 3. Resolve each conflict interactively

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

### 4. Verify

After all conflicts are resolved:

```bash
just dj check
just typecheck
just test-all
```

Fix any issues before continuing.

### 5. Commit

Stage all resolved files and commit:

```bash
git add -A
git commit -m "chore: sync with django-studio template"
```

Inform the user the sync is complete and the project is ready to push.
