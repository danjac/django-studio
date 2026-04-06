# Server-Sent Events

One-way push from server to browser using PostgreSQL LISTEN/NOTIFY over an
async streaming view.

## Contents

- [When to use SSE](#when-to-use-sse)
- [Publishing a notification](#publishing-a-notification)
- [Async SSE view](#async-sse-view)
- [Testing](#testing)
- [HTMX Integration](#htmx-integration)

## When to use SSE

| Need | Pattern |
| ---- | ------- |
| One-way push (notifications, live feed, progress) | SSE + psycopg LISTEN/NOTIFY |
| Bidirectional messaging (chat, collaborative editing) | WebSockets — see `docs/channels.md` |

Start with SSE — it is simpler, works over standard HTTP, and needs no extra
dependencies. Only reach for WebSockets when you need the client to send
messages back over the same connection.

## Publishing a notification

From Python (e.g. inside a django-tasks background task or a signal handler):

```python
import psycopg
from psycopg import sql

from django.conf import settings


def send_notification(channel: str, payload: str) -> None:
    with psycopg.connect(settings.DATABASE_URL) as conn:
        conn.execute(
            sql.SQL("NOTIFY {}, {}").format(
                sql.Identifier(channel),
                sql.Literal(payload),
            )
        )
```

Or from raw SQL (e.g. in a trigger):

```sql
NOTIFY new_comment, '{"comment_id": 42}';
```

## Async SSE view

```python
import psycopg

from django.conf import settings
from django.http import StreamingHttpResponse
from django.views.decorators.cache import never_cache


@never_cache
async def sse_notifications(request):
    async def event_stream():
        conn = await psycopg.AsyncConnection.connect(
            settings.DATABASE_URL,
            autocommit=True,
        )
        try:
            await conn.execute("LISTEN notifications")
            gen = conn.notifies()
            async for notify in gen:
                yield (
                    f"event: notification\n"
                    f"data: {notify.payload}\n\n"
                )
        finally:
            await conn.close()

    return StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
```

Register the view in `urls.py`:

```python
from django.urls import path

from my_app.views import sse_notifications

urlpatterns = [
    path("sse/notifications/", sse_notifications, name="sse-notifications"),
]
```

### Browser: plain JavaScript fallback

```javascript
const source = new EventSource("/sse/notifications/");
source.addEventListener("notification", (e) => {
    const data = JSON.parse(e.data);
    // update the DOM
});
```

## Testing

### Gotchas

**Do not use `AsyncClient` for SSE views.** Django's test client (both sync
and async) fully consumes streaming responses internally. An SSE async
generator that blocks on `conn.notifies()` will hang the test forever — even
with a mock that yields a finite number of items.

**`RequestFactory` requests lack middleware attributes.** Decorators like
`login_required` call `request.auser()`, which is added by
`AuthenticationMiddleware`. Neither `RequestFactory` nor `AsyncRequestFactory`
run middleware, so calling the decorated view directly raises
`AttributeError`. Use `view.__wrapped__` to skip `login_required` and set
`request.user` manually.

### Recommended pattern

Test the auth redirect with the **sync client** (works fine for async views).
Test streaming behaviour by calling the **unwrapped view function** directly
with `AsyncRequestFactory`:

```python
from unittest.mock import AsyncMock, MagicMock

import pytest

from my_app.views import sse_notifications


@pytest.fixture
def _mock_async_pg(mocker):
    async def fake_notifies():
        yield MagicMock(payload='{"count": 1}')

    mock_conn = AsyncMock()
    mock_conn.notifies = fake_notifies
    mocker.patch(
        "my_app.views.psycopg.AsyncConnection.connect",
        new=AsyncMock(return_value=mock_conn),
    )


@pytest.mark.django_db
class TestSseView:
    def test_anonymous_redirected(self, client):
        response = client.get("/sse/notifications/")
        assert response.status_code == 302

    async def test_returns_event_stream(self, user, _mock_async_pg, async_rf):
        request = async_rf.get("/")
        request.user = user
        # Skip login_required — no middleware on request factory
        response = await sse_notifications.__wrapped__(request)
        assert response["Content-Type"] == "text/event-stream"

    async def test_yields_sse_events(self, user, _mock_async_pg, async_rf):
        request = async_rf.get("/")
        request.user = user
        response = await sse_notifications.__wrapped__(request)
        content = b"".join([chunk async for chunk in response.streaming_content])
        assert b"event: notification" in content
```

## HTMX Integration

Vendor the `htmx-ext-sse` extension (see `docs/htmx.md` → Extensions for how
to vendor and load it; `vendors.json` key: `htmx-ext-sse`).

Use `sse-connect` and `sse-swap` to subscribe to server events and swap content
into the DOM:

```html
<div hx-ext="sse" sse-connect="{% url 'sse-notifications' %}" sse-swap="notification">
    <!-- replaced with each incoming event -->
    <p>Waiting for notifications...</p>
</div>
```

The server must send events with a matching event name:

```
event: notification
data: <p>New comment on your post</p>

```

Multiple event types on one connection:

```html
<div hx-ext="sse" sse-connect="{% url 'sse-feed' %}">
    <div sse-swap="comment">No comments yet</div>
    <div sse-swap="like">No likes yet</div>
</div>
```

Use `hx-trigger="sse:<event>"` to fire an HTTP request when an event arrives
(instead of swapping the event data directly):

```html
<div hx-ext="sse" sse-connect="{% url 'sse-feed' %}">
    <div hx-get="{% url 'notifications-list' %}"
         hx-trigger="sse:refresh"
         hx-target="#notifications">
    </div>
</div>
```

Close the connection when the server sends a specific event:

```html
<div hx-ext="sse"
     sse-connect="{% url 'sse-progress' %}"
     sse-swap="progress"
     sse-close="complete">
</div>
```

### References

- [HTMX SSE extension](https://htmx.org/extensions/sse/)
- [psycopg NOTIFY docs](https://www.psycopg.org/psycopg3/docs/advanced/async.html#asynchronous-notifications)
