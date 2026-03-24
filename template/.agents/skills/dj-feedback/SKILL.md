File a GitHub issue against the django-studio template repo. Use this when the
bug or improvement belongs in the template, not this project.

**Steps:**

1. If a description was not provided inline, ask the user to describe the
   problem or improvement in plain text and wait for their reply.

2. From the description, draft a concise issue title (≤72 characters,
   imperative mood, e.g. "Add X", "Fix Y when Z").

3. Show the proposed title to the user:
   ```
   Proposed title: "<title>"
   Post this issue to danjac/django-studio? [y/n]
   ```
   Wait for confirmation. If the user suggests a different title, use theirs.

4. Once confirmed, file the issue:
   ```bash
   gh issue create --repo danjac/django-studio --title "<title>" --body "<description>"
   ```

5. Print the new issue URL.

---

## Help

**/dj-feedback [description]**

Files a GitHub issue against the `danjac/django-studio` template repository.

Use this when you find a bug or want to suggest an improvement to the template
itself — not for issues specific to your project. Requires `gh` CLI authenticated
with GitHub.

Example:
  /dj-feedback "create-view doesn't wire URL for top-level views correctly"
