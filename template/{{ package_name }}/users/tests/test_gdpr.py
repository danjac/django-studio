"""Tests for GDPR right-to-erasure functionality."""

from __future__ import annotations

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.urls import reverse

from {{ package_name }}.users.gdpr import anonymise_user
from {{ package_name }}.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestAnonymiseUser:
    def test_pii_fields_cleared(self):
        user = UserFactory(
            first_name="Alice",
            last_name="Smith",
        )
        original_pk = user.pk
        anonymise_user(user)
        user.refresh_from_db()
        assert user.username == f"deleted-{original_pk}"
        assert user.email == f"deleted-{original_pk}@example.invalid"
        assert user.first_name == ""
        assert user.last_name == ""

    def test_account_deactivated(self):
        user = UserFactory()
        anonymise_user(user)
        user.refresh_from_db()
        assert not user.is_active
        assert not user.has_usable_password()

    def test_email_addresses_deleted(self):
        user = UserFactory()
        EmailAddress.objects.create(user=user, email=user.email, verified=True)
        anonymise_user(user)
        assert not EmailAddress.objects.filter(user=user).exists()

    def test_social_accounts_deleted(self):
        user = UserFactory()
        SocialAccount.objects.create(user=user, provider="google", uid="123")
        anonymise_user(user)
        assert not SocialAccount.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestDeleteAccountView:
    def test_get(self, client, auth_user):
        response = client.get(reverse("users:delete_account"))
        assert response.status_code == 200

    def test_delete_anonymises_user_and_logs_out(self, client, auth_user):
        pk = auth_user.pk
        response = client.delete(
            reverse("users:delete_account"),
            HTTP_X_CSRFTOKEN=client.cookies.get("csrftoken", ""),
        )
        assert response.status_code == 302
        assert response["Location"] == reverse("index")
        auth_user.refresh_from_db()
        assert not auth_user.is_active
        assert auth_user.email == f"deleted-{pk}@example.invalid"
        # Session cleared — subsequent request is anonymous
        response = client.get(reverse("index"))
        assert response.wsgi_request.user.is_anonymous

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get(reverse("users:delete_account"))
        assert response.status_code == 302
        assert "login" in response["Location"]

    def test_unauthenticated_delete_redirects_to_login(self, client):
        response = client.delete(reverse("users:delete_account"))
        assert response.status_code == 302
        assert "login" in response["Location"]
