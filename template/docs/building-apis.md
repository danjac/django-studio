# Building APIs

Patterns for exposing this project's own JSON API — to external clients (mobile apps,
partner integrations, scripts) or to in-page JavaScript where HTMX is not a good fit.

For **consuming** third-party APIs, see `docs/integrating-apis.md`; for receiving
third-party webhooks, see `docs/webhooks.md`.
For HTML views, see `docs/django-views.md` and `docs/htmx.md`.

## Contents

- [When to Build an API](#when-to-build-an-api)
- [Approach](#approach)
- [Layout and URLs](#layout-and-urls)
- [Schemas](#schemas)
- [Error Responses](#error-responses)
- [The api Decorator](#the-api-decorator)
- [Views](#views)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [Pagination](#pagination)
- [CORS](#cors)
- [Rate Limiting](#rate-limiting)
- [Versioning and Compatibility](#versioning-and-compatibility)
- [Testing](#testing)
- [Checklist](#checklist)

## When to Build an API

**Build a JSON API when:**

- A client outside this Django app consumes the data (mobile app, CLI, partner system).
- In-page JavaScript needs structured data rather than HTML — e.g. a chart library,
  a map, or an autocomplete widget that renders its own markup.

**Do not build a JSON API when** the page is rendered by this project and the
interaction is "fetch and swap some HTML". That is HTMX's job: return a partial from
an ordinary view (see `docs/htmx.md`). A JSON endpoint plus client-side rendering
duplicates templates, i18n, and permission checks in JavaScript.

## Approach

Use **plain function-based views + Pydantic** — the same tools used elsewhere in the
project:

- Pydantic models validate request bodies and query parameters, and define the
  response shape explicitly.
- Views return `JsonResponse`.
- A small `api` decorator converts exceptions into consistent JSON errors.

Install Pydantic and configure ruff as described in `docs/packages.md`:

```bash
uv add pydantic
```

**Start without an API framework.** For a handful of endpoints alongside a
server-rendered app, plain Django + `JsonResponse` + Pydantic covers the need with far
less machinery than Django REST Framework or django-ninja. Small, single-purpose
packages are fine when a specific need arises — CORS, rate limiting, OAuth2 — and are
called out in the relevant sections below.

A framework starts to earn its place as the API grows: many resources with repetitive
CRUD, generated OpenAPI docs for external consumers, content negotiation, or
built-in throttling and filtering. When that point comes, django-ninja is the closer
fit — it is Pydantic-native, so the schemas described here carry over. Treat it as a
deliberate decision and ask before adding one.

## Layout and URLs

Keep API code next to the app it exposes, in an `api/` package inside the app. This
keeps the API's views, schemas and routes together and separate from the app's HTML
views and URLs:

```
my_package/
    items/
        api/
            __init__.py
            schemas.py    # Pydantic request/response models
            urls.py       # API routes
            views.py      # API views
        urls.py           # HTML routes
        views.py          # HTML views
        tests/
            __init__.py
            api/
                __init__.py
                test_schemas.py
                test_views.py
            test_views.py     # HTML view tests
```

Infrastructure shared by every app's API — error responses, the `api` decorator,
request parsing, and token authentication — lives in a top-level `api` app:

```
my_package/
    api/
        __init__.py
        apps.py
        auth.py       # token_required
        http.py       # ProblemResponse, ApiError, api, parse_body, parse_query, session_required
        models.py     # ApiToken
        tests/
            __init__.py
            test_auth.py
            test_http.py
```

Add `"my_package.api"` to `INSTALLED_APPS` (it owns the `ApiToken` model) and run
`just dj makemigrations api`.

Mount all API routes under a versioned prefix in `config/urls.py`:

```python
# config/urls.py
path("api/v1/items/", include("my_package.items.api.urls")),
```

```python
# my_package/items/api/urls.py
from django.urls import path

from my_package.items.api import views

app_name = "items_api"

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("<int:pk>/", views.item_detail, name="item_detail"),
]
```

Use a separate `app_name` (`items_api`) so API URL names never collide with HTML ones.

## Schemas

Define **separate input and output models** for every resource. Never serialize a
model instance directly (`model_to_dict`, `serializers.serialize`, `__dict__`) — an
explicit output schema is what stops a new model field (or `password`) from leaking.

```python
# my_package/items/api/schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemIn(BaseModel):
    """Payload for creating or replacing an item."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    quantity: int = Field(ge=0)


class ItemPatch(BaseModel):
    """Payload for partial updates — every field optional."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    quantity: int | None = Field(default=None, ge=0)


class ItemOut(BaseModel):
    """Public representation of an item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    quantity: int
    created: datetime


class ItemListParams(BaseModel):
    """Query parameters for the item list endpoint."""

    model_config = ConfigDict(extra="forbid")

    q: str = ""
    cursor: int | None = None
    limit: int = Field(default=20, ge=1, le=100)
```

Rules:

- `extra="forbid"` on input models — unknown fields are a client bug; reject them
  with 422 rather than silently ignoring them.
- `from_attributes=True` on output models so `ItemOut.model_validate(item)` reads
  attributes from a Django model instance.
- Put constraints (`min_length`, `ge`, `le`) on the schema, not in the view.
- Business rules that need the database (uniqueness, ownership) stay in the view or
  model layer — do not run queries inside Pydantic validators.
- Serialize with `model_dump(mode="json")` so datetimes, UUIDs and Decimals become
  JSON-safe strings.

## Error Responses

Every error the API returns uses the same shape, based on
[RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457), with content type
`application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Validation failed",
  "status": 422,
  "detail": "The request body is invalid.",
  "errors": [
    {"loc": ["quantity"], "msg": "Input should be greater than or equal to 0", "type": "greater_than_equal"}
  ]
}
```

| Status | When |
| ------ | ---- |
| 400 | Malformed request — body is not valid JSON |
| 401 | Missing or invalid credentials (include `WWW-Authenticate`) |
| 403 | Authenticated, but not allowed to perform this action on a visible object |
| 404 | Object does not exist **or** the client may not see it |
| 405 | Method not allowed (handled by `require_http_methods`) |
| 409 | Conflict — e.g. duplicate unique value, stale version |
| 415 | Wrong `Content-Type` |
| 422 | Well-formed JSON that fails schema validation |
| 429 | Rate limited (include `Retry-After`) |
| 500 | Unhandled error — generic message only |

Never put exception messages, stack traces, SQL, or internal IDs in a 500 response.
Log the exception; return a generic title.

Build every error through a `ProblemResponse` — a `JsonResponse` subclass named after
the RFC's "problem details" format. It fills in `type`, `title` (the standard reason
phrase) and `status` from an `HTTPStatus`, plus optional `detail` and extension fields,
and sets the `application/problem+json` content type. For example,
`ProblemResponse(http.HTTPStatus.NOT_FOUND)` returns:

```json
{"type": "about:blank", "title": "Not Found", "status": 404}
```

`ApiError` is the exception counterpart: raise it anywhere inside a view and the `api`
decorator converts it into a `ProblemResponse`.

Add both to `my_package/api/http.py`:

```python
# my_package/api/http.py
import http
from typing import Any

from django.http import JsonResponse


class ProblemResponse(JsonResponse):
    """RFC 9457 problem details response."""

    def __init__(
        self,
        status: http.HTTPStatus,
        detail: str = "",
        **extra: Any,
    ) -> None:
        """Build a problem+json body from a status code and optional details."""
        data = {"type": "about:blank", "title": status.phrase, "status": status.value}
        if detail:
            data["detail"] = detail
        super().__init__(
            data | extra,
            status=status,
            content_type="application/problem+json",
        )


class ApiError(Exception):
    """Raise from an API view to return a specific problem response."""

    def __init__(self, status: http.HTTPStatus, detail: str = "", **extra: Any) -> None:
        """Store the problem details for the api decorator."""
        super().__init__(detail or status.phrase)
        self.status = status
        self.detail = detail
        self.extra = extra
```

## The api Decorator

One decorator translates exceptions into problem responses, so views contain only
the happy path. Add it to `my_package/api/http.py`:

```python
# my_package/api/http.py
import functools
import logging
from collections.abc import Callable

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def api(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Convert exceptions raised by an API view into problem+json responses."""

    @functools.wraps(view)
    def _wrapper(request, *args, **kwargs) -> HttpResponse:
        try:
            return view(request, *args, **kwargs)
        except ApiError as exc:
            return ProblemResponse(exc.status, exc.detail, **exc.extra)
        except ValidationError as exc:
            return ProblemResponse(
                http.HTTPStatus.UNPROCESSABLE_CONTENT,
                "The request is invalid.",
                errors=exc.errors(include_url=False, include_context=False, include_input=False),
            )
        except Http404:
            return ProblemResponse(http.HTTPStatus.NOT_FOUND)
        except PermissionDenied:
            return ProblemResponse(http.HTTPStatus.FORBIDDEN)
        except Exception:
            logger.exception("Unhandled API error in %s", view.__qualname__)
            return ProblemResponse(http.HTTPStatus.INTERNAL_SERVER_ERROR)

    return _wrapper
```

Notes:

- `include_input=False` keeps submitted values (which may include secrets) out of the
  response; `include_context=False` drops non-JSON-serializable context objects.
- `logger.exception` is captured by Sentry's logging integration, so unhandled errors
  are still reported even though the client receives JSON instead of Django's HTML 500
  page.
- Apply `api` **closest to the view function**, with the method guard and auth
  decorator above it (see [Views](#views)).

Parse JSON bodies with a helper that checks content type and syntax before Pydantic
runs:

```python
# my_package/api/http.py
from pydantic import BaseModel


def parse_body[T: BaseModel](request, schema: type[T]) -> T:
    """Validate a JSON request body against a Pydantic model."""
    if request.content_type != "application/json":
        raise ApiError(
            http.HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            "Content-Type must be application/json.",
        )
    try:
        return schema.model_validate_json(request.body)
    except ValidationError as exc:
        if any(error["type"] == "json_invalid" for error in exc.errors()):
            raise ApiError(http.HTTPStatus.BAD_REQUEST, "Malformed JSON.") from exc
        raise


def parse_query[T: BaseModel](request, schema: type[T]) -> T:
    """Validate query string parameters against a Pydantic model."""
    return schema.model_validate(request.GET.dict())
```

`request.GET.dict()` keeps only the last value for repeated keys. For list parameters
(`?tag=a&tag=b`) build the dict explicitly with `request.GET.getlist("tag")`.

## Views

```python
# my_package/items/api/views.py
import http

from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from my_package.api.http import ApiError, api, parse_body, parse_query
from my_package.http.request import AuthenticatedHttpRequest
from my_package.http.response import HttpResponseNoContent
from my_package.items.models import Item
from my_package.items.api.schemas import ItemIn, ItemListParams, ItemOut, ItemPatch
from my_package.api.auth import token_required


@require_http_methods(["GET", "POST"])
@token_required
@api
def item_list(request: AuthenticatedHttpRequest) -> JsonResponse:
    """List the user's items, or create a new one."""
    if request.method == "POST":
        payload = parse_body(request, ItemIn)
        try:
            item = Item.objects.create(owner=request.user, **payload.model_dump())
        except IntegrityError as exc:
            raise ApiError(http.HTTPStatus.CONFLICT, "An item with this name already exists.") from exc
        return JsonResponse(
            ItemOut.model_validate(item).model_dump(mode="json"),
            status=http.HTTPStatus.CREATED,
        )

    params = parse_query(request, ItemListParams)
    return paginated_response(request, Item.objects.for_owner(request.user), params)


@require_http_methods(["GET", "PATCH", "DELETE"])
@token_required
@api
def item_detail(request: AuthenticatedHttpRequest, pk: int) -> JsonResponse | HttpResponseNoContent:
    """Retrieve, update or delete a single item."""
    item = get_object_or_404(Item.objects.for_owner(request.user), pk=pk)

    if request.method == "DELETE":
        item.delete()
        return HttpResponseNoContent()

    if request.method == "PATCH":
        payload = parse_body(request, ItemPatch)
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(item, field, value)
        item.save(update_fields=[*changes, "updated"])

    return JsonResponse(ItemOut.model_validate(item).model_dump(mode="json"))
```

Rules:

- **Always restrict methods** with `require_http_methods` (or `require_safe` /
  `require_POST`), exactly as for HTML views.
- `JsonResponse` refuses non-dict top-level values by default. Always return an
  object (`{"items": [...]}`), never a bare list — it leaves room to add fields later.
- `PATCH` uses `model_dump(exclude_unset=True)` so omitted fields are left alone
  while an explicit `null` is still distinguishable.
- Keep API views **synchronous** unless they call external services; see
  `docs/django-views.md#async-views`.
- Do not return template-rendered HTML or use `messages` from API views.

## Authentication

Choose the mechanism by who the client is:

| Client | Mechanism |
| ------ | --------- |
| JavaScript on this site's own pages | Session cookie + CSRF token |
| Scripts, servers, mobile apps owned by a user | Personal API token (Bearer) |
| Third-party apps acting on behalf of users | OAuth2 — [`django-oauth-toolkit`](https://django-oauth-toolkit.readthedocs.io/) (ask first) |

Never accept passwords over the API, and never put credentials in query strings (they
end up in access logs and browser history).

### Session auth (same-origin JavaScript)

The user is already logged in via allauth, so no extra work is needed: use
`@login_required`-style checks and **keep CSRF protection on**. Send the token from
JavaScript in the `X-CSRFToken` header:

```javascript
await fetch("/api/v1/items/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
  },
  body: JSON.stringify({ name: "Widget", quantity: 1 }),
});
```

For session-authenticated API views, return 401 JSON instead of redirecting to the
login page:

```python
# my_package/api/http.py
def session_required(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Require a logged-in session user; return 401 JSON instead of redirecting."""

    @functools.wraps(view)
    def _wrapper(request, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return ProblemResponse(http.HTTPStatus.UNAUTHORIZED)
        return view(request, *args, **kwargs)

    return _wrapper
```

### Token auth (external clients)

Store tokens **hashed**, like passwords. The plaintext is shown to the user once, at
creation, and never again.

```python
# my_package/api/models.py
import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _l

TOKEN_PREFIX = "myapp_"


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest used to look up a token."""
    return hashlib.sha256(token.encode()).hexdigest()


class ApiTokenQuerySet(models.QuerySet):
    """Custom queryset for API tokens."""

    def active(self) -> "ApiTokenQuerySet":
        """Return tokens that are neither revoked nor expired."""
        return self.filter(revoked__isnull=True).filter(
            models.Q(expires__isnull=True) | models.Q(expires__gt=timezone.now())
        )


class ApiToken(models.Model):
    """A hashed personal API token belonging to a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_l("user"),
        # CASCADE: a token is owned by its user and is meaningless without them
        on_delete=models.CASCADE,
        related_name="api_tokens",
    )
    name = models.CharField(_l("name"), max_length=100)
    digest = models.CharField(max_length=64, unique=True, editable=False)
    last_used = models.DateTimeField(_l("last used"), null=True, blank=True)
    expires = models.DateTimeField(_l("expires"), null=True, blank=True)
    revoked = models.DateTimeField(_l("revoked"), null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = ApiTokenQuerySet.as_manager()

    class Meta:
        verbose_name = _l("API token")
        verbose_name_plural = _l("API tokens")

    def __str__(self) -> str:
        return self.name

    @classmethod
    def create_for(cls, user, name: str) -> tuple["ApiToken", str]:
        """Create a token and return it with the plaintext value (shown once)."""
        plaintext = TOKEN_PREFIX + secrets.token_urlsafe(32)
        token = cls.objects.create(user=user, name=name, digest=hash_token(plaintext))
        return token, plaintext
```

- `secrets.token_urlsafe(32)` gives 256 bits of entropy, so a fast unsalted SHA-256
  is sufficient — slow password hashers are unnecessary for random tokens and would
  make every request expensive.
- The recognisable prefix lets secret scanners (e.g. GitHub push protection) detect
  leaked tokens.
- Let users list, name, and revoke their tokens from their account page. Revoke by
  setting `revoked`, not deleting, so audit history survives.

The decorator:

```python
# my_package/api/auth.py
import functools
import http
from collections.abc import Callable
from datetime import timedelta

from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from my_package.api.http import ProblemResponse
from my_package.api.models import ApiToken, hash_token


def token_required(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Authenticate the request with an `Authorization: Bearer <token>` header."""

    @csrf_exempt
    @login_not_required
    @functools.wraps(view)
    def _wrapper(request, *args, **kwargs) -> HttpResponse:
        scheme, _, credentials = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not credentials:
            return _unauthorized()

        token = (
            ApiToken.objects.active()
            .select_related("user")
            .filter(digest=hash_token(credentials), user__is_active=True)
            .first()
        )
        if token is None:
            return _unauthorized()

        now = timezone.now()
        if token.last_used is None or now - token.last_used > timedelta(minutes=5):
            ApiToken.objects.filter(pk=token.pk).update(last_used=now)

        request.user = token.user
        return view(request, *args, **kwargs)

    return _wrapper


def _unauthorized() -> ProblemResponse:
    response = ProblemResponse(http.HTTPStatus.UNAUTHORIZED)
    response["WWW-Authenticate"] = 'Bearer realm="api"'
    return response
```

Security rules:

- **`csrf_exempt` is only safe because the view ignores cookies.** A token-auth view
  must never fall back to `request.user` from the session. If one endpoint must accept
  both, keep CSRF on and require the token path to be explicitly selected.
- `login_not_required` is needed when `LoginRequiredMiddleware` is enabled (see
  `docs/authentication.md#login-by-default`); otherwise API clients get a 302 to the
  login page. It is harmless when the middleware is not installed.
- Return the same 401 for "no header", "unknown token", "revoked", and "expired" — do
  not tell the client which.
- Throttle `last_used` writes (as above) so every request does not issue an `UPDATE`.
- Serve the API over HTTPS only (already enforced in production settings).

## Authorization

Authentication tells you *who*; authorization is unchanged from HTML views — follow
`docs/authorization.md`:

- **Queryset-as-gate** for fetching objects:
  `get_object_or_404(Item.objects.for_owner(request.user), pk=pk)` → 404, no
  existence leak.
- `request.user.has_perm(...)` → raise `PermissionDenied` (403) only when the object
  is already visible and you are gating a specific action.
- Never trust IDs in the request body for ownership (`owner_id`, `organization_id`) —
  derive them from `request.user` or a URL object fetched through a scoped queryset.

If tokens need narrower scopes than the user's full permissions (e.g. read-only
tokens), add a `scopes` field to `ApiToken`, store the token on `request.auth`, and
express scope checks as `django-rules` predicates so they compose with existing rules.

## Pagination

Prefer **cursor (keyset) pagination** for APIs: stable under concurrent inserts and
constant-cost at any depth. Offset pagination via Django's `Paginator` is acceptable
for small, admin-style datasets.

```python
# my_package/items/api/views.py
def paginated_response(request, queryset, params: ItemListParams) -> JsonResponse:
    """Return one page of items ordered by descending id."""
    queryset = queryset.order_by("-id")
    if params.cursor is not None:
        queryset = queryset.filter(id__lt=params.cursor)

    items = list(queryset[: params.limit + 1])
    has_next = len(items) > params.limit
    items = items[: params.limit]

    next_url = None
    if has_next:
        query = request.GET.copy()
        query["cursor"] = items[-1].id
        next_url = request.build_absolute_uri(f"{request.path}?{query.urlencode()}")

    return JsonResponse(
        {
            "items": [ItemOut.model_validate(item).model_dump(mode="json") for item in items],
            "next": next_url,
        }
    )
```

- Always cap `limit` in the schema (`le=100`) — never let a client request an
  unbounded page.
- Fetch `limit + 1` rows to know whether a next page exists without a `COUNT(*)`.
- Order by a unique column (or a tuple ending in one) so the cursor is unambiguous.
- Use `select_related` / `prefetch_related` for any relation the output schema reads —
  `from_attributes` will otherwise trigger N+1 queries.

## CORS

Only needed when **browser** JavaScript on a *different origin* calls the API. Servers,
mobile apps, and same-origin pages do not need it.

If required, add [`django-cors-headers`](https://github.com/adamchainz/django-cors-headers)
(ask first) and restrict it to the API path and known origins:

```python
# config/settings.py
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_URLS_REGEX = r"^/api/.*$"
```

Never combine `CORS_ALLOW_ALL_ORIGINS = True` with `CORS_ALLOW_CREDENTIALS = True` —
that lets any website make authenticated requests with your users' cookies.

## Rate Limiting

Public or token-authenticated APIs need rate limits to protect against abuse and
runaway clients. Options, in order of preference:

1. **At the edge** — ingress controller or CDN rate limiting, configured in
   infrastructure (see `docs/deployment.md`). No application code.
2. **In Django** — [`django-ratelimit`](https://django-ratelimit.readthedocs.io/)
   (ask first) backed by the existing Redis cache. Key on the token or user, not the
   IP, for authenticated endpoints; return a 429 `ProblemResponse` with a
   `Retry-After` header.

## Versioning and Compatibility

- Version in the URL (`/api/v1/`). Bump the major version only for breaking changes.
- **Non-breaking** (allowed within a version): adding endpoints, adding optional
  request fields, adding response fields.
- **Breaking** (requires a new version): removing or renaming fields, changing types,
  making an optional field required, changing error status codes.
- Clients must ignore unknown response fields; document this for API consumers.
- Use ISO 8601 datetimes with timezone (the default from `model_dump(mode="json")`)
  and string IDs if they could ever exceed JavaScript's safe integer range.

If you publish API docs, generate JSON Schema from the Pydantic models with
`ItemOut.model_json_schema()` rather than maintaining schemas by hand.

## Testing

Test API views through Django's test client. API tests live in a `tests/api/` package
that mirrors the `api/` package: `<app>/tests/api/test_views.py`,
`<app>/tests/api/test_schemas.py`, and so on (shared API infrastructure is tested in `my_package/api/tests/`).

```python
# my_package/items/tests/api/test_views.py
import http

import pytest
from django.urls import reverse

from my_package.items.tests.recipes import ItemRecipe
from my_package.api.models import ApiToken


@pytest.fixture
def api_token(user) -> str:
    _, plaintext = ApiToken.create_for(user, name="test")
    return plaintext


@pytest.fixture
def auth_headers(api_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_token}"}


@pytest.mark.django_db
class TestItemList:
    def test_requires_token(self, client):
        response = client.get(reverse("items_api:item_list"))
        assert response.status_code == http.HTTPStatus.UNAUTHORIZED
        assert response["Content-Type"] == "application/problem+json"
        assert response["WWW-Authenticate"].startswith("Bearer")

    def test_rejects_revoked_token(self, client, user):
        token, plaintext = ApiToken.create_for(user, name="old")
        token.revoked = token.created
        token.save()
        response = client.get(
            reverse("items_api:item_list"),
            headers={"Authorization": f"Bearer {plaintext}"},
        )
        assert response.status_code == http.HTTPStatus.UNAUTHORIZED

    def test_create(self, client, auth_headers):
        response = client.post(
            reverse("items_api:item_list"),
            {"name": "Widget", "quantity": 3},
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == http.HTTPStatus.CREATED
        assert response.json()["name"] == "Widget"

    def test_create_invalid(self, client, auth_headers):
        response = client.post(
            reverse("items_api:item_list"),
            {"name": "", "quantity": -1},
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == http.HTTPStatus.UNPROCESSABLE_CONTENT
        locs = {tuple(error["loc"]) for error in response.json()["errors"]}
        assert locs == {("name",), ("quantity",)}

    def test_create_malformed_json(self, client, auth_headers):
        response = client.post(
            reverse("items_api:item_list"),
            "{not json",
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == http.HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
class TestItemDetail:
    def test_other_users_item_is_404(self, client, auth_headers):
        item = ItemRecipe.make()  # owned by a different user
        response = client.get(
            reverse("items_api:item_detail", kwargs={"pk": item.pk}),
            headers=auth_headers,
        )
        assert response.status_code == http.HTTPStatus.NOT_FOUND
```

Passing a dict with `content_type="application/json"` makes the test client
JSON-encode the body. Use `client.patch(...)` / `client.delete(...)` the same way.

Always cover, per endpoint:

- Missing, invalid, and revoked credentials → 401.
- Another user's object → 404 (not 403, not 200).
- Schema validation failure → 422 with the expected `loc`s.
- The response body contains **only** the fields in the output schema — assert on
  `response.json().keys()` for at least one endpoint per resource.
- CSRF: for session-authenticated endpoints, test with
  `Client(enforce_csrf_checks=True)` to confirm unsafe methods are rejected without a
  token.

## Checklist

- [ ] Endpoint is needed — HTMX partial would not do.
- [ ] Routes under `/api/v1/`, separate `app_name`.
- [ ] Input schema with `extra="forbid"`; separate output schema.
- [ ] `require_http_methods` + auth decorator + `api`.
- [ ] Objects fetched through a user-scoped queryset.
- [ ] `csrf_exempt` only on token-auth views that ignore the session.
- [ ] Pagination capped; related objects preloaded.
- [ ] Tests for 401, 404-for-others, 422, and response field set.
