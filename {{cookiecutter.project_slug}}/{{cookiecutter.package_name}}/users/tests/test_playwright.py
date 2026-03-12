"""E2E tests for user authentication workflows."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def test_login_valid_credentials(page: Page, e2e_user, live_server):
    login_url = f"{live_server.url}{reverse('account_login')}"
    page.goto(login_url)
    page.locator('[name="login"]').fill(e2e_user.username)
    page.locator('[name="password"]').fill("testpass")
    page.get_by_role("button", name="Sign In").click()
    home_url = f"{live_server.url}{reverse('index')}"
    page.wait_for_url(home_url)
    expect(page).to_have_url(home_url)


def test_login_invalid_credentials(page: Page, e2e_user, live_server):
    login_url = f"{live_server.url}{reverse('account_login')}"
    page.goto(login_url)
    page.locator('[name="login"]').fill(e2e_user.username)
    page.locator('[name="password"]').fill("wrongpassword")
    page.get_by_role("button", name="Sign In").click()
    expect(page).to_have_url(login_url)
    expect(page.get_by_role("button", name="Sign In")).to_be_visible()


def test_unauthenticated_redirect_to_login(page: Page, live_server):
    """Protected pages redirect unauthenticated visitors to the login page."""
    page.goto(f"{live_server.url}{reverse('account_email')}")
    expect(page).to_have_url(re.compile(r"/account/login/"))


def test_logout(auth_page: Page, e2e_user, live_server):
    auth_page.get_by_role("button", name=e2e_user.username).click()
    auth_page.get_by_role("button", name="Sign out").click()
    expect(auth_page.get_by_role("link", name="Sign in")).to_be_visible()
