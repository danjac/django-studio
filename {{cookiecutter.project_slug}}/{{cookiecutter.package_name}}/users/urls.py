from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

package_name = "users"

urlpatterns: list[URLPattern | URLResolver] = []
