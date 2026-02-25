from django.template.response import TemplateResponse
from django.views.decorators.http import require_safe

from {{cookiecutter.app_name}}.http.request import HttpRequest


@require_safe
def home(request: HttpRequest) -> TemplateResponse:
    """Home page."""
    return TemplateResponse(request, "home.html")
