from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from {{cookiecutter.package_name}}.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User model admin."""

