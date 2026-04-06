# WebSockets with Django Channels

Bidirectional real-time communication using
[`channels`](https://channels.readthedocs.io/) with
[`channels-redis`](https://pypi.org/project/channels-redis/) as the channel
layer. Redis is already in the stack.

For one-way server push (notifications, live feeds, progress bars), use SSE
instead — see `docs/sse.md`.

## Contents

- [Choosing a Pattern](#choosing-a-pattern)
- [Install](#install)
- [Local development server](#local-development-server)
- [Settings](#settings)
- [ASGI application](#asgi-application)
- [Routing](#routing)
- [Consumer](#consumer)
- [Sending from outside a consumer](#sending-from-outside-a-consumer)
- [Testing](#testing)
- [HTMX Integration](#htmx-integration)

## Choosing a Pattern

| Need | Pattern | Extra packages |
| ---- | ------- | -------------- |
| One-way push (notifications, live feed, progress) | SSE + psycopg LISTEN/NOTIFY — see `docs/sse.md` | none |
| Bidirectional messaging (chat, collaborative editing) | WebSockets + Django Channels | `channels`, `channels-redis` |

## Install

```bash
uv add channels channels-redis
```

## Local development server

Django's built-in `runserver` does not support WebSockets. In local development,
[Daphne](https://github.com/django/daphne) replaces it with an ASGI-capable
version that handles WebSocket connections.

Add `daphne` as a **dev-only** dependency and prepend it to `INSTALLED_APPS`
when `DEBUG=True`. Daphne takes over `runserver` automatically — no changes to
`just serve` are needed.

```bash
uv add --dev daphne
```

```python
# config/settings.py
if DEBUG:
    # Daphne replaces runserver with an ASGI-capable version for WebSocket support.
    # Dev-only dependency — must be first in INSTALLED_APPS.
    INSTALLED_APPS = ["daphne", *INSTALLED_APPS]
```

In production the ASGI server (gunicorn + uvicorn workers or similar) handles
WebSockets natively — `daphne` is not added to `INSTALLED_APPS` there.

## Settings

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

## ASGI application

Update `config/asgi.py` to route WebSocket connections:

```python
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from my_app.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
```

`AuthMiddlewareStack` populates `scope["user"]` from the session cookie so
consumers can access `self.scope["user"]` without additional auth setup.

## Routing

Create `my_app/routing.py`:

```python
from django.urls import path

from my_app.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<room_name>/", ChatConsumer.as_asgi()),
]
```

## Consumer

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

## Sending from outside a consumer

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

Django Channels provides `WebsocketCommunicator` for testing consumers
without a real server. Use the in-memory channel layer in tests:

Add the channel layer override to the existing `_settings_overrides` fixture
in `my_package/tests/fixtures.py` (see `docs/testing.md`):

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

Vendor the `htmx-ext-ws` extension (see `docs/htmx.md` → Extensions for how
to vendor and load it; `vendors.json` key: `htmx-ext-ws`).

Use `ws-connect` to open a connection and `ws-send` on a form to transmit data:

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

### Clearing the input after send (Alpine + htmx-ext-ws)

After a `ws-send` form submits, use the `htmx:ws-after-send` event to clear
the input. htmx dispatches events in both camelCase (`htmx:wsAfterSend`) and
kebab-case (`htmx:ws-after-send`); use the kebab-case form with Alpine because
the camelCase version contains a colon that confuses Alpine's `x-on:` directive
parser.

Add `x-data` for Alpine scope and `@htmx:ws-after-send` on the form:

```html
<form
  x-data
  ws-send
  @submit.prevent
  @htmx:ws-after-send="$refs.input.value = ''"
>
  <input x-ref="input" type="text" name="text_data" autocomplete="off">
  <button type="submit">Send</button>
</form>
```

Do **not** clear the input on `@submit.prevent` — Alpine fires before htmx
reads the form values, which sends an empty payload over the WebSocket.

### References

- [HTMX WebSocket extension](https://htmx.org/extensions/ws/)
- [Django Channels docs](https://channels.readthedocs.io/)
