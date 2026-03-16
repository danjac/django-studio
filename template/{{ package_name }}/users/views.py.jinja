from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from {{ package_name }}.users.gdpr import anonymise_user

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect


@require_http_methods(["GET", "HEAD", "DELETE"])
@login_required
def delete_account(request: HttpRequest) -> TemplateResponse | HttpResponseRedirect:
    if request.method == "DELETE":
        anonymise_user(request.user)
        logout(request)
        messages.success(request, _("Your account has been deleted."))
        return redirect("index")
    return TemplateResponse(request, "account/delete_account.html")
