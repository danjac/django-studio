---
description: Scan for and remove Django anti-patterns introduced by AI or inattentive devs
---

Scan the project for low-quality code patterns. Report every finding before
making any changes. Wait for user confirmation before touching anything.

> **Philosophy:** Ruff already enforces inline-import rules (PLC0415),
> `print()` statements (T201), and `pdb` usage (T100). Let it do its job.
> This skill targets patterns ruff **cannot** catch — and `# noqa` abuse
> that actively defeats ruff.

---

## 1. `# noqa` comments suppressing legitimate warnings

A `# noqa` comment on a line means the developer silenced a tool rather than
fixing the code. The only accepted exception is a genuine circular import at
module load time that truly cannot be resolved by restructuring — and even
then a comment explaining the circular dependency is mandatory.

Common offenders:

| noqa code | Rule | Root cause |
|-----------|------|------------|
| `PLC0415` | Import not at top of file | Inline import — move it |
| `T201`    | `print()` found | Debug leftover — delete it |
| `T100`    | `pdb`/`breakpoint()` found | Debug leftover — delete it |
| `E402`    | Module level import not at top | Import ordering — fix it |

```bash
rg "# noqa" --type py
```

For each hit:

1. Identify the suppressed rule(s).
2. Determine whether the suppression is genuinely justified (unavoidable
   circular import with an explanatory comment — rare).
3. Flag everything that is not justified. For inline imports (`PLC0415`),
   determine whether a circular import genuinely prevents moving it to the
   top of the file. If not, it must be moved.

---

## 2. Redundant `@login_required`

Read `MIDDLEWARE` in the settings file. If
`django.contrib.auth.middleware.LoginRequiredMiddleware` is listed, the
project is **secure by default** — every view requires authentication unless
opted out with `@login_not_required`. In this case, `@login_required`
decorators on individual views are redundant and should be removed.

```bash
rg "@login_required" --type py
```

Flag every occurrence if `LoginRequiredMiddleware` is present. Remove them
(they add noise and mislead readers into thinking other views are public).

---

## 3. `get_user_model()` outside pluggable app code

`get_user_model()` exists for pluggable, reusable apps that must not
hard-code a specific User model. In an application's own code, importing
the User model directly is cleaner and type-safe.

```bash
rg "get_user_model\(\)" --type py
```

For each hit, check whether the file is part of a reusable, installable app
(i.e., intended for distribution on PyPI). If it is project-specific
application code, replace `get_user_model()` with a direct import from the
project's user model module.

---

## 4. Hard-coded status strings in templates

Model status comparisons in templates should use model properties or
template-tag helpers, not raw string literals. Hard-coded strings break if
the choice value ever changes and are harder to read than a named property.

```bash
rg '(status|state)\s*==\s*["\x27][a-z_]+["\x27]' templates/ --type html
```

For each hit, check whether the model has (or should have) a boolean property
(e.g. `is_active`, `is_published`) or a `Status.ACTIVE` constant that can be
compared instead. Suggest the cleaner form; do not change template logic
without confirming the property exists on the model.

---

## 5. `CASCADE` or `SET_NULL` on ForeignKey without justification

The project default is `on_delete=PROTECT` — records are archived, not
deleted. Any `CASCADE` or `SET_NULL` usage must have an accompanying comment
explaining why the default was overridden.

```bash
rg "on_delete\s*=\s*models\.(CASCADE|SET_NULL)" --type py
```

For each hit, check whether there is a comment on the same line or immediately
above explaining the choice. Flag any that lack a justification comment.

---

## 6. `fields = "__all__"` in ModelForms

Exposes every model field to user input, including server-managed fields.

```bash
rg 'fields\s*=\s*["\x27]__all__["\x27]' --type py
```

Flag every occurrence. For each, list the model's fields and ask the user
which ones should be included explicitly.

---

## 7. `ordering` in `Model.Meta`

`Meta.ordering` silently appends `ORDER BY` to **every** queryset for the
model — including `COUNT`, `EXISTS`, and subqueries that don't need it. This
degrades performance, makes query plans harder to read, and hides the sort
intent at the query site where it actually matters.

```bash
rg "^\s+ordering\s*=" --type py
```

