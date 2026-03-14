Audit the codebase for security issues. Report findings in three groups:

- **CRITICAL** — likely exploitable: missing auth, XSS sinks, CSRF bypass, IDOR
- **WARNING** — clear weakness that should be fixed before going live
- **ADVISORY** — best practice gap, lower immediate risk

Work through each section below. Read every referenced file; do not skip
sections because they seem unlikely to have issues.

---

### 1. Settings

Read `config/settings.py` (and any environment-specific overrides).

Local development intentionally uses insecure values (e.g. `DEBUG=True`,
`SESSION_COOKIE_SECURE=False`). That is expected and fine — the audit is not
checking the current runtime value but whether an insecure value can reach
production.

For each setting, apply this decision tree:

1. **Hardcoded to an insecure value** → flag at the severity below; it will
   be insecure in every environment including production.
2. **Read from env with an insecure default** (e.g. `env("DEBUG", default=True)`)
   → flag at the severity below; production will be insecure if the env var
   is not explicitly set.
3. **Read from env with a secure default** (e.g. `env("DEBUG", default=False)`)
   → OK; local dev can override via `.env`, production is safe if the var is
   unset.
4. **Derived from another env-driven setting** (e.g. `SESSION_COOKIE_SECURE = not DEBUG`
   where `DEBUG` is env-driven with `default=False`) → OK.

| Setting | Secure value | Severity if hardcoded insecure or unsafe default |
|---|---|---|
| `DEBUG` | `False` | CRITICAL |
| `SECRET_KEY` | any value from env | CRITICAL |
| `ALLOWED_HOSTS` | explicit list from env | CRITICAL |
| `DATABASE PASSWORD` | from env | CRITICAL |
| `SESSION_COOKIE_SECURE` | `True` | WARNING |
| `CSRF_COOKIE_SECURE` | `True` | WARNING |
| `SECURE_SSL_REDIRECT` | `True` | WARNING |
| `SECURE_HSTS_SECONDS` | `> 0` | WARNING |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` | WARNING |
| `X_FRAME_OPTIONS` | `"DENY"` or `"SAMEORIGIN"` | WARNING |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` | ADVISORY |
| CSP headers | middleware or header present | WARNING |
| Django admin URL | not `"admin/"` | ADVISORY |
| `DEBUG_TOOLBAR` in `INSTALLED_APPS` | guarded by `DEBUG` check | WARNING |

---

### 2. View security

Scan all `views.py` files under `<package_name>/`.

#### 2a. HTTP method decorators

Every view function must have an explicit HTTP method decorator:
`@require_safe`, `@require_POST`, `@require_http_methods([...])`, or
`@require_form_methods` (project custom). A view with no method decorator
accepts any HTTP verb.

Flag as **WARNING** any view that:
- Has no HTTP method decorator
- Accepts `GET` and `POST` without `@require_form_methods` or an explicit
  `@require_http_methods(["GET", "HEAD", "POST"])`

#### 2b. Authentication

**First, check the middleware.** Read `MIDDLEWARE` in `config/settings.py`.

- If `django.contrib.auth.middleware.LoginRequiredMiddleware` is present, the
  project is **secure by default**: every view requires authentication unless
  it explicitly opts out with `@login_not_required`. In this case, do not flag
  missing `@login_required` decorators — the middleware covers them. Instead,
  audit `@login_not_required` views: verify each one is genuinely intended to
  be public (login page, signup, public landing pages, etc.).

- If `LoginRequiredMiddleware` is **not** present, audit each view individually.
  Do not flag a missing `@login_required` as a problem on its own — many views
  are intentionally public (homepage, about page, public listings). Only flag
  as **CRITICAL** when a view without an auth guard:
  - Returns data that is private or scoped to the current user, or
  - Writes to the database on behalf of a user (create, update, delete)

Flag as **WARNING** any view with incorrect decorator ordering. The method
decorator must be outermost, auth decorator next — wrong order means auth
can run after the method check has already rejected the request:

```python
@require_safe        # outermost — correct
@login_required
def my_view(request):
```

#### 2c. Object-level permissions (IDOR)

An Insecure Direct Object Reference occurs when a view fetches an object by
`pk` (or `id`, `slug`) without verifying the current user is allowed to
access or mutate it.

Scan for views that:
1. Accept a `pk` (or `id`, `slug`) URL parameter
2. Fetch the object with `get_object_or_404` or `.get(pk=pk)`
3. Perform a read of sensitive data, or any write/delete
4. Do **not** verify ownership

Both of these patterns are acceptable — flag only when neither is present:

```python
# Pattern A — filter ownership in the query
obj = get_object_or_404(Post, pk=pk, author=request.user)

# Pattern B — fetch then check, raise PermissionDenied or 404
obj = get_object_or_404(Post, pk=pk)
if obj.author != request.user:
    raise PermissionDenied
```

Flag as **CRITICAL** any view where a user could access or mutate another
user's data by changing the `pk` in the URL with no ownership check at all.

---

### 3. XSS

Scan all Python files and all templates under `templates/`.

#### 3a. `mark_safe` and `safe` usage

Flag as **CRITICAL** any `mark_safe(...)` call or `{{ variable | safe }}`
where the value contains user-supplied data or a variable (not a fully static
developer-controlled string).

