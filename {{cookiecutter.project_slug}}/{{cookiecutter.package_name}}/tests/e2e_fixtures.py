from typing import TYPE_CHECKING

import pytest
from allauth.account.models import EmailAddress
from django.urls import reverse

from {{cookiecutter.package_name}}.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.fixture
def e2e_user(transactional_db):
    """Verified user for E2E tests."""
    user = UserFactory()
    EmailAddress.objects.create(user=user, email=user.email, verified=True)
    return user


@pytest.fixture
def auth_page(page: Page, e2e_user, live_server) -> Page:
    """Playwright page authenticated as e2e_user."""
    login_url = f"{live_server.url}{reverse('account_login')}"
    page.goto(login_url)
    page.locator('[name="login"]').fill(e2e_user.username)
    page.locator('[name="password"]').fill("testpass")
    page.get_by_role("button", name="Sign In").click()
    return page
