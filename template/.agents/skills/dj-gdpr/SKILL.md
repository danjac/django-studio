---
description: GDPR compliance audit: PII in models, erasure, consent, logging
---

Audit the project for GDPR compliance issues.

## Required reading

- `docs/GDPR.md`

Report findings in two groups: **REQUIRED** (likely non-compliant) and
**ADVISORY** (worth reviewing).

---

### 1. Personal data in models

Scan all `models.py` files under `<package_name>/`. For each model, identify
fields that likely contain personal data (names containing: `email`, `name`,
`phone`, `address`, `ip`, `location`, `birth`, `gender`, `username`).

For each model with PII fields, check:

| Check | REQUIRED if failing |
|---|---|
| An anonymisation function exists for this model (or the User model covers it) | No anonymisation found |
| Anonymisation covers all identified PII fields | Field missing from anonymisation |
| ForeignKeys to the User model have appropriate `on_delete` | Unclear cascade behaviour on user deletion |

### 2. Right to erasure

Check for a view or utility function that anonymises or deletes a user account:

| Check | REQUIRED if failing |
|---|---|
| An `anonymise_user` function (or equivalent) exists | Missing |
| It sets `is_active = False` | Missing |
| It replaces email with a placeholder | Missing |
| It calls `set_unusable_password()` | Missing |
| It handles related PII models | No cascade to related models |

### 3. Data export (right of access)

Check for a view that exports user data:

| Check | ADVISORY if failing |
|---|---|
| A data export view exists | Missing — implement when the project goes live |
| It requires authentication | Unauthenticated access |
| It covers all models containing user PII | Incomplete export |

### 4. Consent

Check the User model (and any related models) for consent fields:

| Check | ADVISORY if failing |
|---|---|
| Marketing/communication consent field exists | Missing |
| Consent timestamp recorded | Missing |
| Privacy policy version recorded | Missing |

### 5. Logging

Scan `config/settings.py` and any `LOGGING` configuration for handlers that
might log personal data:

| Check | REQUIRED if failing |
|---|---|
| No email addresses in log format strings | PII in log format |
| `send_default_pii = False` in Sentry config (if Sentry enabled) | Sentry sending PII |

### 6. Third-party services

Check `config/settings.py` and installed apps for third-party integrations
that receive user data (email providers, analytics, error tracking):

For each integration found, flag as ADVISORY:
> `<service>` receives user data — verify a Data Processing Agreement is in
> place and data transfer outside EU/EEA is covered.

---

### Report format

```
REQUIRED (likely non-compliant — address before going live):
  [models] User.email has no anonymisation coverage
  [erasure] anonymise_user() does not call set_unusable_password()
  ...

ADVISORY (review before go-live):
  [export] No data export view found
  [consent] No marketing consent field on User model
  [third-party] Mailgun receives user data — verify DPA is in place
  ...

OK:
  [erasure] anonymise_user() found and covers email, username, first_name, last_name
  ...
```

---

## Help

**/dj-gdpr**

Audits the project for GDPR compliance issues.

Checks PII handling in models, data erasure flows, user consent, logging, and
data retention. Reports REQUIRED (likely non-compliant) and ADVISORY findings.
Read `docs/GDPR.md` for the conventions used in this project.

Example:
  /dj-gdpr
