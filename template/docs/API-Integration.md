# API Integration

Patterns for validating data from external HTTP APIs and third-party services.
For HTML form input validation, see `docs/Django-Forms.md`.
For raw request parameter validation in views, see `docs/Django-Views.md`.

## Contents

- [Pydantic for External APIs](#pydantic-for-external-apis)

## Pydantic for External APIs

Use Pydantic when validating structured data from external sources: third-party API
responses, internal service payloads, webhook bodies, or any schema too complex for
manual parsing.

```python
from pydantic import BaseModel, ValidationError


class WeatherResponse(BaseModel):
    temperature: float
    condition: str
    humidity: int


async def fetch_weather(city: str) -> WeatherResponse:
    client = get_http_client()
    response = await client.get(f"/weather/{city}")
    response.raise_for_status()
    try:
        return WeatherResponse.model_validate(response.json())
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
