from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Final

from django.conf import settings
from django.http import HttpResponse{% if cookiecutter.use_pwa == 'y' %}, JsonResponse{% endif %}
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.http import require_POST, require_safe

from {{cookiecutter.package_name}}.http.response import TextResponse

if TYPE_CHECKING:
    from {{cookiecutter.package_name}}.http.request import HttpRequest

_CACHE_TIMEOUT: Final = 60 * 60 * 24 * 365

_cache_control = cache_control(max_age=_CACHE_TIMEOUT, immutable=True, public=True)
_cache_page = cache_page(_CACHE_TIMEOUT)


@require_safe
def index(request: HttpRequest) -> TemplateResponse:
    """Landing page."""
    return TemplateResponse(request, "home.html")


@require_safe
def about(request: HttpRequest) -> TemplateResponse:
    """About page."""
    return TemplateResponse(
        request,
        "about.html",
        {
            "contact_email": settings.CONTACT_EMAIL,
        },
    )


@require_safe
def privacy(request: HttpRequest) -> TemplateResponse:
    """Renders Privacy page."""
    return TemplateResponse(
        request,
        "privacy.html",
        {
            "contact_email": settings.CONTACT_EMAIL,
        },
    )


@require_safe
@_cache_control
@_cache_page
def robots(_) -> TextResponse:
    """Serve robots.txt."""
    return TextResponse(
        "\n".join(
            [
                "User-Agent: *",
                *[f"Allow: {reverse(name)}$" for name in ["index", "about"]],
                "Disallow: /",
            ]
        ),
    )


@require_safe
@_cache_control
@_cache_page
def security(_) -> TextResponse:
    """Serve .well-known/security.txt."""
    return TextResponse(f"Contact: mailto:{settings.CONTACT_EMAIL}")


@require_POST
def accept_cookies(_: HttpRequest) -> HttpResponse:
    """Set the GDPR consent cookie and return an empty 200 response.

    The HTMX ``hx-swap="delete"`` attribute on the cookie banner button
    removes the banner element from the DOM on success.
    """
    response = HttpResponse()
    response.set_cookie(
        settings.GDPR_COOKIE_NAME,
        value="true",
        expires=timezone.now() + datetime.timedelta(days=365),
        secure=settings.USE_HTTPS,
        httponly=True,
        samesite="Lax",
    )
    return response
{% if cookiecutter.use_pwa == 'y' %}


@require_safe
@_cache_control
@_cache_page
def manifest(request: HttpRequest) -> JsonResponse:
    """Serve PWA manifest.json."""
    pwa = settings.PWA_CONFIG
    return JsonResponse(
        {
            "background_color": pwa["background_color"],
            "description": pwa["description"],
            "dir": "ltr",
            "display": "minimal-ui",
            "id": "?homescreen=1",
            "lang": "en",
            "name": request.site.name,
            "orientation": "any",
            "prefer_related_applications": False,
            "scope": reverse("index"),
            "short_name": request.site.name[:12],
            "start_url": reverse("index"),
            "theme_color": pwa["theme_color"],
        }
    )


@require_safe
@_cache_control
@_cache_page
def assetlinks(_) -> JsonResponse:
    """Serve PWA .well-known/assetlinks.json."""
    pwa = settings.PWA_CONFIG["assetlinks"]
    return JsonResponse(
        [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": pwa["package_name"],
                    "sha256_cert_fingerprints": pwa["sha256_fingerprints"],
                },
            }
        ],
        safe=False,
    )
{%- endif %}
