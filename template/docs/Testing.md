# Testing

This project uses pytest with pytest-django for unit tests and Playwright for E2E tests.

## Test Configuration

```ini
# playwright.ini (for E2E tests)
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
asyncio_mode = auto
addopts = -v -x --tb=short -p no:warnings --browser chromium -m e2e
testpaths = my_package
env =
    DJANGO_ALLOW_ASYNC_UNSAFE=true
    USE_CONNECTION_POOL=false
    USE_COLLECTSTATIC=false
    USE_HTTPS=false
    USE_X_FORWARDED_HOST=false
```

```python
# pyproject.toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
asyncio_mode = "auto"
addopts = [
    "-v", "-x", "-p no:warnings", "--ff",
    "--cov", "--reuse-db", "--cov-fail-under=100",
]
markers = ["e2e: end-to-end browser tests with Playwright"]
```

## Running Tests

```bash
just test                      # Unit tests
just test my_package/users  # Specific module
just tw                        # Watch mode
just test-e2e                  # E2E tests (headless)
just test-e2e-headed          # E2E tests (visible browser)
just playwright-install       # Install Chromium for E2E
```

## Test Structure

Tests are colocated with modules:

```
my_package/
    users/
        models.py
        views.py
        tests/
            __init__.py
            fixtures.py
            factories.py
            test_models.py
            test_views.py
            test_playwright.py
```

## Root conftest.py

```python
# conftest.py
pytest_plugins = [
    "my_package.tests.fixtures",
    "my_package.tests.e2e_fixtures",
    "my_package.users.tests.fixtures",
]
```

## Unit Test Fixtures

```python
# my_package/tests/fixtures.py
import pytest
from my_package.users.tests.factories import UserFactory

@pytest.fixture
def user():
    return UserFactory()
```

## E2E Fixtures

```python
# my_package/tests/e2e_fixtures.py
import pytest
from playwright.sync_api import Page

@pytest.fixture
def e2e_user(transactional_db):
    """Verified user for e2e tests."""
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
```

## Factories

```python
# my_package/users/tests/factories.py
from factory import django
from factory.declarations import Sequence
from my_package.users.models import User

class UserFactory(django.DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: f"user-{n}")
    email = Sequence(lambda n: f"user-{n}@example.com")
    password = django.Password("testpass")
```

## Unit Tests

```python
# my_package/users/tests/test_models.py
import pytest

@pytest.mark.django_db
class TestUser:
    def test_name_returns_first_name(self):
        user = UserFactory(first_name="Alice")
        assert user.name == "Alice"
```

## View Tests with HTMX

```python
# my_package/tests/test_views.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestHome:
    def test_home_view(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_htmx_request(self, client):
        response = client.get(
            reverse("home"),
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
```

## E2E Tests

```python
# my_package/tests/test_playwright.py
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_home_page(page: Page, live_server):
    page.goto(f"{live_server.url}/")
    expect(page.locator("h1")).to_contain_text("Welcome")
```

## Test Settings

```python
# my_package/tests/fixtures.py
@pytest.fixture(autouse=True)
def _settings_overrides(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    }
    settings.TASKS = {
        "default": {"BACKEND": "django.tasks.backends.dummy.DummyBackend"}
    }
    settings.ALLOWED_HOSTS = ["testserver", "localhost"]
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
```

## Mocking

Mock at system boundaries only — never mock private methods.

**Rule: do not mock private functions or methods** (names starting with `_`). They are implementation
details. If you need to control behaviour inside a private method, either:

- Intercept the external call the private method makes (HTTP, filesystem, DB), or
- Refactor the private method/function into a public one if it genuinely needs independent testing.

| Boundary type          | Tool                           |
| ---------------------- | ------------------------------ |
| Async HTTP (`aiohttp`) | `aioresponses`                 |
| Any callable/module    | `pytest-mock` (`mocker.patch`) |

```python
# BAD: mocks a private implementation detail
def test_version_check(mocker):
    mocker.patch("my_package.management.commands.sync_vendors._latest_github_version",
                 return_value="2.0.0")
    call_command("sync_vendors", "--check")

# GOOD: intercept the HTTP call the private method makes
from aioresponses import aioresponses

def test_version_check():
    with aioresponses() as m:
        m.get("https://api.github.com/repos/owner/repo/releases/latest",
              payload={"tag_name": "v2.0.0"})
        call_command("sync_vendors", "--check")

# GOOD: mock at a public module boundary
def test_external_api(mocker):
    mock = mocker.patch("my_package.client.get_data")
    mock.return_value = {"result": "mocked"}
    # test logic
```

## Coverage

Coverage is reported on every test run (`--cov-report=term-missing`). The 100% gate is commented out in `pyproject.toml` by default - enable it when the project is mature:

```toml
# pyproject.toml
addopts = [
    ...
    "--cov-fail-under=100",  # uncomment to enforce
]
```

## E2E Selector Rules

Page-wide positional selectors (`[x-data] button`, `.relative button`) match the
first element in DOM order, which is usually a navbar or layout component rather
than the one you intend. This makes tests fragile and hard to debug.

**Rules:**

1. **Scope to the component root.** Always start the locator chain from the
   component's stable `id` or `data-component` attribute (see `docs/Alpine.md`).

2. **Prefer semantic selectors.** Use `get_by_role` with a `name`, `get_by_label`,
   or `get_by_text` rather than CSS class paths.

3. **Avoid `.first()` and `.nth()` unless the element is genuinely a sequence.**
   If you reach for `.first()` to disambiguate, it means your selector is too broad
   — add a scope ancestor instead. When `.first()` is genuinely appropriate (e.g.
   the first item in a list), add a comment explaining why.

```python
# BAD: matches the first button on the entire page
page.locator("[x-data] .relative button").first.click()

# GOOD: scoped to the specific component
upload = page.locator("#file-upload")
upload.get_by_role("button", name="Remove file").click()

# GOOD: when targeting a list item, scope to the list then the item
file_list = page.locator("#file-upload [data-file-list]")
file_list.get_by_role("button", name="Remove file").first.click()
# .first() here is intentional — removing the first file from the list
```

## Troubleshooting

### Playwright E2E tests fail with "Target closed" or SIGTRAP on Linux

If Playwright browser launches suddenly start failing, check whether `/tmp` is full:

```bash
df -h /tmp
du -sh /tmp/* 2>/dev/null | sort -rh | head -20
```

On distributions that mount `/tmp` as a tmpfs (e.g. Fedora), pytest temp directories
(`/tmp/pytest-of-$USER`) can grow to fill the available space. Playwright needs `/tmp`
for browser profile directories and downloads.

**Fix:** Remove stale pytest temp files:

```bash
rm -rf /tmp/pytest-of-$USER
```

Then retry `uv run playwright install` if browser binaries were also cleared.

## When to Use E2E vs Unit Tests

**Use E2E (Playwright) for:**

- JavaScript interactivity (Alpine.js)
- HTMX swapping behavior
- Multi-page flows
- Browser-specific behavior

**Use Unit Tests for:**

- Django view logic
- Model methods
- Form validation
- API responses
