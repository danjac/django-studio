Write one or more Playwright E2E tests that cover a described user interaction.

Read `docs/Testing.md` before writing any test.

**Step 1 — Gather requirements**

**Parsing arguments:** Check whether the first word of $ARGUMENTS matches an
existing app directory under `<package_name>/`. If it does, treat it as
`<app_name>` and the remainder as the description. If it does not match any
app, treat the entire input as the description and leave `<app_name>` unset.

If the description is missing or too vague to act on, ask:

> Describe the interaction to test. Include: what the user does, what page they
> start on, and what the expected outcome is (URL change, visible text, element
> state, etc.).

If `<app_name>` could not be determined from the first word, ask which app the
test file should live in — or confirm it is a top-level test (see Step 2).

Then ask if not clear from the description:

**Authentication** — does this interaction require a logged-in user?
(`auth_page` fixture) or is it accessible anonymously? (`page` fixture)

Do not write any code until you have the description and auth requirement.

---

**Step 2 — Identify the test file**

The target file is:

```
<package_name>/<app_name>/tests/test_playwright.py
```

- If it already exists, append new tests to it.
- If it does not exist, create it with this header:

  ```python
  """E2E tests for <app_name>."""

  import pytest
  from playwright.sync_api import Page, expect

  pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]
  ```

  Then register the shared fixtures plugin in `conftest.py` if not already
  present:

  ```python
  "<package_name>.tests.e2e_fixtures",
  ```

---

**Step 3 — Write the test(s)**

Name each test `test_<what_happens>` using snake_case. One interaction =
one test function.

**Signature:**

```python
# Unauthenticated interaction:
def test_<name>(page: Page, live_server):

# Authenticated interaction:
def test_<name>(auth_page: Page, e2e_user, live_server):
```

**Navigation** — always use `reverse()` to build URLs:

```python
from django.urls import reverse

page.goto(f"{live_server.url}{reverse('<url_name>')}")
```

**Locators** — prefer semantic selectors in this order:

| Priority | Method | Example |
|---|---|---|
| 1 | Role + name | `page.get_by_role("button", name="Submit")` |
| 2 | Label | `page.get_by_label("Email address")` |
| 3 | Placeholder | `page.get_by_placeholder("Search…")` |
| 4 | Text | `page.get_by_text("Welcome back")` |
| 5 | `name` attribute | `page.locator('[name="login"]')` |

Avoid CSS class selectors and XPath. Never use `page.wait_for_timeout()` —
Playwright's `expect()` auto-waits.

**Assertions** — always use `expect()`, never plain `assert`:

```python
expect(page).to_have_url(expected_url)
expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
expect(page.get_by_text("Saved successfully")).to_be_visible()
expect(page.get_by_role("link", name="Sign in").first).to_be_visible()
```

**HTMX interactions** — clicks and form submits that trigger HTMX swaps
require no special handling; `expect()` auto-waits for the DOM update.

**AlpineJS dropdowns** — if a target element is inside an `x-show` block,
click the trigger first:

```python
page.get_by_role("button", name=e2e_user.username).click()
page.get_by_role("button", name="Sign out").click()
```

**Full example:**

```python
def test_user_submits_form_and_sees_success(auth_page: Page, e2e_user, live_server):
    auth_page.goto(f"{live_server.url}{reverse('myapp:create')}")
    auth_page.get_by_label("Title").fill("My item")
    auth_page.get_by_role("button", name="Save").click()
    expect(auth_page.get_by_text("Item created.")).to_be_visible()
```

---

**Step 4 — Verify**

```bash
just test-e2e
```

If any test fails due to a missing CSS rule (e.g. `x-cloak` not working
because Tailwind is uncompiled), remind the user to run:

```bash
just dj tailwind build
```

before re-running the E2E suite.

---

## Help

**djstudio create-e2e [<app_name>] <description>**

Writes Playwright E2E tests for a described user interaction.

Asks for authentication requirement (logged-in vs anonymous) if not clear from
the description. Creates or appends to `test_playwright.py` in the app's tests
directory.

Examples:
  /djstudio create-e2e store "user adds product to cart and checks out"
  /djstudio create-e2e "user resets their password"
