# GDPR

This project operates under GDPR (EU General Data Protection Regulation).
This document gives practical guidance for implementing features that handle
personal data. It is not legal advice — consult a lawyer for compliance
decisions.

**Read this document before implementing any feature that:**
- Collects, stores, or processes user data
- Adds new model fields containing personal information
- Integrates a third-party service that receives user data
- Implements account management, deletion, or export

---

## Contents

- [What counts as personal data](#what-counts-as-personal-data)
- [Data minimisation](#data-minimisation)
- [User deletion — right to erasure](#user-deletion--right-to-erasure)
- [Data export — right of access](#data-export--right-of-access)
- [Consent](#consent)
- [Data retention](#data-retention)
- [Personal data in logs](#personal-data-in-logs)
- [Cookies](#cookies)
- [Third-party services](#third-party-services)
- [Checklist for new features](#checklist-for-new-features)

## What counts as personal data

Any information that can identify a natural person, directly or indirectly:

- Name, email address, username
- IP addresses, device identifiers
- Location data
- Behavioural data (browsing history, purchase history)
- Any combination of fields that together identify someone

When in doubt, treat it as personal data.

---

## Data minimisation

Only collect what is strictly necessary for the feature. Before adding a model
field that stores personal data, ask: do we actually need this, or is an
aggregate or anonymous value sufficient?

---

## User deletion — right to erasure

Users have the right to request deletion of their personal data. Hard-deleting
a `User` row often breaks foreign key integrity. The preferred pattern is
**anonymisation**: overwrite PII fields with anonymous placeholders, deactivate
the account, and preserve the row for referential integrity.

```python
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

def anonymise_user(user: User) -> None:
    """Replace all PII with anonymous values and deactivate the account."""
    anon = f"deleted-{uuid.uuid4().hex}"
    user.email = f"{anon}@deleted.invalid"
    user.first_name = ""
    user.last_name = ""
    user.username = anon
    user.is_active = False
    user.set_unusable_password()
    user.save()
```

When anonymising:
- Cascade to related models that hold PII (profile data, addresses, etc.)
- Delete or anonymise any uploaded files (profile pictures, documents)
- Clear session data for the user
- Remove from any mailing lists / third-party services

Provide an account deletion view that calls `anonymise_user` and logs the
request. Do not silently hard-delete without the user's explicit confirmation.

---

## Data export — right of access

Users have the right to receive a copy of their personal data in a portable
format. Implement an export view that collects all data held for the user and
returns it as a downloadable JSON or ZIP file.

```python
import json
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe

@require_safe
@login_required
def data_export(request):
    user = request.user
    data = {
        "email": user.email,
        "username": user.username,
        "date_joined": user.date_joined.isoformat(),
        # add related data here
    }
    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type="application/json",
    )
    response["Content-Disposition"] = 'attachment; filename="my-data.json"'
    return response
```

---

## Consent

Track marketing/cookie consent explicitly on the user model or a related
`Consent` model — never infer it. Record the timestamp and the version of the
policy the user consented to:

```python
class User(AbstractUser):
    marketing_consent = models.BooleanField(default=False)
    marketing_consent_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_version = models.CharField(max_length=20, blank=True)
```

Do not pre-tick consent checkboxes. Consent must be a positive opt-in action.

---

## Data retention

Do not store personal data indefinitely. Define a retention period for each
type of data and implement automatic cleanup:

- Inactive accounts: define a period (e.g. 2 years of no login) after which
  accounts are anonymised
- Session data: Django's session framework handles expiry — ensure
  `SESSION_COOKIE_AGE` is set appropriately
- Logs: ensure server/application logs are rotated and do not retain PII
  longer than necessary
- Uploaded files: delete media files when the owning record is anonymised or
  deleted

Use a management command or background task for periodic cleanup rather than
relying on ad-hoc deletion.

---

## Personal data in logs

Storing personal data in the **database** is fine — that is the lawful,
intentional processing the user consented to, covered by your privacy policy
and retention policy.

**Application and server logs are different.** Log files (Django logging,
Gunicorn access logs, Sentry) are typically:
- Stored in plaintext with broader access than the DB
- Retained longer than intended, often indefinitely
- Sent to third-party services (Sentry) under different DPA terms
- Not subject to the right-of-erasure flow that covers the DB

Avoid including personal data in log output:

- Do not log email addresses or usernames in log messages
- Do not log full request payloads (which may contain passwords or form data)
- Do not log query parameters that carry identifiers
- IP addresses: acceptable in access logs for security purposes, but define
  a retention period and ensure they are covered by your privacy policy

If you need to trace a request for debugging, log the opaque user ID (integer
PK) rather than the email or name. If you need to identify the user, look them
up in the DB using the ID.

For Sentry, set `send_default_pii = False` in the SDK init to prevent
automatic capture of IP addresses, cookies, and request headers.

---

## Cookies

- **Session cookies** (required for login): no consent needed — these are
  strictly necessary
- **Analytics / tracking cookies**: require explicit opt-in consent before
  setting
- **Third-party embeds** (maps, video players, social widgets): require consent
  before loading — they may set their own tracking cookies

Do not load any third-party JavaScript that sets cookies before consent is
given.

---

## Third-party services

When integrating a service that receives user data (email provider, analytics,
error tracking, payment processor), verify:

1. The provider is GDPR-compliant and offers a Data Processing Agreement (DPA)
2. Data is not transferred outside the EU/EEA without adequate safeguards
   (Standard Contractual Clauses or equivalent)
3. Only the minimum necessary data is sent — do not forward full user objects
   when only an email address is needed

Services already in the stack:
- **Mailgun** — email provider; sign their DPA; do not include unnecessary
  personal data in email metadata
- **Sentry** (if enabled) — configure PII scrubbing in Sentry settings;
  enable `send_default_pii = False`

---

## Checklist for new features

Before shipping any feature that handles personal data:

- [ ] Is data collection limited to what is strictly necessary?
- [ ] Is a retention period defined for any new data stored?
- [ ] Does account deletion/anonymisation cover any new fields or files?
- [ ] Is any personal data included in the data export?
- [ ] Are logs free of PII?
- [ ] If a third-party service is involved, is a DPA in place?
- [ ] If consent is required, is it an explicit opt-in (not pre-ticked)?
