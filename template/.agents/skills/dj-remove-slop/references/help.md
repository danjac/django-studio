**/dj-remove-slop**

Scans the project for common Django anti-patterns introduced by AI assistants
and inattentive developers. Reports all findings grouped by category before
making any changes; waits for confirmation before touching anything.

**What it checks:**

1. `# noqa` comments suppressing legitimate ruff warnings (PLC0415, T201, T100, E402)
2. Redundant `@login_required` when `LoginRequiredMiddleware` is active
3. `get_user_model()` in project-specific code (use a direct import instead)
4. Hard-coded status strings in templates (e.g. `{% if order.status == "pending" %}`)
5. `CASCADE` or `SET_NULL` on ForeignKey without a justification comment
6. `fields = "__all__"` in ModelForms
7. `ordering` in `Model.Meta` (implicit ordering on every queryset)
8. Mutable list literals where tuples should be used (class-level constants)

**Example:**

```
/dj-remove-slop
```

After the report, the agent asks whether to fix all categories or review them
one by one. No files are modified until confirmed.
