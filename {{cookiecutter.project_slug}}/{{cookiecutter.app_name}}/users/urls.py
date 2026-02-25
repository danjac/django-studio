from django.urls import path

from {{cookiecutter.app_name}}.users import views

app_name = "users"

urlpatterns = [
    path("", views.home, name="home"),
]
