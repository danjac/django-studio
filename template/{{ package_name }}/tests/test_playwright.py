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


def test_no_content_security_policy_violations_after_htmx_swap(page: Page, live_server):
    """Swapping in a whole page doesn't run the base template's scripts again."""
    console: list[str] = []
    page.on("console", lambda message: console.append(message.text))
    index_url = f"{live_server.url}{reverse('index')}"
    page.goto(index_url)
    page.evaluate(
        """url => new Promise(resolve => {
            document.addEventListener("htmx:after:swap", resolve, {once: true});
            htmx.ajax("GET", url, {target: "body"});
        })""",
        index_url,
    )
    page.wait_for_load_state("networkidle")
    assert [text for text in console if "Content Security Policy" in text] == []


def test_preserved_stylesheet_survives_htmx_swap(page: Page, live_server, settings):
    """A stylesheet inside an hx-preserve element still applies after a swap.

    htmx moves hx-preserve elements with moveBefore(), and Chromium drops a
    moved <link> stylesheet. The debug toolbar's root is hx-preserve.
    """
    settings.DEBUG = True
    settings.INTERNAL_IPS = ["127.0.0.1"]
    index_url = f"{live_server.url}{reverse('index')}"
    preserved = (
        '<div id="e2e-preserved" hx-preserve>'
        f'<link rel="stylesheet" href="{settings.STATIC_URL}admin/css/base.css"></div>'
    )
    applied = """() => [...document.styleSheets].some(
        sheet => sheet.ownerNode?.parentElement?.id === "e2e-preserved"
    )"""

    page.goto(index_url)
    # Add the element to the page and to the swapped-in response.
    page.evaluate(
        """html => {
            document.body.insertAdjacentHTML("beforeend", html);
            document.addEventListener("htmx:after:request", (evt) => {
                const ctx = evt.detail.ctx;
                ctx.text = ctx.text.replace("</body>", `${html}</body>`);
            });
        }""",
        preserved,
    )
    page.wait_for_function(applied, timeout=5000)

    page.evaluate(
        """url => new Promise(resolve => {
            document.addEventListener("htmx:after:swap", resolve, {once: true});
            htmx.ajax("GET", url, {target: "body"});
        })""",
        index_url,
    )

    assert page.locator("#e2e-preserved").count() == 1
    page.wait_for_function(applied, timeout=5000)
