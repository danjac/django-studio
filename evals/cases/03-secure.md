# Security audit finds seeded vulnerabilities

Covers `/djs-secure`. The setup adds a view to the `users` app with two seeded
holes: it is `@csrf_exempt`, and it updates any user's email by `pk` with no
ownership check (IDOR). The audit must report both as CRITICAL and change no code.

## Setup

```sh
cat >> my_app/users/views.py <<'EOF'


@csrf_exempt
@require_form_methods
@login_required
def update_email(request: AuthenticatedHttpRequest, pk: int) -> RenderOrRedirectResponse:
    """Update a user's email address."""
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.email = request.POST["email"]
        user.save()
        return redirect("index")
    return TemplateResponse(request, "account/delete_account.html")
EOF
sed -i \
  -e 's/^from django.shortcuts import redirect$/from django.shortcuts import get_object_or_404, redirect/' \
  -e 's/^from django.views.decorators.http import require_safe$/from django.views.decorators.csrf import csrf_exempt\nfrom django.views.decorators.http import require_safe/' \
  -e 's/^from my_app.users.gdpr import anonymise_user$/from my_app.users.gdpr import anonymise_user\nfrom my_app.users.models import User/' \
  my_app/users/views.py
sed -i 's|^]$|    path("account/<int:pk>/email/", views.update_email, name="update_email"),\n]|' \
  my_app/users/urls.py
just dj check
```

## Prompt

```text
/djs-secure

Report only. Do not fix anything and do not edit any file, even for CRITICAL
findings: the report is the output of this run. Skip the dependency scan in
section 9 (`uvx pysentry-rs`).
```

## Check

```sh
report="$EVAL_BUILD_OUTPUT"
critical=$(sed -n '/CRITICAL:/,/WARNING:/p' "$report")
echo "$critical"
echo "$critical" | grep -q "update_email"
echo "$critical" | grep -qi "idor"
echo "$critical" | grep -qi "csrf"
git diff --quiet HEAD -- my_app config templates
```

## Review

```text
A security audit of this Django project (package `my_app`) produced the report
below. Check the report against the code.

Verify these facts:

1. Every CRITICAL finding in the report points at code that exists and is
   genuinely exploitable. Quote the code for each.
2. The report flags `update_email` in `my_app/users/views.py` as CRITICAL for
   both the missing ownership check and `@csrf_exempt`.
3. No view in `my_app/**/views.py` has a CRITICAL hole (missing auth on a
   write, IDOR, `csrf_exempt`, XSS sink, SQL built from strings) that the report
   leaves out.

Report:

{build_output}
```
