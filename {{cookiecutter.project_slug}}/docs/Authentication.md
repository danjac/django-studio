# Authentication

This project uses django-allauth for authentication.

## Installation

```bash
uv add django-allauth
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
]
```

Add middleware:

```python
MIDDLEWARE = [
    # ...
    "allauth.account.middleware.AccountMiddleware",
]
```

## Configuration

```python
# settings.py

# Signup fields
ACCOUNT_SIGNUP_FIELDS = [
    "email",
    "username",
]

# Login methods (username or email)
ACCOUNT_LOGIN_METHODS = {"username", "email"}

# Email verification
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION_SUPPORTS_RESEND = True
ACCOUNT_UNIQUE_EMAIL = True

# Password reset
ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True

# Security
ACCOUNT_PREVENT_ENUMERATION = False
```

## URL Configuration

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    # ...
    path("accounts/", include("allauth.urls")),
]
```

## Templates

Customize allauth templates in `templates/account/` and `templates/socialaccount/`:

```
templates/
├── account/
│   ├── login.html
│   ├── signup.html
│   ├── password_reset.html
│   ├── password_change.html
│   ├── email.html
│   └── ...
└── socialaccount/
    ├── login.html
    ├── signup.html
    ├── connections.html
    └── ...
```

Override with custom templates as needed to match your site's design.

## Social Login

Enable social providers via `SOCIALACCOUNT_PROVIDERS`:

```python
# settings.py
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": "your-client-id",
            "secret": "your-secret",
            "key": "",
        }
    },
    # Add more providers as needed
}
```

Add to installed apps:
```python
INSTALLED_APPS = [
    # ...
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # ...
]
```

## Custom User Model

If using a custom user model:

```python
# settings.py
AUTH_USER_MODEL = "users.User"
```

## Testing

For tests, use Django's test client or pytest-django:

```python
def test_login(client, user):
    response = client.post(
        "/accounts/login/",
        {"login": user.email, "password": "testpass"},
    )
    assert response.status_code == 302
```

## Best Practices

1. Use custom templates to match your site design
2. Enable email verification for production
3. Use ACCOUNT_EMAIL_VERIFICATION_BY_CODE for better UX
4. Configure SOCIALACCOUNT_PROVIDERS for social login
5. Use ACCOUNT_PREVENT_ENUMERATION to protect against email enumeration attacks
