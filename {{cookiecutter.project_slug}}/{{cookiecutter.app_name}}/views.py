import datetime

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from {{cookiecutter.app_name}}.http.request import HttpRequest


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
        secure=True,
        httponly=True,
        samesite="Lax",
    )
    return response
