import pytest

from {{cookiecutter.package_name}}.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUser:
    def test_name_returns_first_name(self):
        user = UserFactory(first_name="Alice")
        assert user.name == "Alice"

    def test_name_falls_back_to_username(self):
        user = UserFactory(first_name="")
        assert user.name == user.username
