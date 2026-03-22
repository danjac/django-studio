# API Integration

Patterns for validating data from external HTTP APIs and third-party services.
For HTML form input validation, see `docs/Django-Forms.md`.
For raw request parameter validation in views, see `docs/Django-Views.md`.

## Contents

- [aiohttp HTTP Client](#aiohttp-http-client)
- [Pydantic for External APIs](#pydantic-for-external-apis)
- [Testing](#testing)

## aiohttp HTTP Client

Use `aiohttp` for async HTTP calls to third-party APIs. Never use it in synchronous
views — only in `async def` views or background tasks.

Define a shared `USER_AGENT` string in `config/settings.py`:

```python
# config/settings.py
USER_AGENT = "my-project/1.0"
```

Always use the session as a context manager so it is closed on exit:

```python
import aiohttp
from django.conf import settings


async def fetch_weather(city: str) -> dict:
    async with aiohttp.ClientSession(headers={"User-Agent": settings.USER_AGENT}) as client:
        async with client.get(f"https://api.example.com/weather/{city}") as resp:
            resp.raise_for_status()
            return await resp.json()
```

`raise_for_status()` raises `aiohttp.ClientResponseError` on 4xx/5xx — always call
it before reading the response body. Wrap the call site in `try/except` if you need
to handle specific status codes gracefully:

```python
import aiohttp
from django.conf import settings


async def fetch_data(url: str) -> dict | None:
    try:
        async with aiohttp.ClientSession(headers={"User-Agent": settings.USER_AGENT}) as client:
            async with client.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return None
        raise
    except aiohttp.ClientError as exc:
        raise RuntimeError(f"HTTP request failed: {url}") from exc
```

## Pydantic for External APIs

Use Pydantic when validating structured data from external sources: third-party API
responses, internal service payloads, webhook bodies, or any schema too complex for
manual parsing.

```python
import aiohttp
from django.conf import settings
from pydantic import BaseModel, ValidationError


class WeatherResponse(BaseModel):
    temperature: float
    condition: str
    humidity: int


async def fetch_weather(city: str) -> WeatherResponse:
    async with aiohttp.ClientSession(headers={"User-Agent": settings.USER_AGENT}) as client:
        async with client.get(f"https://api.example.com/weather/{city}") as resp:
            resp.raise_for_status()
            try:
                return WeatherResponse.model_validate(await resp.json())
            except ValidationError as exc:
                raise ValueError(f"Unexpected weather API response: {exc}") from exc
```

Rules:

- Define a `BaseModel` for every external schema you consume — do not key into raw
  dicts.
- Always wrap `.model_validate()` in `try/except ValidationError` and re-raise with
  context so callers know what operation failed.
- Do not use Pydantic for HTML form input — that is Django forms' job.
- See `docs/Packages.md` for the install command and basedpyright configuration.

## Testing

Use `aioresponses` to mock `aiohttp` calls. Always mock at the public module boundary
(the URL), never the internal session methods.

```python
from aioresponses import aioresponses


def test_fetch_weather():
    with aioresponses() as m:
        m.get(
            "https://api.example.com/weather/london",
            payload={"temperature": 12.5, "condition": "cloudy", "humidity": 80},
        )
        result = fetch_weather("london")  # call via asyncio.run or pytest-asyncio
        assert result.temperature == 12.5
```

For `async` test functions, mark with `@pytest.mark.asyncio` (from `pytest-asyncio`):

```python
import pytest
from aioresponses import aioresponses


@pytest.mark.asyncio
async def test_fetch_weather_not_found():
    with aioresponses() as m:
        m.get("https://api.example.com/weather/nowhere", status=404)
        result = await fetch_weather_or_none("nowhere")
        assert result is None
```

Always test both the happy path and error cases (404, 500, network failure).
