# Channels, SSE & WebSockets

Real-time patterns for pushing data from the server to the browser.

## Contents

- [Choosing a Pattern](#choosing-a-pattern)
- [Server-Sent Events with LISTEN/NOTIFY](#server-sent-events-with-listennotify)
- [WebSockets with Django Channels](#websockets-with-django-channels)
- [Testing](#testing)
- [HTMX Integration](#htmx-integration)

## Choosing a Pattern

| Need | Pattern | Extra packages |
| ---- | ------- | -------------- |
| One-way push (notifications, live feed, progress) | SSE + psycopg LISTEN/NOTIFY | none |
| Bidirectional messaging (chat, collaborative editing) | WebSockets + Django Channels | `channels`, `channels-redis` |

Start with SSE — it is simpler, works over standard HTTP, and needs no extra
dependencies. Only reach for WebSockets when you need the client to send
messages back over the same connection.

## Server-Sent Events with LISTEN/NOTIFY

PostgreSQL LISTEN/NOTIFY delivers lightweight pub/sub over the existing database
connection. Pair it with an async SSE view to push events to the browser.

### Publishing a notification

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

### Async SSE view

```python
import asyncio
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

### Browser: connecting with the HTMX SSE extension

See [HTMX Integration — SSE](#sse) below.

For a plain JavaScript fallback:

```javascript
const source = new EventSource("/sse/notifications/");
source.addEventListener("notification", (e) => {
    const data = JSON.parse(e.data);
    // update the DOM
});
```

## WebSockets with Django Channels

For bidirectional real-time communication, use
[`channels`](https://channels.readthedocs.io/) with
[`channels-redis`](https://pypi.org/project/channels-redis/) as the channel
layer. Redis is already in the stack.

### Install

```bash
uv add channels channels-redis
```

### Settings

```python
# config/settings.py

INSTALLED_APPS = [
    ...
    "channels",
]

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL")],
        },
    },
}
```

### ASGI application

Update `config/asgi.py` to route WebSocket connections:

```python
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from my_app.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": URLRouter(websocket_urlpatterns),
    }
)
```

Uvicorn already supports WebSockets — no need to switch to Daphne.

### Routing

Create `my_app/routing.py`:

```python
from django.urls import path

from my_app.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<room_name>/", ChatConsumer.as_asgi()),
]
```

### Consumer

```python
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group, self.channel_name
        )

    async def receive_json(self, content):
        await self.channel_layer.group_send(
            self.room_group,
            {"type": "chat.message", "message": content["message"]},
        )

    async def chat_message(self, event):
        await self.send_json({"message": event["message"]})
```

### Sending from outside a consumer

Use the channel layer from any Django code (views, tasks, signals):

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_to_room(room_name: str, message: str) -> None:
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_name}",
        {"type": "chat.message", "message": message},
    )
```

## Testing

### SSE views

Test the SSE view like any async Django view. Use `AsyncClient` and iterate
over the streaming response:

```python
import pytest

from django.test import AsyncClient


@pytest.mark.django_db
async def test_sse_notifications(mocker):
    mock_notifies = mocker.patch(
        "my_app.views.psycopg.AsyncConnection.connect"
    )
    # ... set up mock to yield test notifications

    client = AsyncClient()
    response = await client.get("/sse/notifications/")
    assert response["Content-Type"] == "text/event-stream"
```

For integration tests, publish a real NOTIFY in the test database and verify
the view yields the expected SSE event.

### WebSocket consumers

Django Channels provides `WebsocketCommunicator` for testing consumers
without a real server. Use the in-memory channel layer in tests:

Add the channel layer override to the existing `_settings_overrides` fixture
in `my_package/tests/fixtures.py` (see `docs/Testing.md`):

```python
@pytest.fixture(autouse=True)
def _settings_overrides(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    }
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
```

```python
import pytest
from channels.testing import WebsocketCommunicator

from my_app.consumers import ChatConsumer


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_chat_consumer_sends_message():
    communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(),
        "/ws/chat/lobby/",
    )
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({"message": "hello"})
    response = await communicator.receive_json_from()
    assert response["message"] == "hello"

    await communicator.disconnect()
```

Key points:

- Use `InMemoryChannelLayer` in tests — no Redis dependency needed.
- Always call `communicator.disconnect()` to avoid leaked connections.
- `WebsocketCommunicator` does not run routing — pass the consumer class
  directly. To test routing, use `channels.testing.ChannelsLiveServerTestCase`.
- For authenticated WebSocket tests, set `communicator.scope["user"]` before
  calling `connect()`.

## HTMX Integration

Both SSE and WebSockets integrate with HTMX via dedicated extensions. See
`docs/HTMX.md` → [Extensions](HTMX.md#extensions) for how to vendor and load
them.

| Pattern | Extension | `vendors.json` key |
| ------- | --------- | ------------------ |
| SSE | [`htmx-ext-sse`](https://htmx.org/extensions/sse/) | `htmx-ext-sse` |
| WebSockets | [`htmx-ext-ws`](https://htmx.org/extensions/ws/) | `htmx-ext-ws` |

### SSE

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

### WebSockets

Add the `htmx-ext-ws` extension, then use `ws-connect` to open a connection and
`ws-send` on a form to transmit data:

```html
<div hx-ext="ws" ws-connect="/ws/chat/lobby/">
    <div id="chat-messages">
        <!-- incoming messages swapped here by id -->
    </div>
    <form ws-send>
        <input name="message" type="text" autocomplete="off">
        <button type="submit">Send</button>
    </form>
</div>
```

The server must return HTML fragments with an `id` attribute — the extension
swaps content by matching element IDs (out-of-band swap):

```python
async def chat_message(self, event):
    html = f'<div id="chat-messages" hx-swap-oob="beforeend"><p>{event["message"]}</p></div>'
    await self.send(text_data=html)
```

Customize the WebSocket constructor (e.g. to add subprotocols):

```javascript
htmx.createWebSocket = function(url) {
    return new WebSocket(url, ["wss"]);
};
```

### References

- [HTMX SSE extension](https://htmx.org/extensions/sse/)
- [HTMX WebSocket extension](https://htmx.org/extensions/ws/)
- [Django Channels docs](https://channels.readthedocs.io/)
- [psycopg NOTIFY docs](https://www.psycopg.org/psycopg3/docs/advanced/async.html#asynchronous-notifications)
