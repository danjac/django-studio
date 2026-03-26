# Authentication

> **Already configured. Do not reinstall, re-add to INSTALLED_APPS, or modify the base allauth settings.**
>
> allauth is fully set up by the project template. The tasks below describe what is already working and how to extend it safely.

## Contents

- [What is already in place](#what-is-already-in-place)
- [Adding a social provider](#adding-a-social-provider)
- [Customising the signup form](#customising-the-signup-form)
- [Login by default](#login-by-default)
- [Invite-only signup](#invite-only-signup)
- [Testing](#testing)

## What is already in place

- `allauth`, `allauth.account`, `allauth.socialaccount` in `INSTALLED_APPS` (`config/settings.py`)
- `allauth.account.middleware.AccountMiddleware` in `MIDDLEWARE`
- `path("account/", include("allauth.urls"))` in `config/urls.py`
- `AUTH_USER_MODEL = "users.User"` - custom user model in `my_package/users/`
- Email/username login, mandatory email verification by code, password reset by code
- All account templates already customised in `templates/account/` and `templates/socialaccount/`
- GDPR cookie consent handled by the cookie banner in `base.html` - **do not add database fields for consent**

## Adding a social provider

Social providers can be added at any time without touching the base allauth setup:

1. Add the provider app to `INSTALLED_APPS` in `config/settings.py`:
   ```python
   "allauth.socialaccount.providers.google",
   ```
2. Run `just dj migrate` — the socialaccount tables are already present.
3. In the Django admin, go to **Social Applications** and create an entry for the
   provider. Enter the **Client ID**, **Secret key**, and any other credentials
   required by that provider. Assign it to the current site.

> **Manual step:** credentials are configured in the admin, not in settings. This
> keeps secrets out of source control. Each environment (dev, staging, production)
> needs its own Social Application record.

Consult the provider's documentation for how to obtain credentials and configure
your app:

- **Google** — [Google Identity: OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
  — create a project in Google Cloud Console, enable the OAuth 2.0 API, add your
  domain to the authorised redirect URIs.
- **GitHub** — [GitHub: Creating an OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app)
  — set the callback URL to `https://<your-domain>/account/google/login/callback/`.
- **LinkedIn** — [LinkedIn: OAuth 2.0](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow)
  — create an app in the LinkedIn Developer Portal and request the `openid`,
  `profile`, and `email` scopes.

For any provider not listed above, see the
[allauth provider reference](https://docs.allauth.org/en/latest/socialaccount/providers/index.html).

## Customising the signup form

To collect extra fields at signup, set `ACCOUNT_SIGNUP_FORM_CLASS` to a form that inherits from `forms.Form` and implements `signup(self, request, user)`:

```python
# my_package/users/forms.py
from django import forms

class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=150)

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"]
        user.save(update_fields=["first_name"])
```

```python
# config/settings.py
ACCOUNT_SIGNUP_FORM_CLASS = "my_package.users.forms.SignupForm"
```

## Login by default

If most of your views require authentication, add Django's `LoginRequiredMiddleware`
to `MIDDLEWARE` in `config/settings.py`. This makes authentication the default — every
view requires login unless explicitly opted out.

```python
MIDDLEWARE = [
    ...
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]
```

Public views (landing page, about page, etc.) must then be marked with `@login_not_required`:

```python
from django.contrib.auth.decorators import login_not_required

@login_not_required
def landing(request):
    ...
```

**allauth compatibility:** allauth's own views (`/account/login/`, `/account/signup/`, etc.)
already apply `@login_not_required` internally — you do not need to exempt them manually.

When `LoginRequiredMiddleware` is active, do **not** add `@login_required` to individual
views — it is redundant and misleading.

## Invite-only signup

To restrict signup to invited users only, add an `Invite` model, a signup form that
validates the invite code, and an admin action that sends invitation emails.

### Model

```python
# <package_name>/users/models.py (or a dedicated invites.py)
import secrets
from django.utils.translation import gettext_lazy as _l

def _generate_invite_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


class Invite(models.Model):
    email = models.EmailField(_l("email"), unique=True)
    code = models.CharField(_l("code"), max_length=6, default=_generate_invite_code)
    sent = models.DateTimeField(_l("sent"), null=True, blank=True)
    claimed = models.DateTimeField(_l("claimed"), null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_l("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invites",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = _l("invite")
        verbose_name_plural = _l("invites")
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(claimed__isnull=True),
                name="unique_code_if_unclaimed",
            ),
        ]

    def __str__(self) -> str:
        return self.email
```

### Signup form

The form validates the code and claims the invite when the user completes signup.
Wire it in via `ACCOUNT_SIGNUP_FORM_CLASS`:

```python
# <package_name>/users/forms.py
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _l

class InviteSignupForm(forms.Form):
    code = forms.CharField(
        label=_l("Invitation code"),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={"autocomplete": "off", "inputmode": "numeric"}),
        help_text=_l("Enter the 6-digit code from your invitation email."),
    )

    def clean_code(self) -> str:
        code = self.cleaned_data["code"]
        try:
            self._invite = Invite.objects.get(code=code, claimed__isnull=True)
        except Invite.DoesNotExist as exc:
            raise forms.ValidationError(
                _l("This invitation code is invalid or has already been used.")
            ) from exc
        return code

    def signup(self, request, user) -> None:
        self._invite.claimed = timezone.now()
        self._invite.user = user
        self._invite.save(update_fields=["claimed", "user", "updated"])
```

```python
# config/settings.py
ACCOUNT_SIGNUP_FORM_CLASS = "<package_name>.users.forms.InviteSignupForm"
```

No custom `AccountAdapter` is needed — signup remains open and the form enforces the gate.

### Admin

The admin creates invites and sends the invitation email on first save:

```python
# <package_name>/users/admin.py
from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.forms import ModelForm, ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _l

from allauth.account.models import EmailAddress

class InviteAdminForm(ModelForm):
    class Meta:
        model = Invite
        fields = ["email"]

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        if (
            User.objects.filter(email__iexact=email).exists()
            or EmailAddress.objects.filter(email__iexact=email).exists()
        ):
            raise ValidationError(_l("A user with this email address already exists."))
        return email


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    form = InviteAdminForm
    list_display = ["email", "code", "sent", "claimed", "user", "created"]
    search_fields = ["email"]
    list_filter = ["sent", "claimed"]
    readonly_fields = ["code", "sent", "claimed", "user", "created", "updated"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.sent is not None:
            return
        site = Site.objects.get_current()
        context = {"invite": obj, "site": site}
        subject = render_to_string("users/invite_email_subject.txt", context).strip()
        body = render_to_string("users/invite_email.txt", context).strip()
        send_mail(subject, body, from_email=None, recipient_list=[obj.email])
        obj.sent = timezone.now()
        obj.save(update_fields=["sent"])
```

Create `templates/users/invite_email_subject.txt` and `templates/users/invite_email.txt`
with the invitation email content.

## Testing

Use `force_login` in unit tests. Do not POST through the allauth signup/login flow unless you are specifically testing the auth flow itself.

```python
def test_profile(client, user):
    client.force_login(user)
    response = client.get(reverse("users:profile"))
    assert response.status_code == 200
```
