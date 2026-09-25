import html
import re

import pytest
from allauth.account.models import EmailAddress
from django.core.validators import validate_email
from django.urls import reverse

# Valid per EmailValidator: ', + and ` are allowed in the local part.
XSS_EMAIL = "a'+alert`1`+'@example.com"


@pytest.mark.django_db
class TestEmailView:
    def test_email_escaped_in_x_data(self, client, auth_user):
        validate_email(XSS_EMAIL)
        EmailAddress.objects.create(
            user=auth_user, email=XSS_EMAIL, verified=True, primary=True
        )
        response = client.get(reverse("account_email"))
        assert response.status_code == 200
        attrs = re.findall(r'x-data="([^"]*)"', response.content.decode())
        assert any("selected" in attr for attr in attrs)
        # The browser decodes entities before Alpine evaluates the expression.
        for attr in attrs:
            assert "'+alert" not in html.unescape(attr)
