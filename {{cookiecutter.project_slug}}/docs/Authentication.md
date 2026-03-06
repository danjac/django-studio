# Authentication

> **Already configured. Do not reinstall, re-add to INSTALLED_APPS, or modify the base allauth settings.**
>
> allauth is fully set up by the project template. The tasks below describe what is already working and how to extend it safely.

## What is already in place

- `allauth`, `allauth.account`, `allauth.socialaccount` in `INSTALLED_APPS` (`config/settings.py`)
- `allauth.account.middleware.AccountMiddleware` in `MIDDLEWARE`
- `path("account/", include("allauth.urls"))` in `config/urls.py`
- `AUTH_USER_MODEL = "users.User"` — custom user model in `{{cookiecutter.package_name}}/users/`
- Email/username login, mandatory email verification by code, password reset by code
- All account templates already customised in `templates/account/` and `templates/socialaccount/`
- GDPR cookie consent handled by the cookie banner in `base.html` — **do not add database fields for consent**

## Adding a social provider

Social providers can be added at any time without touching the base allauth setup:

1. Add the provider app to `INSTALLED_APPS` in `config/settings.py`:
   ```python
   "allauth.socialaccount.providers.google",
   ```
2. Configure credentials in `SOCIALACCOUNT_PROVIDERS` (already has a Google stub):
   ```python
   SOCIALACCOUNT_PROVIDERS = {
       "google": {
           "APP": {"client_id": "…", "secret": "…", "key": ""},
       }
   }
   ```
3. Run `just dj migrate` — the socialaccount tables are already present.

## Customising the signup form

To collect extra fields at signup, set `ACCOUNT_SIGNUP_FORM_CLASS` to a form that inherits from `forms.Form` and implements `signup(self, request, user)`:

```python
# {{cookiecutter.package_name}}/users/forms.py
from django import forms

class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=150)

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"]
        user.save(update_fields=["first_name"])
```

```python
# config/settings.py
ACCOUNT_SIGNUP_FORM_CLASS = "{{cookiecutter.package_name}}.users.forms.SignupForm"
```

## Testing

Use `force_login` in unit tests. Do not POST through the allauth signup/login flow unless you are specifically testing the auth flow itself.

```python
def test_profile(client, user):
    client.force_login(user)
    response = client.get(reverse("users:profile"))
    assert response.status_code == 200
```
