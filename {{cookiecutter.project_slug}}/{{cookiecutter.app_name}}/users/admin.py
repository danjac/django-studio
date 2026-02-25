from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from {{cookiecutter.app_name}}.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User model admin."""

    fieldsets = (
        *tuple(BaseUserAdmin.fieldsets or ()),
        (
            "Preferences",
            {
                "fields": ("send_email_notifications",),
            },
        ),
    )
