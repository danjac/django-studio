from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "{{cookiecutter.package_name}}.users"
    default_auto_field = "django.db.models.BigAutoField"
