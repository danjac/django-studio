import pytest
from django.conf import settings
from django.urls import reverse


class TestIndex:
    @pytest.mark.django_db
    def test_get(self, client):
        response = client.get(reverse("index"))
        assert response.status_code == 200


class TestAbout:
    @pytest.mark.django_db
    def test_get(self, client):
        response = client.get(reverse("about"))
        assert response.status_code == 200


class TestRobots:
    @pytest.mark.django_db
    def test_get(self, client):
        response = client.get(reverse("robots"))
        assert response.status_code == 200
        assert b"User-Agent" in response.content

    @pytest.mark.django_db
    def test_post_not_allowed(self, client):
        response = client.post(reverse("robots"))
        assert response.status_code == 405


class TestSecurity:
    @pytest.mark.django_db
    def test_get(self, client):
        response = client.get(reverse("security"))
        assert response.status_code == 200
        assert b"Contact:" in response.content

    @pytest.mark.django_db
    def test_post_not_allowed(self, client):
        response = client.post(reverse("security"))
        assert response.status_code == 405


class TestAcceptCookies:
    @pytest.mark.django_db
    def test_post(self, client):
        response = client.post(reverse("accept_cookies"))
        assert response.status_code == 200
        assert settings.GDPR_COOKIE_NAME in response.cookies

    @pytest.mark.django_db
    def test_get_not_allowed(self, client):
        response = client.get(reverse("accept_cookies"))
        assert response.status_code == 405
