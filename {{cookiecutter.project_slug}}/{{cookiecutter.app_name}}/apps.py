from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "{{cookiecutter.package_name}}"
    default_auto_field = "django.db.models.BigAutoField"