Flag as **WARNING** every use of `mark_safe(...)` or `| safe` — even on
static strings — as each one bypasses auto-escaping and requires explicit
justification.

`format_html(...)` is safe when used correctly (it escapes all `{}`
arguments), but flag as **WARNING** any `format_html` call that concatenates
with `+` or wraps `mark_safe` inside it.

#### 3b. Passing data to JavaScript

Flag as **CRITICAL** any pattern that writes a variable directly into an
inline `<script>` tag or evaluates it as JS:

```html
<!-- CRITICAL: unescaped variable in script -->
<script>var x = "{{ user_input }}";</script>
```

Safe alternatives include `json_script`, `data-*` attributes (read via
`dataset` in JS), AlpineJS `x-data`/`x-init`, or the `escapejs` filter for
string values embedded in JS expressions — all are acceptable as long as
Django's auto-escaping is active (i.e. `| safe` is not used).

#### 3c. AlpineJS `x-html`

`x-html` sets `innerHTML` and is an XSS sink. Flag as **CRITICAL** any
`x-html` directive where the value is not a fully static, developer-controlled
string.

---

### 4. CSRF

#### 4a. `@csrf_exempt`

Flag as **CRITICAL** every use of `@csrf_exempt`. For each one found, state
the view name and ask the user to confirm it is intentional and why CSRF
protection is not needed (e.g. a token-authenticated API endpoint with no
cookie-based session).

#### 4b. HTMX mutations and CSRF

HTMX requests that use `hx-post`, `hx-put`, `hx-patch`, or `hx-delete` must
include the CSRF token. Check that one of the following is present:

- `django-htmx` middleware (handles this automatically via the `HX-*` headers)
- `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'` on `<body>` or each
  mutating element
- A `<meta name="csrf-token">` read by an HTMX config script

Flag as **WARNING** if HTMX mutations exist but none of these patterns is found.

---

### 5. SQL injection

Scan all Python files for raw database access.

Flag as **CRITICAL** any `.extra()`, `.raw()`, or `cursor.execute()` call
where the query string is built with string formatting (f-string, `%`
formatting, or `+` concatenation) using any variable:

```python
cursor.execute(f"SELECT ... WHERE id = {pk}")        # CRITICAL
Model.objects.raw(f"SELECT ... {user_value}")         # CRITICAL
Model.objects.extra(where=[f"col = '{val}'"])         # CRITICAL
```

Parameterised forms are safe but still flag as **WARNING** — raw SQL bypasses
the ORM and should be reviewed regardless:

```python
cursor.execute("SELECT ... WHERE id = %s", [pk])     # WARNING — raw but safe
```

---

### 6. Open redirects

Scan all views that read a `next`, `redirect_to`, or `return_to` parameter
from `request.GET` or `request.POST`.

Flag as **CRITICAL** any redirect that uses such a value without validation.
The correct pattern:

```python
from django.utils.http import url_has_allowed_host_and_scheme

next_url = request.GET.get("next", "")
if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
    return redirect(next_url)
return redirect(settings.LOGIN_REDIRECT_URL)
```

---

### 7. Mass assignment

Scan all `forms.py` files for `ModelForm` subclasses.

Flag as **WARNING** any `ModelForm` with `fields = "__all__"` — this exposes
every model field to user input, including server-managed fields such as
`author`, `created`, or `is_staff`.

---

### 8. Secrets in code

Note: this project's pre-commit hooks already scan for secrets, so this is a
secondary check. Flag as **CRITICAL** any of the following found as a string
literal rather than loaded from the environment:

- A Django `SECRET_KEY` value (long random string; `django-insecure-*`
  placeholder is acceptable in `.env.example` only)
- API keys (patterns like `sk_live_`, `ghp_`, `AKIA`, `Bearer `)
- Database or service passwords
- OAuth client secrets

---

### 9. Dependency vulnerabilities

Note: `uv-secure` pre-commit already checks this. Run as a secondary check:

```bash
uvx uv-secure
```

Flag every reported vulnerability at its upstream severity (CRITICAL/HIGH →
CRITICAL, MEDIUM → WARNING, LOW → ADVISORY). If `uv-secure` is not available:

```bash
uvx pip-audit
```

---

### Report format

```
CRITICAL:
  [idor] orders/views.py:order_edit — fetches Order by pk with no ownership
    check; any authenticated user can edit any order
  [csrf] templates/checkout/payment.html — <form method="post"> missing
    {% csrf_token %}
  [xss] templates/profile/bio.html:14 — {{ bio | safe }} with user content
  ...

WARNING:
  [settings] SESSION_COOKIE_SECURE not set
  [settings] SECURE_SSL_REDIRECT not set
  [views] products/views.py:product_list — no HTTP method decorator
  [sql] reports/queries.py:42 — raw cursor.execute(), verify parameterisation
  ...

ADVISORY:
  [settings] Admin served at default "admin/" path
  [forms] inventory/forms.py:ProductForm — fields = "__all__"
  ...

OK:
  No csrf_exempt usage found
  No mark_safe() usage found
  CSRF token present in all POST forms checked
  ...
```

After listing all findings, print a one-line summary:

```
X critical · Y warnings · Z advisory
```

If there are CRITICAL findings, recommend addressing them before any public
deployment and offer to fix each one. Wait for the user to confirm before
making any changes.
