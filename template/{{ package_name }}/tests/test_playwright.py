"""E2E tests for site-wide page behaviour."""

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

if TYPE_CHECKING:
    from playwright.sync_api import Page

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def test_no_content_security_policy_violations(page: Page, live_server):
    """Scripts on the base template run under the Content-Security-Policy."""
    console: list[str] = []
    # Playwright inspects the handler signature, so leave it unannotated
    page.on("console", lambda message: console.append(message.text))
    page.goto(f"{live_server.url}{reverse('index')}")
    page.wait_for_load_state("networkidle")
    assert [text for text in console if "Content Security Policy" in text] == []
