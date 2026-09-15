# Webhooks

A webhook is an HTTP `POST` a third-party service (payment provider, Git host, CRM)
sends to this project when something happens on their side. Treat every webhook
request as **untrusted, possibly duplicated, possibly out of order, and possibly
replayed**.

For calling third-party APIs (including re-fetching objects a webhook refers to), see
`docs/integrating-apis.md`. For exposing this project's own JSON API, see
`docs/building-apis.md`.

## Contents

- [Check for a ready-made integration first](#check-for-a-ready-made-integration-first)
- [The flow](#the-flow)
- [Layout](#layout)
- [Secrets](#secrets)
- [Signature verification](#signature-verification)
- [Recording events](#recording-events)
- [Schemas](#schemas)
- [The view](#the-view)
- [Processing in a task](#processing-in-a-task)
- [Local development](#local-development)
- [Testing](#testing)

## Check for a ready-made integration first

- **Email events** (bounces, complaints, opens): `django-anymail` is already installed
  and ships signed tracking and inbound webhooks for every ESP it supports. Use its
  `tracking` / `inbound` signals — see
  [Anymail: tracking webhooks](https://anymail.dev/en/stable/sending/tracking/) and
  `docs/sending-emails.md`. Do not hand-roll these.
- **Provider SDKs** (e.g. Stripe) often include a signature verification helper. Use
  it instead of reimplementing the scheme below — but keep the rest of this section's
  flow (idempotency, background processing).

## The flow

Every webhook view does the same five things, in this order:

1. **Verify the signature** against the raw request body. Reject anything else.
2. **Reject stale timestamps** to block replayed requests.
3. **Parse the envelope** (event ID and type) with Pydantic.
4. **Record the event once**, keyed by the provider's event ID.
5. **Enqueue a background task** and return `200` immediately.

Business logic never runs in the request. Providers time out after a few seconds and
retry on any non-2xx response, so slow or failing handlers turn into duplicate
deliveries.

## Layout

Group a provider's webhook code in a `webhooks/` package inside the app that owns
the behaviour:

```
my_package/
    billing/
        models.py             # WebhookEvent
        tasks.py              # process_webhook_event
        webhooks/
            __init__.py
            schemas.py        # Pydantic payload models
            signatures.py     # verify_signature
            urls.py
            views.py
        tests/
            webhooks/
                __init__.py
                test_signatures.py
                test_views.py
            test_tasks.py
```

```python
# config/urls.py
path("webhooks/", include("my_package.billing.webhooks.urls")),
```

```python
# my_package/billing/webhooks/urls.py
from django.urls import path

from my_package.billing.webhooks import views

app_name = "billing_webhooks"

urlpatterns = [
    path("acme/", views.acme_webhook, name="acme"),
]
```

## Secrets

Store the signing secret in the environment, never in code or the database:

```python
# config/settings.py
ACME_WEBHOOK_SECRETS = env.list("ACME_WEBHOOK_SECRETS", default=[])
```

Use a **list** so the secret can be rotated: add the new secret, update it in the
provider dashboard, then remove the old one. Add the variable to the deployment
secrets described in `docs/deployment.md`.

## Signature verification

The exact scheme is provider-specific — read their docs. Most use HMAC-SHA256 over a
timestamp and the raw body. This example assumes a header of the form
`Acme-Signature: t=1726400000,v1=<hex digest>`:

```python
# my_package/billing/webhooks/signatures.py
import hashlib
import hmac
import time

TOLERANCE_SECONDS = 300


class InvalidSignatureError(Exception):
    """The webhook signature is missing, malformed, stale, or does not match."""


def verify_signature(
    body: bytes,
    header: str,
    secrets: list[str],
    *,
    now: float | None = None,
) -> None:
    """Raise InvalidSignatureError unless the header signs the body with a known secret."""
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
    try:
        timestamp = int(parts["t"])
        signature = parts["v1"]
    except KeyError as exc:
        raise InvalidSignatureError("Malformed signature header") from exc
    except ValueError as exc:
        raise InvalidSignatureError("Malformed timestamp") from exc

    current = time.time() if now is None else now
    if abs(current - timestamp) > TOLERANCE_SECONDS:
        raise InvalidSignatureError("Timestamp outside tolerance")

    message = f"{timestamp}.".encode() + body
    for secret in secrets:
        expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, signature):
            return
    raise InvalidSignatureError("Signature mismatch")
```

Rules:

- **Verify the raw bytes** (`request.body`). Never re-serialize parsed JSON and sign
  that — key order and whitespace will differ.
- **Always use `hmac.compare_digest`**; `==` leaks timing information.
- **No secrets configured means reject everything** — the loop above falls through
  to `InvalidSignatureError` when `secrets` is empty. Never skip verification in
  development; use the provider's test secret instead.
- IP allowlists are an optional extra layer, never a substitute for signatures.

## Recording events

Store each delivery once. A unique constraint on the provider's event ID makes
retries and duplicate deliveries harmless:

```python
# my_package/billing/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _l


class WebhookEvent(models.Model):
    """A webhook delivery received from a third-party provider."""

    class Status(models.TextChoices):
        PENDING = "pending", _l("Pending")
        PROCESSED = "processed", _l("Processed")
        IGNORED = "ignored", _l("Ignored")
        FAILED = "failed", _l("Failed")

    provider = models.CharField(_l("provider"), max_length=50)
    event_id = models.CharField(_l("event ID"), max_length=255)
    event_type = models.CharField(_l("event type"), max_length=100)
    payload = models.JSONField(_l("payload"))
    status = models.CharField(
        _l("status"),
        max_length=20,
        choices=Status,
        default=Status.PENDING,
    )
    error = models.TextField(_l("error"), blank=True)
    received = models.DateTimeField(_l("received"), auto_now_add=True)
    processed = models.DateTimeField(_l("processed"), null=True, blank=True)

    class Meta:
        verbose_name = _l("webhook event")
        verbose_name_plural = _l("webhook events")
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "event_id"],
                name="unique_webhook_event",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.event_type}:{self.event_id}"
```

Register it in the admin (read-only) so failed events can be inspected. Payloads may
contain personal data — prune processed events on a schedule (see
`docs/cron-jobs.md`) and follow `docs/gdpr.md`.

## Schemas

Webhook payloads are a **provider-controlled** schema that grows over time. Unlike
`docs/building-apis.md` (where input models use `extra="forbid"`), webhook models
must **ignore unknown fields** — Pydantic's default — so a new provider field does
not break ingestion.

Validate the envelope in the view and the event-specific data in the task:

```python
# my_package/billing/webhooks/schemas.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class WebhookEnvelope(BaseModel):
    """Fields common to every Acme webhook."""

    id: str
    type: str
    created: datetime
    data: dict[str, Any]


class InvoicePaidData(BaseModel):
    """Payload for `invoice.paid` events."""

    invoice_id: str
    customer_id: str
    amount: int
    currency: str
```

## The view

```python
# my_package/billing/webhooks/views.py
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from pydantic import ValidationError

from my_package.billing.models import WebhookEvent
from my_package.billing.tasks import process_webhook_event
from my_package.billing.webhooks.schemas import WebhookEnvelope
from my_package.billing.webhooks.signatures import InvalidSignatureError, verify_signature
from my_package.http.request import HttpRequest

logger = logging.getLogger(__name__)


@csrf_exempt
@login_not_required
@require_POST
def acme_webhook(request: HttpRequest) -> HttpResponse:
    """Receive, verify and enqueue an Acme webhook."""
    try:
        verify_signature(
            request.body,
            request.headers.get("Acme-Signature", ""),
            settings.ACME_WEBHOOK_SECRETS,
        )
    except InvalidSignatureError as exc:
        logger.warning("Rejected Acme webhook: %s", exc)
        return HttpResponseBadRequest()

    try:
        envelope = WebhookEnvelope.model_validate_json(request.body)
    except ValidationError:
        logger.warning("Malformed Acme webhook payload")
        return HttpResponseBadRequest()

    with transaction.atomic():
        event, created = WebhookEvent.objects.get_or_create(
            provider="acme",
            event_id=envelope.id,
            defaults={
                "event_type": envelope.type,
                "payload": envelope.model_dump(mode="json"),
            },
        )
        if created:
            transaction.on_commit(lambda: process_webhook_event.enqueue(event_id=event.pk))

    return HttpResponse()
```

Rules:

- **`csrf_exempt` is required and safe here** — the signature, not a cookie, is the
  credential. `login_not_required` is needed if `LoginRequiredMiddleware` is enabled
  (see `docs/authentication.md#login-by-default`).
- **Return 200 for duplicates** (`created` is `False`) — the provider is retrying an
  event you already have.
- **Return 200 for event types you do not handle.** A non-2xx makes the provider retry
  (and eventually disable the endpoint). Filter irrelevant types in the task, or
  unsubscribe from them in the provider dashboard.
- **Return 400 for bad signatures and malformed envelopes** with an empty body — do
  not explain why to the caller. Log the reason at `WARNING`.
- **Enqueue with `transaction.on_commit`** so the task never runs before the
  `WebhookEvent` row is committed.
- Do not log full payloads or signature headers — they may contain personal data or
  enough to replay a request.

## Processing in a task

```python
# my_package/billing/tasks.py
import logging

from django.db import transaction
from django.tasks import task
from django.utils import timezone

from my_package.billing.models import Invoice, WebhookEvent
from my_package.billing.webhooks.schemas import InvoicePaidData

logger = logging.getLogger(__name__)


@task
def process_webhook_event(*, event_id: int) -> None:
    """Apply a recorded webhook event. Safe to run more than once."""
    with transaction.atomic():
        event = WebhookEvent.objects.select_for_update().get(pk=event_id)
        if event.status != WebhookEvent.Status.PENDING:
            return

        match event.event_type:
            case "invoice.paid":
                data = InvoicePaidData.model_validate(event.payload["data"])
                Invoice.objects.filter(
                    external_id=data.invoice_id,
                    paid__isnull=True,
                ).update(paid=event.payload["created"])
                event.status = WebhookEvent.Status.PROCESSED
            case _:
                event.status = WebhookEvent.Status.IGNORED

        event.processed = timezone.now()
        event.save(update_fields=["status", "processed"])
```

Rules:

- **Handlers must be idempotent.** Even with the unique constraint, write updates so
  that applying the same event twice is a no-op (`paid__isnull=True` above).
- **Events can arrive out of order.** Do not assume `created` precedes `updated`.
  Compare the event's timestamp (or a provider version field) against what is stored,
  and skip older events.
- **Do not trust the payload for anything security-sensitive.** For high-value events
  (payments, plan changes), re-fetch the object from the provider's API with the
  client patterns in `docs/integrating-apis.md` before acting on it.
- Pass only the event's primary key to the task — task arguments must be
  JSON-serializable, and the row is the source of truth.
- If processing raises, let the exception propagate so the task backend records the
  failure and Sentry reports it. Mark the event `FAILED` from a management command or
  admin action when you give up on retries, rather than swallowing errors in the task.

## Local development

Providers cannot reach `localhost`. Use the provider's CLI forwarder if it has one
(e.g. `stripe listen --forward-to`), or a tunnel such as
[`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
or `ngrok`. Configure the test-mode signing secret in `.env`.

## Testing

Build real signatures in tests rather than mocking `verify_signature`. A small helper
keeps tests readable:

```python
# my_package/billing/tests/webhooks/test_views.py
import hashlib
import hmac
import json
import time

import pytest
from django.urls import reverse

from my_package.billing.models import WebhookEvent

SECRET = "whsec_test"  # noqa: S105


def signed_post(client, payload: dict, *, secret: str = SECRET, timestamp: int | None = None):
    body = json.dumps(payload).encode()
    ts = int(time.time()) if timestamp is None else timestamp
    digest = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return client.post(
        reverse("billing_webhooks:acme"),
        body,
        content_type="application/json",
        headers={"Acme-Signature": f"t={ts},v1={digest}"},
    )


@pytest.fixture(autouse=True)
def _webhook_secret(settings):
    settings.ACME_WEBHOOK_SECRETS = [SECRET]


EVENT = {
    "id": "evt_123",
    "type": "invoice.paid",
    "created": "2026-01-01T00:00:00Z",
    "data": {"invoice_id": "in_1", "customer_id": "cus_1", "amount": 1000, "currency": "eur"},
}


@pytest.mark.django_db
class TestAcmeWebhook:
    def test_valid(self, client, django_capture_on_commit_callbacks, mocker):
        enqueue = mocker.patch("my_package.billing.webhooks.views.process_webhook_event.enqueue")
        with django_capture_on_commit_callbacks(execute=True):
            response = signed_post(client, EVENT)
        assert response.status_code == 200
        event = WebhookEvent.objects.get(provider="acme", event_id="evt_123")
        enqueue.assert_called_once_with(event_id=event.pk)

    def test_duplicate_is_accepted_once(self, client, django_capture_on_commit_callbacks, mocker):
        enqueue = mocker.patch("my_package.billing.webhooks.views.process_webhook_event.enqueue")
        with django_capture_on_commit_callbacks(execute=True):
            signed_post(client, EVENT)
            response = signed_post(client, EVENT)
        assert response.status_code == 200
        assert WebhookEvent.objects.count() == 1
        enqueue.assert_called_once()

    def test_wrong_secret(self, client):
        response = signed_post(client, EVENT, secret="wrong")
        assert response.status_code == 400
        assert not WebhookEvent.objects.exists()

    def test_stale_timestamp(self, client):
        response = signed_post(client, EVENT, timestamp=int(time.time()) - 3600)
        assert response.status_code == 400

    def test_no_secrets_configured(self, client, settings):
        settings.ACME_WEBHOOK_SECRETS = []
        response = signed_post(client, EVENT)
        assert response.status_code == 400
```

Test the task directly with `.call()`, which runs it synchronously without a backend:

```python
# my_package/billing/tests/test_tasks.py
@pytest.mark.django_db
def test_process_is_idempotent():
    event = WebhookEventRecipe.make(event_type="invoice.paid", payload=EVENT)
    process_webhook_event.call(event_id=event.pk)
    process_webhook_event.call(event_id=event.pk)
    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.PROCESSED
```

Cover, per provider:

- Valid delivery → 200, event recorded, task enqueued once.
- Duplicate delivery → 200, no second row, no second task.
- Wrong secret, stale timestamp, missing header, no secrets configured → 400.
- Unhandled event type → task marks it `IGNORED`.
- Running the task twice has the same effect as running it once.
