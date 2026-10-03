# Server-Sent Events

One-way push from server to browser using PostgreSQL LISTEN/NOTIFY over an
async streaming view.

## Contents

- [When to use SSE](#when-to-use-sse)
- [How it fits together](#how-it-fits-together)
- [Publishing a notification](#publishing-a-notification)
- [The broker](#the-broker)
- [Async SSE view](#async-sse-view)
- [Local development](#local-development)
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

## How it fits together

Each worker process holds **one** LISTEN connection, shared by every open
stream in that process. A broker task reads notifications from it and puts
each payload on the queues of the streams that should receive it. An open
stream costs an `asyncio.Queue`, not a Postgres connection, so the number of
open browser tabs does not count against `max_connections`.

All notifications go on one channel, and the payload carries the recipient's
user ID. The broker routes on that ID, so each user receives only their own
events.

NOTIFY is not durable: a notification sent while a stream is disconnected is
lost. Treat events as signals to re-fetch state from a normal view (see
[Reacting to named events](#reacting-to-named-events)), not as the data itself.

## Publishing a notification

From Python (e.g. inside a django-tasks background task or a signal handler):

```python
# my_package/notifications/sse.py
import json

from django.db import connection

CHANNEL = "notifications"


def send_notification(user_id: int, data: str) -> None:
    payload = json.dumps({"user_id": user_id, "data": data})
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_notify(%s, %s)", [CHANNEL, payload])
```

This runs on Django's own database connection. Inside a transaction, Postgres
delivers the notification only when the transaction commits, so listeners never
see an event for a row that was rolled back. Keep payloads small (the limit is
8000 bytes); send an ID and let the client fetch the rest.

Or from SQL (e.g. in a trigger):

```sql
SELECT pg_notify(
    'notifications',
    json_build_object('user_id', NEW.user_id, 'data', 'new_comment')::text
);
```

## The broker

```python
# my_package/notifications/sse.py
import asyncio
import contextlib
import json
import logging
from collections import defaultdict
from collections.abc import AsyncIterator

import psycopg
from psycopg import sql

from django.conf import settings

logger = logging.getLogger(__name__)


class Broker:
    """Fan one LISTEN connection per process out to per-stream queues."""

    def __init__(self) -> None:
        self._queues: defaultdict[int, set[asyncio.Queue[str]]] = defaultdict(set)
        self._task: asyncio.Task[None] | None = None

    @contextlib.asynccontextmanager
    async def subscribe(self, user_id: int) -> AsyncIterator[asyncio.Queue[str]]:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._listen())
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        self._queues[user_id].add(queue)
        try:
            yield queue
        finally:
            self._queues[user_id].discard(queue)
            if not self._queues[user_id]:
                del self._queues[user_id]

    def dispatch(self, payload: str) -> None:
        message = json.loads(payload)
        for queue in self._queues.get(message["user_id"], ()):
            # A stalled client drops events rather than blocking everyone else.
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(message["data"])

    async def _listen(self) -> None:
        while True:
            try:
                async with await psycopg.AsyncConnection.connect(
                    settings.DATABASE_URL,
                    autocommit=True,
                ) as conn:
                    await conn.execute(
                        sql.SQL("LISTEN {}").format(sql.Identifier(CHANNEL))
                    )
                    async for notify in conn.notifies():
                        self.dispatch(notify.payload)
            except psycopg.OperationalError:
                logger.exception("SSE listener lost its connection; reconnecting")
                await asyncio.sleep(1)


broker = Broker()
```

The listener starts with the first subscriber and reconnects if Postgres drops
the connection. The module-level `broker` is one instance per process, which
is one per event loop under the Uvicorn workers that production runs (see
`docs/docker.md`).

## Async SSE view

```python
# my_package/notifications/views.py
import asyncio

from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse
from django.views.decorators.cache import never_cache

from my_package.http.request import AuthenticatedHttpRequest
from my_package.notifications.sse import broker

HEARTBEAT_SECONDS = 20


@login_required
@never_cache
async def sse_notifications(request: AuthenticatedHttpRequest) -> StreamingHttpResponse:
    user = await request.auser()

    async def event_stream():
        async with broker.subscribe(user.pk) as queue:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), HEARTBEAT_SECONDS)
                except TimeoutError:
                    # A comment line keeps proxies from closing an idle stream.
                    yield ": ping\n\n"
                    continue
                yield f"event: notification\ndata: {data}\n\n"

    return StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
```

Use `await request.auser()`, not `request.user`: reading `request.user` in an
async view runs a synchronous database query and raises
`SynchronousOnlyOperation`.

When the browser disconnects, the server cancels the generator, and the
`async with` block removes its queue from the broker.

Register the view in `urls.py`:

```python
from django.urls import path

from my_package.notifications.views import sse_notifications

urlpatterns = [
    path("sse/notifications/", sse_notifications, name="sse-notifications"),
]
```

### Browser: plain JavaScript fallback

```javascript
const source = new EventSource("/sse/notifications/");
source.addEventListener("notification", (e) => {
    // e.data is the string passed to send_notification()
    // update the DOM
});
```

## Local development

`just serve` runs Django's WSGI `runserver`, which buffers async streaming
responses until they finish, so an SSE stream never reaches the browser. Add
Daphne as an ASGI-capable `runserver`, as described in
[Local development server](channels.md#local-development-server) in `docs/channels.md`.

## Testing

### Gotchas

**Do not use `AsyncClient` for SSE views.** Django's test client (both sync
and async) fully consumes streaming responses internally. An endless SSE
stream will hang the test forever.

**`AsyncRequestFactory` requests have no `auser()`.** It is added by
`AuthenticationMiddleware`, which the request factory does not run. Set
`request.auser` yourself; `login_required` then passes as well.

### Recommended pattern

Test routing on the broker directly, without a database connection. Test the
auth redirect with the **sync client** (works fine for async views). Test the
stream by calling the view with `AsyncRequestFactory` and reading the first
chunk:

```python
# my_package/notifications/tests/test_sse.py
import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from my_package.notifications import views
from my_package.notifications.sse import Broker


@pytest.fixture
def broker(mocker):
    broker = Broker()
    mocker.patch.object(broker, "_listen", new=AsyncMock())
    mocker.patch.object(views, "broker", broker)
    return broker


class TestBroker:
    async def test_routes_to_recipient_only(self, broker):
        async with broker.subscribe(1) as mine, broker.subscribe(2) as theirs:
            broker.dispatch(json.dumps({"user_id": 1, "data": "hello"}))
            assert mine.get_nowait() == "hello"
            assert theirs.empty()

    async def test_unsubscribe_removes_queue(self, broker):
        async with broker.subscribe(1):
            pass
        broker.dispatch(json.dumps({"user_id": 1, "data": "hello"}))
        assert not broker._queues


@pytest.mark.django_db
class TestSseView:
    def test_anonymous_redirected(self, client):
        response = client.get("/sse/notifications/")
        assert response.status_code == 302

    async def test_yields_sse_event(self, user, broker, async_rf):
        request = async_rf.get("/")
        request.auser = AsyncMock(return_value=user)
        response = await views.sse_notifications(request)
        assert response["Content-Type"] == "text/event-stream"

        stream = aiter(response.streaming_content)
        first = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)  # let the view subscribe
        broker.dispatch(json.dumps({"user_id": user.pk, "data": "hello"}))
        assert await first == b"event: notification\ndata: hello\n\n"
```

## HTMX Integration

Vendor the `htmx-ext-sse` extension (see `docs/htmx.md` → Extensions for how
to vendor and load it; `vendors.json` key: `htmx-ext-sse`).

In htmx 4 the extension uses `hx-sse:connect` — there is no `hx-ext` declaration,
and `sse-swap` has been removed. The two remaining behaviours are:

- **Unnamed messages** (`data:` with no `event:` line) are swapped into the
  connecting element using its own `hx-target` / `hx-swap`.
- **Named events** (`event: notification`) are dispatched as DOM events on the
  connecting element, carrying `event.detail.data` and `event.detail.id`. They
  are never swapped directly — use `hx-trigger` or `hx-on:` to react to them.

### Swapping unnamed messages

```html
<div hx-sse:connect="{% url 'sse-notifications' %}"
     hx-target="#notifications"
     hx-swap="afterbegin">
</div>

<div id="notifications">
    <p>Waiting for notifications...</p>
</div>
```

The server sends the HTML fragment with no event name:

```
data: <p>New comment on your post</p>

```

### Reacting to named events

The view in "Async SSE view" above sends `event: notification`. Named events
bubble from the connecting element, so a sibling can re-fetch a rendered
partial when one arrives:

```html
<div hx-sse:connect="{% url 'sse-feed' %}"></div>

<div id="notifications"
     hx-get="{% url 'notifications-list' %}"
     hx-trigger="notification from:body"
     hx-target="this">
</div>
```

This is usually the better pattern for anything non-trivial: the server pushes
a bare signal and the markup is still rendered by a normal Django view.

To handle the payload in JavaScript instead, use `hx-on:`:

```html
<div hx-sse:connect="{% url 'sse-progress' %}"
     hx-on:progress="this.textContent = JSON.parse(event.detail.data).percent + '%'">
</div>
```

Close the connection when the server sends a specific event:

```html
<div hx-sse:connect="{% url 'sse-progress' %}"
     hx-sse:close="complete">
</div>
```

### References

- [HTMX SSE extension](https://four.htmx.org/extensions/hx-sse/)
- [psycopg NOTIFY docs](https://www.psycopg.org/psycopg3/docs/advanced/async.html#asynchronous-notifications)
