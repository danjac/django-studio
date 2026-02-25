from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from health_check.views import HealthCheckView

from {{cookiecutter.app_name}} import views

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("robots.txt", views.robots, name="robots"),
    path(".well-known/security.txt", views.security, name="security"),
    path("accept-cookies/", views.accept_cookies, name="accept_cookies"),
    path("", include("{{cookiecutter.app_name}}.users.urls")),
    path("account/", include("allauth.urls")),
    path(
        "ht/live/",
        HealthCheckView.as_view(checks=["health_check.Database"]),
        name="health_check_live",
    ),
    path(
        "ht/ready/",
        HealthCheckView.as_view(
            checks=[
                "health_check.Cache",
                "health_check.Database",
            ]
        ),
        name="health_check_ready",
    ),
    path(settings.ADMIN_URL, admin.site.urls),
]

if "django_browser_reload" in settings.INSTALLED_APPS:  # pragma: no cover
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

if "debug_toolbar" in settings.INSTALLED_APPS:  # pragma: no cover
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
