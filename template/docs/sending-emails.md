# Sending Emails

This project uses Mailgun for transactional email in production.

## Contents

- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Development](#development)
- [Anymail](#anymail)
- [Email Templates](#email-templates)
- [Best Practices](#best-practices)

## Configuration

Email backends are configured with the [`MAILERS`](https://docs.djangoproject.com/en/6.1/ref/settings/#mailers)
setting (Django 6.1+), which works like `CACHES` or `STORAGES`. The legacy
`EMAIL_BACKEND` / `EMAIL_HOST` / `EMAIL_*` settings are deprecated — do not add them.

```python
# settings.py
if MAILGUN_API_KEY := env("MAILGUN_API_KEY", default=None):
    MAILGUN_API_URL = env("MAILGUN_API_URL", default="https://api.mailgun.net/v3")
    MAILGUN_SENDER_DOMAIN = env("MAILGUN_SENDER_DOMAIN")

    ANYMAIL = {
        "MAILGUN_API_KEY": MAILGUN_API_KEY,
        "MAILGUN_API_URL": MAILGUN_API_URL,
        "MAILGUN_SENDER_DOMAIN": MAILGUN_SENDER_DOMAIN,
    }

    MAILERS = {
        "default": {
            "BACKEND": "anymail.backends.mailgun.EmailBackend",
        },
    }
```

Without `MAILGUN_API_KEY`, the `default` mailer is built from `EMAIL_URL`
(e.g. `smtp://localhost:1025`, `console://`), mapped to the backend's `OPTIONS`
(`host`, `port`, `username`, `password`, `use_tls`, ...).

### Multiple mailers

Add further aliases to `MAILERS` for mail that needs a different backend or
account (e.g. newsletters), and select one with `using`:

```python
from django.core import mail

mail.send_mail(..., using="newsletters")
mail.mailers["newsletters"].send_messages(messages)
```

Use `mail.mailers.default` instead of the deprecated `mail.get_connection()`,
and `using=` instead of the deprecated `connection=` argument.

## Environment Variables

```bash
MAILGUN_API_KEY=your-api-key
MAILGUN_SENDER_DOMAIN=your-domain.com
```

## Testing

The test runner replaces the backend of every configured mailer with the
in-memory backend, so tests never send real email. Assert on
`django.core.mail.outbox`.

## Development

For local development, use Mailpit:

```yaml
# docker-compose.yml
mailpit:
  image: axllent/mailpit:v1.27
  ports:
    - "8025:8025"  # Web UI
    - "1025:1025"  # SMTP
```

The default `EMAIL_URL=smtp://localhost:1025` sends mail to Mailpit. To print
emails to the console instead:

```bash
# .env
EMAIL_URL=console://
```

Access Mailpit web UI at http://localhost:8025 to view captured emails.

## Anymail

`django-anymail` is already in `pyproject.toml`. It provides the email backend abstraction used above.

Benefits:
- Easy to switch email providers
- Unified API for sending
- Tracking and webhook support

## Email Templates

Django email templates:

```python
from django.core.mail import send_mail

send_mail(
    subject="Subject",
    message="Plain text message",
    html_message="<p>HTML message</p>",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=["user@example.com"],
)
```

## Best Practices

1. Use `DEFAULT_FROM_EMAIL` consistently
2. Use HTML templates for rich emails
3. Provide plain-text fallback
4. Track bounces and complaints via webhooks
5. Use Mailpit in development to avoid sending real emails
