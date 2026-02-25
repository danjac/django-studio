from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "{{cookiecutter.app_name}}"
    default_auto_field = "django.db.models.BigAutoField"
