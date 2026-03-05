import pytest
from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
class TestIndex:
    def test_get(self, client):
        response = client.get(reverse("index"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestAbout:
    def test_get(self, client):
        response = client.get(reverse("about"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestPrivacy:
    def test_get(self, client):
        response = client.get(reverse("privacy"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestRobots:
    def test_get(self, client):
        response = client.get(reverse("robots"))
        assert response.status_code == 200
        assert b"User-Agent" in response.content

    def test_post_not_allowed(self, client):
        response = client.post(reverse("robots"))
        assert response.status_code == 405


@pytest.mark.django_db
class TestSecurity:
    def test_get(self, client):
        response = client.get(reverse("security"))
        assert response.status_code == 200
        assert b"Contact:" in response.content

    def test_post_not_allowed(self, client):
        response = client.post(reverse("security"))
        assert response.status_code == 405


@pytest.mark.django_db
class TestAcceptCookies:
    def test_post(self, client):
        response = client.post(reverse("accept_cookies"))
        assert response.status_code == 200
        assert settings.GDPR_COOKIE_NAME in response.cookies

    def test_get_not_allowed(self, client):
        response = client.get(reverse("accept_cookies"))
        assert response.status_code == 405