For each hit inside a `Meta` class:

1. Note the model and the ordering field(s).
2. Find every queryset on that model (in views, managers, services) that
   relies on the implicit ordering.
3. Add explicit `.order_by(...)` to those querysets.
4. Remove the `ordering` line from `Meta`.

**Exception:** through-model intermediary tables with a natural sort key
(e.g. `position` on a drag-and-drop ordering model) *may* keep `ordering`
if the sort is truly universal — flag these as **advisory** rather than
**required** and let the user decide.

---

## 8. Mutable class-level constants — lists instead of tuples

Class-level constants (model `Meta` attributes, form `Meta` attributes,
permission lists, etc.) should be tuples, not lists. A list is mutable and
signals the wrong intent; a tuple is the correct Python idiom for a fixed
sequence that is never modified after definition.

```bash
rg "ClassVar\[list" --type py
```

Also catch bare list literals on common Django class attributes:

```bash
rg "^\s+(ordering|fields|exclude|permissions|default_permissions)\s*=\s*\[" --type py
```

For each hit, replace the list literal `[...]` with a tuple `(...)`.
For `ClassVar[list[X]]` type annotations, update to `tuple[X, ...]` — **no
`ClassVar` wrapper**. `ClassVar` is only needed for mutable class attributes
(lists, dicts) to prevent dataclass/type-checker confusion. Tuples are
immutable, so the plain type annotation `CONSTANT: tuple[str, ...] = (...)`
is correct and sufficient.

---

## 9. Low-quality redirect assertions in tests

Redirect assertions written against raw status codes and `response["Location"]`
are harder to read and more brittle than Django's built-in `response.url`.

```bash
rg 'status_code\s*==\s*30[0-9]' --type py
rg 'response\["Location"\]' --type py
```

Apply these mechanical fixes:

1. `assert response.status_code == 302` + `assert response["Location"] == X`
   → `assert response.url == X`
2. `assert response.status_code == 302` + `assert response.url == X` (already present)
   → drop the now-redundant `status_code` line
3. `assert response.status_code == 302` + `assert "X" in response["Location"]`
   → `assert "X" in response.url`
4. `assert response.status_code == 302` + `assert response["Location"].endswith(X)`
   → `assert response.url.endswith(X)`
5. Bare `assert response.status_code == 302` with no URL check
   → leave unchanged (destination unknown; flagging only)

---

## Report format

Present findings grouped by category before taking any action:

```
NOQA ABUSE (§1)
  payments/services.py:88   from stripe import Charge  # noqa: PLC0415
  utils/helpers.py:77       print("debug here")  # noqa: T201

REDUNDANT @login_required (§2)
  orders/views.py:8         @login_required on order_list (LoginRequiredMiddleware active)

get_user_model() (§3)
  notifications/models.py:3  get_user_model() — project-specific code, use direct import

HARD-CODED STATUS STRINGS (§4)
  templates/orders/list.html:14  {% if order.status == "pending" %}

CASCADE/SET_NULL WITHOUT COMMENT (§5)
  products/models.py:23  category = ForeignKey(Category, on_delete=models.CASCADE)

MODELFORM __all__ (§6)
  contacts/forms.py:12  fields = "__all__"

Meta.ordering (§7)
  orders/models.py:18   ordering = ["-created_at"]  → move to queryset .order_by()
  comments/models.py:9  ordering = ["position"]     → advisory (position model)

Mutable class constants (§8)
  accounts/forms.py:12  fields = ["name", "email"]       → change to tuple
  reports/models.py:7   ClassVar[list[str]] = [...]       → tuple[str, ...] = (...) (no ClassVar needed for tuples)

Redirect assertions (§9)
  orders/tests.py:44    assert response.status_code == 302; assert response["Location"] == "/orders/"
                        → assert response.url == "/orders/"
  orders/tests.py:71    assert response.status_code == 302  (no URL check — flagged only)
```

After presenting, ask:

> Found N issues across M categories. Should I fix all of them, or review
> category by category?

Do not modify any file until the user confirms. Once confirmed, apply the
fixes, then run:

```bash
just check-all
```

Fix any failures before presenting the final summary.
