# Sending Emails

This project uses Mailgun for transactional email in production.

## Configuration

```python
# settings.py
if MAILGUN_API_KEY := env("MAILGUN_API_KEY", default=None):
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    MAILGUN_API_URL = env("MAILGUN_API_URL", default="https://api.mailgun.net/v3")
    MAILGUN_SENDER_DOMAIN = env("MAILGUN_SENDER_DOMAIN")

    ANYMAIL = {
        "MAILGUN_API_KEY": MAILGUN_API_KEY,
        "MAILGUN_API_URL": MAILGUN_API_URL,
        "MAILGUN_SENDER_DOMAIN": MAILGUN_SENDER_DOMAIN,
    }
```

## Environment Variables

```bash
MAILGUN_API_KEY=your-api-key
MAILGUN_SENDER_DOMAIN=your-domain.com
```

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

```python
# settings.py (development)
EMAIL_BACKEND = "anymail.backends.console.EmailBackend"
# Or use SMTP:
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
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
