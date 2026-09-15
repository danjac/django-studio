# App README structure

Use this structure for `<package_name>/<app>/README.md`. Omit any section that does
not apply (e.g. no API, no webhooks) — do not leave empty headings. Keep the order.

Sections marked *(authored)* come from the user; *(derived)* come from the code; see
`SKILL.md` for how each kind is treated on update. Do not copy these markers into
the README.

````markdown
# <App name>

<One or two sentences: what this app is responsible for, and what it is not.> (authored)

## Concepts

(authored) Domain terms this app introduces and what they mean in the business —
not the model fields.

- **Invoice** — a bill sent to a customer for one billing period.
- **Void** — cancelling a sent invoice; the number is never reused.

## Business rules

Rule text is authored; *Enforced in* is derived.

| Rule | Why | Enforced in |
| ---- | --- | ----------- |
| An invoice's total cannot change once sent | Legal requirement for issued invoices | `billing/models.py::Invoice.save` |
| Only organisation admins can void invoices | _TODO: confirm with finance_ | `billing/rules.py::can_void_invoice` |

## Lifecycle

(authored meaning, derived states) State machines for models with a status field.

```
draft ──send──▶ sent ──pay──▶ paid
                  └──void──▶ void
```

- **draft** — editable, not visible to the customer.
- **sent** — ...

## API

(derived) Endpoints under `api/`. Auth and error conventions: `docs/building-apis.md`.

| Method | Path | Auth | Request | Response |
| ------ | ---- | ---- | ------- | -------- |
| GET | `/api/v1/invoices/` | Token | `InvoiceListParams` | `InvoiceOut` (paginated) |
| POST | `/api/v1/invoices/` | Token | `InvoiceIn` | `InvoiceOut` |

## Integrations

(derived, with authored notes) Third-party services this app calls or receives
webhooks from. Patterns: `docs/integrating-apis.md`, `docs/webhooks.md`.

| Provider | Direction | Used for | Code | Settings |
| -------- | --------- | -------- | ---- | -------- |
| Acme Payments | Webhook in | Mark invoices paid | `billing/webhooks/views.py::acme_webhook` | `ACME_WEBHOOK_SECRETS` |

## Background work

(derived) Tasks, management commands and scheduled jobs.

| Name | Kind | Trigger | Purpose |
| ---- | ---- | ------- | ------- |
| `process_webhook_event` | Task | Acme webhook | Apply payment events |
| `send_invoice_reminders` | Command | Cron, daily | Email customers with overdue invoices |

## Personal data

(derived) Where this app stores personal data and how it is erased. See
`docs/gdpr.md`.

## Gotchas and decisions

(authored) Things that look wrong but are intentional, known limitations, and
planned changes.

## Reference

(derived) Where to look in the code.

- Models: `billing/models.py` — `Invoice`, `WebhookEvent`
- Permissions: `billing/rules.py`
- URLs: `billing_*` namespaces in `billing/urls.py`, `billing/api/urls.py`
- Depends on: `organizations`, `users`
````
