"""E2E tests for user authentication workflows."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_login_valid_credentials(page: Page, e2e_user, live_server):
    login_url = f"{live_server.url}{reverse('account_login')}"
    page.goto(login_url)
    page.locator('[name="login"]').fill(e2e_user.username)
    page.locator('[name="password"]').fill("testpass")
    page.get_by_role("button", name="Sign In").click()
    home_url = f"{live_server.url}{reverse('home')}"
    page.wait_for_url(home_url)
    expect(page).to_have_url(home_url)


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_login_invalid_credentials(page: Page, e2e_user, live_server):
    login_url = f"{live_server.url}{reverse('account_login')}"
    page.goto(login_url)
    page.locator('[name="login"]').fill(e2e_user.username)
    page.locator('[name="password"]').fill("wrongpassword")
    page.get_by_role("button", name="Sign In").click()
    expect(page).to_have_url(login_url)
    expect(page.get_by_role("button", name="Sign In")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_unauthenticated_redirect_to_login(page: Page, live_server):
    """Protected pages redirect unauthenticated visitors to the login page."""
    page.goto(f"{live_server.url}{reverse('account_email')}")
    expect(page).to_have_url(re.compile(r"/account/login/"))


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_logout(auth_page: Page, live_server):
    auth_page.get_by_role("button", name="Sign out").click()
    expect(auth_page.get_by_role("link", name="Sign in")).to_be_visible()
