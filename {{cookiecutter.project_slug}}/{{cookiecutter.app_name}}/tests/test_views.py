import pytest
from django.conf import settings
from django.urls import reverse


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
